# ZFS Root (Alternative) — root-on-ZFS via ZFSBootMenu

!!! warning "This is a documented alternative, not this build's canonical path"
    The canonical install for the MS-S1 MAX is **plain ext4 root (500 GB) with GRUB**, created by Ubuntu's guided installer (Subiquity) — see [Disk Partitioning](disk-partitioning.md) and the [Installation Walkthrough](installation-walkthrough.md). This page preserves the fuller **root-on-ZFS via [ZFSBootMenu](https://zfsbootmenu.org/)** procedure for anyone who wants OS boot environments badly enough to accept the trade-offs below. Everything here puts `/` on a ZFS pool named `rpool`; the canonical build does not.

## Why this is the alternative, not the default

This project originally made root-on-ZFS the canonical install. Building and live-testing it surfaced enough friction on the **critical boot path** to demote it:

- **Ubuntu Server's installer has no root-on-ZFS path.** Subiquity (and its `autoinstall` automation) cannot put root on ZFS, so the entire install below is a manual live-environment procedure — partition, `zpool create`, `debootstrap`, chroot, ZFSBootMenu by hand. The guided installer that produces the canonical ext4 root is simply not available for this layout.
- **The upstream guides stop at 22.04.** OpenZFS's official Ubuntu root-on-ZFS HOWTOs were never updated past 22.04. The procedure here is adapted best-practice, not an upstream-supported path — you are on your own for version-specific breakage.
- **The boot path could not be rehearsed in the lab.** ZFSBootMenu is a UEFI executable; the VirtualBox ARM firmware used for the [ZFS lab](../../zfs/virtualbox-lab.md) cannot run it, so the one component that stands between you and an unbootable box is exactly the one the lab can never exercise. `msai lab install-zfs-root` rehearses the pool/dataset/debootstrap mechanics, but not the ZFSBootMenu boot itself.
- **The OpenZFS + kernel 7.0 combo is flagged EXPERIMENTAL.** On 26.04 it prints `EXPERIMENTAL` warnings and, during live testing, produced a real `zpool export` "pool is busy" wedge. For a *data* pool that is an inconvenience; for the *root* pool it is an unbootable machine.

The upside you are buying with that risk is genuine: OS-level snapshots as **boot environments**, so a bad `apt upgrade` or kernel is a one-keystroke rollback rather than a reinstall. Under the canonical build everything that matters (containers, VMs, data) already lives on ZFS with full snapshot coverage — only the thin, rebuildable OS layer loses rollback. If you want that layer covered too, this is the path.

!!! info "Rehearse it first"
    `msai lab install-zfs-root` walks the pool creation, dataset layout, and debootstrap of this flow inside a VM. It is the safe way to build muscle memory before doing it on the real disks. See the lab README for details.

## Layout — root-on-ZFS, two independent pools

The drive placement matches the canonical build (4 TB in the fast slot, 2 TB in the slow slot); only the primary drive's partitioning differs.

### Primary NVMe (slot 1, 4 TB, PCIe 4.0 x4) — boot + root + hot data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| EFI System | 512 MB | FAT32 (esp) | `/boot/efi` | Holds the ZFSBootMenu EFI binary |
| Pool member | ~4 TB | (ZFS) | — | Entire remainder -> `rpool` |

No separate `/boot` partition and no classic `bpool`/`rpool` split. ZFSBootMenu finds a kernel/initramfs pair directly inside a dataset at boot time — it doesn't need GRUB's workaround of a small, feature-limited boot pool sitting outside the main pool. One pool, one EFI partition, that's it.

### Secondary NVMe (slot 2, 2 TB, PCIe 4.0 x1) — bulk cold data

| Partition | Size | Filesystem | Mount | Purpose |
|-----------|------|------------|-------|---------|
| ZFS data | 2 TB | (ZFS) | — | Entire disk -> `tank`, a fully independent pool |

`tank` is not part of `rpool` and is never striped with it — these are two separate pools on two separate disks, imported independently. This is identical to the canonical build's `tank`; only `rpool` (holding root) is specific to this alternative.

