# Boot Issues

This page covers diagnosing and resolving boot problems on Ubuntu Server 26.04 LTS. This build boots **plain ext4 root via GRUB** (see [Disk Partitioning](../installation/disk-partitioning.md)) — the data lives on two ZFS pools (`hot`, `tank`), but root itself is boring ext4.

!!! note "Took the ZFS Root alternative?"
    If you followed the [ZFS Root (Alternative)](../installation/zfs-root-alternative.md), your box boots via **ZFSBootMenu**, not GRUB — recovery is different (boot environments, `efibootmgr`, no `grub-install`). The full ZFSBootMenu recovery flow, hotkeys, and reinstall/repair steps live on that page. This page's GRUB recovery is for the canonical ext4 build.

## Boot Process Overview

### Normal Boot Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                    1. UEFI/BIOS                              │
│              Hardware initialization                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    2. GRUB Bootloader                        │
│            Load kernel and initramfs                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    3. Kernel + initramfs                     │
│            Load drivers, mount ext4 root                     │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    4. systemd (PID 1)                        │
│            Start services, import ZFS pools, reach target    │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    5. Login Prompt                           │
│                System ready                                  │
└─────────────────────────────────────────────────────────────┘
```

## Identifying Boot Stage

### Where Did It Fail?

| Symptom | Stage | See Section |
|---------|-------|-------------|
| No POST, no display | Hardware/BIOS | [BIOS reset](../../getting-started/bios-setup.md#recovering-from-a-bad-bios-state) |
| GRUB menu not shown | GRUB | GRUB Recovery |
| "GRUB rescue>" prompt | GRUB config | GRUB Recovery |
| Kernel panic | Kernel | Kernel Issues |
| systemd errors | Init | systemd Issues |
| A ZFS pool missing after boot | ZFS pool import | Filesystem / Pool Issues |
| Services fail | Services | Service Recovery |

## Accessing Recovery Mode

### From GRUB Menu

1. At boot, hold **Shift** (BIOS) or **Esc** (UEFI) to show GRUB
2. Select **Advanced options for Ubuntu**
3. Select **Ubuntu with Linux x.x.x (recovery mode)**

### Recovery Menu Options

| Option | Use For |
|--------|---------|
| resume | Continue normal boot |
| clean | Free up disk space |
| dpkg | Repair broken packages |
| fsck | Check filesystem |
| grub | Update GRUB |
| network | Enable networking |
| root | Drop to root shell |
| system-summary | Show system info |

### Drop to Root Shell

From recovery menu:

1. Select **root**
2. Press Enter for maintenance shell
3. Remount filesystem as read-write:

```bash
mount -o remount,rw /
```

## GRUB Recovery

### "GRUB rescue>" Prompt

System can't find GRUB configuration:

```bash
# List available partitions
grub rescue> ls
# (hd0) (hd0,gpt1) (hd0,gpt2) (hd0,gpt3)

# Find partition with /boot (the 1 GB ext4 /boot on the primary)
grub rescue> ls (hd0,gpt2)/
# Should list vmlinuz, initrd.img, grub/

# Set prefix and load normal module
grub rescue> set prefix=(hd0,gpt2)/grub
grub rescue> insmod normal
grub rescue> normal
```

### Reinstall GRUB

Boot from live USB, then (device paths for this build's ext4 layout — see [Disk Partitioning](../installation/disk-partitioning.md); the primary 4 TB NVMe is `nvme0n1`):

```bash
# Mount root filesystem (nvme0n1p3 = 500 GB ext4 root)
sudo mount /dev/nvme0n1p3 /mnt

# Mount /boot (nvme0n1p2) and EFI (nvme0n1p1)
sudo mount /dev/nvme0n1p2 /mnt/boot
sudo mount /dev/nvme0n1p1 /mnt/boot/efi

# Mount virtual filesystems
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys

# Chroot into system
sudo chroot /mnt

# Reinstall GRUB (target the whole disk, not a partition)
grub-install /dev/nvme0n1
update-grub

# Exit and reboot
exit
sudo reboot
```

### Fix GRUB Configuration

From recovery shell or chroot:

```bash
# Update GRUB config
update-grub

