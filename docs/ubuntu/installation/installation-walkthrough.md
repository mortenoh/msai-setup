# Installation Walkthrough

Step-by-step guide through the Ubuntu Server 26.04 LTS installer with security-focused choices.

!!! info "26.04 Server installer changes"
    The 26.04 live-server ISO **automatically installs the HWE/OEM kernel** when it detects matching hardware (such as Strix Halo). On the MS-S1 Max this means you no longer need to install `linux-oem-*` manually after first boot. Defaults also include **dracut** (replacing `initramfs-tools`), **TPM-backed full-disk encryption**, and **crash dumps enabled by default**.

## Boot from Installation Media

### Initial Boot

1. Insert USB boot media
2. Power on and enter boot menu (F12, F8, or manufacturer-specific)
3. Select USB device (UEFI mode if available)

### GRUB Menu

Select from the boot menu:

- **Try or Install Ubuntu Server** - Proceed with installation
- **Check disc for defects** - Verify installation media (recommended first time)
- **Boot from first hard disk** - Skip if you want to abort

!!! tip "Verify Media First"
    If you haven't verified the boot media, select "Check disc for defects" to ensure data integrity.

## Language and Keyboard

### Language Selection

Select your preferred language for the installation process:

1. Use arrow keys to navigate
2. Press Enter to select
3. English is recommended for server environments (better documentation coverage)

### Keyboard Layout

1. Select "Layout" and choose your keyboard layout
2. Optionally select a variant
3. Test the layout by typing in the test field
4. Select "Done" when satisfied

## Installation Type

### Choose Installation Source

Options:

- **Ubuntu Server** - Standard installation from media
- **Ubuntu Server (minimized)** - Smaller footprint, fewer packages

!!! note "Minimized Installation"
    The minimized variant excludes documentation, locales, and some utilities. Consider this for containers or highly constrained environments.

### Network Installation

If your system has network access, you may be offered:

- **Install from local media** - Use the ISO on the USB
- **Install from network** - Download packages during install

Select local media for offline installation or network for latest packages.

## Network Configuration

### Interface Detection

The installer auto-detects network interfaces:

```
enp5s0: eth (not connected)
enp6s0: eth
  DHCPv4: 192.168.1.50/24
  Gateway: 192.168.1.1
```

### DHCP vs Static

**DHCP (Recommended for installation):**

- Accept the auto-configured address
- Configure static IP post-installation via Netplan
- Ensures connectivity for package downloads

**Static IP during installation:**

1. Select the interface
2. Choose "Edit IPv4"
3. Select "Manual"
4. Enter:
   - Subnet: `192.168.1.0/24`
   - Address: `192.168.1.100`
   - Gateway: `192.168.1.1`
   - Name servers: `1.1.1.1,8.8.8.8`
   - Search domains: (optional)

### Proxy Configuration

If your network requires a proxy:

```
http://proxy.example.com:3128
```

Leave blank if no proxy is needed.

### Mirror Selection

The default archive mirror is typically appropriate. Change only if:

- You have a local mirror
- Geographic mirrors are faster
- Corporate policy requires specific mirrors

## Storage Configuration

### Layout Selection

When prompted, select **Custom storage layout**. Do not use guided/entire-disk — it will reformat the wrong drive on a two-NVMe box.

### Create Partitions on the Primary 2 TB NVMe

Follow the canonical layout in [Disk Partitioning](disk-partitioning.md): plain ext4 root, no LUKS, no LVM. The secondary 4 TB NVMe is **left untouched** at installer time; ZFS will claim it post-install.

**EFI System Partition:**

1. Select free space on the primary NVMe
2. "Add GPT Partition"
3. Size: `512M`
4. Format: `fat32`
5. Mount: `/boot/efi`

**Boot Partition:**

1. Select remaining free space on the primary NVMe
2. "Add GPT Partition"
3. Size: `1G`
4. Format: `ext4`
5. Mount: `/boot`

**Root Partition:**

1. Select remaining free space on the primary NVMe
2. "Add GPT Partition"
3. Size: `1024G` (1 TB; installer may round)
4. Format: `ext4`
5. Mount: `/`

**Leave the rest unallocated:**

- ~1 TB of free space on the primary NVMe — will become a ZFS pool member.
- The entire 4 TB secondary NVMe — also a ZFS pool member.

### Review and Confirm

The storage summary should look approximately like:

```
nvme0n1                   disk   2.0T
  nvme0n1p1               part   512M  /boot/efi  (fat32)
  nvme0n1p2               part   1.0G  /boot       (ext4)
  nvme0n1p3               part   1.0T  /           (ext4)
  (free space)                   ~1.0T

nvme1n1                   disk   4.0T
  (free space)                   4.0T
```

