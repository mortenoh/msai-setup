# ZFS Troubleshooting

When things go wrong. Symptom-first, ordered by frequency.

## "I rebooted and the pool isn't there"

Most common cause: the `zfs-import-cache` or `zfs-mount` service didn't run, or the cache file is stale.

```bash
# Is the pool importable?
sudo zpool import           # list available pools (without importing)

# Import manually
sudo zpool import tank

# If it complains about device paths
sudo zpool import -d /dev/disk/by-id tank
```

Once imported, verify systemd unit health for next boot:

```bash
systemctl status zfs-import-cache.service zfs-mount.service zfs.target
```

If `zfs-import-cache.service` is failing because the cache file is missing/stale, regenerate it:

```bash
sudo zpool export tank
sudo zpool import tank          # re-imports and writes /etc/zfs/zpool.cache
sudo systemctl restart zfs-import-cache.service
```

If you specifically don't want a cache file (e.g. on systems with rotating disks at unstable paths):

```bash
sudo systemctl disable zfs-import-cache.service
sudo systemctl enable zfs-import-scan.service
```

The `scan` service scans all attached devices at boot instead of relying on the cache. Slower at boot but more robust.

## "zpool import says pool I/O is currently suspended"

Usually means a leaf vdev disappeared mid-operation. Status:

```bash
sudo zpool status -v
```

If the device is missing, fix the underlying issue (cable, slot, etc.). If it's there but ZFS doesn't recognise it:

```bash
sudo zpool clear tank
sudo zpool online tank <device>
```

## "zpool import fails with: a vdev is missing"

```bash
sudo zpool import
   pool: tank
     id: 1234567890123456789
  state: UNAVAIL
 status: One or more devices are missing from the system.
```

Diagnose:

- A drive is unplugged, dead, or named differently after a kernel update.
- The pool was built with kernel device names and they reordered.

Try by-id discovery:

```bash
sudo zpool import -d /dev/disk/by-id
```

If the pool was originally created with `/dev/sdb`-style names, the cache file may have stale paths. Force re-search:

```bash
sudo zpool import -d /dev/disk/by-id tank
# After successful import:
sudo zpool export tank
sudo zpool import -d /dev/disk/by-id tank   # this time writes the new cache
```

## "Pool is DEGRADED"

A vdev lost redundancy but reads/writes still work:

```bash
sudo zpool status -v tank
```

