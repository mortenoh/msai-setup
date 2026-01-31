# Pool Creation

## Overview

Create a ZFS pool from:

- Remaining ~1 TB on internal NVMe
- Entire 4 TB secondary NVMe

## Install ZFS

```bash
sudo apt install -y zfsutils-linux
```

## Identify Disks

```bash
lsblk
ls -la /dev/disk/by-id/
```

!!! tip "Use disk IDs"
    Always use `/dev/disk/by-id/` paths, not `/dev/sdX` which can change.

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

```bash
zpool status tank
zpool list tank
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