# Verify config
cat /boot/grub/grub.cfg | grep menuentry
```

### GRUB Boot Parameters

At GRUB menu, press **e** to edit, then modify the `linux` line:

| Parameter | Purpose |
|-----------|---------|
| single | Single-user mode |
| init=/bin/bash | Boot directly to bash |
| systemd.unit=rescue.target | Rescue target |
| systemd.unit=emergency.target | Emergency target |
| nomodeset | Disable kernel mode setting |
| quiet splash | Hide boot messages |
| nosplash | Show boot messages |

Press **Ctrl+X** or **F10** to boot with modified parameters.

## LUKS Encryption Issues

!!! note "Not applicable to this build's default layout"
    This build uses an **unencrypted plain ext4 root** (no LUKS). LUKS unlock, recovery keys, and header backup/restore only apply if you followed the "Encrypted Alternative — LUKS + LVM" path in [Disk Partitioning](../installation/disk-partitioning.md#encrypted-alternative-zfs-native-encryption-or-luks-lvm); the `cryptsetup` man pages cover that path. (ZFS native encryption on the `hot`/`tank` data pools, if used, is unlocked with `zfs load-key` after the pool imports — it does not gate boot.)

## Kernel Issues

### Kernel Panic

If system panics on boot:

1. Boot previous kernel from GRUB
2. At GRUB menu, select **Advanced options**
3. Select older kernel version

### Remove Problematic Kernel

From recovery mode or live USB:

```bash
# List installed kernels
dpkg --list | grep linux-image

# Remove specific kernel
sudo apt remove linux-image-x.x.x-generic

# Update GRUB
sudo update-grub
```

### Reinstall Current Kernel

```bash
sudo apt install --reinstall linux-image-$(uname -r)
sudo update-grub
```

## systemd Issues

### Emergency Mode

System boots to emergency shell:

```bash
# Check what failed
systemctl --failed

# Check specific unit
systemctl status failed-unit.service
journalctl -u failed-unit.service

# Try to start graphical target
systemctl isolate graphical.target

# Or multi-user
systemctl isolate multi-user.target
```

### Dependency Failures

```bash
# Check dependency tree
systemctl list-dependencies multi-user.target

# Check what's blocking
systemctl list-jobs
```

### Skip Failed Services

Temporarily disable problematic service:

```bash
# Mask service (prevents start)
systemctl mask problematic.service

# Boot should proceed
systemctl isolate multi-user.target

# Later, fix and unmask
systemctl unmask problematic.service
```

## Filesystem / Pool Issues

### fsck the ext4 Root

The root, `/boot`, and `/boot/efi` are classic filesystems — a corrupted root is an `fsck`, not a ZFS operation:

```bash
# Boot to recovery mode or live USB

# Check the root filesystem (unmount first if from live USB)
sudo umount /dev/nvme0n1p3
sudo fsck -y /dev/nvme0n1p3

# For the running root, use recovery mode — it runs fsck automatically,
# or force one on next boot:
sudo touch /forcefsck
```

### Fix fstab Errors

A bad fstab entry can prevent boot:

```bash
# From recovery mode with remounted root
mount -o remount,rw /

# Edit fstab
nano /etc/fstab

# Common issues:
# - Wrong UUID (check with blkid)
# - Missing partition
# - Typo in mount point

# Comment out problematic line with #, reboot, fix properly
```

Get correct UUIDs with `sudo blkid`. Note the ZFS pools (`hot`, `tank`) have **no fstab entries** — they mount natively via ZFS, so a broken fstab can only affect the ext4/FAT mounts (`/`, `/boot`, `/boot/efi`).

### A ZFS Data Pool Won't Import

ZFS does **not** use `fsck` — there is no `zpool fsck`. Integrity is checked and repaired with `zpool scrub` and read back with `zpool status`; ZFS self-heals corrupted blocks it can reconstruct from checksums. The data pools (`hot`, `tank`) are imported by `zfs-import-cache.service` after root is already up, so a pool problem does not stop boot — you land at a login prompt with a pool missing.

```bash
# See importable pools (scan by-id for stability)
sudo zpool import -d /dev/disk/by-id

# Force-import a pool that was not cleanly exported
sudo zpool import -f -d /dev/disk/by-id hot
sudo zpool import -f -d /dev/disk/by-id tank

# Last resort: roll back the last few transactions of a damaged pool
sudo zpool import -F -f hot
```

### Detect and Repair Pool Corruption

```bash
# Health and error counters for both pools
zpool status -v hot
zpool status -v tank

