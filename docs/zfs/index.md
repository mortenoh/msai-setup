# ZFS Storage

ZFS is the storage backbone of this build — **including root itself**. The host OS lives on `rpool/ROOT/ubuntu` (boot environments via [ZFSBootMenu](https://zfsbootmenu.org/)), and everything else that matters — Incus instance storage, databases, media, models, backups — lives on ZFS too, split across **two independent pools, one per physical NVMe**: `rpool` on the fast 4 TB drive (slot 1, PCIe 4.0 x4) and `tank` on the slow 2 TB drive (slot 2, PCIe 4.0 x1). No pool is striped across both drives.

This section is intentionally deep. It's meant to be read end-to-end before the install, and many pages include an exercise you can recreate in a VirtualBox lab (see [VirtualBox Lab](virtualbox-lab.md)) without touching the real hardware.

!!! info "ZFS is the canonical filesystem for this build"
    ZFS is the **production, source-of-truth** filesystem here — root, Incus instance datasets, databases, media, models, and backups all live on it, and nothing else in this build stores real data. The [Bcachefs](../bcachefs/index.md) section is documented purely as an experimental/exploratory alternative to learn from; it is **not** used anywhere on the MS-S1 MAX.

## Why ZFS for this build

The headline features:

- **Copy-on-write filesystem.** ZFS never overwrites a block in place. Every change writes new blocks and updates a metadata pointer. This is what enables instant atomic snapshots, consistent online filesystems, and the option to roll back.
- **End-to-end checksums.** Every block stores a checksum in its parent block, transitively up to the uberblock. Bit-rot, cable noise, or controller bugs are detected on every read. With redundancy, ZFS self-heals corrupted blocks.
- **Snapshots and clones.** Snapshots are O(1) and (initially) take zero space; they grow only as the live filesystem diverges. Clones are writable forks of a snapshot.
- **Inline compression.** `lz4` is faster than not compressing in almost all cases (less data to read = less I/O wait). `zstd` trades CPU for better ratios.
- **Datasets as a unit of policy.** Per-dataset compression, recordsize, quotas, mount options, snapshot retention. Without LVM gymnastics.
- **Send/receive replication.** `zfs send | zfs receive` ships snapshots between pools, locally or over SSH, with bookmark-based incrementals.
- **Native encryption.** Per-dataset AES-256-GCM with raw send/receive that keeps data encrypted in transit.

## The pool plan for this build

Two independent pools, each a single-disk vdev on its own drive. See [Datasets](datasets.md) for the full property layout and [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) for the canonical device layout.

```
rpool  (fast 4 TB NVMe, slot 1, PCIe 4.0 x4 — root + hot data)
  +-- /dev/disk/by-id/nvme-...-part2   (whole disk after the 512 MB EFI partition)

rpool/
  +-- ROOT/ubuntu       mountpoint=/, canmount=noauto (the OS; boot environments live here)
  +-- home
  +-- incus             Incus's ZFS storage backend (one dataset per instance, auto-managed)
  +-- db                recordsize=16K (per-service databases)
  +-- ai                recordsize=1M, compression=off (GGUF/safetensors already compressed)

tank   (slow 2 TB NVMe, slot 2, PCIe 4.0 x1 — bulk/cold data)
  +-- /dev/disk/by-id/nvme-...          (whole disk)

tank/
  +-- media             recordsize=1M, compression=lz4
  +-- nextcloud-data    the snapshot-critical one
  +-- nextcloud-app
  +-- backups           compression=zstd-3
```

Two design choices worth flagging up front:

1. **Two independent single-disk pools, no redundancy, no striping across drives.** With only two unequal-speed NVMe devices on the MS-S1 MAX, each pool is one disk. We rely on snapshots + replication (see [Backup & Recovery](../operations/backup.md)) instead of RAID. If you lose a drive, you restore that pool from a remote replica. Two separate pools (rather than one striped across both) mean anything on `rpool` is guaranteed on the fast drive — see [Pool Creation → Two pools, not one stripe](pool-creation.md#two-pools-not-one-stripe). The [VirtualBox Lab](virtualbox-lab.md) shows how to wire up mirrored and raidz setups so you can practice them even though the real install isn't using them.
2. **ZFS is on root.** Root is `rpool/ROOT/ubuntu`, booted by [ZFSBootMenu](https://zfsbootmenu.org/) (see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md)). Snapshots become boot environments: a bad `apt upgrade` or kernel is a rollback, not a reinstall. Ext4 root remains a documented alternative but is no longer the default.
3. **Instance storage is Incus's, not hand-carved.** Containers and VMs are ZFS datasets under `rpool/incus`, created and owned by Incus automatically — there is no manual `tank/containers/<svc>` or `tank/vm` tree anymore. See [Incus storage](../incus/storage.md).

## Section map

| Page | What you'll learn |
|---|---|
| [Concepts](concepts.md) | vdevs, pool topology, COW, checksums, ARC, ZIL, transaction groups, ashift. The mental model. |
| [VirtualBox Lab](virtualbox-lab.md) | Hands-on labs you can run on a Mac/Linux box with VirtualBox before touching the real hardware. |
| [Partitioning](partitioning.md) | GPT, alignment, `gdisk`/`parted`/`sgdisk`, wiping old metadata, by-id paths. |
| [Pool Creation](pool-creation.md) | Topology decisions, ashift, ARC cap, pool features, autotrim/autoexpand/autoreplace. |
| [Encryption](encryption.md) | Native ZFS encryption, keyformats, raw send/receive, key rotation. |
| [Datasets](datasets.md) | Property reference, inheritance, quotas vs reservations, sync modes, recordsize per workload. |
| [Snapshots](snapshots.md) | Snapshots, bookmarks, holds, clones+promotion, diff, send/receive flags. |
| [VM Storage](vm-storage.md) | How Incus backs VM disks with ZFS zvols under `rpool/incus`; volblocksize/recordsize background; cross-refs to [Incus storage](../incus/storage.md). |
| [Docker Integration](docker-integration.md) | Bind-mounting host ZFS datasets into the nested Docker-in-Incus stack (two-layer chain), recordsize per workload. |
| [Tuning](tuning.md) | ARC sizing, prefetch, txg timeout, write throttle, recordsize choice. |
| [Operations](operations.md) | Scrubs, replacing disks, expanding pools, monitoring, regular maintenance. |
| [Troubleshooting](troubleshooting.md) | Pool import failures, missing cache, force-import, corrupted data recovery. |

If you're new to ZFS, read [Concepts](concepts.md) first, then jump to the [VirtualBox Lab](virtualbox-lab.md) and exercise everything before touching the production install.
