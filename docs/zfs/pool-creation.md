# Pool Creation

Turning identified, prepped devices into a working pool. This page covers the actual `zpool create` for the MS-S1 MAX build, plus the design choices behind every flag.

## Prerequisites

- ZFS userland installed (`sudo apt install -y zfsutils-linux`).
- Devices identified and prepped per [Partitioning](partitioning.md): primary's 4th partition is empty, secondary disk is wiped clean.
- ARC cap planned (see below).
- Decision made on encryption (see [Encryption](encryption.md)) — easier to set at create time than to retrofit.

## The actual `zpool create` for this build

```bash
PRIMARY_PART=/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_<serial>-part4
SECONDARY=/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_4TB_<serial>

sudo zpool create \
    -o ashift=12 \
    -o autotrim=on \
    -O compression=lz4 \
    -O atime=off \
    -O xattr=sa \
    -O acltype=posixacl \
    -O dnodesize=auto \
    -O mountpoint=/mnt/tank \
    tank \
    "$PRIMARY_PART" \
    "$SECONDARY"
```

That's it. One pool, two single-disk top-level vdevs (effectively a stripe), with sensible defaults set at create time so they're inherited by all child datasets.

Verify:

```bash
sudo zpool status tank
sudo zpool list tank
zfs get compression,recordsize,atime,xattr,acltype tank
```

The rest of this page is "why those flags, what to do differently if your situation differs".

## Pool-level options (`-o`)

These attach to the **pool**, not to datasets. Set at create time; many can be changed later but some can't.

### `ashift=12` — locked at create time

The log2 of the smallest IO unit ZFS will use to a vdev. `ashift=12` = 4 KiB blocks, the right setting for any 512e / 4Kn / NVMe disk you'll encounter today.

**Cannot be changed**. Set wrong -> recreate the pool. Always set it explicitly even though current OpenZFS picks 12 by default — being explicit means you'll spot mistakes faster.

### `autotrim=on`

Periodic background TRIM on SSDs and NVMe — tells the underlying device which blocks are free so its garbage collection can run efficiently.

- `on`: ZFS issues TRIM requests in the background as space is freed. Light overhead.
- `off`: explicit manual TRIM via `zpool trim tank` only.

On NVMe, `autotrim=on` is the right answer for this build. On HDD-only pools, it doesn't do anything.

### `autoreplace=on` (optional)

When set, ZFS automatically uses a spare disk to replace a failed pool member. Requires spare vdevs (`zpool add tank spare …`). Not relevant here (no spares on a 2-disk box).

### `autoexpand=on` (optional)

When a pool's underlying device(s) grow (e.g. you replaced a 4 TB disk with an 8 TB disk in a mirror), `autoexpand=on` makes the pool see the new capacity automatically. Without it, you'd run `zpool online -e tank <device>` manually after the resilver.

### `cachefile=/etc/zfs/zpool.cache` (default)

Where ZFS records the list of imported pools. Stored on the boot disk so systemd's `zfs-import-cache.service` can re-import the pool at boot. Don't override unless you're doing root-on-ZFS or using `zfs-import-scan.service` instead.

## Filesystem-level options (`-O`) — inherited by every dataset

These set the **defaults** for the root dataset (`tank`); child datasets inherit unless overridden. Setting them at create time avoids having to remember to set them later.

### `compression=lz4`

