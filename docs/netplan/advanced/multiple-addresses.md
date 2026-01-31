# Multiple IP Addresses

## Overview

Servers often need multiple IP addresses for:

- Virtual hosting (multiple websites)
- Service separation (different IPs for different services)
- High availability (floating IPs)
- Network migration (temporary dual addressing)

## Multiple Addresses on One Interface

### Basic Multiple Addresses

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Primary
        - 192.168.1.101/24    # Secondary
        - 192.168.1.102/24    # Tertiary
      routes:
        - to: default
          via: 192.168.1.1
```

### With Labels (Compatibility)

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24:
            label: "eth0"
        - 192.168.1.101/24:
            label: "eth0:web"
        - 192.168.1.102/24:
            label: "eth0:mail"
```

Labels help identify addresses in `ip addr` output and some legacy applications.

## Different Subnets

### Multiple Networks on One Interface

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Primary network
        - 10.0.0.100/24       # Secondary network
        - 172.16.0.100/24     # Third network
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 10.0.0.1
        - to: 172.16.0.0/12
          via: 172.16.0.1
```

### Public and Private

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 203.0.113.100/24    # Public IP
        - 10.0.0.100/24       # Private IP (management)
      routes:
        - to: default
          via: 203.0.113.1
        - to: 10.0.0.0/8
          via: 10.0.0.1
```

## IPv4 and IPv6

### Dual Stack with Multiple Addresses

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        # IPv4 addresses
        - 192.168.1.100/24
        - 192.168.1.101/24
        # IPv6 addresses
        - "2001:db8::100/64"
        - "2001:db8::101/64"
      routes:
        - to: default
          via: 192.168.1.1
        - to: "::/0"
          via: "2001:db8::1"
```

## Address Lifetime

### Permanent Addresses (Default)

```yaml
addresses:
  - 192.168.1.100/24
```

### Addresses with Lifetime

```yaml
addresses:
  - 192.168.1.100/24:
      lifetime: 0           # Permanent (default)
  - 192.168.1.200/24:
      lifetime: 3600        # Expires in 1 hour
```

## Floating/Virtual IPs

### For High Availability

Primary server:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Real IP
        - 192.168.1.200/24    # Floating IP (when primary)
      routes:
        - to: default
          via: 192.168.1.1
```

Secondary server (floating IP managed by HA software):

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.101/24    # Real IP
        # Floating IP (192.168.1.200) added by keepalived/pacemaker
      routes:
        - to: default
          via: 192.168.1.1
```

## CIDR Considerations

### Same Subnet

```yaml
addresses:
  - 192.168.1.100/24
  - 192.168.1.101/24    # Same /24, redundant route
```

### Host Addresses

For IPs that shouldn't create subnet routes:

```yaml
addresses:
  - 192.168.1.100/24    # Creates route for 192.168.1.0/24
  - 10.10.10.10/32      # No route created (loopback-style)
```

## Service Binding Examples

### Web Server Virtual Hosts

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Main site
        - 192.168.1.101/24    # Blog
        - 192.168.1.102/24    # API
```

Apache configuration:

```apache
<VirtualHost 192.168.1.100:443>
    ServerName www.example.com
</VirtualHost>

<VirtualHost 192.168.1.101:443>
    ServerName blog.example.com
</VirtualHost>

<VirtualHost 192.168.1.102:443>
    ServerName api.example.com
</VirtualHost>
```

### Database Replication

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Client connections
        - 10.0.0.100/24       # Replication traffic
```

## Loopback Addresses

### Additional Loopback IPs

```yaml
network:
  version: 2
  ethernets:
    lo:
      addresses:
        - 127.0.0.1/8         # Standard
        - 10.255.255.1/32     # Service IP
        - 10.255.255.2/32     # Another service
```

Loopback IPs are useful for:
- BGP anycast
- Service addresses
- Testing

## Dynamic Address Management

### Adding Addresses Dynamically

While netplan manages static config, you can add temporary addresses:

```bash
# Add temporary address
ip addr add 192.168.1.150/24 dev eth0

# Remove temporary address
ip addr del 192.168.1.150/24 dev eth0
```

!!! warning "Persistence"
    Manually added addresses are lost on reboot or netplan apply.

## Address Order

### Primary Address Selection

The first address is typically used as the source for outgoing connections:

```yaml
addresses:
  - 192.168.1.100/24    # Used as source IP
  - 192.168.1.101/24    # Secondary
```

### Explicit Source Selection

Some applications allow specifying source IP:

```bash
# Ping from specific source
ping -I 192.168.1.101 8.8.8.8

# curl with source
curl --interface 192.168.1.101 https://example.com
```

## Verifying Configuration

### Check All Addresses

```bash
# All addresses
ip addr show

# Specific interface
ip addr show dev eth0

# Just IPv4
ip -4 addr show dev eth0

# Just IPv6
ip -6 addr show dev eth0
```

### Check Address Labels

```bash
ip addr show dev eth0 | grep "inet.*label"
```

### Test Connectivity from Each Address

```bash
# Test each IP
for ip in 192.168.1.100 192.168.1.101 192.168.1.102; do
    echo "Testing $ip"
    ping -c 1 -I $ip 8.8.8.8
done
```

## Troubleshooting

### Address Not Added

```bash
# Check netplan syntax
sudo netplan generate

# Check systemd-networkd logs
journalctl -u systemd-networkd -f

# Verify generated config
cat /run/systemd/network/*netplan*.network
```

### Duplicate Address

```bash
# Check for duplicates
ip addr show | grep "192.168.1.100"

# May appear on multiple interfaces after misconfiguration
```

### Wrong Source Address

```bash
# Check routing table for source
ip route get 8.8.8.8

# May need policy routing for specific source requirements
```

## Best Practices

1. **Document all addresses** - Keep a record of what each IP is for
2. **Use labels** - Makes troubleshooting easier
3. **Plan CIDR carefully** - Avoid redundant routes
4. **Consider security** - Each IP may need firewall rules
5. **Test bindings** - Verify services bind to correct IPs
6. **Use DNS** - Don't rely on remembering IPs
