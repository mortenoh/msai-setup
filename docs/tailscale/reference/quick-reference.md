# Quick Reference

## Installation

```bash
# One-line install (Linux)
curl -fsSL https://tailscale.com/install.sh | sh

# Package manager
# Ubuntu/Debian
sudo apt install tailscale

# Fedora/RHEL
sudo dnf install tailscale

# Arch
sudo pacman -S tailscale
```

## Basic Commands

```bash
# Connect
sudo tailscale up

# Disconnect (keep auth)
sudo tailscale down

# Logout (remove auth)
sudo tailscale logout

# Status
tailscale status

# Your IP
tailscale ip
```

## Connection Options

```bash
# With SSH server
sudo tailscale up --ssh

# Accept MagicDNS
sudo tailscale up --accept-dns

# Accept subnet routes
sudo tailscale up --accept-routes

# Use auth key
sudo tailscale up --auth-key=tskey-auth-xxxxx

# Custom hostname
sudo tailscale up --hostname=my-server

# Force re-auth
sudo tailscale up --force-reauth
```

## Exit Nodes

```bash
# Advertise as exit node
sudo tailscale up --advertise-exit-node

# Use exit node
sudo tailscale up --exit-node=exit-server

# Allow LAN access with exit node
sudo tailscale up --exit-node=exit-server --exit-node-allow-lan-access

# List exit nodes
tailscale exit-node list

# Stop using exit node
sudo tailscale up --exit-node=
```

## Subnet Routing

```bash
# Advertise routes
sudo tailscale up --advertise-routes=192.168.1.0/24

# Multiple routes
sudo tailscale up --advertise-routes=192.168.1.0/24,10.0.0.0/8

# Accept routes on clients
sudo tailscale up --accept-routes
```

## Diagnostics

```bash
# Status
tailscale status
tailscale status --json

# Network check
tailscale netcheck

# Ping peer
tailscale ping my-server

# DNS status
tailscale dns status

# Debug info
tailscale debug prefs
tailscale debug netmap

# Bug report
tailscale bugreport
```

## File Transfer (Taildrop)

```bash
# Send file
tailscale file cp document.pdf my-laptop:

# Send multiple
tailscale file cp *.jpg my-laptop:

# Receive files
tailscale file get ~/Downloads/

# Auto-receive
tailscale file get --loop ~/Taildrop/
```

## Serve & Funnel

```bash
# Serve port to tailnet
tailscale serve 3000

# Serve with HTTPS
tailscale serve https / http://localhost:3000

# Serve static files
tailscale serve / /var/www/html

# Serve status
tailscale serve status

# Stop serving
tailscale serve off

# Funnel (public)
tailscale funnel 443

# Funnel status
tailscale funnel status

# Stop funnel
tailscale funnel off
```

## SSH

```bash
# Connect via Tailscale SSH
ssh user@my-server

# Or using tailscale command
tailscale ssh user@my-server

# Enable SSH on server
sudo tailscale up --ssh
```

## Persistent Settings

```bash
# Set operator (allows non-root)
sudo tailscale set --operator=$USER

# Enable auto-update
sudo tailscale set --auto-update

# Enable SSH
sudo tailscale set --ssh
```

## Service Management

```bash
# Start
sudo systemctl start tailscaled

# Stop
sudo systemctl stop tailscaled

# Restart
sudo systemctl restart tailscaled

# Enable at boot
sudo systemctl enable tailscaled

# View logs
journalctl -u tailscaled -f
```

## IP Forwarding (for subnet/exit)

```bash
# Enable
echo 'net.ipv4.ip_forward = 1' | sudo tee -a /etc/sysctl.conf
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

## Docker Quick Start

```bash
docker run -d \
  --name=tailscale \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  -v /dev/net/tun:/dev/net/tun \
  -v tailscale-state:/var/lib/tailscale \
  -e TS_AUTHKEY=tskey-auth-xxxxx \
  -e TS_STATE_DIR=/var/lib/tailscale \
  tailscale/tailscale:latest
```

## Common URLs

| Resource | URL |
|----------|-----|
| Admin Console | https://login.tailscale.com/admin |
| Machines | https://login.tailscale.com/admin/machines |
| DNS | https://login.tailscale.com/admin/dns |
| ACLs | https://login.tailscale.com/admin/acls |
| Auth Keys | https://login.tailscale.com/admin/settings/keys |
| Downloads | https://tailscale.com/download |

## Quick Troubleshooting

| Issue | Command |
|-------|---------|
| Check status | `tailscale status` |
| Check network | `tailscale netcheck` |
| Test connectivity | `tailscale ping peer` |
| View logs | `journalctl -u tailscaled -f` |
| Re-authenticate | `sudo tailscale up --force-reauth` |
| Generate bug report | `tailscale bugreport` |
