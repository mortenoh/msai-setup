# Pool Creation

## Overview

Create a ZFS pool from:

- Remaining ~1 TB on internal NVMe (partition)
- Entire 4 TB secondary NVMe (whole disk)

!!! note "Prerequisites"
    If using a partition from your boot disk, see [Disk Partitioning](partitioning.md) first.

## Install ZFS

```bash
sudo apt install -y zfsutils-linux
```

## Identify Disks

List block devices to see partitions:

```bash
lsblk
```

Get persistent disk and partition IDs:

```bash
ls -la /dev/disk/by-id/ | grep nvme
```

Example output:

```
nvme-Samsung_SSD_990_PRO_2TB_XXXXX -> ../../nvme0n1
nvme-Samsung_SSD_990_PRO_2TB_XXXXX-part1 -> ../../nvme0n1p1
nvme-Samsung_SSD_990_PRO_2TB_XXXXX-part2 -> ../../nvme0n1p2
nvme-Samsung_SSD_990_PRO_2TB_XXXXX-part3 -> ../../nvme0n1p3
nvme-Samsung_SSD_990_PRO_2TB_XXXXX-part4 -> ../../nvme0n1p4
nvme-Samsung_SSD_990_PRO_4TB_YYYYY -> ../../nvme1n1
```

For this setup, you need:

- `nvme-...-part4` - ZFS partition on internal NVMe
- `nvme-..._4TB_...` - Entire secondary NVMe

!!! tip "Use disk IDs"
    Always use `/dev/disk/by-id/` paths, not `/dev/nvme0n1` which can change between boots.

## Create Pool

### Single Pool (No Redundancy)

For this setup, we prioritize capacity over redundancy:

```bash
sudo zpool create \
    -o ashift=12 \
    -O atime=off \
    -O compression=lz4 \
    -O xattr=sa \
    -O acltype=posixacl \
    tank \
    /dev/disk/by-id/nvme-internal-part4 \
    /dev/disk/by-id/nvme-secondary
```

### Options Explained

| Option | Purpose |
|--------|---------|
| `ashift=12` | 4K sector alignment |
| `atime=off` | Disable access time updates |
| `compression=lz4` | Enable compression |
| `xattr=sa` | Store extended attributes in inodes |
| `acltype=posixacl` | Enable POSIX ACLs |

## Verify Pool

Check pool status:

```bash
zpool status tank
```

Expected output:

```
  pool: tank
 state: ONLINE
config:

        NAME                                    STATE     READ WRITE CKSUM
        tank                                    ONLINE       0     0     0
          nvme-Samsung_SSD_990_PRO_2TB-part4    ONLINE       0     0     0
          nvme-Samsung_SSD_990_PRO_4TB          ONLINE       0     0     0

errors: No known data errors
```

Check pool capacity:

```bash
zpool list tank
```

Verify properties were applied:

```bash
zfs get compression,atime,xattr,acltype tank
```

## Set Mount Point

```bash
sudo zfs set mountpoint=/mnt/tank tank
```

## Auto-Import on Boot

ZFS pools import automatically via systemd. Verify:

```bash
systemctl status zfs-import-cache.service
systemctl status zfs-mount.service
```

## Pool Health

Check regularly:

```bash
# Pool status
zpool status

# I/O statistics
zpool iostat 1

# Scrub for errors
sudo zpool scrub tank
```

!!! warning "No Redundancy"
    This pool has no redundancy. Data protection relies on snapshots and backups.
