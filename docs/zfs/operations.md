# ZFS Operations

The day-2 / day-N stuff: keeping the pool healthy, expanding it, replacing disks, monitoring. Reference material organised by task.

## The boring weekly cadence

What "running ZFS well" looks like in practice:

- **Every week**: scrub runs (scheduled). You read the report.
- **Every month**: review snapshot space; prune anything sanoid missed.
- **Every quarter**: do a real restore test from your off-host backup.
- **Whenever you change something risky**: snapshot first, work, snapshot after.

ZFS itself does the heavy lifting. Your job is mostly to read its reports.

## Scrubs

A scrub reads every allocated block in the pool, verifies its checksum, and (with redundancy) repairs anything corrupt. Run weekly.

### Manual scrub

```bash
sudo zpool scrub tank          # start
sudo zpool scrub -p tank       # pause
sudo zpool scrub -s tank       # stop / cancel

# Watch progress
sudo zpool status tank
watch -n 5 zpool status tank
```

A scrub on this build (1 TB + 4 TB pool, mostly used) takes maybe 8-20 hours depending on how full it is. It's I/O-throttled by default to not interfere with regular work, but you'll notice the disk activity.

### Schedule a weekly scrub

Ubuntu's `zfsutils-linux` package installs `zfs-scrub@.service`/`zfs-scrub@.timer` for you. Enable it on the pool:

```bash
sudo systemctl enable --now zfs-scrub-monthly@tank.timer

# Or weekly:
sudo systemctl enable --now zfs-scrub-weekly@tank.timer

# Check
systemctl list-timers | grep zfs-scrub
```

For a homelab, **monthly is fine**. For a production storage server with millions of files, weekly. The point is "regular", not "frequent".

### Reading scrub output

```bash
sudo zpool status -v tank
```

Healthy result:

```
  pool: tank
 state: ONLINE
  scan: scrub repaired 0B in 02:34:11 with 0 errors on Sun May 17 04:34:11 2026
config:
  NAME                                       STATE     READ WRITE CKSUM
  tank                                       ONLINE       0     0     0
    nvme-Samsung_SSD_990_PRO_2TB_xxx-part4   ONLINE       0     0     0
    nvme-Samsung_SSD_990_PRO_4TB_yyy         ONLINE       0     0     0
errors: No known data errors
```

Unhealthy result (one of):

- `scrub repaired X in ...` with non-zero CKSUM counts → a leaf disk had bad blocks; ZFS healed them from redundancy. **If redundancy exists**, this is "do nothing right now but watch the disk".
- `state: DEGRADED` → a vdev lost a leaf; reads work from remaining redundancy but you need to act.
- `errors: <N> data errors, see ...` → some files are permanently lost because no redundancy was available to repair them.

For the MS-S1 MAX's no-redundancy pool, any CKSUM errors are immediately problematic — there's nothing to heal from. The repair path is to identify the affected files, restore them from off-host backup, and decide whether to replace the failing disk.

## Disk replacement

Procedure for swapping a pool member (e.g. a failing drive identified by `zpool status`):

### 1. Identify the device

```bash
sudo zpool status -v tank

# What's the by-id path of the failing device?
ls -la /dev/disk/by-id/ | grep -E '(failing-serial|nvme)'
```

### 2. Offline (if it isn't already auto-offlined)

```bash
sudo zpool offline tank /dev/disk/by-id/nvme-failing-serial-part4
```

### 3. Physically replace the device

If the drive is still readable, you don't strictly have to offline it — ZFS will copy data live during `zpool replace`. If the drive is dying, offline first.

Shut down, swap, boot back up. (For the MS-S1 MAX with two M.2 slots, opening the chassis requires the slide-out tray procedure documented by Minisforum.)

### 4. Identify the new device

```bash
ls -la /dev/disk/by-id/ | grep -v part
NEW=/dev/disk/by-id/nvme-NewDrive-Serial
```

### 5. Replace

```bash
sudo zpool replace tank /dev/disk/by-id/nvme-failing-serial-part4 "$NEW"
```

ZFS starts resilvering — reconstructing the failed disk's data onto the new one. On a redundant pool, this works from the surviving redundancy. On a single-disk-vdev (no redundancy), the only source is the original device, so it had better still be readable.

### 6. Watch the resilver

```bash
sudo zpool status tank
```

You'll see `resilver in progress` with percentage and ETA. The pool stays usable throughout.

When done:

```bash
sudo zpool status tank        # state: ONLINE; resilvered Xs of YGB
```