### Why root-on-ZFS here

- **Root gets ZFS too.** The OS itself gets ZFS's checksums, compression, and — critically — **snapshots as boot environments**. A bad `apt upgrade` or kernel update is a ZFSBootMenu boot-environment rollback, not a reinstall.
- **ZFSBootMenu over GRUB.** GRUB's ZFS module has real limitations (it can't read every ZFS feature flag, historically breaking if a pool gains a feature GRUB doesn't understand), which is why classic root-on-ZFS guides split a `bpool`/`rpool` pair to work around it. ZFSBootMenu boots via its own dracut-built EFI executable instead of GRUB reading ZFS directly, so that split isn't needed.
- **No LUKS by default.** ZFS native encryption is the modern equivalent if you want encryption — set it on `rpool` at creation time and ZFSBootMenu prompts for the passphrase at boot.

## Creating the Layout (manual, live environment)

This is deliberately a manual process. Ubuntu Server's installer (Subiquity), including its `autoinstall` automation, has **no root-on-ZFS path**. The step-by-step command sequence below (live environment, partitioning, `zpool create` for both pools, bootstrapping Ubuntu into `rpool`, chroot, ZFSBootMenu install) is the whole install for this alternative — there is no guided-installer shortcut.

## Boot the Live/Rescue Environment

Because the install happens from a shell rather than the guided installer, you first need a live Ubuntu environment where you can run arbitrary commands.

### Initial Boot

1. Insert the Ubuntu Server 26.04 USB boot media.
2. Power on and enter the boot menu (F12, F8, or manufacturer-specific).
3. Select the USB device in **UEFI mode**.

### Reach a Shell

From the ISO's GRUB menu, select **Try or Install Ubuntu Server**. When the installer's first screen appears, open a shell instead of proceeding through the wizard:

- Press **Ctrl+Alt+F2** (or select **Help -> Enter shell** from the installer menu) to drop to a root shell on the live system.

A dedicated live/desktop environment that boots straight to a shell (e.g. an Ubuntu live image) works equally well — anything where you have a root prompt and network access.

## Prepare the Live Environment

### Network Access

`debootstrap` downloads the base system over the network, so the live environment needs connectivity. DHCP over a wired 10GbE port is simplest:

```bash
# Confirm an interface picked up an address
ip -br addr

# If not, bring one up with DHCP (replace enp6s0 with your interface)
sudo dhclient enp6s0
```

### Install ZFS Tooling in the Live Environment

The live shell needs the ZFS userspace tools and partitioning utilities to create the pools:

```bash
sudo apt update
sudo apt install -y debootstrap gdisk dosfstools zfsutils-linux
```

## Identify the Drives

This is the single most dangerous step. Confirm which physical NVMe is the 4 TB (primary/fast, slot 1) and which is the 2 TB (secondary/slow, slot 2) **before** running anything destructive.

```bash
# Human-readable overview — check the SIZE column
lsblk -d -o NAME,SIZE,MODEL

# NVMe-specific listing (model, serial, capacity)
sudo nvme list
```

Prefer stable `/dev/disk/by-id/...` paths over `/dev/nvme0n1` — kernel enumeration order (`nvme0n1` vs `nvme1n1`) is not guaranteed stable across boots, and pools created against a by-id path survive a reshuffle:

```bash
ls -l /dev/disk/by-id/ | grep nvme

# Export the two device paths once, verified, and reuse them everywhere below
export PRIMARY_DISK=/dev/disk/by-id/nvme-<4TB-model-and-serial>
export SECONDARY_DISK=/dev/disk/by-id/nvme-<2TB-model-and-serial>
```

!!! danger "Confirm SIZE before continuing"
    `$PRIMARY_DISK` must be the **4 TB** drive and `$SECONDARY_DISK` the **2 TB** drive. Every destructive command below reads these variables — a swap here formats the wrong disk. Re-run `lsblk -d -o NAME,SIZE,MODEL` and eyeball the sizes one more time.

## Partition and Create Both Pools

