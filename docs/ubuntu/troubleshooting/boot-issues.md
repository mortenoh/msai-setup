# Boot Issues

This page covers diagnosing and resolving boot problems on Ubuntu Server 24.04 LTS.

## Boot Process Overview

### Normal Boot Sequence

```
┌─────────────────────────────────────────────────────────────┐
│                    1. UEFI/BIOS                              │
│              Hardware initialization                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. GRUB Bootloader                        │
│            Load kernel and initramfs                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. Kernel + initramfs                     │
│        Load drivers, unlock LUKS, mount root                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. systemd (PID 1)                        │
│            Start services, reach target                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. Login Prompt                           │
│                System ready                                  │
└─────────────────────────────────────────────────────────────┘
```

## Identifying Boot Stage

### Where Did It Fail?

| Symptom | Stage | See Section |
|---------|-------|-------------|
| No POST, no display | Hardware/BIOS | Hardware issue |
| GRUB menu not shown | GRUB | GRUB Recovery |
| "GRUB rescue>" prompt | GRUB config | GRUB Recovery |
| Stuck at LUKS prompt | LUKS unlock | LUKS Issues |
| Kernel panic | Kernel | Kernel Issues |
| systemd errors | Init | systemd Issues |
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

# Find partition with /boot
grub rescue> ls (hd0,gpt2)/boot/
# Should list vmlinuz, initrd.img, grub/

# Set prefix and load normal module
grub rescue> set prefix=(hd0,gpt2)/boot/grub
grub rescue> insmod normal
grub rescue> normal
```

### Reinstall GRUB

Boot from live USB, then:

```bash
# Mount root filesystem
sudo mount /dev/sda2 /mnt

# Mount EFI (if UEFI)
sudo mount /dev/sda1 /mnt/boot/efi

# Mount virtual filesystems
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys

# Chroot into system
sudo chroot /mnt

# Reinstall GRUB
grub-install /dev/sda
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

### Wrong Passphrase

If LUKS passphrase isn't working:

```bash
# Boot from live USB
# Find LUKS partition
lsblk

# Test unlock
sudo cryptsetup open /dev/sda3 cryptroot
# Enter passphrase

# If successful, mount and continue boot
sudo mount /dev/mapper/vg--system-lv--root /mnt
```

### Add Recovery Key

From live USB with volume unlocked:

```bash
# Add additional passphrase
sudo cryptsetup luksAddKey /dev/sda3

# Or add key file
sudo cryptsetup luksAddKey /dev/sda3 /path/to/keyfile
```

### LUKS Header Backup/Restore

```bash
# Backup (do this on healthy system!)
sudo cryptsetup luksHeaderBackup /dev/sda3 --header-backup-file luks-header.img

# Restore from backup
sudo cryptsetup luksHeaderRestore /dev/sda3 --header-backup-file luks-header.img
```

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

## Filesystem Issues

### fsck on Boot

If filesystem check fails:

```bash
# Boot to recovery mode or live USB

# Check filesystem (unmount first if needed)
sudo umount /dev/sda2
sudo fsck -y /dev/sda2

# For root filesystem, use recovery mode
# It will run fsck automatically
```

### Fix fstab Errors

Bad fstab entry can prevent boot:

```bash
# From recovery mode with remounted root
mount -o remount,rw /

# Edit fstab
nano /etc/fstab

# Common issues:
# - Wrong UUID (check with blkid)
# - Missing partition
# - Typo in mount point

# Comment out problematic line with #
# Reboot and fix properly
```

### Get Correct UUIDs

```bash
# List all UUIDs
sudo blkid

# Update fstab with correct UUID
# UUID=xxxx-xxxx /mount/point ext4 defaults 0 2
```

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

# Check netplan config
cat /etc/netplan/*.yaml

# Fix syntax issues
netplan generate
# Shows errors

# Apply working config
netplan apply
```

## Live USB Recovery

### Boot from Live USB

1. Create Ubuntu live USB
2. Boot from USB
3. Select "Try Ubuntu"

### Chroot into System

```bash
# Find your partitions
lsblk

# Mount root
sudo mount /dev/sda2 /mnt

# If LUKS encrypted
sudo cryptsetup open /dev/sda3 cryptroot
sudo mount /dev/mapper/vg--system-lv--root /mnt

# Mount other partitions
sudo mount /dev/sda1 /mnt/boot/efi
sudo mount --bind /dev /mnt/dev
sudo mount --bind /proc /mnt/proc
sudo mount --bind /sys /mnt/sys

# Chroot
sudo chroot /mnt

# Now run repairs as if on actual system
# Exit when done
exit
sudo reboot
```

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
grub-install /dev/sda        # Reinstall GRUB
update-grub                  # Update config

# Kernel
dpkg --list | grep linux-image  # List kernels

# Filesystem
fsck -y /dev/sda2            # Fix filesystem
blkid                        # Show UUIDs

# systemd
systemctl --failed           # Show failures
systemctl mask service       # Prevent start
systemctl isolate target     # Switch target
```

## Prevention

### Keep Backup Kernels

```bash
# Don't autoremove all old kernels
# Keep at least one previous version

# Check how many to keep
grep -r "APT::NeverAutoRemove" /etc/apt/
```

### Backup LUKS Header

```bash
# Critical! Do this on healthy system
sudo cryptsetup luksHeaderBackup /dev/sda3 \
    --header-backup-file /safe/location/luks-header-backup.img
```

### Backup GRUB

```bash
# Copy current config
sudo cp -r /boot/grub /safe/location/grub-backup
```

## Next Steps

If you've resolved boot issues, continue to [Network Issues](network-issues.md) for network troubleshooting.
