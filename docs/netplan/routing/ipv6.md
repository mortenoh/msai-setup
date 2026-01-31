# IPv6 Configuration

## IPv6 Overview

IPv6 provides a vastly larger address space and eliminates the need for NAT in most cases.

```
IPv4: 192.168.1.100              (32 bits)
IPv6: 2001:0db8:85a3:0000:0000:8a2e:0370:7334 (128 bits)
      └──────┘ └──┘ └──┘ └──────────────────┘
      Prefix  Site Sub   Interface ID
```

## IPv6 Address Types

| Type | Prefix | Description |
|------|--------|-------------|
| Global Unicast | 2000::/3 | Public routable addresses |
| Link-Local | fe80::/10 | Auto-configured, single link only |
| Unique Local | fc00::/7 | Private addresses (like RFC1918) |
| Multicast | ff00::/8 | One-to-many delivery |
| Loopback | ::1/128 | Localhost |

## Basic IPv6 Configuration

### SLAAC (Stateless Auto-Configuration)

Most common for simple setups:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
      accept-ra: true    # Accept Router Advertisements
```

### DHCPv6

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true        # Use DHCPv6
```

### Static IPv6

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - "2001:db8::100/64"
      routes:
        - to: default
          via: 192.168.1.1
        - to: "::/0"
          via: "2001:db8::1"
      nameservers:
        addresses:
          - 1.1.1.1
          - "2606:4700:4700::1111"
```

## Dual Stack Configuration

### Full Dual Stack

```yaml
network:
  version: 2
  ethernets:
    eth0:
      # IPv4
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

      # IPv6
      addresses:
        - "2001:db8:1::100/64"
      routes:
        - to: "::/0"
          via: "2001:db8:1::1"

      nameservers:
        addresses:
          - 192.168.1.1
          - 1.1.1.1
          - "2001:db8:1::1"
          - "2606:4700:4700::1111"
```

### DHCP Dual Stack

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
```

### DHCP IPv4 + Static IPv6

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
      addresses:
        - "2001:db8::100/64"
      routes:
        - to: "::/0"
          via: "2001:db8::1"
```

## Router Advertisements (RA)

### Accept RA (Client Mode)

```yaml
network:
  version: 2
  ethernets:
    eth0:
      accept-ra: true
      dhcp6: false
```

RA provides:
- Default gateway
- Prefix information
- DNS servers (if configured)
- Other network parameters

### RA Options

```yaml
network:
  version: 2
  ethernets:
    eth0:
      accept-ra: true
      ipv6-address-generation: eui64    # Or stable-privacy
      ipv6-privacy: true                # Use privacy extensions
```

### Disable RA

For routers or when using static config:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      accept-ra: false
      addresses:
        - "2001:db8::1/64"
```

## Link-Local Addresses

Always present, auto-configured from MAC:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      link-local: [ipv6]    # Enable IPv6 link-local
      # Default is [ipv4, ipv6]
```

### Disable Link-Local

```yaml
network:
  version: 2
  ethernets:
    eth0:
      link-local: []        # No link-local addresses
```

## IPv6 Privacy Extensions

### Enable Privacy Extensions

Generate random interface IDs instead of MAC-based:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp6: true
      ipv6-privacy: true    # Use temporary addresses
```

### Address Generation Modes

```yaml
network:
  version: 2
  ethernets:
    eth0:
      accept-ra: true
      ipv6-address-generation: stable-privacy  # Stable but private
      # Options: eui64, stable-privacy
```

## Multiple IPv6 Addresses

### Primary and Secondary

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - "2001:db8::100/64"     # Primary
        - "2001:db8::101/64"     # Secondary
        - "2001:db8::102/64"     # Another
```

### Different Prefixes

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - "2001:db8:1::100/64"   # Production prefix
        - "2001:db8:2::100/64"   # Management prefix
```

## IPv6 Routing

### Default Gateway

```yaml
routes:
  - to: "::/0"                   # Default route
    via: "2001:db8::1"
```

### Static Routes

```yaml
routes:
  - to: "::/0"
    via: "2001:db8::1"

  - to: "2001:db8:100::/48"
    via: "2001:db8::254"

  - to: "fd00::/8"               # ULA range
    via: "2001:db8::253"
```

### Route Metrics

