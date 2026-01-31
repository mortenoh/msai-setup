# MagicDNS

## Overview

MagicDNS provides automatic DNS for your Tailscale network, allowing you to use hostnames instead of IP addresses.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    MagicDNS Resolution                                       │
│                                                                              │
│   Without MagicDNS            With MagicDNS                                 │
│   ──────────────────          ─────────────                                 │
│   ssh 100.100.100.5           ssh my-server                                 │
│   ping 100.100.100.3          ping laptop                                   │
│   curl 100.100.100.2:8080     curl nas:8080                                 │
│                                                                              │
│   Hard to remember             Easy, memorable names                        │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Enabling MagicDNS

### Admin Console

1. Go to **DNS** tab in admin console
2. Enable **MagicDNS**
3. Optionally enable **Override local DNS**

### CLI

```bash
# Enable MagicDNS on device
sudo tailscale up --accept-dns
```

## DNS Names

### Full Names

Every device gets a full DNS name:

```
<hostname>.<tailnet-name>.ts.net
```

Examples:
- `my-laptop.tailnet.ts.net`
- `home-server.tailnet.ts.net`
- `work-pc.tailnet.ts.net`

### Short Names

Within your tailnet, short names work:

```bash
# These all work
ping my-laptop
ssh home-server
curl http://nas:8080
```

### Viewing DNS Names

```bash
# Your DNS name
tailscale status --json | jq -r '.Self.DNSName'

# All devices
tailscale status
```

## Tailnet Name

Your tailnet name determines the domain suffix:

| Account Type | Tailnet Name | Example Domain |
|--------------|--------------|----------------|
| Personal | `tailXXXXX.ts.net` | `laptop.tail12345.ts.net` |
| Custom domain | `example.com` | `laptop.example.com` |
| GitHub org | `org-name.github` | `server.org-name.github` |

### Custom Domain

For Google Workspace or Microsoft 365 users:

1. Verify domain ownership in admin console
2. Enable custom domain
3. Devices accessible at `hostname.yourdomain.com`

## DNS Configuration

### Global Nameservers

Set nameservers for all DNS queries:

```
Admin Console → DNS → Global nameservers
```

Add your preferred DNS servers:
- `1.1.1.1` (Cloudflare)
- `8.8.8.8` (Google)
- `9.9.9.9` (Quad9)

### Split DNS

Route specific domains to specific nameservers:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Split DNS Example                                         │
│                                                                              │
│   Domain                 Nameserver         Purpose                         │
│   ─────────────────────────────────────────────────────────────────         │
│   *.corp.example.com     100.100.100.10     Internal corporate DNS          │
│   *.home.local           192.168.1.1        Home network DNS                │
│   (everything else)      1.1.1.1            Public DNS                      │
│                                                                              │
│   Queries for corp.example.com → internal nameserver                        │
│   Queries for github.com → public DNS                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

Configure in admin console:

1. Go to **DNS** → **Nameservers**
2. Click **Add nameserver**
3. Select **Restricted to domain**
4. Enter domain and nameserver IP

### Example Split DNS

| Domain | Nameserver | Notes |
|--------|------------|-------|
| `corp.example.com` | `100.100.100.5` | Internal DNS on Tailscale |
| `home.lan` | `192.168.1.1` | Home router DNS |

## Search Domains

Add domains to the search path:

```bash
# Without search domain
ping server.corp.example.com

# With search domain configured
ping server  # Automatically tries server.corp.example.com
```

Configure in admin console under **DNS** → **Search domains**.

## Override Local DNS

When enabled, Tailscale DNS overrides system DNS:

```bash
# Check if override is active
cat /etc/resolv.conf

# Should show Tailscale resolver
# nameserver 100.100.100.100
```

### When to Enable

- You want consistent DNS across all devices
- Local DNS is unreliable
- You need split DNS everywhere

### When to Disable

- Local DNS provides important records
- You need local mDNS (.local domains)
- Some apps need system DNS

## DNS Queries

### Testing Resolution

```bash
# Query via Tailscale
tailscale dns query my-server

# Standard dig
dig my-server.tailnet.ts.net

# Check resolution
nslookup my-server
```

### DNS Status

```bash
tailscale dns status
```

Shows:
- Current nameservers
- Whether MagicDNS is enabled
- Active search domains

## Troubleshooting DNS

### DNS Not Working

```bash
# Check MagicDNS is enabled
tailscale dns status

# Verify accept-dns is set
tailscale status --json | jq '.Self.CapMap'

# Check resolv.conf
cat /etc/resolv.conf

# Restart resolvconf
sudo systemctl restart systemd-resolved
```

### Short Names Don't Resolve

```bash
# Try full name
ping my-server.tailnet.ts.net

# Check search domains
cat /etc/resolv.conf | grep search

# Verify MagicDNS in admin console
```

### Split DNS Not Working

```bash
# Test specific query
dig @100.100.100.5 internal.corp.example.com

# Check nameserver is reachable
tailscale ping 100.100.100.5

# Verify route to nameserver
ip route get 100.100.100.5
```

### resolv.conf Issues

Some systems don't update resolv.conf properly:

```bash
# For systemd-resolved systems
sudo systemctl restart systemd-resolved

# For NetworkManager
sudo systemctl restart NetworkManager

# Manual override (not persistent)
sudo tee /etc/resolv.conf << EOF
nameserver 100.100.100.100
search tailnet.ts.net
EOF
```

## DNS with Containers

### Docker

```yaml
# docker-compose.yml
services:
  myapp:
    dns:
      - 100.100.100.100
    dns_search:
      - tailnet.ts.net
```

### Kubernetes

```yaml
apiVersion: v1
kind: Pod
spec:
  dnsPolicy: None
  dnsConfig:
    nameservers:
      - 100.100.100.100
    searches:
      - tailnet.ts.net
```

## Private DNS Servers

Run your own DNS server on Tailscale:

### Example: Pi-hole

```bash
# Install Pi-hole on a Tailscale device
curl -sSL https://install.pi-hole.net | bash

# Add as nameserver in Tailscale
# Admin Console → DNS → Add nameserver
# IP: 100.100.100.X (Pi-hole's Tailscale IP)
```

### Example: AdGuard Home

```bash
# Run AdGuard Home
docker run -d \
  --name adguard \
  -p 53:53/udp \
  -p 3000:3000 \
  adguard/adguardhome

# Add to Tailscale DNS
```

## Best Practices

1. **Enable MagicDNS** for easy device access
2. **Use split DNS** for internal domains
3. **Set global nameservers** for consistent external DNS
4. **Add search domains** for frequently accessed domains
5. **Test resolution** after configuration changes

## DNS Records

MagicDNS provides:

| Record Type | Example |
|-------------|---------|
| A | `my-server.tailnet.ts.net → 100.100.100.5` |
| AAAA | `my-server.tailnet.ts.net → fd7a:115c:...` |
| PTR | `100.100.100.5 → my-server.tailnet.ts.net` |

No CNAME, MX, or TXT records (use external DNS for those).
