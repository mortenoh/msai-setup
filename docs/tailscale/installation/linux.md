# Linux Installation

## Quick Install

The easiest way to install Tailscale on Linux:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

This script detects your distribution and installs appropriately.

## Ubuntu/Debian

### Package Repository

```bash
# Add Tailscale's GPG key
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg | \
  sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null

# Add repository (Ubuntu 22.04 Jammy example)
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.tailscale-keyring.list | \
  sudo tee /etc/apt/sources.list.d/tailscale.list

# Install
sudo apt update
sudo apt install tailscale
```

### Distribution-Specific URLs

| Distribution | Codename | Repository URL |
|--------------|----------|----------------|
| Ubuntu 24.04 | noble | `ubuntu/noble` |
| Ubuntu 22.04 | jammy | `ubuntu/jammy` |
| Ubuntu 20.04 | focal | `ubuntu/focal` |
| Debian 12 | bookworm | `debian/bookworm` |
| Debian 11 | bullseye | `debian/bullseye` |

Example for Debian:

```bash
curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.noarmor.gpg | \
  sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null

curl -fsSL https://pkgs.tailscale.com/stable/debian/bookworm.tailscale-keyring.list | \
  sudo tee /etc/apt/sources.list.d/tailscale.list

sudo apt update && sudo apt install tailscale
```

## RHEL/CentOS/Fedora

### Fedora

```bash
# Add repository
sudo dnf config-manager --add-repo https://pkgs.tailscale.com/stable/fedora/tailscale.repo

# Install
sudo dnf install tailscale

# Enable and start
sudo systemctl enable --now tailscaled
```

### RHEL/CentOS/Rocky/Alma

```bash
# Add repository
sudo dnf config-manager --add-repo https://pkgs.tailscale.com/stable/rhel/9/tailscale.repo

# Install
sudo dnf install tailscale

# Enable and start
sudo systemctl enable --now tailscaled
```

## Arch Linux

### Official Repository

```bash
sudo pacman -S tailscale

sudo systemctl enable --now tailscaled
```

### AUR (if needed)

```bash
yay -S tailscale-bin
```

## openSUSE

```bash
# Add repository
sudo zypper ar -f https://pkgs.tailscale.com/stable/opensuse/tumbleweed/tailscale.repo

# Install
sudo zypper install tailscale

# Enable and start
sudo systemctl enable --now tailscaled
```

## Static Binary

For unsupported distributions or minimal systems:

```bash
# Download latest release
curl -fsSL https://pkgs.tailscale.com/stable/tailscale_latest_amd64.tgz | tar xzf -

# Install binaries
sudo cp tailscale_*/tailscale tailscale_*/tailscaled /usr/local/bin/

# Create systemd service
sudo cat > /etc/systemd/system/tailscaled.service << 'EOF'
[Unit]
Description=Tailscale node agent
Documentation=https://tailscale.com/kb/
Wants=network-pre.target
After=network-pre.target NetworkManager.service systemd-resolved.service

[Service]
ExecStartPre=/usr/local/bin/tailscaled --cleanup
ExecStart=/usr/local/bin/tailscaled --state=/var/lib/tailscale/tailscaled.state --socket=/run/tailscale/tailscaled.sock
ExecStopPost=/usr/local/bin/tailscaled --cleanup
Restart=on-failure
RuntimeDirectory=tailscale
RuntimeDirectoryMode=0755
StateDirectory=tailscale
StateDirectoryMode=0700

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl enable --now tailscaled
```

## Post-Installation

### Start Tailscale

```bash
# Authenticate
sudo tailscale up
```

This opens a URL in your terminal. Open it in a browser to authenticate.

### Verify Installation

```bash
# Check daemon status
sudo systemctl status tailscaled

# Check connection status
tailscale status

# View your IP
tailscale ip
```

### Enable IP Forwarding (for subnet routing/exit nodes)

```bash
# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

## Service Management

### Systemd Commands

```bash
# Start/stop/restart
sudo systemctl start tailscaled
sudo systemctl stop tailscaled
sudo systemctl restart tailscaled

# Enable/disable at boot
sudo systemctl enable tailscaled
sudo systemctl disable tailscaled

# View logs
sudo journalctl -u tailscaled -f
```

### Daemon Configuration

The daemon (`tailscaled`) accepts various flags:

```bash
# View current configuration
cat /etc/default/tailscaled
# or
cat /etc/sysconfig/tailscaled

# Common options:
# PORT=41641                    # WireGuard port
# FLAGS="--state=/var/lib/tailscale/tailscaled.state"
```

## Updating

### Package Manager

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade tailscale

# Fedora/RHEL
sudo dnf upgrade tailscale

# Arch
sudo pacman -Syu tailscale
```

### Auto-Update

Tailscale can update itself:

```bash
# Enable auto-update
sudo tailscale set --auto-update
```

## Uninstalling

### Package Manager

```bash
# Ubuntu/Debian
sudo apt remove tailscale
sudo apt purge tailscale  # Remove config too

# Fedora/RHEL
sudo dnf remove tailscale

# Arch
sudo pacman -Rns tailscale
```

### Complete Removal

```bash
# Stop service
sudo systemctl stop tailscaled
sudo systemctl disable tailscaled

# Remove packages
sudo apt remove --purge tailscale

# Remove state and config
sudo rm -rf /var/lib/tailscale
sudo rm -rf /etc/tailscale

# Remove from tailnet (admin console or CLI)
# The device will appear as "offline" until removed
```

## Troubleshooting Installation

### Service Won't Start

```bash
# Check logs
sudo journalctl -u tailscaled --no-pager -n 50

# Check socket permissions
ls -la /run/tailscale/

# Manual start for debugging
sudo tailscaled --verbose=2
```

### Permission Errors

```bash
# Ensure user is in appropriate groups
sudo usermod -aG sudo $USER  # Or wheel on RHEL

# Or use root
sudo tailscale up
```

### Network Issues

```bash
# Check if daemon is running
pgrep tailscaled

# Check interface
ip addr show tailscale0

# Network diagnostics
tailscale netcheck
```

### Key Expiry

```bash
# If key expired, re-authenticate
sudo tailscale up

# Or use a pre-auth key
sudo tailscale up --auth-key=tskey-auth-xxxxx
```

## Headless/Unattended Installation

For servers or automated deployments:

```bash
# Generate auth key in admin console first
# https://login.tailscale.com/admin/settings/keys

# Install and authenticate
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --auth-key=tskey-auth-xxxxx --ssh
```

### Ansible Example

```yaml
- name: Install Tailscale
  hosts: servers
  become: yes
  tasks:
    - name: Add Tailscale repository
      shell: curl -fsSL https://tailscale.com/install.sh | sh
      args:
        creates: /usr/bin/tailscale

    - name: Start and authenticate Tailscale
      shell: tailscale up --auth-key={{ tailscale_auth_key }} --ssh
      when: tailscale_auth_key is defined
```

### Cloud-Init

```yaml
#cloud-config
packages:
  - curl

runcmd:
  - curl -fsSL https://tailscale.com/install.sh | sh
  - tailscale up --auth-key=tskey-auth-xxxxx --ssh
```