Identify the bad device and follow [Operations → Disk replacement](operations.md#disk-replacement).

For a no-redundancy pool (single-disk vdev), there's no DEGRADED state — there's only ONLINE or UNAVAIL. UNAVAIL = the pool is offline; data is unreachable until the disk comes back or is replaced (in which case you restore from backup).

## "Pool is FAULTED / UNAVAIL"

The pool can't be opened. Several flavours:

### Too many missing devices

```
state: FAULTED
status: One or more devices could not be used because the label is missing
        or invalid.  There are insufficient replicas for the pool to continue
        functioning.
```

For a redundant pool, more leaves are missing than the topology can tolerate. Find them.

For a no-redundancy pool, any leaf missing is fatal.

### Corrupted metadata

```
state: FAULTED
status: The pool metadata is corrupted and the pool cannot be opened.
```

Try rewinding to an earlier transaction group:

```bash
sudo zpool import -F tank
sudo zpool import -X tank        # more aggressive: extreme rewind
```

`-F` rolls back the last few txgs. `-X` allows discarding more state. **Both lose data** since the rewind point. Read-only first for forensics:

```bash
sudo zpool import -o readonly=on tank
```

This recovers when something corrupted the pool's recent metadata but earlier txgs were OK (rare; usually power-loss + flaky hardware).

### Hostid mismatch

```
state: ONLINE
status: ... The pool was last accessed by another system.
```

A pool was imported on a different host (`/etc/hostid`) and not cleanly exported. Force import:

```bash
sudo zpool import -f tank
```

This is normal after restoring a backup, moving disks between machines, or rebuilding the host with a different hostid.

## "I can't destroy a snapshot — dataset is busy"

Something holds it open. The two common causes:

### A clone

```bash
zfs list -t all | grep <snapshot-name>
# Or
zfs get origin <pool>
```

Destroy the clone first, or promote it (which moves the dependency).

### A hold

```bash
zfs holds <pool>/<dataset>@<snapshot>
# tag       creation
# sentinel  Sun May 17 14:23:11 2026

sudo zfs release sentinel <pool>/<dataset>@<snapshot>
```

If you don't know what set the hold, releasing it is safe — the hold mechanism is purely advisory.

## "zpool status shows checksum errors"

ZFS detected bit-flips during a scrub or normal read.

```bash
sudo zpool status -v tank
```

The `-v` output lists affected file paths if data was permanently lost (no redundancy to repair from), or just shows error counts if ZFS healed them.

Actions:

1. **Note the affected disk(s)**. The leaf vdev with non-zero CKSUM counts is the culprit. Often it's the device whose SMART data also shows issues.
2. **Check SMART** for the device:

   ```bash
   sudo smartctl -a /dev/nvme0n1
   sudo nvme smart-log /dev/nvme0n1
   ```
3. **Restore affected files from backup** if any data was unrecoverable.
4. **Replace the disk** if the error count is growing or SMART confirms the device is degrading.
5. **Clear the counters** once the underlying issue is resolved:

   ```bash
   sudo zpool clear tank
   ```

## "zfs send" or `syncoid` errors out partway

The send stream broke. The receiver may have a partial state.

```bash
# On the receiver, find the resume token
zfs get receive_resume_token backup/foo

# On the sender, resume the same stream
sudo zfs send -t <token> | ssh backup-host 'sudo zfs receive -s backup/foo'
```

This requires `-s` was passed to the original `zfs receive` (syncoid does this by default). Without `-s`, the destination doesn't know how to resume — you'd start over.

If a resume isn't possible:

```bash
# Receiver: remove the partial dataset
sudo zfs destroy backup/foo
# Sender: re-send fresh
sudo zfs send -R tank/foo@latest | ssh backup-host 'sudo zfs receive backup/foo'
```

## "zfs receive: destination already exists"

```
cannot receive new filesystem stream: destination 'backup/foo' exists
```

You can:

- `-F` to force-receive, which **destroys** any state on the destination newer than the incoming snapshot's ancestor.
- Pick a different destination.
- Manually `sudo zfs destroy -r backup/foo` first (irreversible).

`-F` is appropriate when the destination is purely a replica and the source is authoritative.

## "zfs unmount" fails with "umount: target is busy"

A process holds a file open on the dataset:

```bash
sudo lsof +D /mnt/tank/foo
sudo fuser -mv /mnt/tank/foo
```

Stop the offending process, or force the unmount:

```bash
sudo zfs unmount -f tank/foo
```

`-f` is brutal; pending writes may be lost. Prefer fixing the underlying process. Common culprits are Docker containers (`docker stop ...`), shells (`cd` out of the directory), and forgotten `tail -f` sessions.

## "zfs mount" fails with "filesystem already mounted"

ZFS thinks the dataset is mounted but `findmnt` shows it isn't, or vice versa. Recover state:

```bash
sudo zfs unmount -a
sudo zfs mount -a
```

If a directory exists at the mountpoint with non-ZFS contents, ZFS refuses to mount over it. Investigate that directory before forcing.

## "Pool is full but `df` says I have space"

ZFS reserves the last few percent of pool capacity for metadata. `zfs list` is honest about what you can use; `df` reports the underlying filesystem-like number and can mislead.

```bash
zfs list tank
# NAME   USED   AVAIL   REFER   MOUNTPOINT
# tank   4.8T   200G    ...     /mnt/tank
```

Compare with snapshot usage:

```bash
zfs list -t snapshot -o name,used,refer -s used | tail -20
```

Old snapshots that uniquely hold large amounts of data are the usual culprits. Destroy the oldest first.

## "I deleted important data; can I restore from a snapshot?"

If you have a snapshot from before the deletion:

```bash
# Find it
zfs list -t snapshot -o name,creation tank/<dataset>

# Browse it
ls /mnt/tank/<dataset>/.zfs/snapshot/<snap-name>/

# Copy a specific file back
cp /mnt/tank/<dataset>/.zfs/snapshot/<snap>/path/to/file /mnt/tank/<dataset>/path/to/file
```

If you need to roll the entire dataset back:

```bash
sudo zfs rollback -r tank/<dataset>@<snap>
```

This is irreversible — newer snapshots and changes since `<snap>` are gone.

## "send is mind-numbingly slow"

Profile:

```bash
sudo zfs send -nv tank/foo@s2                   # confirm size
sudo zfs send tank/foo@s2 | pv > /dev/null      # measure source rate
```

Common causes / fixes:

- **CPU on the SSH cipher**: switch to `chacha20-poly1305@openssh.com` (`ssh -c chacha20-poly1305@openssh.com ...`).
- **Compression already negotiated to gzip on SSH**: turn it off (`-o Compression=no`); ZFS compression already minimised what's on the wire.
- **No `-c` flag**: add `-c` to `zfs send` to keep compressed blocks compressed in transit.
- **No `-L` flag**: large datasets with `recordsize=1M` benefit from `-L`.
- **Receiving side sync writes**: ensure the receive target dataset isn't `sync=always`.
- **Network bottleneck**: `iperf3` between hosts to confirm raw throughput.

## "syncoid says it can't find a common snapshot"

The source and destination have no shared ancestor. Either:

- Use `--no-sync-snap` to retry against an existing snapshot rather than auto-creating one.
- Run with `-r --recursive` from the parent dataset.
- Recreate the destination from scratch and full-send.

## "ARC is huge / system is sluggish"

The default ARC cap is 50% of RAM — 64 GB on a 128 GB box. Cap it:

```bash
echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf
echo 17179869184 | sudo tee /sys/module/zfs/parameters/zfs_arc_max
sudo update-initramfs -u
```

See [Pool Creation → ARC](pool-creation.md#cap-the-arc-size) and [Tuning → ARC](tuning.md#arc-sizing).

## "I can't load encryption keys after a reboot"

```bash
sudo zfs load-key tank/secrets
# error: incorrect or missing key
```

Causes:

- The key file is missing (`keylocation=file:///...` and the file isn't there).
- You're typing the wrong passphrase. (There is no recovery — see [Encryption → Lost passphrase](encryption.md#lost-passphrase).)
- A `zfs change-key` was performed; the old passphrase no longer works.

Check `keylocation`:

```bash
zfs get keylocation,keyformat tank/secrets
```

## "DKMS rebuild failed after kernel upgrade"

Symptom: `zfs.ko` failed to build, modprobe fails, pool can't import.

```bash
# Diagnose
sudo dkms status
sudo apt-get install --reinstall zfs-dkms

# Or build manually
sudo dkms remove zfs/<version> --all
sudo dkms install zfs/<version>

# Confirm
modprobe zfs
```

If the kernel upgrade was the issue, look in `/var/lib/dkms/zfs/<version>/build/make.log` for the actual failure (often it's a missing kernel header package).

```bash
sudo apt install linux-headers-$(uname -r)
```

## "zfs commands hang"

A frozen ZFS thread (deadlock, hardware fault) can hang admin commands. Check:

```bash
ps -ef | grep zfs
sudo cat /proc/spl/kstat/zfs/tank/state
dmesg | tail -50
```

For a hardware-induced lock-up: there's not much you can do live. Reboot, watch the imports, replace the bad disk if dmesg blames a specific device.

If `zpool` hangs while no I/O is happening, sometimes it's a hung systemd-zfs unit. Restart:

```bash
sudo systemctl restart zfs.target
```

## "I broke `/etc/zfs/zpool.cache`"

The cache file holds the list of pools to auto-import. If it's corrupted, the pool won't auto-mount but you can still import manually:

```bash
sudo zpool export tank
sudo zpool import tank
# This rewrites the cache file with current state.
```

If the cache file is completely gone, `zpool import` (without arguments) scans for available pools — slower but works.

## When to nuke and pave

There are scenarios where the right answer is "destroy the pool and restore from backup":

- Massive metadata corruption that `-F` / `-X` can't recover.
- Multiple disk failures beyond the topology's redundancy.
- An accidental `zpool destroy` (truly irreversible — there is no undo).

This is why the [Backup & Recovery](../operations/backup.md) strategy includes an off-host replica. If everything goes wrong, you reinstall the host, create a fresh pool, and `zfs receive` from the backup target.

The [Rebuild Checklist](../operations/rebuild-checklist.md) treats this as the worst-case scenario.

## When to ask for help

Beyond the OpenZFS man pages and the OpenZFS GitHub issues, the helpful resources:

- [OpenZFS docs](https://openzfs.github.io/openzfs-docs/) — canonical reference.
- [OpenZFS GitHub Discussions](https://github.com/openzfs/zfs/discussions) — active community.
- [reddit r/zfs](https://reddit.com/r/zfs) — practical Q&amp;A.
- `man 8 zfs` and `man 8 zpool` — well-written and detailed.

For data-recovery scenarios beyond "rollback to a snapshot", paid recovery services exist. Local backups are cheaper.