!!! danger "Destructive Action"
    Proceeding will erase the selected disks. Verify both drive identities — the slot 1 drive is the 2 TB; the slot 2 drive is the 4 TB and must show **no partitions**.

Select "Done" and confirm when prompted.

## Profile Setup

### Server Identity

| Field | Recommendation |
|-------|----------------|
| Your name | Full name (for GECOS field) |
| Your server's name | Hostname (e.g., `srv-ubuntu-01`) |
| Pick a username | Lowercase, no spaces (e.g., `admin`) |
| Choose a password | Strong password (also used by `sudo`) |
| Confirm password | Re-enter password |

**Hostname Guidelines:**

- Use lowercase letters, numbers, hyphens
- No underscores or spaces
- Follow your organization's naming convention
- Examples: `web01`, `srv-ubuntu-prod`, `ms-s1-max`

### Ubuntu Pro

Ubuntu Pro offers additional security features:

- **Extended Security Maintenance** - 10 years of security updates
- **Kernel Livepatch** - Kernel updates without reboot
- **FIPS compliance** - For regulated environments
- **CIS hardening tools** - Compliance automation

For personal use, Ubuntu Pro is free for up to 5 machines. Register at [ubuntu.com/pro](https://ubuntu.com/pro).

If you have a token, enter it. Otherwise, select "Skip for now" or "Continue without Ubuntu Pro".

## SSH Setup

### Enable OpenSSH Server

Select **Install OpenSSH server** - this is essential for remote management.

### SSH Key Import

Options for importing your public SSH key:

1. **Import SSH identity: from GitHub**
   - Enter your GitHub username
   - Your public keys from GitHub are imported
   - Convenient and secure

2. **Import SSH identity: from Launchpad**
   - Enter your Launchpad username

3. **No** - Add keys manually post-installation

!!! tip "GitHub Key Import"
    Importing from GitHub is the easiest secure option. Ensure your GitHub account has your current SSH public keys.

If you import keys, password authentication can be disabled by default.

## Featured Server Snaps

The installer offers additional software via Snap packages:

| Snap | Description |
|------|-------------|
| docker | Container runtime |
| nextcloud | Personal cloud |
| kubernetes | Container orchestration |

**Recommendation: Skip all**

- Install software post-installation for better control
- Snaps have auto-update behavior that may not suit servers
- Package versions may differ from what you want

Select "Done" without checking any boxes.

## Installation Progress

The installer now:

1. Partitions the disk
2. Formats filesystems
3. Installs the base system
4. Configures the bootloader
5. Installs selected packages
6. Configures SSH with your keys

This takes 5-15 minutes depending on hardware.

### Monitor Progress

The installation log shows detailed progress:

- Package installation
- Configuration steps
- Any warnings or errors

Watch for red text indicating problems.

## Installation Complete

When finished:

1. Remove the USB installation media
2. Select "Reboot Now"

## First Boot

### Boot to Login

After BIOS/UEFI, the GRUB bootloader appears briefly and the system boots straight through to the login prompt. With the canonical plain-ext4 layout (no LUKS) there is no disk-passphrase step.

### Login Prompt

After boot completes:

```
Ubuntu 26.04 LTS srv-ubuntu-01 tty1

srv-ubuntu-01 login: _
```

Log in with the username and password you created.

### Verify SSH Access

From another machine:

```bash
# Using password
ssh admin@192.168.1.100

# Using key (if imported during install)
ssh admin@192.168.1.100
# Should not prompt for password
```

## Post-Installation Verification

Run these checks after first login:

```bash
# Check Ubuntu version
lsb_release -a

# Verify disk layout
lsblk

# Check network
ip addr show
ip route show

# Verify SSH service
systemctl status ssh

# Check for updates
sudo apt update
sudo apt list --upgradable
```

## Troubleshooting Installation

### Installer Crashes

- Try "Safe graphics" mode from boot menu
- Check hardware compatibility
- Verify ISO integrity

### Network Not Detected

- Check cable connection
- Verify interface is supported
- May need firmware packages post-installation

!!! note "LUKS not used by default"
    The canonical layout has no disk encryption, so there is no passphrase to unlock. If you chose the optional LUKS+LVM alternative from [Disk Partitioning](disk-partitioning.md), see that page for unlock troubleshooting.

### Bootloader Not Installed

- Re-run installer, select "Install bootloader"
- Or manually install from live USB:
  ```bash
  sudo chroot /target
  grub-install /dev/nvme0n1
  update-grub
  ```

## Next Step

Continue to [Post-Install Checklist](post-install-checklist.md) to complete initial system hardening.
