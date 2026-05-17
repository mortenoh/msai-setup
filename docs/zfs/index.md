# ZFS Storage

ZFS is the storage backbone of this build. The host OS is on a boring ext4 root; everything that matters — VM disks, container data, media, models, backups — lives in a ZFS pool that spans the leftover ~1 TB on the primary NVMe plus the entire 4 TB secondary NVMe.

This section is intentionally deep. It's meant to be read end-to-end before the reinstall, and many pages include an exercise you can recreate in a VirtualBox lab (see [VirtualBox Lab](virtualbox-lab.md)) without touching the real hardware.

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

```
zpool tank (single pool, no redundancy)
  +-- /dev/disk/by-id/nvme-...-part4   (~1 TB partition on primary 2 TB NVMe, PCIe 4.0 x4)
  +-- /dev/disk/by-id/nvme-...          (4 TB whole secondary NVMe, PCIe 4.0 x1)

Datasets (sketch — see datasets.md for the full layout):
tank/
  +-- media/            recordsize=1M, compression=lz4
  +-- nextcloud-data/   recordsize=128K (default)
  +-- nextcloud-app/    recordsize=128K
  +-- db/               recordsize=16K, primarycache=metadata for some
  +-- vm/               recordsize=64K
  +-- ai/               recordsize=1M, compression=off (GGUF is already compressed)
  +-- containers/       recordsize=128K
  +-- backups/          compression=zstd-3
```

Two design choices worth flagging up front:

1. **Single-vdev pool, no redundancy.** With only two unequal-size devices on the MS-S1 MAX, real-world redundancy options are limited. We rely on snapshots + replication (see [Backup & Recovery](../operations/backup.md)) instead. If you lose a drive, you restore from a remote replica. The [VirtualBox Lab](virtualbox-lab.md) shows how to wire up mirrored and raidz setups so you can practice them even though the real install isn't using them.
2. **ZFS is not on root.** Root is plain ext4 on the primary NVMe (see [Disk Partitioning](../ubuntu/installation/disk-partitioning.md)). This keeps the boot path boring and makes a host rebuild possible without touching pool data.

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
| [VM Storage](vm-storage.md) | Files-on-dataset vs zvols, volblocksize, TRIM/discard, libvirt integration. |
| [Docker Integration](docker-integration.md) | overlay2-over-ext4 with bind mounts into ZFS, recordsize per workload. |
| [Tuning](tuning.md) | ARC sizing, prefetch, txg timeout, write throttle, recordsize choice. |
| [Operations](operations.md) | Scrubs, replacing disks, expanding pools, monitoring, regular maintenance. |
| [Troubleshooting](troubleshooting.md) | Pool import failures, missing cache, force-import, corrupted data recovery. |

If you're new to ZFS, read [Concepts](concepts.md) first, then jump to the [VirtualBox Lab](virtualbox-lab.md) and exercise everything before touching the production install.