# Start a scrub (verifies every block against its checksum)
sudo zpool scrub hot
sudo zpool scrub tank

# If a scrub reports repaired/permanent errors, clear the counters after review
sudo zpool clear hot
```

!!! note "No redundancy on this build — scrub detects, it can't always repair"
    Each pool is a single-disk vdev (snapshots + off-host replication substitute for RAID). A scrub will *detect* corruption via checksums, but with no redundant copy it can only repair blocks that have `copies>1` or ditto metadata. Permanent errors mean restoring the affected dataset from a snapshot or backup — see [ZFS Datasets](../../zfs/datasets.md) and the [rebuild checklist](../../operations/rebuild-checklist.md).

## Network Prevents Boot

### Waiting for Network

If boot hangs waiting for network:

```bash
# Temporarily disable network wait
systemctl mask systemd-networkd-wait-online.service

# Boot, then fix network config
# Then unmask
systemctl unmask systemd-networkd-wait-online.service
```

### Fix Netplan

From recovery:

```bash
mount -o remount,rw /

# Check netplan config (networkd renderer for this build)
cat /etc/netplan/*.yaml

# Validate — shows errors
netplan generate

# Apply working config
netplan apply
```

## Live USB Recovery

### Boot from Live USB

1. Create Ubuntu live USB
2. Boot from USB
3. Select "Try Ubuntu", or the Server ISO's shell

### Chroot into System

```bash
# Find your partitions
lsblk

# Mount root (nvme0n1p3 = 500 GB ext4 root on the primary)
sudo mount /dev/nvme0n1p3 /mnt

# Mount /boot (nvme0n1p2) and EFI (nvme0n1p1)
sudo mount /dev/nvme0n1p2 /mnt/boot
sudo mount /dev/nvme0n1p1 /mnt/boot/efi

# Mount virtual filesystems
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys

# Chroot
sudo chroot /mnt

# Now run repairs as if on actual system (reinstall kernel/GRUB, fix netplan)
# Exit when done
exit
sudo reboot
```

If you also need the data pools from the live environment: `sudo apt install -y zfsutils-linux` then `sudo zpool import -f -d /dev/disk/by-id hot` (and `tank`).

!!! note "LUKS+LVM alternative"
    If you followed the encrypted alternative from [Disk Partitioning](../installation/disk-partitioning.md#encrypted-alternative-zfs-native-encryption-or-luks-lvm), unlock first with `sudo cryptsetup open /dev/nvme0n1p3 cryptroot` and mount the resulting `/dev/mapper/...` root device instead of `nvme0n1p3`.

## Quick Reference

### Boot to Different Targets

From GRUB, add to linux line:

```
systemd.unit=rescue.target      # Rescue mode
systemd.unit=emergency.target   # Emergency mode
systemd.unit=multi-user.target  # No GUI
init=/bin/bash                  # Direct bash
```

### Key Commands

```bash
# Recovery mode
mount -o remount,rw /        # Remount root writable

# GRUB
grub-install /dev/nvme0n1    # Reinstall GRUB (whole disk)
update-grub                  # Update config

# Kernel
dpkg --list | grep linux-image  # List kernels

# ext4 filesystem
fsck -y /dev/nvme0n1p3       # Fix root filesystem
blkid                        # Show UUIDs

# ZFS data pools
zpool status -v hot          # Health + errors
zpool scrub hot              # Verify/repair (ZFS has no fsck)
zpool import -f -d /dev/disk/by-id hot   # Recovery import

# systemd
systemctl --failed           # Show failures
systemctl mask service       # Prevent start
systemctl isolate target     # Switch target
```

## Prevention

### Keep Backup Kernels

```bash
# Don't autoremove all old kernels — keep at least one previous version
# so a bad kernel is a GRUB "Advanced options" pick, not a reinstall

# Check how many to keep
grep -r "APT::NeverAutoRemove" /etc/apt/
```

### Back Up GRUB and the ESP

```bash
# Copy current GRUB config and record the EFI boot entries
sudo cp -r /boot/grub /safe/location/grub-backup
sudo efibootmgr -v > ~/efi-boot-entries.txt
```

### Scrub On A Schedule

```bash
# A monthly scrub catches silent corruption on the data pools before it spreads
sudo zpool scrub hot
sudo zpool scrub tank
```

## Next Steps

If you've resolved boot issues, continue to [Network Issues](network-issues.md) for network troubleshooting.
