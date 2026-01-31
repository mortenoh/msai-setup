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
KexAlgorithms sshd_config,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

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

### Update fstab

Add security mount options for non-root partitions:

```bash
sudo nano /etc/fstab
```

Update mount options:

```
# Root - defaults only (needs exec for system)
/dev/mapper/vg--system-lv--root /     ext4 defaults 0 1

# Home - restrict device files and setuid
/dev/mapper/vg--system-lv--home /home ext4 defaults,nodev,nosuid 0 2

# Var - restrict device files and setuid
/dev/mapper/vg--system-lv--var  /var  ext4 defaults,nodev,nosuid 0 2

# Tmp - full restrictions
/dev/mapper/vg--system-lv--tmp  /tmp  ext4 defaults,nodev,nosuid,noexec 0 2
```

Apply changes:

```bash
# Remount all
sudo mount -o remount /home
sudo mount -o remount /var
sudo mount -o remount /tmp

# Verify
mount | grep -E "(home|var|tmp)"
```

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

## Quick Verification Checklist

Run through this checklist before considering the system ready:

```bash
# SSH key auth works
ssh -o PasswordAuthentication=no user@server echo "Key auth OK"

# Firewall enabled
sudo ufw status | grep -q "Status: active"

# Time sync working
timedatectl | grep -q "synchronized: yes"

# Updates installed
apt list --upgradable 2>/dev/null | grep -c upgradable

# Disk encryption active
sudo cryptsetup status cryptroot

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
| SSH hardened | Required |
| Firewall enabled | Required |
| Auto-updates enabled | Recommended |
| Kernel hardening | Recommended |
| Mount options secured | Recommended |
| Unnecessary services disabled | Recommended |

## Next Steps

The basic installation is complete. Continue with:

1. [System Configuration](../system/index.md) - User management, sudo, PAM
2. [Security Hardening](../security/index.md) - Comprehensive security measures
3. [Networking Configuration](../networking.md) - Static IP, advanced networking

For a complete hardening checklist, see [Reference Checklist](../reference/checklist.md).
