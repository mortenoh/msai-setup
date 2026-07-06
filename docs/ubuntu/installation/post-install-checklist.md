# Post-Install Checklist

Essential first-boot tasks to establish a secure baseline before putting the system into production.

## Immediate Actions

Perform these tasks immediately after first login.

### System Update

```bash
# Update package lists and upgrade all packages
sudo apt update && sudo apt upgrade -y
```

!!! warning "Reboot After Kernel Updates"
    If kernel packages were updated, reboot before continuing:
    ```bash
    sudo reboot
    ```

### Set Timezone

```bash
# List available timezones
timedatectl list-timezones | grep Europe

# Set timezone
sudo timedatectl set-timezone Europe/Oslo

# Verify
timedatectl
```

### Configure NTP

Ensure time synchronization is active:

```bash
# Check status
timedatectl status

# Should show: NTP service: active

# If not active
sudo timedatectl set-ntp true
```

### Verify Hostname

```bash
# Check current hostname
hostnamectl

# Change if needed
sudo hostnamectl set-hostname srv-ubuntu-01
```

Update `/etc/hosts` if hostname changed:

```bash
sudo nano /etc/hosts
```

Add/update:
```
127.0.1.1   srv-ubuntu-01
```

## MS-S1 MAX Hardware Verification

Confirm the Strix-Halo-specific hardware came up correctly under the 26.04 / Linux 7.0 kernel.

### 10GbE (Realtek RTL8127)

The `r8169` driver gained RTL8127A support in Linux 6.16, so 26.04's 7.0 kernel binds both 10GbE ports natively. No `r8127-dkms` required (the older 24.04 guides recommending DKMS are stale).

```bash
# Both 10GbE NICs should appear with state UP after cabling
ip -br link

# Confirm the driver bound is r8169
sudo lspci -k | grep -A3 -i "ethernet"
```

