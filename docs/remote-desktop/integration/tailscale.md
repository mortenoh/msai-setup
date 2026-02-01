# Remote Desktop over Tailscale

Tailscale provides secure, zero-config access to your VMs from anywhere. This is the recommended approach for remote desktop access.

## Why Tailscale

| Traditional Approach | Tailscale Approach |
|---------------------|-------------------|
| Port forward 3389/5900 | No port forwarding |
| Expose to internet | Never exposed |
| Complex firewall rules | Zero config |
| Dynamic DNS needed | MagicDNS built-in |
| VPN setup complexity | One command |

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Tailscale Network                         │
│                                                               │
│  ┌─────────────┐                        ┌─────────────────┐  │
│  │   macOS     │                        │   Home Server   │  │
│  │   Laptop    │◄──────────────────────►│   (Host)        │  │
│  │             │    WireGuard Tunnel    │                 │  │
│  │ 100.64.0.1  │    (direct or relay)   │   100.64.0.2    │  │
│  └─────────────┘                        └────────┬────────┘  │
│                                                  │            │
│                                         ┌────────▼────────┐  │
│                                         │      VMs        │  │
│                                         │  VNC: 5900      │  │
│                                         │  RDP: 3389      │  │
│                                         │  SPICE: 5901    │  │
│                                         └─────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

## Setup

### Prerequisites

- Tailscale account ([tailscale.com](https://tailscale.com))
- Tailscale installed on all devices

### Server Setup

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Start and authenticate
sudo tailscale up

# Verify
tailscale status
```

### macOS Client Setup

```bash
# Install via Homebrew
brew install --cask tailscale
```

Or download from [tailscale.com/download](https://tailscale.com/download).

Sign in through the menu bar icon.

### Find Your Tailscale Addresses

```bash
# On server
tailscale status
# 100.64.0.2   server          user@email.com  linux   -

# MagicDNS hostname
tailscale status --json | jq -r '.Self.DNSName'
# server.tail-network.ts.net
```

## Connecting to VMs

### VNC (Linux VMs)

```bash
# Using MagicDNS
open vnc://server.tail-network.ts.net:5900

# Using Tailscale IP
open vnc://100.64.0.2:5900
```

### RDP (Windows VMs)

In Microsoft Remote Desktop:
1. Add PC
2. PC name: `server.tail-network.ts.net`
3. Port: 3389 (or specify: `server.tail-network.ts.net:3389`)
4. Connect

### SPICE

```bash
remote-viewer spice://server.tail-network.ts.net:5900
```

## Firewall Configuration

### On Host Server

Allow VNC/RDP only from Tailscale network:

```bash
# Allow VNC from Tailscale only
sudo ufw allow in on tailscale0 to any port 5900:5910 proto tcp

# Allow RDP from Tailscale only
sudo ufw allow in on tailscale0 to any port 3389 proto tcp

# Deny from other interfaces
sudo ufw deny 5900:5910/tcp
sudo ufw deny 3389/tcp
```

### Verify Rules

```bash
sudo ufw status verbose | grep -E "5900|3389|tailscale"
```

## VM Network Options

### Option 1: NAT with Port Forward (Simple)

VMs on NAT network, forward ports from host:

```bash
# Forward host:5901 to VM:5900
sudo iptables -t nat -A PREROUTING -i tailscale0 -p tcp --dport 5901 -j DNAT --to-destination 192.168.122.10:5900
sudo iptables -A FORWARD -p tcp -d 192.168.122.10 --dport 5900 -j ACCEPT
```

Connect: `vnc://server.tail-network.ts.net:5901`

### Option 2: Bridge Network (Direct Access)

VMs on bridged network get their own IPs:

```bash
# VM is on same subnet as host
# Connect directly to VM's LAN IP through subnet router
```

Requires Tailscale [subnet router](../../tailscale/features/subnet-routers.md).

### Option 3: Tailscale on VMs (Best)

Install Tailscale in each VM:

```bash
# Inside Linux VM
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Inside Windows VM
# Download and install from tailscale.com
```

Connect directly:
```bash
open vnc://linux-vm.tail-network.ts.net:5900
# RDP: windows-vm.tail-network.ts.net
```

## Subnet Router

Expose VM network via Tailscale subnet router.

### Enable on Host

```bash
# Advertise VM network
sudo tailscale up --advertise-routes=192.168.122.0/24

# Enable IP forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

### Approve in Admin Console

1. Open [Tailscale Admin Console](https://login.tailscale.com/admin/machines)
2. Find server, click "..."
3. Edit route settings
4. Approve 192.168.122.0/24

### Connect to VMs

```bash
# Direct to VM's NAT IP
open vnc://192.168.122.10:5900
```

Works from any Tailscale client.

## Performance Optimization

### Check Connection Type

```bash
tailscale status
# Look for "direct" vs "relay"

tailscale ping server
# Shows latency and path
```

### Direct Connection

Direct connections are faster:
- Same network: Always direct
- Different networks: Usually direct via UDP hole punching
- Restrictive NAT: May relay through Tailscale DERP servers

### Optimize for Relayed Connections

If relayed, reduce bandwidth:
- Lower color depth
- Reduce resolution
- Increase compression

## Access Control

### Tailscale ACLs

Restrict who can access which VMs:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["server:*"]
    },
    {
      "action": "accept",
      "src": ["user@email.com"],
      "dst": ["server:5900", "server:3389"]
    }
  ]
}
```

### Per-VM Access

With Tailscale on each VM:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:developers"],
      "dst": ["dev-vm:5900"]
    },
    {
      "action": "accept",
      "src": ["group:qa"],
      "dst": ["qa-vm:3389"]
    }
  ]
}
```

## Troubleshooting

### Cannot Connect

```bash
# Check Tailscale is connected
tailscale status

# Verify route to server
tailscale ping server

# Check if direct or relayed
tailscale netcheck
```

### Connection Times Out

1. Verify VNC/RDP service running on host
2. Check firewall allows tailscale0
3. Verify VM is running and accessible from host

### Slow Performance

1. Check if relayed: `tailscale status`
2. If relayed, check UDP ports open (41641)
3. Reduce quality settings in client
4. Check for network congestion

### MagicDNS Not Resolving

```bash
# Check DNS status
tailscale status

# Verify MagicDNS enabled
# In Tailscale Admin Console > DNS

# Test resolution
nslookup server.tail-network.ts.net
```

## Example Configurations

### Single VM Server

```
Server (100.64.0.2) - Tailscale installed
  └── Windows VM (NAT, port forward 3389)

From macOS:
  MS Remote Desktop → server.tail-network.ts.net:3389
```

### Multi-VM Lab

```
Server (100.64.0.2) - Tailscale + Subnet Router
  ├── Linux Dev (192.168.122.10:5900)
  ├── Windows Work (192.168.122.11:3389)
  └── Linux Test (192.168.122.12:5900)

From macOS:
  VNC → 192.168.122.10:5900 (via subnet route)
  RDP → 192.168.122.11:3389 (via subnet route)
```

### Enterprise Style

```
Each VM has Tailscale installed:
  ├── dev-vm.tail-network.ts.net:5900
  ├── windows-vm.tail-network.ts.net:3389
  └── test-vm.tail-network.ts.net:5900

ACLs control access per user/group
```

## Related

- [Tailscale Overview](../../tailscale/index.md)
- [Subnet Routers](../../tailscale/features/subnet-routers.md)
- [MagicDNS](../../tailscale/features/magicdns.md)
- [VNC Setup](../vnc/index.md)
- [RDP Setup](../rdp/index.md)