### 7. Detach (if it was a mirror you partially replaced)

For a mirror, `zpool replace` automatically detaches the old device. For more complex topologies you might need:

```bash
sudo zpool detach tank /dev/disk/by-id/nvme-old-...-part4
```

## Expanding a pool

ZFS pools grow in two ways: **bigger disks** (replace each disk in a vdev with a bigger one, then `autoexpand` or `online -e`) and **more vdevs** (add a new top-level vdev).

### Bigger disks

If `autoexpand=on` was set at pool creation (it wasn't here; we can set it now):

```bash
sudo zpool set autoexpand=on tank
```

Then any time you replace all leaves of a vdev with bigger devices, the pool grows automatically once the last replacement finishes.

If `autoexpand=off`:

```bash
sudo zpool online -e tank /dev/disk/by-id/nvme-NewBigDrive
```

after each replacement.

### More vdevs

To add a new top-level vdev (more capacity, no redundancy change):

```bash
sudo zpool add tank /dev/disk/by-id/nvme-NewThirdDrive
```

The pool now stripes across three vdevs. **No data is rebalanced** to the new vdev — existing blocks stay where they are, only new writes go to the wider stripe. Over time the pool's stored data spreads as data churns.

To attach a mirror partner to an existing single-disk vdev:

```bash
sudo zpool attach tank /dev/disk/by-id/nvme-Existing-part4 /dev/disk/by-id/nvme-NewMirror
```

This converts the single-disk vdev into a 2-way mirror. The new disk resilvers.

### What you cannot do (mostly)

- **Cannot shrink** a pool except by removing a top-level vdev (which only works in some topologies — not raidz, mostly mirrors/stripes; the `device_removal` feature).
- **Cannot convert** a stripe of two disks into a single mirror without recreating the pool. (You can attach a mirror partner to each leaf, ending up with two mirrors that stripe — but that's two more disks, not a topology change.)
- **Cannot easily change** raidz1 to raidz2. OpenZFS 2.3+ adds `raidz_expansion` for adding a disk to an existing raidz vdev, but not for changing parity level.

## Monitoring

### `zpool status`

The most-run command. Read it carefully:

```bash
sudo zpool status -v tank
```

Key fields:

- `state`: should be ONLINE.
- `scan:`: last scrub or resilver result.
- per-device `READ WRITE CKSUM`: should all be zero. Any non-zero values are events to investigate.

Clear stale error counts after investigation:

```bash
sudo zpool clear tank
```

### `zpool iostat`

Live throughput / IOPS / latency:

```bash
sudo zpool iostat -v tank 2
sudo zpool iostat -v -l tank 2        # include latency columns
sudo zpool iostat -y -p 5 tank         # 5s samples, in bytes/units
```

### `zfs list`

Capacity overview:

```bash
zfs list
zfs list -t all                       # include snapshots
zfs list -o name,used,available,referenced,compressratio,mountpoint
```

### ARC stats

```bash
arc_summary                    # if installed
arcstat 1                      # samples ARC stats every second
cat /proc/spl/kstat/zfs/arcstats
```

The interesting numbers:

- `hits / (hits + misses)` — hit ratio. 95%+ healthy.
- `c` vs `c_max` — current target size vs upper bound. If c is at c_max and you have spare RAM, raise `zfs_arc_max`.
- `arc_meta_used` — metadata-only portion of ARC.

### Prometheus integration

`node_exporter` ships a `zfs` collector enabled by default on Linux. It exposes ARC metrics, pool IO stats, and per-dataset usage. Grafana dashboards exist on grafana.com — search for "ZFS" or "node_exporter zfs".

## Pool import/export

Exporting a pool flushes pending writes, unmounts datasets, and removes the pool from the live kernel:

```bash
sudo zpool export tank
```

Useful before:

- Physically moving disks.
- Reinstalling the host (see [Rebuild Checklist](../operations/rebuild-checklist.md)).
- Major maintenance.

Importing brings the pool back online:

```bash
# Scan for available pools
sudo zpool import

# Import a specific pool
sudo zpool import tank

# Import with options
sudo zpool import -d /dev/disk/by-id tank        # search by-id paths only
sudo zpool import -fR /mnt tank                   # force; altroot under /mnt
sudo zpool import -o readonly=on tank             # read-only (forensics)
sudo zpool import -F tank                         # rewind to a previous txg (recovery)
```

`-F` is a recovery option: try to import the pool by rewinding to an older transaction group. Use only when normal import fails. See [Troubleshooting](troubleshooting.md).

## Trim

`autotrim=on` (set at pool create) issues TRIM lazily as space is freed. You can also force:

```bash
sudo zpool trim tank
sudo zpool trim -w tank          # wait until complete
```

After a large `zfs destroy`, a manual TRIM can speed up SSD garbage collection.

Schedule monthly trim (above and beyond autotrim) only if you've measured that the drives benefit. Most NVMe behave the same with or without scheduled trims when autotrim is on.

## Pool-level capacity discipline

ZFS performance degrades as the pool fills, accelerating sharply above ~80%. Some specific points:

- Up to ~80%: linear allocation, near-best performance.
- 80-90%: ZFS switches to a slower "best-fit" allocator. Write speeds drop.
- 90%+: ZFS reserves the last few percent for system metadata; you may see write failures.

For this build, treat 80% as "alarm" and 90% as "drop everything and prune":

```bash
zfs list -o name,used,available,quota tank
```

Set up an alert in Uptime Kuma / Prometheus to ping you well before then.

## Sanity-checking metadata

```bash
# What's actually using space?
sudo zfs list -o name,used,refer,usedsnap,usedds,usedchild -t filesystem tank

# Which datasets have heavy snapshot tails?
sudo zfs list -t snapshot -o name,used,refer -s used | tail -20
```

Old snapshots that uniquely hold lots of blocks are usually the right place to prune.

## Reading errors and self-healing

When `zpool status` shows non-zero CKSUM counts on a leaf:

```bash
sudo zpool status -v tank
# config:
#   tank          ONLINE       0     0     0
#     mirror-0    ONLINE       0     0     0
#       disk1     ONLINE       0     0     0
#       disk2     ONLINE       0     0    12        <-- bad
#
# errors: No known data errors
```

This says: disk2 returned 12 checksum-bad blocks, ZFS healed them from disk1's good copies (because mirror), the data is fine. Disk2 is showing wear; **watch it**, and replace if the count grows.

```bash
# Note current counts
sudo zpool status > /tmp/status-pre.txt

# Force re-read of suspect data (scrub) to see if errors recur
sudo zpool scrub tank

# After scrub, compare
sudo zpool status -v tank
```

A scrub that doesn't repeat the errors might indicate transient I/O (cable noise, brief controller hiccup). Persistent or growing errors mean disk replacement.

## When a disk vanishes

```bash
sudo zpool status -v tank
# state: DEGRADED
#   nvme-...-part4   UNAVAIL  ...
```

Causes:

- Disk physically removed or dead.
- Cable failure / NVMe controller hiccup.
- `udev` named it something unexpected (this is why by-id paths matter).

Recovery:

```bash
# Did the kernel detect the disk under a different name?
lsblk
ls -la /dev/disk/by-id/

# If it's back under a different name:
sudo zpool clear tank
sudo zpool online tank /dev/disk/by-id/<correct-path>

# If it's gone for good:
sudo zpool replace tank /dev/disk/by-id/<old-path> /dev/disk/by-id/<new-disk>
```

## What ZFS does and doesn't tell you

ZFS surfaces:

- Pool topology and health (`zpool status`).
- Per-leaf read/write/checksum error counts.
- Scrub/resilver progress.
- Capacity per dataset.

ZFS does **not** surface:

- SMART data for the underlying disks. Use `smartctl -a /dev/nvme0n1` separately.
- NVMe wear levelling / write-amplification. Use `nvme smart-log /dev/nvme0n1`.
- Temperature. Use `sensors` or `nvme` SMART output.

A monitoring stack should pull SMART/NVMe stats independently of ZFS stats. node_exporter + a SMART exporter is the standard pattern.

## Common day-N commands cheat-sheet

```bash
# Quick pool health
sudo zpool status -v tank

# Capacity
zfs list -o name,used,avail,refer,mountpoint

# Snapshots, biggest first
zfs list -t snapshot -o name,used,refer -s used | tac | head

# Compression ratio
zfs list -o name,used,compressratio

# Force a scrub
sudo zpool scrub tank

# Force a TRIM
sudo zpool trim -w tank

# Detect bit rot historically
zpool history tank | grep -E 'scrub|repaired'

# Show all properties
zfs get all tank/foo
zpool get all tank
```

## Next steps

- [Troubleshooting](troubleshooting.md) — when things go wrong.
- [Backup & Recovery](../operations/backup.md) — replication and restore.
- [Tuning](tuning.md) — ARC, prefetch, recordsize.