If a port is missing, rebooting once after the install upgrade usually does it. As a fallback only, install [PeterSuh-Q3/r8127](https://github.com/PeterSuh-Q3/r8127) DKMS.

### MediaTek MT7925 WiFi

Works out of the box in 7.0. If you don't plan to use WiFi on a server, leave it disabled.

### GPU (gfx1151)

```bash
# Driver bound
lspci -k | grep -A3 -i vga

# Kernel sees the iGPU
ls /dev/dri/
# Expect: card0, renderD128
```

For the full ROCm/AI stack, continue to [Quick Start](../../ai/gpu/quick-start.md).

### USB4 stability

Front and rear USB4 ports should both work fine on BIOS 1.06+ — the ASPM/hot-plug flaw that used to affect the rear USB4 V2 ports under Linux was fixed in BIOS 1.05 (see [BIOS Setup -> Firmware Version](../../getting-started/bios-setup.md#firmware-version)). Use whichever ports fit your cabling.

## Install Tailscale

Tailscale is this build's remote-management plane: the host is reachable on the LAN and over Tailscale, and isn't meant to sit directly on the public internet. Install it now, before touching UFW or SSH hardening below — it gives you a second, independent access path in case a firewall or sshd change locks you out over the LAN.

### Add the Repository and Install

```bash
# Determine the right Tailscale suite for this Ubuntu release
# (falls back to 24.04's "noble" if 26.04's "resolute" isn't published yet)
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
if ! curl -sfI "https://pkgs.tailscale.com/stable/ubuntu/${CODENAME}.noarmor.gpg" >/dev/null; then
    CODENAME=noble
fi

curl -fsSL "https://pkgs.tailscale.com/stable/ubuntu/${CODENAME}.noarmor.gpg" | \
  sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL "https://pkgs.tailscale.com/stable/ubuntu/${CODENAME}.tailscale-keyring.list" | \
  sudo tee /etc/apt/sources.list.d/tailscale.list

sudo apt update && sudo apt install -y tailscale
```

### Authenticate and Verify

```bash
sudo tailscale up
```

This prints a URL — open it in a browser on any device to approve the node into your tailnet. Then verify:

```bash
tailscale status
tailscale ip -4
```

!!! note "Tailscale SSH (`--ssh`) is optional"
    Adding `--ssh` to `tailscale up` turns on Tailscale's own SSH server, governed entirely by Tailscale ACLs — it bypasses the sshd hardening (fail2ban, ciphers, `PermitRootLogin no`, etc.) configured below. If you want the mesh network only and plan to keep using hardened sshd, leave `--ssh` off. See [Tailscale + SSH](../../tailscale/integration/ssh.md) for the trade-off.

For other distributions, other install methods, and day-2 operations (ACLs, exit nodes, Funnel), see the full [Tailscale](../../tailscale/index.md) section.

## Verify SSH Security

### Check SSH Configuration

```bash
# Verify SSH is running
systemctl status ssh

# Check key-based auth works
# From another machine:
ssh username@server-ip
```

### Secure SSH Settings

Edit `/etc/ssh/sshd_config.d/hardening.conf`:

```bash
sudo nano /etc/ssh/sshd_config.d/hardening.conf
```

Add these settings:

```
# Disable root login
PermitRootLogin no

# Disable password authentication (only if key auth works!)
PasswordAuthentication no

# Enable public key authentication
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit authentication attempts
MaxAuthTries 3

# Set login grace time
LoginGraceTime 60

# Disable X11 forwarding (unless needed)
X11Forwarding no

# Disable TCP forwarding (unless needed)
AllowTcpForwarding no

# Use strong key exchange algorithms
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Restrict client public key algorithms (refuse legacy ssh-rsa SHA1)
PubkeyAcceptedAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256

# Use strong ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com

# Use strong MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Log level
LogLevel VERBOSE
```

Apply changes:

```bash
# Test configuration
sudo sshd -t

# Restart SSH
sudo systemctl restart ssh
```

!!! danger "Test Before Disconnecting"
    Before closing your current SSH session, open a new terminal and verify you can still connect. Don't lock yourself out!

For comprehensive SSH hardening, see the [SSH Server Hardening](../../ssh/server/hardening.md) guide.

## Install Essential Packages

### Minimal Essential Set

```bash
sudo apt install -y \
    vim \
    htop \
    tmux \
    git \
    curl \
    wget \
    unzip \
    rsync \
    tree \
    jq \
    net-tools \
    dnsutils \
    tcpdump \
    iotop \
    sysstat
```

### Purpose of Each Package

| Package | Purpose |
|---------|---------|
| vim | Text editor |
| htop | Interactive process viewer |
| tmux | Terminal multiplexer (persistent sessions) |
| git | Version control |
| curl/wget | HTTP clients |
| unzip | Archive extraction |
| rsync | Efficient file sync |
| tree | Directory visualization |
| jq | JSON processing |
| net-tools | Legacy network tools (ifconfig, netstat) |
| dnsutils | DNS lookup tools (dig, nslookup) |
| tcpdump | Network packet capture |
| iotop | I/O monitoring |
| sysstat | System performance tools (sar, iostat) |

## Configure Firewall

### Enable UFW

```bash
# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - do this first!)
sudo ufw allow ssh

# Enable firewall
sudo ufw enable

# Verify status
sudo ufw status verbose
```

For comprehensive firewall configuration, see the [Networking & Firewall](../../networking/index.md) section.

## Secure Mount Options

### EFI fstab entry, ZFS dataset properties for the rest

This build is **root-on-ZFS** (see [Disk Partitioning](disk-partitioning.md)). The only fstab entry is the EFI partition — `rpool` and `tank` datasets mount natively via ZFS, so hardening flags like `nodev,nosuid,noexec` become per-dataset ZFS **properties** instead of fstab columns.

Confirm the EFI entry created during install is present and hardened in `/etc/fstab`:

```bash
sudo nano /etc/fstab
```

It should read (UUID from `blkid` on your EFI partition):

```
UUID=<efi-uuid>   /boot/efi   vfat   umask=0077,fmask=0077,dmask=0077   0 1
```

For everything else, set ZFS properties on the datasets where it makes sense (e.g. scratch/tmp datasets that never need to execute binaries):

```bash
# Example: lock down a service scratch dataset
sudo zfs set devices=off setuid=off exec=off rpool/some-dataset

# Root itself keeps the defaults — it needs exec/setuid/devices for a working system
zfs get exec,setuid,devices rpool/ROOT/ubuntu
```

See [Disk Partitioning -> Mount Options for Security](disk-partitioning.md#mount-options-for-security) for the authoritative reference on the per-dataset property approach.

### Secure /dev/shm

Add to fstab:

```
tmpfs /dev/shm tmpfs defaults,nodev,nosuid,noexec 0 0
```

Remount:

```bash
sudo mount -o remount /dev/shm
```

## Enable Automatic Security Updates

### Install and Configure unattended-upgrades

```bash
# Install
sudo apt install -y unattended-upgrades

# Enable automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
# Select "Yes"
```

### Verify Configuration

```bash
# Check status
sudo systemctl status unattended-upgrades

# View configuration
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

For detailed configuration, see [Unattended Upgrades](../updates/unattended-upgrades.md).

## Basic Kernel Hardening

### Apply sysctl Settings

Create `/etc/sysctl.d/99-security.conf`:

```bash
sudo nano /etc/sysctl.d/99-security.conf
```

Add essential hardening:

```ini
# Disable IP forwarding (unless needed for routing/containers)
net.ipv4.ip_forward = 0
net.ipv6.conf.all.forwarding = 0

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# Don't send ICMP redirects
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0

# Enable TCP SYN cookies (SYN flood protection)
net.ipv4.tcp_syncookies = 1

# Ignore broadcast pings
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP errors
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Enable reverse path filtering
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Log martian packets
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1

# Disable source routing
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv6.conf.all.accept_source_route = 0

# Restrict core dumps
fs.suid_dumpable = 0

# Randomize virtual address space
kernel.randomize_va_space = 2
```

Apply:

```bash
sudo sysctl --system
```

For comprehensive kernel hardening, see [Kernel Hardening](../security/kernel-hardening.md).

## Create Privileged User (if not done during install)

### Add Admin User

```bash
# Create user
sudo adduser admin

# Add to sudo group
sudo usermod -aG sudo admin

# Verify groups
groups admin
```

### Set Up SSH Keys

```bash
# On the server, as the new user
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Add your public key
echo "ssh-ed25519 AAAA... your-email@example.com" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

## Disable Unnecessary Services

### Review Enabled Services

```bash
# List enabled services
systemctl list-unit-files --state=enabled

# List running services
systemctl list-units --type=service --state=running
```

### Common Services to Consider Disabling

| Service | Disable If |
|---------|------------|
| cups | No printing needed |
| avahi-daemon | No mDNS/Bonjour needed |
| bluetooth | No Bluetooth hardware |
| ModemManager | No modem hardware |

```bash
# Disable a service
sudo systemctl disable --now service-name
```

## Verify System Health

### Check System Status

```bash
# System overview
systemctl status

# Failed units
systemctl --failed

# Disk usage
df -h

# Memory usage
free -h

# CPU and load
uptime
```

### Check Logs for Issues

```bash
# Recent boot messages
sudo dmesg | tail -50

# System journal
sudo journalctl -b -p err

# Authentication attempts
sudo journalctl -u ssh --since today
```

## Verify ZFS Pools and Boot Environment

Confirm both pools imported and are healthy, and that a boot environment exists to roll back to if a future upgrade goes wrong.

```bash
# Both pools ONLINE, no errors
zpool status rpool
zpool status tank

# tank auto-imports on subsequent boots once imported once; if it is missing:
#   sudo zpool import -d /dev/disk/by-id tank

# The running root is the ZFS boot environment
zfs list -o name,mountpoint,canmount rpool/ROOT/ubuntu
mount | grep -q 'rpool/ROOT/ubuntu on / ' && echo "Root is a ZFS boot environment"
```

### Take a baseline boot environment snapshot

Before the system goes into production, snapshot the freshly hardened root so there is always a known-good environment to return to via ZFSBootMenu:

```bash
# Snapshot the current root boot environment
sudo zfs snapshot rpool/ROOT/ubuntu@post-install-baseline

# Confirm it exists (this is the rollback target if a bad upgrade breaks boot)
zfs list -t snapshot -r rpool/ROOT
```

To roll back later, select the snapshot as a boot environment from the ZFSBootMenu screen at boot — see [Boot Issues](../troubleshooting/boot-issues.md) for the recovery flow.

## Quick Verification Checklist

Run through this checklist before considering the system ready:

```bash
# SSH key auth works
ssh -o PasswordAuthentication=no user@server echo "Key auth OK"

# Both ZFS pools healthy
zpool status rpool | grep -q "state: ONLINE"
zpool status tank | grep -q "state: ONLINE"

# A boot environment snapshot exists to roll back to
zfs list -t snapshot rpool/ROOT/ubuntu@post-install-baseline

# Firewall enabled
sudo ufw status | grep -q "Status: active"

# Tailscale connected
tailscale status | grep -q "^100\."

# Time sync working
timedatectl | grep -q "synchronized: yes"

# Updates installed
apt list --upgradable 2>/dev/null | grep -c upgradable

# Fail2ban running (if installed)
systemctl is-active fail2ban

# No failed services
systemctl --failed --quiet
```

## Post-Install Summary

| Task | Status |
|------|--------|
| System updated | Required |
| Timezone configured | Required |
| Both ZFS pools ONLINE (`rpool`, `tank`) | Required |
| Baseline boot-environment snapshot taken | Required |
| Tailscale installed | Required |
| SSH hardened | Required |
| Firewall enabled | Required |
| Auto-updates enabled | Recommended |
| Kernel hardening | Recommended |
| Mount options secured (EFI fstab + dataset properties) | Recommended |
| Unnecessary services disabled | Recommended |

## Next Steps

The basic installation is complete. Continue with:

1. [System Configuration](../system/index.md) - User management, sudo, PAM
2. [Security Hardening](../security/index.md) - Comprehensive security measures
3. [Networking Configuration](../networking.md) - Static IP, advanced networking
4. [Tailscale](../../tailscale/index.md) - ACLs, exit nodes, subnet routers, and Funnel/Serve (already installed above)

For a complete hardening checklist, see [Reference Checklist](../reference/checklist.md).
