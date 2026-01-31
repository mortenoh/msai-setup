# Subnet Routers

## Overview

Subnet routers allow Tailscale devices to access entire networks without installing Tailscale on every device.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Subnet Router Architecture                                │
│                                                                              │
│   Tailscale Network                   Home Network (192.168.1.0/24)         │
│                                       ─────────────────────────────         │
│   ┌──────────────┐                    ┌─────────────────────────────┐       │
│   │   Laptop     │                    │  ┌─────┐ ┌─────┐ ┌─────┐   │       │
│   │  (remote)    │                    │  │ NAS │ │Cam  │ │Print│   │       │
│   │   100.x.x.1  │                    │  │.100 │ │.101 │ │.102 │   │       │
│   └──────┬───────┘                    │  └─────┘ └─────┘ └─────┘   │       │
│          │                            │           │                 │       │
│          │                            │  ┌───────┴───────┐         │       │
│   ┌──────┴───────┐                    │  │ Subnet Router │         │       │
│   │    Phone     │────── Tailscale ───┼─▶│   100.x.x.2   │         │       │
│   │   100.x.x.3  │        tunnel      │  │   .1 (LAN)    │         │       │
│   └──────────────┘                    │  └───────────────┘         │       │
│                                       └─────────────────────────────┘       │
│                                                                              │
│   NAS, Camera, Printer don't need Tailscale installed!                      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Use Cases

| Scenario | Benefit |
|----------|---------|
| **Home network access** | Access NAS, printers, cameras remotely |
| **Office network** | Reach internal servers without individual install |
| **IoT devices** | Connect devices that can't run Tailscale |
| **Legacy systems** | Access old systems without modifications |
| **Lab networks** | Reach test environments |

## Setting Up a Subnet Router

### 1. Enable IP Forwarding

```bash
# Enable IPv4 forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf

# Enable IPv6 forwarding (if needed)
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf

# Apply
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

### 2. Advertise Routes

```bash
sudo tailscale up --advertise-routes=192.168.1.0/24
```

Multiple subnets:

```bash
sudo tailscale up --advertise-routes=192.168.1.0/24,192.168.2.0/24,10.0.0.0/8
```

### 3. Approve Routes

In admin console:
1. Go to **Machines**
2. Click the subnet router device
3. Click **Edit route settings**
4. Enable the advertised routes

Or use ACL auto-approvers (see below).

### 4. Accept Routes on Clients

```bash
# On devices that need to reach the subnet
sudo tailscale up --accept-routes
```

## Route Configuration

### Check Advertised Routes

```bash
# View routes this device advertises
tailscale status --json | jq '.Self.AllowedIPs'
```

### Check Accepted Routes

```bash
# View routes available to this device
ip route show | grep tailscale
```

### Verify Routing

```bash
# Trace route to subnet device
traceroute 192.168.1.100

# Should go through Tailscale interface
```

## Multiple Subnet Routers

### Redundancy

Run subnet routers on multiple devices for failover:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Redundant Subnet Routers                                  │
│                                                                              │
│                          192.168.1.0/24                                     │
│                                │                                             │
│              ┌─────────────────┼─────────────────┐                          │
│              │                 │                 │                          │
│        ┌─────┴─────┐     ┌─────┴─────┐     ┌─────┴─────┐                   │
│        │  Router 1 │     │  Router 2 │     │  Devices  │                   │
│        │ (primary) │     │ (backup)  │     │           │                   │
│        │ 100.x.x.1 │     │ 100.x.x.2 │     │           │                   │
│        └───────────┘     └───────────┘     └───────────┘                   │
│              │                 │                                             │
│              └────────┬────────┘                                            │
│                       │                                                      │
│               Tailscale routes                                              │
│               to nearest/fastest                                            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Both devices advertise the same routes:

```bash
# On router 1
sudo tailscale up --advertise-routes=192.168.1.0/24

# On router 2
sudo tailscale up --advertise-routes=192.168.1.0/24
```

Tailscale automatically routes to the best available router.

### Different Subnets

Route different networks through different routers:

```bash
# Home router
sudo tailscale up --advertise-routes=192.168.1.0/24

