# Exit Nodes

## Overview

Exit nodes route your internet traffic through another device on your Tailscale network, similar to a traditional VPN.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Exit Node Traffic Flow                                    │
│                                                                              │
│   Without Exit Node                 With Exit Node                          │
│   ──────────────────                ──────────────                          │
│                                                                              │
│   Your Device                       Your Device                             │
│       │                                 │                                   │
│       │ (your IP)                       │ (Tailscale)                       │
│       ▼                                 ▼                                   │
│   Internet                          Exit Node                               │
│                                         │                                   │
│                                         │ (exit node's IP)                  │
│                                         ▼                                   │
│                                     Internet                                │
│                                                                              │
│   Traffic appears from              Traffic appears from                    │
│   YOUR location                     EXIT NODE's location                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Use Cases

| Use Case | Benefit |
|----------|---------|
| **Untrusted WiFi** | Encrypt traffic on public networks |
| **Geographic access** | Access region-locked content |
| **IP consistency** | Always appear from same IP |
| **Privacy** | Hide real IP from destinations |
| **Home network access** | Route through home internet |

## Setting Up an Exit Node

### Prerequisites

Enable IP forwarding on the exit node:

```bash
# Enable IPv4 forwarding
echo 'net.ipv4.ip_forward = 1' | sudo tee /etc/sysctl.d/99-tailscale.conf

# Enable IPv6 forwarding
echo 'net.ipv6.conf.all.forwarding = 1' | sudo tee -a /etc/sysctl.d/99-tailscale.conf

# Apply
sudo sysctl -p /etc/sysctl.d/99-tailscale.conf
```

### Advertise as Exit Node

```bash
sudo tailscale up --advertise-exit-node
```

### Approve in Admin Console

1. Go to **Machines** in admin console
2. Find the device
3. Click **Edit route settings**
4. Enable **Use as exit node**

Or approve via CLI with proper ACLs.

## Using an Exit Node

### CLI

```bash
# List available exit nodes
tailscale exit-node list

# Use a specific exit node
sudo tailscale up --exit-node=my-server

# Use exit node and allow LAN access
sudo tailscale up --exit-node=my-server --exit-node-allow-lan-access

# Stop using exit node
sudo tailscale up --exit-node=
```

### GUI Applications

- **macOS**: Menu bar → Exit Nodes → Select node
- **Windows**: System tray → Exit Nodes → Select node
- **iOS/Android**: App → Use exit node → Select node

## Exit Node Configuration

### Allow LAN Access

By default, using an exit node routes ALL traffic. To keep local network access:

```bash
sudo tailscale up --exit-node=my-server --exit-node-allow-lan-access
```

This keeps these ranges local:
- `192.168.0.0/16`
- `172.16.0.0/12`
- `10.0.0.0/8`
- `169.254.0.0/16`
- `fe80::/10`

### Suggested Exit Node

Enable auto-selection of best exit node:

```bash
sudo tailscale up --exit-node-allow-lan-access
# Then use suggested in GUI
```

## Exit Node Types

### Personal Exit Node

Your own device running Tailscale:

```bash
# On home server
sudo tailscale up --advertise-exit-node --ssh
```

Benefits:
- No extra cost
- Full control
- Known location

### Mullvad Exit Nodes

Tailscale partners with Mullvad VPN:

1. Enable in admin console (**Settings** → **Mullvad**)
2. Select Mullvad exit node from list
3. Traffic exits through Mullvad servers

Benefits:
- Multiple global locations
- Commercial VPN privacy
- No self-hosting required

## Multiple Exit Nodes

You can have multiple exit nodes for redundancy or location options:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Multiple Exit Nodes                                       │
│                                                                              │
│   Home Server (NY)              Office Server (SF)        Cloud (EU)        │
│   ┌─────────────┐              ┌─────────────┐          ┌─────────────┐    │
│   │ exit-home   │              │ exit-office │          │ exit-eu     │    │
│   │ 100.x.x.1   │              │ 100.x.x.2   │          │ 100.x.x.3   │    │
│   └─────────────┘              └─────────────┘          └─────────────┘    │
│         │                            │                        │             │
│         └────────────────────────────┴────────────────────────┘             │
│                                      │                                       │
│                              Choose based on:                               │
│                              • Location needs                               │
│                              • Latency                                      │
│                              • Availability                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Checking Exit Node Status

### Current Exit Node

```bash
tailscale status
# Shows "exit node" next to active exit node

tailscale status --json | jq '.ExitNodeStatus'
```

### Verify IP

```bash
# Check your external IP
curl -s ifconfig.me
curl -s https://ipinfo.io/ip

# Should show exit node's IP, not yours
```

## Exit Node Best Practices

### For Exit Node Hosts

1. **Use a reliable connection** - Downtime affects all users
2. **Monitor bandwidth** - Exit traffic uses your connection
3. **Enable IP forwarding** - Required for routing
4. **Consider firewall rules** - May need to allow forwarding

### For Exit Node Users

1. **Test connectivity** - Verify connection works
2. **Enable LAN access** - If you need local resources
3. **Check for leaks** - DNS, WebRTC, etc.
4. **Switch when needed** - Use exit node only when necessary

## Docker Exit Node

Run an exit node in Docker:

```yaml
# docker-compose.yml
version: "3.8"

services:
  tailscale-exit:
    image: tailscale/tailscale:latest
    container_name: tailscale-exit
    cap_add:
      - NET_ADMIN
      - NET_RAW
      - SYS_MODULE
    volumes:
      - /dev/net/tun:/dev/net/tun
      - tailscale-state:/var/lib/tailscale
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
      - TS_EXTRA_ARGS=--advertise-exit-node
    sysctls:
      - net.ipv4.ip_forward=1
      - net.ipv6.conf.all.forwarding=1
    network_mode: host
    restart: unless-stopped

volumes:
  tailscale-state:
```

## Cloud Exit Node

### AWS EC2

```bash
#!/bin/bash
# User data for EC2 instance

# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Enable forwarding
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
sysctl -p

# Start as exit node
tailscale up --auth-key=tskey-auth-xxxxx --advertise-exit-node --hostname=aws-exit
```

### Cheap VPS Exit Node

Many cheap VPS providers work well:
- DigitalOcean ($4-6/mo)
- Vultr ($3.50/mo)
- Hetzner (€3/mo)
- Oracle Cloud (free tier)

## Troubleshooting

### Exit Node Not Working

```bash
# Check exit node is advertising
tailscale status

# Verify IP forwarding on exit node
sysctl net.ipv4.ip_forward
# Should return: net.ipv4.ip_forward = 1

# Check if approved in admin console
```

### Slow Through Exit Node

```bash
# Check latency to exit node
tailscale ping exit-node-name

# Check if using direct connection
tailscale status
# "direct" is better than "relay"

# Check exit node's internet speed
# SSH to exit node and test
speedtest-cli
```

### DNS Leaks

```bash
# Test for DNS leaks
curl https://dnsleaktest.com/

# Ensure Tailscale DNS is active
tailscale dns status
```

### Some Sites Don't Work

Some sites block VPN/datacenter IPs:
- Use a residential exit node (home server)
- Try different exit node location
- Check if exit node IP is blocklisted

## Security Considerations

### Exit Node Trust

When using an exit node, that device can see:
- Your DNS queries
- Destination IPs
- Unencrypted traffic metadata

Only use exit nodes you trust.

### Exit Node as Attack Surface

Exit node hosts should:
- Keep systems updated
- Monitor for unusual traffic
- Use firewall rules appropriately
- Consider separate device for exit node
