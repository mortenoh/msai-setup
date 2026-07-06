# Disk Partitioning

This page is the canonical disk layout for the MS-S1 MAX install: **plain ext4 root on the primary 2 TB NVMe, with ZFS picking up the leftover space and the entire 4 TB secondary NVMe**.

Authoritative spec (slot speeds matter — see warning below): [Minisforum MS-S1 MAX product page](https://www.minisforum.com/products/ms-s1-max).

!!! note "Two storage slots, two speeds"
    The MS-S1 MAX exposes **two M.2 slots: PCIe 4.0 x4 (primary) and PCIe 4.0 x1 (secondary)**. The x1 slot tops out around 2 GB/s — fine for ZFS-backed media and cold data, slow for VM disks or hot databases. Put the 2 TB drive in the x4 slot, the 4 TB drive in the x1 slot, and keep VM disks on the primary drive.

## Canonical Layout — plain ext4 root + ZFS data pool

This is the layout used by [`hardware.md`](../../getting-started/hardware.md), [`zfs/partitioning.md`](../../zfs/partitioning.md), and the [`rebuild-checklist.md`](../../operations/rebuild-checklist.md).

### Internal NVMe (slot 1, 2 TB, PCIe 4.0 x4)

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| EFI System | 512 MB | FAT32 (esp) | `/boot/efi` | UEFI bootloader |
| Boot | 1 GB | ext4 | `/boot` | Kernel, initramfs |
| Root | 1 TB | ext4 | `/` | Host OS, container compose files, libvirt VM XML |
| Unallocated | ~1 TB | — | (ZFS) | Pool member, added post-install |

### Secondary NVMe (slot 2, 4 TB, PCIe 4.0 x1)

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| ZFS data | 4 TB | (ZFS) | (ZFS) | Pool member, entire disk |

ZFS pool creation happens after Ubuntu is installed — see [ZFS Partitioning](../../zfs/partitioning.md) and [ZFS Pool Creation](../../zfs/pool-creation.md). At installation time, just **leave the ~1 TB on the primary disk and the entire 4 TB drive unallocated**. Do not let the installer's "guided" mode touch the secondary drive.

### Why this layout

- **ext4 root is boring infrastructure**. Excellent recovery tooling, zero operational surprises, mature `e2fsck`.
- **Separate `/boot`** survives a corrupted root and gives GRUB a stable home.
- **ZFS is for data only, never root**. Snapshots and backups protect data; the OS is rebuildable.
- **No LVM**. The root drive doesn't need volume management — `/` either fits or doesn't. The 1 TB target leaves plenty of headroom.
- **No LUKS by default** on this build. The host lives on a private network behind UFW/Tailscale; LUKS just adds a remote-unlock problem on a headless box. See the "Encrypted alternative" section below if you need it.

## Creating Partitions in the Ubuntu 26.04 Installer

### Step 1 — pick Custom storage layout

When the storage screen appears, choose **Custom storage layout**. Do not use guided/entire-disk — it will format the wrong drive.

### Step 2 — partition the 2 TB primary NVMe

1. Select the primary NVMe.
2. Add partition: **size 512 MB**, format **fat32**, mount `/boot/efi`.
3. Add partition: **size 1 GB**, format **ext4**, mount `/boot`.
4. Add partition: **size 1 TB** (`1024G` or `1000G` depending on installer rounding), format **ext4**, mount `/`.
5. Leave the remaining ~1 TB as **free space**.

### Step 3 — leave the 4 TB secondary NVMe alone

Confirm the secondary NVMe is listed but has **no partitions**. If the installer pre-created any, delete them. ZFS will claim the whole disk later.

### Step 4 — review and confirm

The summary should look approximately like:

```
nvme0n1               disk   2.0T
  nvme0n1p1           part   512M  /boot/efi  (fat32)
  nvme0n1p2           part   1.0G  /boot       (ext4)
  nvme0n1p3           part   1.0T  /           (ext4)
  (free space)               ~1.0T

nvme1n1               disk   4.0T
  (free space)               4.0T
```

!!! danger "Verify before confirming"
    Proceeding wipes the selected disks. Double-check that you've identified the correct drives and that the 4 TB drive has no partitions defined.

## Mount Options for Security

For a server, harden mount options in `/etc/fstab` after install:

```
# /etc/fstab
/dev/nvme0n1p1   /boot/efi  vfat   umask=0077,fmask=0077,dmask=0077  0 1
/dev/nvme0n1p2   /boot      ext4   defaults,nodev,nosuid,noexec      0 2
/dev/nvme0n1p3   /          ext4   defaults                          0 1
```

If you want stricter isolation, mount `/tmp` and `/var/log` as separate filesystems (or `tmpfs` for `/tmp`) with `nodev,nosuid,noexec` — but on this build the simpler unified ext4 root is sufficient. ZFS datasets under `/mnt/tank/` get their own per-dataset mount options.

## Post-Partitioning Verification

```bash
# View block devices
lsblk

# Verify the partition layout
sudo parted /dev/nvme0n1 print
sudo parted /dev/nvme1n1 print

# Check fstab is sane
cat /etc/fstab
findmnt /

# Free space available for ZFS
sudo parted /dev/nvme0n1 unit GB print free
```

## Encrypted Alternative — LUKS + LVM

If you do need full-disk encryption on the root drive (regulated environment, physical-theft concern), the layout below works but adds operational overhead on a headless box. You'll need either a yubikey/Tang/Clevis unlock mechanism, an out-of-band unlock channel (BMC/IPMI — not present on the MS-S1 MAX), or you'll have to walk to the machine to type the passphrase on reboot.

### LUKS + LVM layout

| Partition | Size | Type | Purpose |
|-----------|------|------|---------|
| EFI System | 512 MB | FAT32 | UEFI bootloader |
| Boot | 1 GB | ext4 | Kernel (unencrypted by necessity) |
| LUKS container | 1 TB | LUKS2 | Holds the LVM physical volume |
| Unallocated | ~1 TB | — | ZFS pool member (encrypted via ZFS native encryption if needed) |

### LVM volumes within the LUKS container

| Volume | Size | Mount | Notes |
|--------|------|-------|-------|
| `lv-root` | 100 GB | `/` | OS only |
| `lv-var` | 200 GB | `/var` | Docker bind-mount targets land here unless redirected to ZFS |
| `lv-var-log` | 50 GB | `/var/log` | `nodev,nosuid,noexec` |
| `lv-tmp` | 20 GB | `/tmp` | `nodev,nosuid,noexec` |
| `lv-swap` | 16 GB | swap | Optional; sized for hibernation if used |
| (free) | ~614 GB | — | Reserved for future growth |

Sizing assumes you push container/VM data into ZFS rather than `/var`. If you keep Docker's default `/var/lib/docker` and don't bind-mount, grow `lv-var` accordingly.

### LUKS unlock on a headless box

The reasonable options on this hardware:

- **Walk-up unlock**: Connect a keyboard and the HDMI output for first boot. Painful for reboots.
- **`dropbear-initramfs`**: Open SSH in the initramfs so you can unlock remotely. Add `dropbear-initramfs` and copy your unlock SSH key into `/etc/dropbear/initramfs/authorized_keys`. Works well, requires the box to have a stable IP/static route at unlock time.
- **Clevis + Tang**: Network-bound disk encryption against a Tang server elsewhere on your network. Unlock is automatic when the Tang server is reachable. Good for a homelab with a separate always-on Tang host.

If you go this route, plan the unlock mechanism *before* you encrypt — locking yourself out of the only host is not a fun recovery exercise.

### Encryption walkthrough sketch

This is intentionally a sketch — the canonical, more detailed walkthrough is built around the plain-ext4 layout above. For the LUKS path, the additional installer steps are:

1. Create EFI and `/boot` as above.
2. Create a third partition of 1 TB on the primary NVMe; mark it for use as an encrypted volume.
3. Set a strong passphrase (≥20 chars; store in a password manager).
4. On the resulting dm-crypt device, create an LVM volume group (`vg-system`).
5. Create logical volumes per the table above.
6. Mount each LV to its target.
7. Leave the remaining ~1 TB and the entire secondary NVMe unallocated for ZFS.

For LUKS key-slot management, recovery keys, and `cryptsetup luksDump`, see the `cryptsetup` man pages — they're better than anything we'd duplicate here.

## Next Step

Continue to [Installation Walkthrough](installation-walkthrough.md) to proceed through the Ubuntu installer.