### Partition the primary 4 TB NVMe

```bash
sgdisk --zap-all "$PRIMARY_DISK"
sgdisk -n1:1M:+512M -t1:EF00 "$PRIMARY_DISK"   # EFI
sgdisk -n2:0:0      -t2:BF00 "$PRIMARY_DISK"   # ZFS pool member (rest of disk)
```

### Create rpool (primary, fast drive)

```bash
zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on -O canmount=off -O mountpoint=none \
    -R /mnt \
    rpool "${PRIMARY_DISK}-part2"

zfs create -o canmount=off -o mountpoint=none rpool/ROOT
zfs create -o canmount=noauto -o mountpoint=/ rpool/ROOT/ubuntu
zfs create -o mountpoint=/home rpool/home
```

`rpool/ROOT/ubuntu` uses `canmount=noauto` deliberately — with more than one boot environment present, ZFS must not try to auto-mount all of them; ZFSBootMenu (or an explicit `zfs mount`) decides which one actually becomes `/` at boot. Mount it now so `debootstrap` has a target:

```bash
zfs mount rpool/ROOT/ubuntu
zfs mount rpool/home
```

### Partition and create tank (secondary, slow drive)

```bash
sgdisk --zap-all "$SECONDARY_DISK"
sgdisk -n1:0:0 -t1:BF00 "$SECONDARY_DISK"

zpool create \
    -o ashift=12 -o autotrim=on \
    -O acltype=posixacl -O xattr=sa -O compression=lz4 \
    -O relatime=on \
    -R /mnt \
    tank "${SECONDARY_DISK}-part1"
```

`tank` holds no boot environments, so it skips the `canmount=off` / `ROOT` dance. Its data datasets (`tank/media`, `tank/backups`, etc.) are created later — see [ZFS Datasets](../../zfs/datasets.md).

### Format and mount the EFI partition

```bash
mkfs.vfat -F32 -n EFI "${PRIMARY_DISK}-part1"
mkdir -p /mnt/boot/efi
mount "${PRIMARY_DISK}-part1" /mnt/boot/efi
```

## Bootstrap Ubuntu into rpool

Install a minimal Ubuntu 26.04 base system into the mounted `rpool/ROOT/ubuntu` with `debootstrap`. The 26.04 suite is `resolute`; if the archive hasn't published a `resolute` path yet (common in the first weeks after an LTS release), fall back to `noble` (24.04) and dist-upgrade later:

```bash
# Pick the newest published suite, falling back to noble if resolute isn't live yet
SUITE=resolute
if ! curl -sfI "http://archive.ubuntu.com/ubuntu/dists/${SUITE}/Release" >/dev/null; then
    echo "Ubuntu archive suite '$SUITE' not published yet; falling back to noble"
    SUITE=noble
fi

debootstrap "$SUITE" /mnt http://archive.ubuntu.com/ubuntu
```

Copy the pool cache so the target system imports the same pools it was built on:

```bash
mkdir -p /mnt/etc/zfs
cp /etc/zfs/zpool.cache /mnt/etc/zfs/ 2>/dev/null || true
```

## Chroot and Configure

### Bind-mount and enter the chroot

```bash
mount --make-private --rbind /dev  /mnt/dev
mount --make-private --rbind /proc /mnt/proc
mount --make-private --rbind /sys  /mnt/sys

chroot /mnt /usr/bin/env SUITE="$SUITE" bash --login
```

### APT sources, base packages, kernel, and ZFS

Inside the chroot, write the APT sources for the suite you bootstrapped, then install the kernel and ZFS:

```bash
cat > /etc/apt/sources.list <<EOF
deb http://archive.ubuntu.com/ubuntu ${SUITE} main restricted universe multiverse
deb http://archive.ubuntu.com/ubuntu ${SUITE}-updates main restricted universe multiverse
deb http://security.ubuntu.com/ubuntu ${SUITE}-security main restricted universe multiverse
EOF

apt update

# linux-generic on 26.04 is the 7.0 kernel that already supports gfx1151.
# dosfstools for the EFI FS, zfs-initramfs to build a ZFS-aware (dracut) initramfs,
# zfsutils-linux at a version that understands the pool feature flags created above.
apt install -y --no-install-recommends \
    linux-generic \
    dosfstools \
    zfsutils-linux \
    zfs-initramfs \
    curl \
    efibootmgr \
    nano
```

