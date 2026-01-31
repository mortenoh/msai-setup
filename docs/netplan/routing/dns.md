# DNS Configuration

## DNS in Netplan

Netplan configures DNS through the `nameservers` key, which tells systemd-resolved (or NetworkManager) which DNS servers to use.

```
┌──────────────────────────────────────────────────────────┐
│                        Application                        │
│                            │                              │
│                            ▼                              │
│                    systemd-resolved                       │
│                     127.0.0.53:53                         │
│                            │                              │
│              ┌─────────────┼─────────────┐               │
│              ▼             ▼             ▼               │
│         eth0 DNS      eth1 DNS      wg0 DNS             │
│         1.1.1.1       10.0.0.1      10.10.0.1           │
│        (global)      (internal)    (vpn.local)          │
└──────────────────────────────────────────────────────────┘
```

## Basic DNS Configuration

### Static DNS Servers

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
```

### Multiple DNS with Search Domains

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        search:
          - example.com
          - internal.example.com
        addresses:
          - 192.168.1.1
          - 1.1.1.1
          - 8.8.8.8
```

### IPv6 DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - "2001:db8::100/64"
      nameservers:
        addresses:
          - 1.1.1.1
          - "2606:4700:4700::1111"  # Cloudflare IPv6
          - 8.8.8.8
          - "2001:4860:4860::8888"  # Google IPv6
```

## DHCP DNS

### Use DHCP DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-dns: true     # Use DNS from DHCP
```

### Override DHCP DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-dns: false    # Ignore DHCP DNS
      nameservers:
        addresses:
          - 1.1.1.1       # Use these instead
          - 8.8.8.8
```

### Combine DHCP and Static DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-dns: true     # Keep DHCP DNS
      nameservers:
        addresses:
          - 1.1.1.1       # Add static DNS (may be additional or override)
```

## Search Domains

### Single Domain

```yaml
nameservers:
  search:
    - example.com
  addresses:
    - 192.168.1.1
```

With this config, `ping server` resolves as `server.example.com`.

### Multiple Search Domains

```yaml
nameservers:
  search:
    - dev.example.com      # Tried first
    - staging.example.com  # Tried second
    - example.com          # Tried third
  addresses:
    - 192.168.1.1
```

### Per-Interface Domains

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      nameservers:
        search: [corp.example.com]
        addresses: [192.168.1.1]

    eth1:
      addresses:
        - 10.0.0.100/24
      nameservers:
        search: [lab.example.com]
        addresses: [10.0.0.1]
```

## Split DNS

Route DNS queries for specific domains to specific servers.

### VPN Split DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.2/24
      nameservers:
        search: [corp.internal, vpn.internal]
        addresses: [10.10.10.1]
      key: "PRIVATE_KEY"
      peers:
        - keys:
            public: "SERVER_KEY"
          endpoint: "vpn.example.com:51820"
          allowed-ips: [10.0.0.0/8]
```

systemd-resolved routes `*.corp.internal` and `*.vpn.internal` to VPN DNS.

### Multiple Networks

```yaml
network:
  version: 2
  ethernets:
    # Public interface
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1
      nameservers:
        addresses: [1.1.1.1]

    # Internal network
    eth1:
      addresses:
        - 10.0.0.10/24
      nameservers:
        search: [internal.corp.com, corp.com]
        addresses: [10.0.0.1, 10.0.0.2]
```

## DNS Over TLS/HTTPS

### With systemd-resolved

Configure via resolved.conf (not netplan):

```ini
# /etc/systemd/resolved.conf
[Resolve]
DNS=1.1.1.1#cloudflare-dns.com 1.0.0.1#cloudflare-dns.com
DNSOverTLS=yes
```

### Netplan DNS + Resolved DoT

```yaml
# /etc/netplan/00-config.yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-dns: false
      # DNS handled by resolved.conf
```

## Verifying DNS Configuration

### Check systemd-resolved