See [Concepts -> Compression](concepts.md#compression). `lz4` is the right default; safe everywhere, cheap on Zen 5. Override per-dataset only when you know better (e.g. `compression=off` for `tank/ai` where GGUF files are already compressed; `compression=zstd-3` for `tank/backups`).

### `atime=off`

`atime=on` (the default for compatibility) updates the access timestamp on every file read, which generates **a write for every read**. Turning it off saves a lot of IOPS for very little practical loss — atime is used by almost nothing in practice. If you have a tool that needs it (some mail-spool implementations), set `relatime=on` instead, which updates atime only when it would otherwise have been older than mtime.

### `xattr=sa`

Where extended attributes are stored:

- `xattr=on` (legacy default): stored in a hidden directory entry per file. Two seeks per xattr access.
- `xattr=sa` (recommended): stored in the inode (system attribute). One seek. Better performance.

`xattr=sa` is what every modern guide recommends; it's only "not the default" for historical compatibility.

### `acltype=posixacl`

Enables POSIX ACLs (`setfacl`/`getfacl`). Off by default for historical reasons. Turn it on — many services (Samba, container runtimes) expect them.

### `dnodesize=auto`

The size of a directory-node (inode equivalent). `auto` lets ZFS choose larger dnodes when needed for things like SA-stored xattrs. Pairs naturally with `xattr=sa`.

### `mountpoint=/mnt/tank`

Where the pool's root dataset is mounted. `/mnt/tank` is the convention in this build (per [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) and START.md). Alternatives:

- `mountpoint=/tank` — keeps paths shorter (`/tank/media` vs `/mnt/tank/media`); some prefer this.
- `mountpoint=none` — pool root is unmounted; you mount only specific datasets. Useful for "pool of zvols" setups.
- `mountpoint=legacy` — don't auto-mount; use `/etc/fstab`. Mostly for root-on-ZFS.

If you change the convention to `/tank`, sweep the rest of the docs (every `/mnt/tank/...` path).

### Options to consider per-dataset, not pool-wide

These are commonly *not* set at the pool level because they're workload-specific:

- `recordsize` — block size; default 128 K. Tune per dataset.
- `sync` — sync write behaviour. Default is fine for the pool root.
- `primarycache` / `secondarycache` — what ARC/L2ARC caches for this dataset.
- `redundant_metadata=most` (default `all`) — keep all metadata triple-copied; `most` keeps fewer copies of some metadata for ~5-10% space savings. Worth setting on truly bulk datasets if you want it.

See [Datasets](datasets.md) for the full property reference.

## Cap the ARC size

The Adaptive Replacement Cache defaults to ~50% of system RAM. On a 128 GB box that's 64 GB silently consumed by cache — which collides with the memory budget for VMs and Ollama/llama.cpp.

Set a hard cap **before** the pool gets heavy use:

```bash
# /etc/modprobe.d/zfs.conf
echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf

# Apply on next boot (initramfs needs updating because zfs is in there)
sudo update-initramfs -u

# Set it live without rebooting (matches modprobe.d on next boot)
echo 17179869184 | sudo tee /sys/module/zfs/parameters/zfs_arc_max
cat /sys/module/zfs/parameters/zfs_arc_max
```

Sane caps for this hardware:

| Workload mix | ARC cap | Bytes |
|---|---|---|
| Heavy LLM (Ollama / llama.cpp hot, minimal disk I/O on tank) | 8 GiB | `8589934592` |
| Mixed: VMs + AI + services (recommended default) | 16 GiB | `17179869184` |
| Mostly cold storage, ZFS-heavy reads, modest VM/LLM | 32 GiB | `34359738368` |

You can also set a minimum (`zfs_arc_min`) and force a more aggressive shrink target if you observe lots of memory pressure under inference. Most users don't need to.

See [Tuning](tuning.md) for ARC internals (`primarycache`, prefetch tuning, `arc_meta_limit`).

## Verify the pool

```bash
sudo zpool status -v tank
sudo zpool list -v tank
zfs list -o name,used,available,referenced,mountpoint
zfs get all tank | head -40
```

You should see:

- pool state `ONLINE`
- two leaf devices, both `ONLINE` with no errors
- ARC stats sane (`cat /proc/spl/kstat/zfs/arcstats | grep '^size'`)
- pool mounted at `/mnt/tank`

## Pool features (compatibility level)

ZFS pools have **features** that you can enable. They're additive: enabling a feature on a pool means the on-disk format starts using it, and the pool can no longer be imported by ZFS implementations that don't know that feature.

```bash
sudo zpool get all tank | grep feature@
```

Each row is `feature@<name> <state>`, where state is `disabled`, `enabled`, or `active`. New pools have most features `enabled` (announced but not yet used) and start using them as datasets/data are created.

For a single-host pool that you're not moving between ZFS implementations, leave them at the defaults. If you're planning to send/receive across implementations (e.g. to a FreeBSD backup host), check compatibility profiles:

```bash
ls /etc/zfs/compatibility.d/
sudo zpool create -o compatibility=openzfs-2.1-linux ...
```

Common pitfalls:

- A pool created on the newest OpenZFS can't always be imported on an older one. Check the `version` and `feature` flags before moving pools.
- A pool with `crypto` features `active` can't be imported by a build without encryption support.

## Pool features worth knowing about

| Feature | What it does | When you care |
|---|---|---|
| `async_destroy` | Async dataset destroy in the background | Default; harmless. |
| `large_blocks` | Allow recordsize up to 1 MiB | You set `recordsize=1M`. |
| `large_dnode` | Allow larger dnodes (matches `dnodesize=auto`) | Pairs with `xattr=sa`. |
| `lz4_compress`, `zstd_compress` | The compression algorithms | Activated when you set the property. |
| `encryption` | Native dataset encryption | See [Encryption](encryption.md). |
| `raidz_expansion` (2.3+) | Add a disk to an existing raidz | Useful if you ever go raidz. |
| `head_errlog` | Better tracking of corrupted files across snapshots | Default in 2.2+. |
| `device_removal` | Allow removing a top-level vdev (non-raidz) | Lets you shrink a pool. |

## Stripping vs adding redundancy after the fact

You **can** attach a mirror partner to a single-disk vdev:

```bash
sudo zpool attach tank "$PRIMARY_PART" /dev/disk/by-id/<new-disk>
```

This converts the single-disk vdev into a 2-way mirror. The new disk resilvers from the existing one.

You **cannot** turn an existing stripe of two top-level vdevs into a single mirror — that's a different topology. The closest you can do is `zpool replace` plus juggling, which is risky and not worth it on a tiny home pool.

## Setting the pool to auto-import at boot

Ubuntu's `zfs-import-cache.service` + `zfs-mount.service` units handle this automatically once the pool is created. Verify:

```bash
systemctl status zfs-import-cache.service zfs-mount.service zfs.target
sudo zpool export tank && sudo zpool import tank   # round-trip to confirm the import works
```

If you ever boot and the pool isn't imported, see [Troubleshooting -> Pool Import Failures](troubleshooting.md#pool-import-failures).

## What this pool is *not*

It's worth re-stating the trade-offs explicitly:

- **Not redundant.** A failed primary partition or the secondary NVMe = a dead pool. Mitigated by snapshots + off-host replication.
- **Asymmetric IO.** The 4 TB drive is on a PCIe 4.0 x1 link (~2 GB/s ceiling). For VM disks and hot databases, prefer the partition on the primary drive (PCIe 4.0 x4). See [Datasets](datasets.md) for per-dataset placement hints.
- **Two top-level vdevs of different sizes.** ZFS will allocate proportionally; the larger device will see more writes. Fine for this workload but worth knowing.

## What to do next

- [Encryption](encryption.md) — set this up before creating sensitive datasets if you want it.
- [Datasets](datasets.md) — carve up the pool into per-workload datasets with proper properties.
- [Tuning](tuning.md) — runtime knobs for ARC, prefetch, write throttle.
- [Operations](operations.md) — scrubs, replace, expand, monitor.