!!! note "zfsutils-linux version must match the pool features"
    The `zfsutils-linux` inside the target must be new enough to open the feature flags `zpool create` set from the live environment. Installing from the same 26.04 archive you bootstrapped keeps them aligned; if you fell back to `noble`, dist-upgrade to 26.04 before relying on the pools long-term.

### Hostname and hosts

```bash
echo ms-s1-max > /etc/hostname
cat > /etc/hosts <<EOF
127.0.0.1   localhost
127.0.1.1   ms-s1-max
EOF
```

### Networking (netplan, systemd-networkd renderer)

Matching this repo's [networking convention](../networking.md) — Netplan with the `networkd` renderer, no NetworkManager:

```bash
cat > /etc/netplan/00-installer-config.yaml <<EOF
network:
  version: 2
  renderer: networkd
  ethernets:
    enp6s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
EOF
chmod 600 /etc/netplan/00-installer-config.yaml
```

Use DHCP instead by replacing the interface block with `dhcp4: true`. Adjust `enp6s0` to your actual interface name.

### fstab — EFI partition only

The ZFS datasets mount natively; only the EFI partition needs an fstab entry:

```bash
EFI_UUID=$(blkid -s UUID -o value "${PRIMARY_DISK}-part1")
cat >> /etc/fstab <<EOF
UUID=${EFI_UUID}   /boot/efi   vfat   umask=0077,fmask=0077,dmask=0077   0 1
EOF
```

`rpool` and `tank` deliberately have **no fstab entries** — they are ZFS-native mounts. Hardening flags like `nodev,nosuid,noexec` become per-dataset ZFS **properties** instead of fstab columns:

```bash
# Example: lock down a service scratch dataset
zfs set devices=off setuid=off exec=off rpool/some-dataset
```

### Create the admin user with SSH key auth

Create the initial privileged user and import your SSH public key. This build's convention is to **import keys from GitHub** — the easiest secure option — with a manual `authorized_keys` fallback:

```bash
# Create the admin user (adjust the username)
adduser admin
usermod -aG sudo admin

# Set a root/admin password for console recovery
passwd admin

# Preferred: import public keys straight from your GitHub account
apt install -y ssh-import-id openssh-server
sudo -u admin ssh-import-id gh:<your-github-username>

# Manual fallback if you would rather paste a key directly:
#   sudo -u admin mkdir -p /home/admin/.ssh && sudo -u admin chmod 700 /home/admin/.ssh
#   echo "ssh-ed25519 AAAA... you@example.com" | sudo -u admin tee -a /home/admin/.ssh/authorized_keys
#   sudo -u admin chmod 600 /home/admin/.ssh/authorized_keys
```

## Install ZFSBootMenu

This step replaces GRUB entirely. ZFSBootMenu is a self-contained UEFI executable (built with dracut) that, at boot, imports `rpool`, finds the kernel/initramfs pair inside `rpool/ROOT/ubuntu`, and kexecs into it. There is no `grub-install`, no `update-grub`, no `/boot/grub`.

### Tell ZFSBootMenu the kernel command line

ZFSBootMenu reads the kernel command line for a boot environment from a ZFS property on that dataset:

```bash
zfs set org.zfsbootmenu:commandline="quiet loglevel=4" rpool/ROOT/ubuntu
```

### Option A — prebuilt EFI binary (simplest)

ZFSBootMenu publishes a signed, prebuilt release image. Drop it into the EFI System Partition:

```bash
mkdir -p /boot/efi/EFI/ZBM
curl -o /boot/efi/EFI/ZBM/VMLINUZ.EFI -L https://get.zfsbootmenu.org/efi
cp /boot/efi/EFI/ZBM/VMLINUZ.EFI /boot/efi/EFI/ZBM/VMLINUZ-BACKUP.EFI
```

