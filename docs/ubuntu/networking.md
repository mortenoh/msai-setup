# Networking

Ubuntu Server uses Netplan for network configuration with systemd-networkd as the default renderer.

!!! tip "Comprehensive Netplan Guide"
    For in-depth Netplan coverage including bridges, bonds, VLANs, and advanced routing, see the [Netplan Configuration Guide](../netplan/index.md).

## Quick Configuration

### Basic Static IP

Edit `/etc/netplan/00-installer-config.yaml`:

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
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

### DHCP Configuration

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: true
```

### Apply Configuration

```bash
# Test configuration (reverts after 2 minutes if no confirmation)
sudo netplan try

# Apply configuration
sudo netplan apply
```

## Verification

```bash
# Check IP addresses
ip addr show

# Check routes
ip route show

# Check DNS
resolvectl status

# Test connectivity
ping -c 3 8.8.8.8
ping -c 3 google.com
```

## Interface Naming

Find your interface name:

```bash
ip link show
```

Common patterns:

| Pattern | Description |
|---------|-------------|
| `enp5s0` | PCI Ethernet |
| `eno1` | Onboard Ethernet |
| `ens192` | Hotplug slot |
| `eth0` | Legacy naming (rare) |

## Common Tasks

### Multiple IP Addresses

```yaml
network:
  ethernets:
    enp5s0:
      addresses:
        - 192.168.1.100/24
        - 192.168.1.101/24
```

### Multiple DNS Servers

```yaml
network:
  ethernets:
    enp5s0:
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
          - 9.9.9.9
        search:
          - example.com
```

### Static Routes

```yaml
network:
  ethernets:
    enp5s0:
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.0.0.0/8
          via: 192.168.1.254
```

## Troubleshooting

### Configuration Issues

```bash
# Check syntax
sudo netplan generate

# Debug apply
sudo netplan --debug apply
```

### Common Problems

| Problem | Solution |
|---------|----------|
| No IP address | Check DHCP server or static config |
| Can't reach gateway | Check cable, subnet mask, gateway IP |
| DNS not working | Check nameservers configuration |
| Routes wrong | Verify routes section in netplan |

### Reset Network

```bash
# Restart networking
sudo systemctl restart systemd-networkd

# Or reapply netplan
sudo netplan apply
```

## Security Considerations

Netplan manages network configuration, not security. For network security:

- See [Firewall](firewall.md) for UFW configuration
- See [Firewall & Security Guide](../networking/index.md) for comprehensive firewall coverage

## Related Documentation

| Topic | Location |
|-------|----------|
| Full Netplan Guide | [Netplan Configuration](../netplan/index.md) |
| Bridges | [Netplan Bridges](../netplan/interfaces/bridges.md) |
| VLANs | [Netplan VLANs](../netplan/interfaces/vlans.md) |
| Firewall | [Firewall Guide](../networking/index.md) |
