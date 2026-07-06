# Pool Creation

Turning identified, prepped devices into a working pool. This page covers the actual `zpool create` for the MS-S1 MAX build, plus the design choices behind every flag.

## Prerequisites

- ZFS userland installed (`sudo apt install -y zfsutils-linux`).
- Devices identified and prepped per [Partitioning](partitioning.md): the primary 4 TB drive's `-part2` is empty (after its 512 MB EFI partition), the secondary 2 TB drive's `-part1` is wiped clean.
- ARC cap planned (see below).
- Decision made on encryption (see [Encryption](encryption.md)) — easier to set at create time than to retrofit.

!!! note "This build creates two pools, not one"
    `rpool` (root + hot data) on the fast 4 TB primary and `tank` (bulk/cold data) on the slow 2 TB secondary. The **canonical, authoritative `zpool create` invocations live in [ZFS Root (Alternative)](../ubuntu/installation/zfs-root-alternative.md#create-rpool-primary-fast-drive)** — this page reproduces them for the ZFS-mechanics context and explains every flag. If the two ever drift, the installation docs win.

## The actual `zpool create` for this build

`rpool` is created first (it holds root and is bootstrapped into during install), then `tank`. Both use `-R /mnt` as an altroot during the live-environment install so datasets mount under `/mnt` while bootstrapping; after the first real boot they mount at their natural paths (`/`, `/home`, `/tank`, …).

### `rpool` — primary, fast 4 TB drive

```bash
PRIMARY_PART=/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_4TB_<serial>-part2

sudo zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on -O canmount=off -O mountpoint=none \
    -R /mnt \
    rpool "$PRIMARY_PART"

# The boot-environment container and the first boot environment
sudo zfs create -o canmount=off -o mountpoint=none rpool/ROOT
sudo zfs create -o canmount=noauto -o mountpoint=/ rpool/ROOT/ubuntu
sudo zfs create -o mountpoint=/home rpool/home
```

`rpool/ROOT/ubuntu` is `canmount=noauto` on purpose — with more than one boot environment present, ZFS must not auto-mount all of them; ZFSBootMenu (or an explicit `zfs mount`) picks which one becomes `/` at boot. The remaining hot-data datasets (`rpool/incus`, `rpool/db`, `rpool/ai`) are created in [Datasets](datasets.md).

### `tank` — secondary, slow 2 TB drive

```bash
SECONDARY_PART=/dev/disk/by-id/nvme-Samsung_SSD_990_PRO_2TB_<serial>-part1

sudo zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    -R /mnt \
    tank "$SECONDARY_PART"
```

`tank` needs no `canmount=off` / `ROOT` dance — it holds no boot environments, just data datasets (`tank/media`, `tank/nextcloud-*`, `tank/backups` — see [Datasets](datasets.md)). It mounts at `/tank` after boot.

That's it. Two independent pools, each a single-disk top-level vdev, with sensible defaults set at create time so they're inherited by all child datasets.

Verify both:

```bash
sudo zpool status rpool
sudo zpool status tank
sudo zpool list
zfs get compression,relatime,xattr,acltype rpool tank
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

See [Concepts -> Compression](concepts.md#compression). `lz4` is the right default; safe everywhere, cheap on Zen 5. Set at create time on both pools, and override per-dataset only when you know better (e.g. `compression=off` for `rpool/ai` where GGUF files are already compressed; `compression=zstd-3` for `tank/backups`).

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

### `mountpoint` — `none` on `rpool`, default `/tank` on `tank`

`rpool` is created `mountpoint=none` (its root dataset never mounts; only its children — `/`, `/home`, `/tank`'s datasets, etc. — do). This is the root-on-ZFS convention: the pool root is a namespace container, and `rpool/ROOT/ubuntu` provides `/`.

`tank` takes the default mountpoint (`/tank`), so its datasets land at `/tank/media`, `/tank/backups`, and so on after boot. The `-R /mnt` altroot only shifts these during the live-environment install (`/mnt/tank/...`); it is not persisted. Runtime paths in the rest of these docs are `/tank/...` and `/rpool/...` (for the handful of `rpool` data datasets like `/rpool/ai`), never `/mnt/tank/...`.

Other values you'll see:

- `mountpoint=legacy` — don't auto-mount; use `/etc/fstab`. Only the EFI partition uses fstab on this build.
- `mountpoint=none` — a namespace-only dataset (like `rpool` and `rpool/ROOT`).

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
| Heavy LLM (Ollama / llama.cpp hot, minimal disk I/O) | 8 GiB | `8589934592` |
| Mixed: VMs + AI + services (recommended default) | 16 GiB | `17179869184` |
| Mostly cold storage, ZFS-heavy reads, modest VM/LLM | 32 GiB | `34359738368` |

You can also set a minimum (`zfs_arc_min`) and force a more aggressive shrink target if you observe lots of memory pressure under inference. Most users don't need to.

See [Tuning](tuning.md) for ARC internals (`primarycache`, prefetch tuning, `arc_meta_limit`).

## Verify the pools

```bash
sudo zpool status -v rpool
sudo zpool status -v tank
sudo zpool list -v
zfs list -o name,used,available,referenced,mountpoint
zfs get all rpool | head -40
```

You should see:

- both pools' state `ONLINE`
- one leaf device per pool, `ONLINE` with no errors
- ARC stats sane (`cat /proc/spl/kstat/zfs/arcstats | grep '^size'`)
- `rpool` root unmounted (`mountpoint=none`); `rpool/ROOT/ubuntu` at `/`; `tank` at `/tank`

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

## Adding redundancy after the fact

You **can** attach a mirror partner to either single-disk pool's vdev, if you ever add a third drive:

```bash
sudo zpool attach rpool "$PRIMARY_PART" /dev/disk/by-id/<new-disk>
```

This converts the single-disk vdev into a 2-way mirror. The new disk resilvers from the existing one. The MS-S1 MAX only has two M.2 slots, so in practice there's no spare drive to do this with — snapshots + replication are the redundancy story instead.

## Setting the pools to auto-import at boot

`rpool` is imported by the initramfs/ZFSBootMenu path (it *is* root — the system can't boot otherwise). `tank` is imported by Ubuntu's `zfs-import-cache.service` + `zfs-mount.service` units once created. Verify:

```bash
systemctl status zfs-import-cache.service zfs-mount.service zfs.target
sudo zpool export tank && sudo zpool import tank   # round-trip to confirm tank imports cleanly
```

Do **not** casually export `rpool` on a running system — it's your root. If a pool isn't imported after boot, see [Troubleshooting → Pool Import Failures](troubleshooting.md#pool-import-failures).

## Two pools, not one stripe

It's worth re-stating the trade-offs explicitly:

- **Neither pool is redundant.** Each is a single-disk vdev — a failed drive means that whole pool is gone (`rpool` = root + hot data, `tank` = bulk data). Mitigated by snapshots + off-host replication, not RAID.
- **Two pools instead of one striped across both — a deliberate choice.** The 4 TB drive is on PCIe 4.0 x4 (~8 GB/s); the 2 TB is on x1 (~2 GB/s ceiling). An earlier draft folded both drives into one striped `tank` pool, but ZFS's allocator spreads writes across all top-level vdevs by free space — there is no per-dataset device pinning, so "keep hot data on the fast drive" was unenforceable. **Two independent pools give a real guarantee**: anything on `rpool` is on the fast drive, full stop; anything on `tank` is on the slow drive. That's why databases and model files moved to `rpool` and only bulk/cold data stays on `tank`. See [Datasets → A note on device placement](datasets.md#a-note-on-device-placement).
- **Each pool sizes to its one disk.** No proportional-allocation surprises across mismatched vdevs, because there's only one vdev per pool.

## What to do next

- [Encryption](encryption.md) — set this up before creating sensitive datasets if you want it.
- [Datasets](datasets.md) — carve up the pool into per-workload datasets with proper properties.
- [Tuning](tuning.md) — runtime knobs for ARC, prefetch, write throttle.
- [Operations](operations.md) — scrubs, replace, expand, monitor.