# Office router
sudo tailscale up --advertise-routes=10.0.0.0/8
```

## ACL Auto-Approvers

Automatically approve routes in your ACL policy:

```json
{
  "autoApprovers": {
    "routes": {
      "192.168.1.0/24": ["tag:router"],
      "10.0.0.0/8": ["group:admins"]
    }
  },
  "tagOwners": {
    "tag:router": ["group:admins"]
  }
}
```

Then tag the device:

```bash
sudo tailscale up --advertise-routes=192.168.1.0/24 --advertise-tags=tag:router
```

## 4via6 Subnet Routers

Access IPv4 subnets over IPv6-only paths:

```bash
sudo tailscale up --advertise-routes=192.168.1.0/24 --snat-subnet-routes=false
```

## Site-to-Site Networking

Connect multiple physical networks:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Site-to-Site with Tailscale                               │
│                                                                              │
│   Office A (NYC)                              Office B (SF)                 │
│   192.168.1.0/24                              192.168.2.0/24                │
│                                                                              │
│   ┌──────────────┐                            ┌──────────────┐              │
│   │   Servers    │                            │   Servers    │              │
│   │   Desktops   │                            │   Desktops   │              │
│   └──────┬───────┘                            └──────┬───────┘              │
│          │                                           │                       │
│   ┌──────┴───────┐         Tailscale          ┌──────┴───────┐              │
│   │   Router A   │◄─────────────────────────► │   Router B   │              │
│   │   100.x.x.1  │                            │   100.x.x.2  │              │
│   └──────────────┘                            └──────────────┘              │
│                                                                              │
│   Router A advertises: 192.168.1.0/24                                       │
│   Router B advertises: 192.168.2.0/24                                       │
│                                                                              │
│   Devices in NYC can reach SF devices at 192.168.2.x                        │
│   Devices in SF can reach NYC devices at 192.168.1.x                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Setup on each router:

```bash
# NYC Router
sudo tailscale up --advertise-routes=192.168.1.0/24 --accept-routes

# SF Router
sudo tailscale up --advertise-routes=192.168.2.0/24 --accept-routes
```

## SNAT vs Non-SNAT

### Default (SNAT enabled)

Traffic from Tailscale appears to come from the subnet router:

```
Client (100.x.x.1) → Router (100.x.x.2) → NAS sees: 192.168.1.1 (router's LAN IP)
```

Pros:
- Works without configuration on LAN devices
- No routing changes needed on LAN

### Non-SNAT

Preserve original source IP:

```bash
sudo tailscale up --advertise-routes=192.168.1.0/24 --snat-subnet-routes=false
```

```
Client (100.x.x.1) → Router → NAS sees: 100.x.x.1
```

Requires:
- LAN devices must have route back to Tailscale IPs
- Or router configured as default gateway

## Troubleshooting

### Routes Not Working

```bash
# Check routes are advertised
tailscale status --json | jq '.Self.AllowedIPs'

# Check routes are approved (admin console)

# Check accept-routes on client
tailscale status --json | jq '.Self'

# Check IP forwarding on router
sysctl net.ipv4.ip_forward
```

### Can't Reach Devices

```bash
# Verify Tailscale connectivity
tailscale ping subnet-router

# Check routing table
ip route get 192.168.1.100

# Test from subnet router itself
ping 192.168.1.100  # Should work

# Check firewall on subnet router
sudo iptables -L FORWARD -n -v
```

### Asymmetric Routing

If return traffic doesn't go through Tailscale:

```bash
# On subnet router, ensure it's the gateway
# Or enable SNAT (default)

# Check SNAT status
tailscale debug prefs | grep SNAT
```

### Firewall Issues

```bash
# Allow forwarding in iptables
sudo iptables -A FORWARD -i tailscale0 -j ACCEPT
sudo iptables -A FORWARD -o tailscale0 -j ACCEPT

# For nftables
sudo nft add rule inet filter forward iifname "tailscale0" accept
sudo nft add rule inet filter forward oifname "tailscale0" accept
```

## Platform-Specific Notes

### Linux

Standard setup as described above.

### macOS

Must use System Extension (not App Store version) for subnet routing.

### Windows

```powershell
# Enable IP forwarding
Set-NetIPInterface -Forwarding Enabled

# Advertise routes
tailscale up --advertise-routes=192.168.1.0/24
```

### Docker

```yaml
services:
  tailscale-router:
    image: tailscale/tailscale:latest
    cap_add:
      - NET_ADMIN
      - NET_RAW
    sysctls:
      - net.ipv4.ip_forward=1
    network_mode: host
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_EXTRA_ARGS=--advertise-routes=192.168.1.0/24
```

## Best Practices

1. **Use dedicated device** for subnet routing when possible
2. **Enable redundancy** with multiple subnet routers
3. **Document routes** for network clarity
4. **Use ACL auto-approvers** for automation
5. **Monitor bandwidth** - all subnet traffic goes through router
6. **Consider security** - subnet router can see all traffic
