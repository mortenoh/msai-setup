# Boot Issues

This page covers diagnosing and resolving boot problems on Ubuntu Server 26.04 LTS. This build boots **root-on-ZFS via [ZFSBootMenu](https://zfsbootmenu.org/)** (see [Disk Partitioning](../installation/disk-partitioning.md)) — there is no GRUB anywhere in this architecture. If you followed the ext4 alternative instead, the GRUB-based recovery in this page's git history applies to you.

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
│                    2. ZFSBootMenu (EFI binary)               │
│        Import rpool, find kernel/initramfs in a dataset      │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    3. Kernel + initramfs (dracut)            │
│        Load drivers, mount rpool/ROOT/ubuntu as root         │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    4. systemd (PID 1)                        │
│            Start services, reach target                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              v
┌─────────────────────────────────────────────────────────────┐
│                    5. Login Prompt                           │
│                System ready                                  │
└─────────────────────────────────────────────────────────────┘
```

ZFSBootMenu replaces GRUB entirely: the firmware launches the ZFSBootMenu EFI executable directly, it imports `rpool`, and it kexecs the kernel/initramfs pair it finds inside the selected boot environment (`rpool/ROOT/ubuntu` by default).

## Identifying Boot Stage

### Where Did It Fail?

| Symptom | Stage | See Section |
|---------|-------|-------------|
| No POST, no display | Hardware/BIOS | [BIOS reset](../../getting-started/bios-setup.md#recovering-from-a-bad-bios-state) |
| Firmware boots to nothing / falls through to next device | ZFSBootMenu not found | ZFSBootMenu Recovery |
| ZFSBootMenu appears but can't import the pool | ZFS pool import | ZFSBootMenu Recovery |
| Selected boot environment fails to boot | Boot environment / kernel | ZFSBootMenu Recovery, Kernel Issues |
| Kernel panic | Kernel | Kernel Issues |
| systemd errors | Init | systemd Issues |
| Services fail | Services | Service Recovery |

## ZFSBootMenu Recovery

ZFSBootMenu *is* the bootloader. When it launches it shows a short countdown, then boots the default boot environment. Press any key (**Esc**, **Space**, or an arrow key) during the countdown to stay in the menu.

### ZFSBootMenu Hotkeys

From the ZFSBootMenu screen:

| Key | Action |
|-----|--------|
| `Enter` | Boot the selected boot environment |
| Arrow keys / `j` `k` | Navigate the boot-environment list |
| `Ctrl+E` | Edit the kernel command line for this one boot |
| `Ctrl+K` | Select a different kernel within the environment |
| `Ctrl+S` | Snapshot menu (create / clone / **roll back** a boot environment) |
| `Ctrl+A` | Set the selected environment as the default (`bootfs`) |
| `Ctrl+P` | Show `zpool status` |
| `Ctrl+R` | Drop to the ZFSBootMenu **recovery shell** |
| `Ctrl+H` | Help / full key list |

### Boot a Different (Working) Boot Environment

If the current root is broken (bad upgrade, bad kernel), select a previous boot environment or snapshot instead:

1. At the ZFSBootMenu screen, use the arrow keys to highlight a healthy environment or an older snapshot of `rpool/ROOT/ubuntu`.
2. Press `Enter` to boot it once, or `Ctrl+A` to make it the persistent default.
3. To roll a snapshot back into a bootable environment, press `Ctrl+S`, pick the snapshot, and choose clone/rollback.

This snapshot-rollback path is the whole point of boot environments — a bad `apt upgrade` is a one-keystroke recovery, not a reinstall.

### Drop to the Emergency Shell

Press `Ctrl+R` at the ZFSBootMenu screen to get a recovery shell with the ZFS tools available. From there you can inspect and repair the pool:

```bash
# See what pools are visible
zpool import

# Force-import the root pool read-write into /mnt
zpool import -f -R /mnt rpool

# Mount the boot environment explicitly if it did not auto-mount
zfs mount rpool/ROOT/ubuntu

# Inspect, then chroot if you need to run commands against the installed system
chroot /mnt
```

### ZFSBootMenu Doesn't Appear At All

If the firmware skips ZFSBootMenu (falls through to the next boot device or a "no bootable device" message), the EFI boot entry is missing or misordered. From a live/rescue environment:

```bash
# List EFI entries and boot order
sudo efibootmgr -v

# ZFSBootMenu missing? See "Reinstall / Repair ZFSBootMenu" below.
# Present but not first? Reorder it to the front (use the real hex IDs):
sudo efibootmgr -o 0003,0000,2001
```

## Reinstall / Repair ZFSBootMenu

There is no `grub-install` here — recovery means re-placing the EFI binary and re-registering the `efibootmgr` entry. Boot a live/rescue environment, import the pool, and mount the EFI partition:

```bash
# Import the root pool into /mnt (by-id paths are the most reliable)
sudo zpool import -f -d /dev/disk/by-id -R /mnt rpool
sudo zfs mount rpool/ROOT/ubuntu

# Identify and mount the EFI partition (part1 of the 4 TB primary NVMe)
export PRIMARY_DISK=/dev/disk/by-id/nvme-<4TB-model-and-serial>
sudo mkdir -p /mnt/boot/efi
sudo mount "${PRIMARY_DISK}-part1" /mnt/boot/efi
```

Re-fetch the prebuilt ZFSBootMenu image (or re-run `generate-zbm` inside a chroot if you build from source):

```bash
sudo mkdir -p /mnt/boot/efi/EFI/ZBM
sudo curl -o /mnt/boot/efi/EFI/ZBM/VMLINUZ.EFI -L https://get.zfsbootmenu.org/efi
sudo cp /mnt/boot/efi/EFI/ZBM/VMLINUZ.EFI /mnt/boot/efi/EFI/ZBM/VMLINUZ-BACKUP.EFI
```

Re-register the EFI boot entry:

```bash
sudo efibootmgr --create \
    --disk "$PRIMARY_DISK" --part 1 \
    --label "ZFSBootMenu" \
    --loader '\EFI\ZBM\VMLINUZ.EFI'

sudo efibootmgr -v      # confirm it is present and first in the order
```

### Fix the Kernel Command Line

ZFSBootMenu reads the kernel command line for a boot environment from a ZFS property, not a `grub.cfg`. To change it permanently:

```bash
# From the running system or a chroot
sudo zfs set org.zfsbootmenu:commandline="quiet loglevel=4" rpool/ROOT/ubuntu

# Verify
zfs get org.zfsbootmenu:commandline rpool/ROOT/ubuntu
```

To override the command line for a single boot only, press `Ctrl+E` at the ZFSBootMenu screen and edit it inline.

### ZFSBootMenu Emergency Command Line Parameters

Add these to the command line (via `Ctrl+E`, or the `org.zfsbootmenu:commandline` property) to reach a minimal system:

| Parameter | Purpose |
|-----------|---------|
| `single` | Single-user mode |
| `systemd.unit=rescue.target` | Rescue target |
| `systemd.unit=emergency.target` | Emergency target |
| `init=/bin/bash` | Boot directly to bash |
| `nomodeset` | Disable kernel mode setting |
| `zbm.show` | Force ZFSBootMenu to stop at the menu instead of auto-booting |

## LUKS / Encryption Issues

!!! note "Not applicable to this build's default layout"
    This build uses an **unencrypted root-on-ZFS** pool (no LUKS, no ZFS native encryption). Passphrase unlock, recovery keys, and header backup/restore only apply if you chose an encrypted path — see [Encrypted Alternative](../installation/disk-partitioning.md#encrypted-alternative-zfs-native-encryption-or-luks-lvm) in Disk Partitioning. ZFS native encryption composes with ZFSBootMenu, which prompts for the passphrase at the boot menu when a boot environment's dataset is encrypted.

## Kernel Issues

### Kernel Panic

With boot environments, a bad kernel is almost never worth debugging in place — the fast fix is to boot a previous, known-good environment or snapshot:

1. Interrupt the ZFSBootMenu countdown (press a key).
2. Highlight a previous boot environment or an older snapshot of `rpool/ROOT/ubuntu`.
3. Press `Enter` to boot it, or `Ctrl+S` to roll a snapshot back.

### Why not just remove the kernel package?

On ext4 you would `apt remove` the bad kernel and `update-grub`. Inside a ZFS boot environment that is the wrong instinct: the failing kernel lives in the *same* dataset you would have to boot to remove it, and removing packages doesn't undo whatever else the bad upgrade changed. **Rolling back to a previous boot environment is the correct move** — it reverts the kernel and everything else in one atomic step.

If you do need to manage kernels from a known-good environment:

```bash
# List installed kernels
dpkg --list | grep linux-image

# Reinstall the current kernel (rebuilds the dracut initramfs ZFSBootMenu reads)
sudo apt install --reinstall linux-generic
sudo update-initramfs -c -k all
```

There is no `update-grub` step — ZFSBootMenu finds the kernel/initramfs inside the dataset directly at boot.

## systemd Issues

### Emergency Mode

System boots to emergency shell:

```bash
# Check what failed
systemctl --failed

# Check specific unit
systemctl status failed-unit.service
journalctl -u failed-unit.service

# Try to reach multi-user
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

Temporarily disable a problematic service:

```bash
# Mask service (prevents start)
systemctl mask problematic.service

# Boot should proceed
systemctl isolate multi-user.target

# Later, fix and unmask
systemctl unmask problematic.service
```

## Filesystem / Pool Issues

ZFS does **not** use `fsck` — there is no `zpool fsck`. Integrity is checked and repaired with `zpool scrub` and read back with `zpool status`; ZFS self-heals corrupted blocks it can reconstruct from checksums.

### Detect and Repair Corruption

```bash
# Health and error counters for both pools
zpool status -v rpool
zpool status -v tank

# Start a scrub (verifies every block against its checksum)
sudo zpool scrub rpool
sudo zpool scrub tank

# Watch progress
zpool status rpool

# If a scrub reports repaired/permanent errors, clear the counters after review
sudo zpool clear rpool
```

!!! note "No redundancy on this build — scrub detects, it can't always repair"
    Each pool is a single-disk vdev (snapshots + off-host replication substitute for RAID). A scrub will *detect* corruption via checksums, but with no redundant copy it can only repair blocks that have `copies>1` or ditto metadata. Permanent errors mean restoring the affected dataset from a snapshot or backup — see [ZFS Datasets](../../zfs/datasets.md) and the [rebuild checklist](../../operations/rebuild-checklist.md).

### A Pool Won't Import

```bash
# See importable pools (scan by-id for stability)
sudo zpool import -d /dev/disk/by-id

# Force-import a pool that was not cleanly exported
sudo zpool import -f -d /dev/disk/by-id rpool
sudo zpool import -f -d /dev/disk/by-id tank

# Last resort: roll back the last few transactions of a damaged pool
sudo zpool import -F -f rpool
```

### Fix a Bad EFI fstab Entry

The only fstab entry in this build is the EFI partition (ZFS datasets mount natively, so a broken fstab can only affect `/boot/efi`, not root). From a working boot environment or the ZFSBootMenu recovery shell:

```bash
# Get the EFI partition UUID
sudo blkid | grep -i vfat

# Fix or comment out the /boot/efi line
sudo nano /etc/fstab
```

## Network Prevents Boot

### Waiting for Network

If boot hangs waiting for network:

```bash
# Temporarily disable network wait
systemctl mask systemd-networkd-wait-online.service

# Boot, then fix network config, then unmask
systemctl unmask systemd-networkd-wait-online.service
```

### Fix Netplan

```bash
# Check netplan config (networkd renderer for this build)
cat /etc/netplan/*.yaml

# Validate — shows errors
netplan generate

# Apply working config
netplan apply
```

## Live USB Recovery

### Boot from Live USB

1. Create an Ubuntu live USB.
2. Boot from it and reach a root shell (Try Ubuntu, or the Server ISO's shell).
3. Install ZFS tools if the live image lacks them: `sudo apt install -y zfsutils-linux`.

### Import the Pool and Chroot

There are no `mount /dev/nvme0n1p3 /mnt` device mounts here — the root filesystem is a ZFS dataset. Import the pool with an alternate root and the dataset mounts itself:

```bash
# Import rpool into /mnt (by-id paths survive enumeration reshuffles)
sudo zpool import -f -d /dev/disk/by-id -R /mnt rpool

# rpool/ROOT/ubuntu is canmount=noauto — mount it explicitly
sudo zfs mount rpool/ROOT/ubuntu
sudo zfs mount rpool/home

# Mount the EFI partition (part1 of the 4 TB primary NVMe) for bootloader work
export PRIMARY_DISK=/dev/disk/by-id/nvme-<4TB-model-and-serial>
sudo mount "${PRIMARY_DISK}-part1" /mnt/boot/efi

# Bind-mount virtual filesystems and chroot
sudo mount --rbind /dev  /mnt/dev
sudo mount --rbind /proc /mnt/proc
sudo mount --rbind /sys  /mnt/sys
sudo chroot /mnt

# ... run repairs (reinstall kernel, re-run efibootmgr, fix netplan) ...

exit
sudo zpool export rpool
sudo reboot
```

If you also need `tank`, `sudo zpool import -f -d /dev/disk/by-id tank`.

## Quick Reference

### ZFSBootMenu Hotkeys (at the boot screen)

```
Enter     Boot selected environment
Ctrl+E    Edit kernel command line for this boot
Ctrl+S    Snapshot menu (roll back a boot environment)
Ctrl+A    Set selected environment as default
Ctrl+R    Recovery shell
Ctrl+P    zpool status
```

### Key Commands

```bash
# EFI boot entries
efibootmgr -v                       # List entries + boot order
efibootmgr -o 0003,0000             # Reorder (ZFSBootMenu first)

# ZFSBootMenu binary + kernel command line
curl -o /boot/efi/EFI/ZBM/VMLINUZ.EFI -L https://get.zfsbootmenu.org/efi
zfs set org.zfsbootmenu:commandline="quiet loglevel=4" rpool/ROOT/ubuntu

# Pools
zpool status -v rpool               # Health + errors
zpool scrub rpool                   # Verify/repair (ZFS has no fsck)
zpool import -f -d /dev/disk/by-id -R /mnt rpool   # Recovery import

# Kernel / initramfs
dpkg --list | grep linux-image      # List kernels
update-initramfs -c -k all          # Rebuild dracut initramfs

# systemd
systemctl --failed                  # Show failures
systemctl mask service              # Prevent start
systemctl isolate target            # Switch target
```

## Prevention

### Keep Boot Environments (instead of backup kernels)

Boot environments are this build's rollback mechanism. Keep a few around and snapshot before risky changes:

```bash
# Snapshot root before an upgrade
sudo zfs snapshot rpool/ROOT/ubuntu@pre-upgrade-$(date +%F)

# List boot-environment snapshots (rollback targets in ZFSBootMenu)
zfs list -t snapshot -r rpool/ROOT
```

`sanoid` automates this retention on `rpool/ROOT` — see [Backups](../../operations/rebuild-checklist.md).

### Back Up the EFI Binary and Boot Entries

There is no GRUB config to back up. What matters is the ZFSBootMenu EFI binary (already duplicated as `VMLINUZ-BACKUP.EFI` during install) and the `efibootmgr` entries:

```bash
# Record the current EFI boot entries and order
sudo efibootmgr -v > ~/efi-boot-entries.txt

# Keep a copy of the ZFSBootMenu image off the ESP
sudo cp /boot/efi/EFI/ZBM/VMLINUZ.EFI /safe/location/zbm-VMLINUZ.EFI
```

### Scrub On A Schedule

```bash
# A monthly scrub catches silent corruption before it spreads
sudo zpool scrub rpool
sudo zpool scrub tank
```

## Next Steps

If you've resolved boot issues, continue to [Network Issues](network-issues.md) for network troubleshooting.