```yaml
routes:
  - to: "::/0"
    via: "2001:db8::1"
    metric: 100                  # Primary

  - to: "::/0"
    via: "2001:db8::2"
    metric: 200                  # Backup
```

## IPv6 on VLANs

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.10:
      id: 10
      link: eth0
      addresses:
        - 10.10.10.100/24
        - "2001:db8:10::100/64"
      routes:
        - to: default
          via: 10.10.10.1
        - to: "::/0"
          via: "2001:db8:10::1"
```

## IPv6 on Bridges

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
        - "2001:db8::100/64"
      routes:
        - to: default
          via: 192.168.1.1
        - to: "::/0"
          via: "2001:db8::1"
      accept-ra: false
```

## IPv6 Tunnels

### 6in4 Tunnel

IPv6 over IPv4:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1

  tunnels:
    he-ipv6:
      mode: sit
      local: 203.0.113.10
      remote: 216.66.80.26      # Hurricane Electric endpoint
      addresses:
        - "2001:470:xxxx::2/64"
      routes:
        - to: "::/0"
          via: "2001:470:xxxx::1"
```

### 6to4 (Deprecated)

```yaml
network:
  version: 2
  tunnels:
    tun6to4:
      mode: sit
      local: 203.0.113.10
      remote: any
      addresses:
        - "2002:cb00:710a::1/16"  # 2002:IPv4-hex
```

## IPv6-Only Configuration

### Pure IPv6

```yaml
network:
  version: 2
  ethernets:
    eth0:
      accept-ra: true
      dhcp6: true
      link-local: [ipv6]    # No IPv4 link-local
```

### IPv6 with NAT64/DNS64

For accessing IPv4 services:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp6: true
      nameservers:
        addresses:
          - "2001:db8::64"  # DNS64 server
```

## Disable IPv6

### Completely Disable

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: false
      accept-ra: false
      link-local: [ipv4]    # IPv4 only
```

### Kernel Parameter

```bash
# Temporary
sysctl -w net.ipv6.conf.all.disable_ipv6=1

# Permanent in /etc/sysctl.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
```

## Verifying IPv6

### Check Addresses

```bash
# All addresses
ip -6 addr show

# Specific interface
ip -6 addr show dev eth0
```

### Check Routes

```bash
# IPv6 routes
ip -6 route show

# Default route
ip -6 route show default
```

### Check Connectivity

```bash
# Ping IPv6
ping6 2001:4860:4860::8888

# Or modern ping
ping -6 google.com

# Trace route
traceroute6 google.com
```

### Check RA

```bash
# View received RAs
rdisc6 eth0

# Or
ndisc6 -r eth0
```

## Troubleshooting IPv6

### No IPv6 Address

```bash
# Check if IPv6 is enabled
cat /proc/sys/net/ipv6/conf/eth0/disable_ipv6
# 0 = enabled, 1 = disabled

# Check RA acceptance
cat /proc/sys/net/ipv6/conf/eth0/accept_ra

# Check interface is up
ip link show eth0

# Check for RA on network
rdisc6 eth0
```

### IPv6 Address But No Connectivity

```bash
# Check default route
ip -6 route show default

# Check gateway is reachable
ping6 <gateway-ip>

# Check firewall
ip6tables -L -n
```

### Privacy Address Issues

```bash
# Check privacy settings
cat /proc/sys/net/ipv6/conf/eth0/use_tempaddr
# 0 = disabled, 2 = prefer temporary

# Check addresses
ip -6 addr show dev eth0 scope global
```

### Duplicate Address Detection (DAD) Failed

```bash
# Check for DAD status
ip -6 addr show dev eth0 | grep tentative

# If address stuck in tentative:
ip -6 addr del <address> dev eth0
ip -6 addr add <address> dev eth0
```

## IPv6 Best Practices

1. **Use dual stack** - Support both IPv4 and IPv6
2. **Use static addresses for servers** - Predictable addressing
3. **Use SLAAC for clients** - Simpler management
4. **Enable privacy extensions on clients** - Better privacy
5. **Plan your prefix allocation** - Use /64 for each network
6. **Document your addressing** - IPv6 addresses are hard to remember
7. **Test IPv6 connectivity** - Many issues go unnoticed
8. **Use ULA for internal** - fc00::/7 for private networks
