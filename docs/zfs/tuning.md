# ZFS Tuning

Runtime knobs that matter on this hardware. ZFS has hundreds of module parameters; most you'll never touch. This page covers the ones that meaningfully change behaviour on a 128 GB / NVMe / mixed-workload home server.

## Where the knobs live

ZFS exposes tunables as Linux module parameters:

```bash
# All current values
ls /sys/module/zfs/parameters/

# Live read
cat /sys/module/zfs/parameters/zfs_arc_max
cat /sys/module/zfs/parameters/zfs_prefetch_disable

# Live write (changes apply immediately; lost on reboot)
echo 17179869184 | sudo tee /sys/module/zfs/parameters/zfs_arc_max

# Persist across reboots: drop a file in /etc/modprobe.d/
sudo tee /etc/modprobe.d/zfs.conf > /dev/null <<'EOF'
options zfs zfs_arc_max=17179869184
options zfs zfs_arc_min=8589934592
options zfs zfs_txg_timeout=5
EOF
sudo update-initramfs -u
```

Tunables in `/etc/modprobe.d/zfs.conf` take effect at the next boot. Updating initramfs is needed only if ZFS is in your initramfs (it's not on this build because root is ext4), but it's harmless.

Documentation:

```bash
modinfo zfs | grep parm        # list all params with descriptions
man 4 zfs                       # narrative documentation, but spotty
```

The canonical reference is the [OpenZFS man pages](https://openzfs.github.io/openzfs-docs/man/index.html); `man 4 zfs` on Ubuntu mirrors it.

## ARC sizing

The biggest knob you'll touch.

### `zfs_arc_max` and `zfs_arc_min`

```
zfs_arc_max — upper bound for ARC size, in bytes (0 = default ~50% RAM)
zfs_arc_min — lower bound; ARC will not shrink below this
```

This build sets `zfs_arc_max=17179869184` (16 GiB) at install time. Adjust based on observed workload:

```bash
# What's the ARC currently doing?
cat /proc/spl/kstat/zfs/arcstats | grep -E '^(size|c|c_max|c_min|hits|misses)'

# Higher-level summary
arc_summary -p 1     # if installed
arcstat 1 5          # 5 samples, 1 second apart
```

Things to look for:

- `size` near `c_max` → cache is filling the bound; healthy.
- High `hits / (hits+misses)` ratio (`hit%`) — 95%+ is good for typical workloads.
- Low hit rate **and** plenty of free RAM → consider raising `zfs_arc_max`.
- Low hit rate **and** RAM-constrained workloads (VMs/AI) — leave it where it is; ARC is correctly being held back.

### `zfs_arc_min`

Set to a value that gives ZFS enough working space — typically `arc_max / 2`. ZFS will resist shrinking below this even under memory pressure from other processes. Without it, an aggressive Ollama load can drain ARC to almost nothing, making subsequent ZFS reads slow.

```bash
echo $((8 * 1024 * 1024 * 1024)) | sudo tee /sys/module/zfs/parameters/zfs_arc_min
```

### `primarycache` (per-dataset)

What ARC actually caches for a given dataset:

- `all` (default): metadata + data
- `metadata`: only metadata (file/dir structure, indirect blocks). Useful for "I read this dataset once and won't read it again" — media archives, cold backups.
- `none`: no caching at all. Rare.

```bash
sudo zfs set primarycache=metadata tank/media
sudo zfs set primarycache=metadata tank/backups
```

This frees ARC for datasets where reads benefit from caching (database, VM disks, model files).

## Prefetch

ZFS speculatively prefetches blocks that look like part of a sequential read.

### `zfs_prefetch_disable`

- `0` (default): prefetch enabled. Right for sequential workloads (media, model loading).
- `1`: prefetch disabled. Sometimes helps random-heavy workloads where prefetch wastes bandwidth.

On NVMe, prefetch is usually a clear win; leave it on. On older HDDs with high seek cost, disabling prefetch on random-heavy datasets can help.

### `zfetch_max_distance`

Max bytes ahead ZFS will prefetch on a given stream. Default is 8 MB; raising it (16-64 MB) helps very-sequential workloads (large media files, model `mmap` reads).

```bash
echo 67108864 | sudo tee /sys/module/zfs/parameters/zfetch_max_distance
# Persist:
echo "options zfs zfetch_max_distance=67108864" | sudo tee -a /etc/modprobe.d/zfs.conf
```

## Transaction group timing

### `zfs_txg_timeout`

How often ZFS forces a transaction group to close and flush:

- Default: 5 seconds.
- Smaller values: more frequent flushes, more even latency, slightly less peak throughput.
- Larger values: bigger batches, better throughput but bursty latency.

Leave at 5 for most workloads. Reduce to 1-3 if you observe latency spikes during sustained write workloads (large container image pulls, big LLM model downloads).

### `zfs_dirty_data_max` / `zfs_dirty_data_sync_percent`

The amount of dirty (un-flushed) data ZFS will accumulate. Defaults scale with RAM and are usually right. If you see "write throttle" stalls in `dmesg` or unusual write latency under heavy load, this is the knob.

```bash
cat /sys/module/zfs/parameters/zfs_dirty_data_max
```

## Write throttle

When dirty data approaches the limit, ZFS starts **throttling writes** so producers don't out-run consumers. Symptoms: write syscalls block for tens to hundreds of milliseconds.

Look for throttling:

```bash
# Watch the "delay" column under zpool iostat
sudo zpool iostat -v -y 5 tank
```

The throttle is generally **a feature, not a bug** — it's protecting you from OOM. If you're seeing it constantly, the underlying problem is usually:

- ARC too large for available RAM
- Disks slower than the workload demands
- A specific dataset with bad `recordsize` causing huge write amplification

Mitigations in order of preference:

1. Tune `recordsize` per dataset (see below).
2. Cap ARC tighter so more RAM is available for the write buffer.
3. Move hot data off the slow disk (the secondary 4 TB NVMe on this build is x1 — keep VM disks and DB on the primary).

## `recordsize` per workload

The single most-impactful per-dataset property after compression.

Recordsize is the **maximum** block size; small files use smaller blocks. But for files that exceed recordsize, ZFS chops them into recordsize chunks. Wrong recordsize for the workload causes:

- **Read amplification** if recordsize is too big (reading 1 KB requires loading a 1 MB block).
- **Write amplification** if recordsize is too small for the file (lots of indirect block updates).

| Workload | Recordsize | Reason |
|---|---|---|
| Database (Postgres, MySQL) | 16 K (or match the DB page size) | Avoid read-modify-write of large records on small updates. |
| VM disk images (qcow2 on dataset) | 64 K | Balance between guest small-IO and bulk operations. |
| Zvol for VM disk | volblocksize=8 K-16 K (Windows NTFS), 64 K (Linux) | See [VM Storage](vm-storage.md). |
| Media files (movies, TV, music) | 1 M | Sequential reads of large files; minimise metadata. |
| ML model files (GGUF, safetensors) | 1 M | Sequential mmap reads; large records help. |
| General home directory / mixed | 128 K (default) | Compromise. |
| Backup target (large archives) | 1 M | Mostly sequential writes/reads. |
| Mail (Maildir-style many small files) | 16 K | Small writes dominate. |

Set per dataset:

```bash
sudo zfs set recordsize=1M tank/media
sudo zfs set recordsize=16K tank/db
sudo zfs set recordsize=64K tank/vm
```

Changing recordsize only affects **future** writes. Existing data keeps its original block size until rewritten.

## `sync` mode

```
sync=standard   # honour application sync requests (default — correct)
sync=always     # treat every write as sync (slow; useful for testing/correctness)
sync=disabled   # treat every write as async (fast; can lose recent writes on crash)
```

`sync=disabled` is a footgun pretending to be a knob. It speeds up sync-write-heavy workloads dramatically — but if the host crashes, the last ~5 seconds of "synced" writes weren't actually on stable storage.

Legitimate uses:

- Throwaway data (CI scratch directories, ephemeral container state).
- Datasets where the app already does its own durability (e.g. Postgres with `synchronous_commit=off` — you're already in "may lose recent transactions" territory anyway).

Anywhere else, leave it `standard`.

## `logbias`

Controls how ZIL writes are placed:

- `latency` (default): minimise sync-write latency by writing the ZIL twice (to the ZIL slot AND the final destination during txg commit).
- `throughput`: writes go straight to the final location, ZIL just marks them. Lower latency penalty on the first sync write but higher aggregate I/O on async-heavy workloads.

Almost no one needs to change this. Mentioned because old guides bring it up.

## `redundant_metadata`

```
redundant_metadata=all   # default; metadata is triple-copied
redundant_metadata=most  # less metadata redundancy
```

Saves 5-10% space on metadata-heavy datasets (lots of small files) at the cost of marginal reliability. Only worth it on bulk-data datasets where you're storage-constrained.

```bash
sudo zfs set redundant_metadata=most tank/media
```

## Memory accounting cheat-sheet

```bash
# What's ZFS using?
arc_summary 2>/dev/null | head -30
cat /proc/spl/kstat/zfs/arcstats | grep -E '^size'

# What's free?
free -h

# Per-process
top -o %MEM
```

A common confusion: `free -h` reports ARC as "used" but Linux's memory pressure code knows it's reclaimable. So `free -h` showing low "available" with high ZFS ARC isn't actually a problem — the kernel will shrink ARC under genuine memory pressure (down to `zfs_arc_min`).

## Power-management interactions

NVMe drives have APST (Autonomous Power State Transition) which can cause measurable latency on first I/O after idle. Usually not a problem; if it is:

```bash
# Check current power state
sudo nvme get-feature /dev/nvme0n1 --feature-id=2

# Disable APST entirely (boot param)
# Add to GRUB_CMDLINE_LINUX in /etc/default/grub:
#   nvme_core.default_ps_max_latency_us=0
```

Worth doing if you observe occasional 100ms+ latency on idle NVMe drives. Otherwise leave alone.

## `autotrim` and manual TRIM

`autotrim=on` (set at pool creation) keeps SSDs/NVMe happy in the background. You can also force a one-shot TRIM:

```bash
sudo zpool trim tank
sudo zpool trim -w tank   # wait for completion
```

A manual TRIM is useful after a big delete/destroy operation. Schedule weekly if your workload involves a lot of churn:

```bash
# /etc/cron.weekly/zpool-trim
#!/bin/sh
/sbin/zpool trim -w tank
```

## Things people tune that don't actually help

- `dedup=on` — almost never a win. RAM cost is enormous; space savings are usually less than the RAM you spent. Leave off.
- `compression=gzip-9` — slower than `zstd-3` for similar ratios. Use zstd instead.
- `primarycache=none` — almost never useful; defeats most of ZFS's read-side performance.
- `prefetch_disable=1` everywhere — premature optimisation. Disable per-dataset if profiling shows it helps; not globally.

## Monitoring tunables in practice

If you want continuous visibility, add ZFS metrics to Prometheus via `node_exporter`'s `zfs` collector (enabled by default on Linux). Grafana has community dashboards for `node_exporter_zfs` — search for "ZFS ARC" on grafana.com.

For ad-hoc tuning sessions:

```bash
# What's eating IOPS?
sudo zpool iostat -v -l tank 2

# What's the ARC up to?
arc_summary -s arc

# What's the txg pipeline doing?
cat /proc/spl/kstat/zfs/tank/txgs
```

## Next steps

- [Operations](operations.md) — scrubs, replace, expand, monitor.
- [Troubleshooting](troubleshooting.md) — pool import failures, recovery.
