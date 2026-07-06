# Installation Walkthrough

Step-by-step guide to installing Ubuntu Server 26.04 LTS **root-on-ZFS with ZFSBootMenu** on the MS-S1 MAX, following the canonical [Disk Partitioning](disk-partitioning.md) layout (two independent pools: `rpool` on the fast 4 TB primary NVMe, `tank` on the slow 2 TB secondary NVMe).

!!! warning "This is a manual install — you do not run Subiquity's guided installer end-to-end"
    Ubuntu Server's installer (Subiquity), including its `autoinstall` automation, has **no root-on-ZFS path**. There are no familiar guided storage screens here. Instead you boot the Server ISO into a live/rescue shell and run the partitioning, `zpool create`, `debootstrap`, chroot, and ZFSBootMenu steps by hand. If you were expecting the point-and-click storage wizard, that is intentional — see [Disk Partitioning](disk-partitioning.md#creating-the-layout) for why.

!!! info "26.04 kernel and initramfs"
    Ubuntu 26.04 ships **Linux 7.0** as its `linux-generic` kernel, which already supports the Strix Halo iGPU (`gfx1151`) — no separate HWE/OEM metapackage is needed for a manual debootstrap install (the auto-install of `linux-oem-*` only happens inside Subiquity, which you are not using). 26.04 also defaults to **dracut** for the initramfs, which is what ZFSBootMenu itself is built with.

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

!!! tip "Verify media first"
    On a first install, verifying the ISO checksum (or using the ISO's "Check disc for defects" option) rules out a corrupt image before you commit to a manual process.

## Language and Keyboard

If you booted through the installer's first screens to reach the shell, set language and keyboard there as usual — they affect the console you are about to work in:

1. **Language:** English is recommended for server environments (best documentation coverage).
2. **Keyboard:** select your layout (and variant), then test it in the field provided — a wrong layout makes typing device paths error-prone, and one wrong character in a `zpool create` wipes the wrong disk.

## Prepare the Live Environment

### Network Access

`debootstrap` downloads the base system over the network, so the live environment needs connectivity. DHCP over a wired 10GbE port is simplest:

```bash
# Confirm an interface picked up an address
ip -br addr

# If not, bring one up with DHCP (replace enp6s0 with your interface)
sudo dhclient enp6s0
```

Static addressing during install is possible but unnecessary — configure the permanent static IP later, inside the target system's netplan (below).

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

These are the exact commands from [Disk Partitioning](disk-partitioning.md#creating-the-layout) — do not substitute different ones.

### Partition the primary 4 TB NVMe

```bash
sgdisk --zap-all "$PRIMARY_DISK"
sgdisk -n1:1M:+512M -t1:EF00 "$PRIMARY_DISK"   # EFI
sgdisk -n2:0:0      -t2:BF00 "$PRIMARY_DISK"   # ZFS pool member (rest of disk)
```

### Create `rpool` (primary, fast drive)

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

`rpool/ROOT/ubuntu` is `canmount=noauto` on purpose — with more than one boot environment present, ZFS must not auto-mount all of them; ZFSBootMenu (or an explicit `zfs mount`) picks which one becomes `/`. Mount it now so `debootstrap` has a target:

```bash
zfs mount rpool/ROOT/ubuntu
zfs mount rpool/home
```

### Partition and create `tank` (secondary, slow drive)

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

## Bootstrap Ubuntu into `rpool`

Install a minimal Ubuntu 26.04 base system into the mounted `rpool/ROOT/ubuntu` with `debootstrap`. The 26.04 suite is `resolute`; if the archive hasn't published a `resolute` path yet (common in the first weeks after an LTS release), fall back to `noble` (24.04) and dist-upgrade later — the same fallback convention this repo uses for the Docker and Tailscale repos:

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

`rpool` and `tank` deliberately have **no fstab entries** — they are ZFS-native mounts. See [Disk Partitioning -> Mount Options for Security](disk-partitioning.md#mount-options-for-security) for the per-dataset property approach that replaces fstab hardening lines.

### Create the admin user with SSH key auth

Create the initial privileged user and import your SSH public key. This build's convention (preserved from the original guided-install flow) is to **import keys from GitHub** — the easiest secure option — with a manual `authorized_keys` fallback:

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

Password authentication and root login are hardened off later in the [Post-Install Checklist](post-install-checklist.md#verify-ssh-security); OpenSSH is installed here so the box is reachable on first boot.

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

Confirm the entries and their order:

```bash
efibootmgr -v
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

### Login Prompt

After boot completes:

```
Ubuntu 26.04 LTS ms-s1-max tty1

ms-s1-max login: _
```

Log in with the `admin` user you created in the chroot.

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

From another machine, confirm key-based SSH:

```bash
ssh admin@192.168.1.100
# Should log in without a password prompt if your GitHub key was imported
```

## Post-Installation Verification

Run these checks after first login:

```bash
# Ubuntu version (dist-upgrade to 26.04 first if you fell back to noble)
lsb_release -a

# Both pools healthy
zpool status
zpool list

# Boot environment layout
zfs list -r rpool/ROOT

# Kernel and network
uname -r
ip addr show
ip route show

# SSH service
systemctl status ssh

# Confirm ZFSBootMenu's EFI entry is registered
sudo efibootmgr -v | grep -i zfsbootmenu
```

## Troubleshooting Installation

### ZFSBootMenu doesn't appear at boot

The firmware is booting something else (or nothing). From a live environment, check and reorder the EFI entries:

```bash
sudo efibootmgr -v
# Note the ZFSBootMenu entry's hex ID (e.g. Boot0003), then move it first:
sudo efibootmgr -o 0003,0000,....
```

If no ZFSBootMenu entry exists at all, re-register it (mount the EFI partition and re-run the `efibootmgr --create` command above). Full recovery steps live in [Boot Issues](../troubleshooting/boot-issues.md).

### Pools won't import on first boot

```bash
# Force-import by scanning by-id paths (from a live environment if needed)
sudo zpool import -d /dev/disk/by-id -f rpool
sudo zpool import -d /dev/disk/by-id -f tank
```

### `debootstrap` fails to reach the archive

Confirm live-environment networking (`ip -br addr`, `ping -c3 archive.ubuntu.com`) and that the `$SUITE` fallback to `noble` triggered if `resolute` isn't published yet.

### No network detected in the live environment

- Check the 10GbE cable and that the port shows state UP in `ip -br link`.
- The RTL8127 NIC binds natively on the 7.0 kernel; on an older live ISO you may need to `sudo dhclient` manually or use a different port.

## Next Step

Continue to [Post-Install Checklist](post-install-checklist.md) to complete initial system hardening.