```bash
# Overall status
resolvectl status

# Per-interface DNS
resolvectl dns

# Domain routing
resolvectl domain

# Query test
resolvectl query example.com
```

### Check Effective DNS

```bash
# Current DNS servers
resolvectl status

# Or check resolv.conf
cat /etc/resolv.conf

# Or systemd stub
cat /run/systemd/resolve/resolv.conf
```

### Test Resolution

```bash
# Using system resolver
host example.com

# Using specific server
host example.com 1.1.1.1

# Detailed query
dig example.com

# Trace resolution path
dig +trace example.com
```

## DNS Caching

### systemd-resolved Cache

```bash
# View cache statistics
resolvectl statistics

# Flush cache
resolvectl flush-caches

# Reset statistics
resolvectl reset-statistics
```

### Disable Caching

```ini
# /etc/systemd/resolved.conf
[Resolve]
Cache=no
```

## Common DNS Servers

| Provider | IPv4 | IPv6 |
|----------|------|------|
| Cloudflare | 1.1.1.1, 1.0.0.1 | 2606:4700:4700::1111, ::1001 |
| Google | 8.8.8.8, 8.8.4.4 | 2001:4860:4860::8888, ::8844 |
| Quad9 | 9.9.9.9, 149.112.112.112 | 2620:fe::fe, 2620:fe::9 |
| OpenDNS | 208.67.222.222, 208.67.220.220 | 2620:119:35::35, ::53 |

### Privacy-Focused Configuration

```yaml
nameservers:
  addresses:
    - 1.1.1.1          # Cloudflare (privacy focused)
    - 9.9.9.9          # Quad9 (malware blocking)
```

### Security-Focused Configuration

```yaml
nameservers:
  addresses:
    - 9.9.9.9          # Quad9 (blocks malware domains)
    - 208.67.222.222   # OpenDNS (optional filtering)
```

## Local DNS Server

### Point to Local Resolver

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      nameservers:
        search: [home.local]
        addresses:
          - 192.168.1.1    # Local Pi-hole, AdGuard, etc.
```

### Fallback DNS

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      nameservers:
        addresses:
          - 192.168.1.1    # Primary (local)
          - 1.1.1.1        # Fallback (public)
```

## Troubleshooting DNS

### DNS Not Working

```bash
# Check resolved is running
systemctl status systemd-resolved

# Check DNS configuration
resolvectl status

# Test with known-good server
host example.com 1.1.1.1

# Check netplan config
cat /etc/netplan/*.yaml | grep -A5 nameservers
```

### Wrong DNS Server Used

```bash
# Check per-link DNS
resolvectl dns

# Check routing domains
resolvectl domain

# Verify configuration applied
cat /run/systemd/resolve/resolv.conf
```

### Slow DNS Resolution

```bash
# Check if DNS server responds
time host example.com

# Try different server
time host example.com 1.1.1.1

# Check for timeout issues
timeout 2 host example.com || echo "Timeout!"
```

### Search Domain Not Working

```bash
# Check search domains
resolvectl domain

# Test short name resolution
host server  # Should try server.example.com

# Check ndots setting
cat /etc/resolv.conf | grep ndots
```

### mDNS/LLMNR Issues

```bash
# Check mDNS status
resolvectl mdns

# Check LLMNR status
resolvectl llmnr

# Disable if causing issues
# /etc/systemd/resolved.conf
# MulticastDNS=no
# LLMNR=no
```

## Best Practices

1. **Use multiple DNS servers** - At least 2 for redundancy
2. **Include local and public** - Local for internal, public for fallback
3. **Set search domains** - Simplifies accessing internal resources
4. **Consider privacy** - Use privacy-focused DNS (1.1.1.1, 9.9.9.9)
5. **Enable DoT/DoH** - For encrypted DNS queries
6. **Test after changes** - Verify resolution works
7. **Monitor DNS health** - DNS failures break everything