### Option B — build from source with `generate-zbm`

If you want a locally built image (e.g. to pin ZFS versions), install the package and configure `/etc/zfsbootmenu/config.yaml`:

```bash
apt install -y zfsbootmenu

cat > /etc/zfsbootmenu/config.yaml <<'EOF'
Global:
  ManageImages: true
  BootMountPoint: /boot/efi
  DracutConfDir: /etc/zfsbootmenu/dracut.conf.d
Components:
  Enabled: false
EFI:
  ImageDir: /boot/efi/EFI/ZBM
  Versions: false
  Enabled: true
Kernel:
  CommandLine: quiet loglevel=0
EOF

generate-zbm
```

Either option leaves a bootable EFI image at `/boot/efi/EFI/ZBM/VMLINUZ.EFI`.

### Register the EFI boot entry

Point the firmware at the ZFSBootMenu image with `efibootmgr`. `$PRIMARY_DISK` is the whole 4 TB device; `-p 1` is the EFI partition:

```bash
efibootmgr --create \
    --disk "$PRIMARY_DISK" --part 1 \
    --label "ZFSBootMenu" \
    --loader '\EFI\ZBM\VMLINUZ.EFI'

# Optional backup entry pointing at the copied image
efibootmgr --create \
    --disk "$PRIMARY_DISK" --part 1 \
    --label "ZFSBootMenu (backup)" \
    --loader '\EFI\ZBM\VMLINUZ-BACKUP.EFI'
```

### Rebuild the initramfs and leave the chroot

```bash
update-initramfs -c -k all

exit                      # leave the chroot
umount -R /mnt/boot/efi
umount -R /mnt/dev /mnt/proc /mnt/sys
zpool export tank
zpool export rpool
```

## First Boot

1. Remove the USB installation media.
2. Reboot.
3. The firmware hands off to **ZFSBootMenu** (not GRUB). It briefly shows the boot-environment menu; if left alone it boots the default environment (`rpool/ROOT/ubuntu`) after a short countdown.

### Verify pools and SSH

```bash
# rpool imported automatically as the root pool
zpool status rpool

# tank was not part of the bootstrap chroot — import it once, then it persists
sudo zpool import tank
zpool status tank

# Confirm the running root is the ZFS boot environment
zfs list -o name,mountpoint,canmount rpool/ROOT/ubuntu
mount | grep ' / '
```

After first boot, continue through the [Post-Install Checklist](post-install-checklist.md) for hardening — the steps are the same regardless of root filesystem, except the mount-options section (ext4 fstab vs ZFS properties).

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

## Live USB Recovery

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

## Operational Deltas vs the Canonical (ext4) Build

Choosing this alternative changes a few operational details relative to the canonical ext4-root build:

- **Snapshot the OS too.** `sanoid` should cover `rpool/ROOT` in addition to the data datasets, so there is always a known-good boot environment to return to. On the canonical build the OS root is *not* snapshotted (it is disposable and reproducible from the walkthrough); here it is a first-class snapshot target.
- **Boot-environment rollback is your fast path.** A broken OS is usually a boot-environment rollback (interrupt the ZFSBootMenu countdown, pick a prior environment or roll a `rpool/ROOT/ubuntu` snapshot back) rather than a reinstall. This is the recovery move the canonical build gives up.
- **Replicating root is optional but cheap.** A `syncoid rpool/ROOT` to a LAN replica lets a same-hardware rebuild `zfs receive` a working root instead of re-running this whole manual install.
- **The EFI binary and boot entries are what you back up**, not a `grub.cfg` — keep a copy of `VMLINUZ.EFI` off the ESP and record `efibootmgr -v` output.

## Next Step

Back to the canonical path: [Disk Partitioning](disk-partitioning.md) and the [Installation Walkthrough](installation-walkthrough.md). For post-install hardening, [Post-Install Checklist](post-install-checklist.md).
