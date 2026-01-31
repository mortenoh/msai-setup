# Disk Partitioning

## Overview

Before creating a ZFS pool, you may need to partition disks. This guide covers partitioning the internal NVMe to coexist with ext4 root.

## When to Partition

| Scenario | Partition Needed |
|----------|------------------|
| Dedicated disk for ZFS | No - use whole disk |
| ZFS alongside ext4 root | Yes - create partition for ZFS |
| Adding spare space from boot disk | Yes - create partition from free space |

For this setup:

- **Internal NVMe (2TB)**: Partitioned - ext4 root + ZFS partition
- **Secondary NVMe (4TB)**: Whole disk for ZFS

## Identify Disks

List block devices:

```bash
lsblk
```

Example output:

```
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
nvme0n1     259:0    0   1.8T  0 disk
├─nvme0n1p1 259:1    0   512M  0 part /boot/efi
├─nvme0n1p2 259:2    0     1G  0 part /boot
└─nvme0n1p3 259:3    0   500G  0 part /
nvme1n1     259:4    0   3.6T  0 disk
```

Get persistent disk IDs:

```bash
ls -la /dev/disk/by-id/ | grep nvme
```

!!! tip "Use disk IDs"
    Always reference disks by `/dev/disk/by-id/` paths. Device names like `/dev/nvme0n1` can change between boots.

## Plan Partition Layout

Target layout for internal NVMe:

| Partition | Size | Purpose |
|-----------|------|---------|
| p1 | 512 MB | EFI System |
| p2 | 1 GB | /boot |
| p3 | 500 GB - 1 TB | / (ext4 root) |
| p4 | Remaining | ZFS pool member |

## Partition Internal NVMe

### Check Free Space

```bash
sudo fdisk -l /dev/nvme0n1
```

If the disk has unallocated space after the root partition, you can create a new partition.

### Create ZFS Partition

Using `gdisk` (recommended for GPT disks):

```bash
sudo gdisk /dev/nvme0n1
```

Commands:

1. `p` - Print partition table (verify current layout)
2. `n` - New partition
    - Partition number: 4 (or next available)
    - First sector: (press Enter for default - starts after last partition)
    - Last sector: (press Enter for default - uses remaining space)
    - Hex code: `bf00` (Solaris root - recognized by ZFS)
3. `p` - Verify new partition
4. `w` - Write changes and exit

### Alternative: Using fdisk

```bash
sudo fdisk /dev/nvme0n1
```

Commands:

1. `p` - Print partition table
2. `n` - New partition
    - Partition type: primary
    - Partition number: 4
    - First sector: (default)
    - Last sector: (default)
3. `t` - Change partition type
    - Partition: 4
    - Type: `bf` (Solaris root)
4. `w` - Write and exit

## Verify Partitions

After partitioning:

```bash
lsblk
```

Expected output:

```
NAME        MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
nvme0n1     259:0    0   1.8T  0 disk
├─nvme0n1p1 259:1    0   512M  0 part /boot/efi
├─nvme0n1p2 259:2    0     1G  0 part /boot
├─nvme0n1p3 259:3    0   500G  0 part /
└─nvme0n1p4 259:4    0     1T  0 part
nvme1n1     259:5    0   3.6T  0 disk
```

Verify partition IDs are available:

```bash
ls -la /dev/disk/by-id/ | grep nvme
```

Look for entries like:

- `nvme-<model>-part4` - The new ZFS partition
- `nvme-<model>` - The secondary disk (whole disk)

## Important Notes

!!! warning "Backup First"
    Always backup important data before modifying partition tables.

!!! note "Live System"
    If modifying the boot disk on a running system, consider booting from a live USB. Some partition changes require a reboot to take effect.

!!! info "Secondary Disk"
    The 4TB secondary NVMe needs no partitioning - ZFS will use the entire disk.

## Next Steps

Proceed to [Pool Creation](pool-creation.md) to create the ZFS pool from these devices.
