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

Ubuntu 26.04 ships OpenZFS in the main archive. The DKMS module builds against the running kernel on first install; if you're on the Ubuntu-provided HWE kernel (the default on this hardware), you get a prebuilt kmod and DKMS only triggers on kernel upgrades.

!!! note "ZFS and Secure Boot"
    With Secure Boot enabled, the ZFS DKMS module must be MOK-signed before it loads, or `modprobe zfs` fails silently and the pool won't import. This build keeps Secure Boot **disabled** (see [BIOS Setup](../getting-started/bios-setup.md)) to avoid that complication. If you specifically need Secure Boot, enrol a MOK before installing ZFS.

## Cap the ARC Size

ZFS defaults its Adaptive Replacement Cache (ARC) to ~50% of system RAM. On a 128 GB box that's 64 GB silently consumed by cache — which collides with the memory budget for VMs and Ollama/llama.cpp.

Set a hard cap **before** importing the pool or doing anything memory-heavy:

```bash
# Cap ARC at 16 GiB
echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf

# Apply on next reboot (initramfs needs updating because zfs is in there)
sudo update-initramfs -u
```

Sane caps for this hardware:

| Workload mix | ARC cap |
|---|---|
| Heavy LLM (Ollama/llama.cpp hot) | 8 GiB (`8589934592`) |
| Mixed: VMs + AI + services (recommended default) | 16 GiB (`17179869184`) |
| Mostly cold storage, ZFS-heavy reads | 32 GiB (`34359738368`) |

You can also set/check `zfs_arc_max` at runtime without rebooting, useful for tuning:

```bash
# Inspect
cat /sys/module/zfs/parameters/zfs_arc_max

# Change live (still picks up modprobe.d on next boot)
echo 17179869184 | sudo tee /sys/module/zfs/parameters/zfs_arc_max
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
