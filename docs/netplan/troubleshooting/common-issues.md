# Common Netplan Issues

## Quick Reference

| Problem | Solution |
|---------|----------|
| YAML syntax error | Check indentation (spaces, not tabs) |
| Network not applying | `sudo netplan apply` |
| Lost remote access | Use `netplan try` for safe testing |
| DHCP not working | Check interface name, cable, switch |
| Static IP conflicts | Verify IP isn't used elsewhere |
| DNS not working | Check nameservers config |
| Bridge not working | Interface must have no IP, add to bridge |

## Syntax Errors

### Tab Characters

YAML requires spaces, not tabs:

```bash
# Find tabs in file
cat -A /etc/netplan/config.yaml | grep "^I"

# Error message
Error in network definition: expected mapping
```

**Fix**: Replace tabs with spaces (2 per indent level).

### Indentation Errors

```yaml
# WRONG
network:
  version: 2
   ethernets:    # Extra space!
```

```yaml
# CORRECT
network:
  version: 2
  ethernets:    # Aligned with version
```

### Missing Quotes

```yaml
# WRONG - interpreted as octal
mtu: 0900

# CORRECT - quotes for clarity
mtu: 9000

# WRONG - IPv6 needs quotes
addresses:
  - 2001:db8::1/64

# CORRECT
addresses:
  - "2001:db8::1/64"
```

### Missing Version

```yaml
# WRONG - missing version
network:
  ethernets:
    eth0:
      dhcp4: true

# CORRECT
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

## Configuration Not Applying

### Changes Not Taking Effect

```bash
# Regenerate and apply
sudo netplan generate
sudo netplan apply

# Force restart of backend
sudo systemctl restart systemd-networkd

# Or for NetworkManager
sudo systemctl restart NetworkManager
```

### Conflicting Configurations

```bash
# Check for multiple files
ls -la /etc/netplan/

# Check for same interface in multiple files
grep -r "eth0" /etc/netplan/

# Files are processed in order - later overrides earlier
# Use single file or explicit ordering
```

### Wrong Renderer

```bash
# Check which renderer is active
grep renderer /etc/netplan/*.yaml

# networkd for servers (default on Ubuntu Server)
# NetworkManager for desktops
```

## Interface Issues

### Interface Not Found

```bash
# List available interfaces
ip link show

# Check interface name matches
# Names are case-sensitive

# Common naming schemes:
# - Predictable: enp5s0, ens192
# - Classic: eth0, eth1
# - Virtual: veth*, tap*, virbr*
```

### Interface Down

```bash
# Check interface state
ip link show eth0

# Bring up manually
sudo ip link set eth0 up

# Check for hardware issues
dmesg | grep eth0
```

### Cable/Link Issues

```bash
# Check carrier
cat /sys/class/net/eth0/carrier
# 1 = link up, 0 = link down

# Check speed
ethtool eth0 | grep Speed
```

## DHCP Problems

### No IP Address

```bash
# Check DHCP is configured
grep dhcp4 /etc/netplan/*.yaml

# Check interface is up
ip link show eth0

# Check DHCP client running
journalctl -u systemd-networkd | grep DHCP

# Request manually
dhclient eth0
```

### Wrong IP Address

```bash
# Release and renew
sudo dhclient -r eth0
sudo dhclient eth0

# Or restart networking
sudo netplan apply
```

### DHCP Server Not Reachable

```bash
# Check connectivity to DHCP server
# (can't ping if no IP, but check for errors)
journalctl -u systemd-networkd | tail -50

# Check cable, switch, VLAN
```

## Static IP Problems

### IP Not Assigned

```bash
# Check configuration
cat /etc/netplan/*.yaml

# Verify IP not in use
arping 192.168.1.100

# Check for typos in address (CIDR required)
# WRONG: 192.168.1.100
# CORRECT: 192.168.1.100/24
```

### Duplicate IP

```bash
# Check for duplicates
arping 192.168.1.100

# If another device has it, change IP or that device
```

## Gateway Issues

### No Default Route

```bash
# Check routes
ip route show

# Check gateway configuration
grep -A5 routes /etc/netplan/*.yaml
```

### Wrong Gateway

```bash
# Check gateway in config
grep via /etc/netplan/*.yaml

# Verify gateway is reachable
ping 192.168.1.1
```

### Gateway Unreachable

```bash
# Check if gateway is on same subnet
# IP: 192.168.1.100/24
# Gateway: 192.168.1.1 ✓
# Gateway: 192.168.2.1 ✗ (different subnet)

# Use on-link if needed
routes:
  - to: default
    via: 192.168.1.1
    on-link: true
```

## DNS Problems

### No Name Resolution

```bash
# Check DNS servers
resolvectl status

# Test DNS
dig google.com @1.1.1.1

# Check configuration
grep -A5 nameservers /etc/netplan/*.yaml
```

### Wrong DNS Servers

```bash
# Check configured servers
resolvectl dns

# Override with static
nameservers:
  addresses: [1.1.1.1, 8.8.8.8]
```

### DNS Not Using Netplan Config

```bash
# Check if DHCP is overriding
dhcp4-overrides:
  use-dns: false
nameservers:
  addresses: [1.1.1.1]
```

## Bridge Problems

### Bridge Has No IP

```bash
# Ensure IP is on bridge, not physical interface
ethernets:
  eth0:
    dhcp4: false  # No IP here

bridges:
  br0:
    interfaces:
      - eth0
    addresses:
      - 192.168.1.100/24  # IP on bridge
```

### Interface Not Joining Bridge

```bash
# Check interface exists
ip link show eth0

# Check bridge configuration
bridge link show

# Check interface isn't already in use
ip addr show eth0
# Should show no IP if going to bridge
```

### Bridge Blocking Traffic

```bash
# Check STP state
bridge link show

# Disable STP for single-bridge setups
parameters:
  stp: false
  forward-delay: 0
```

## VLAN Problems

### VLAN Interface Not Created

```bash
# Check 8021q module
lsmod | grep 8021q

# Load if missing
sudo modprobe 8021q

# Check configuration
vlans:
  eth0.10:      # Note the naming
    id: 10
    link: eth0  # Parent interface
```

### VLAN No Traffic

```bash
# Check switch configuration
# Port must be trunk or correct access VLAN

# Check VLAN ID matches switch
ip -d link show eth0.10 | grep vlan
```

## Bond Problems

### Bond Not Forming

```bash
# Check bonding module
lsmod | grep bonding

# Check interfaces are down first
ethernets:
  eth0:
    dhcp4: false
  eth1:
    dhcp4: false
```

### Bond Mode Issues

```bash
# Check bond status
cat /proc/net/bonding/bond0

# Verify switch supports mode
# 802.3ad requires LACP on switch
# active-backup needs no switch config
```

## Performance Issues

### Slow Network

```bash
# Check negotiated speed
ethtool eth0 | grep Speed

# Check for errors
ip -s link show eth0

# Check MTU
ip link show eth0 | grep mtu
```

### Packet Drops

```bash
# Check interface statistics
ip -s link show eth0

# Check ring buffers
ethtool -g eth0
```

## Recovery Procedures

### Lost Remote Access

If locked out after netplan changes:

1. Access via console (physical, IPMI, cloud console)
2. Restore backup: `cp /etc/netplan/backup.yaml /etc/netplan/config.yaml`
3. Apply: `netplan apply`

### Emergency Network Reset

```bash
# Remove all configs
rm /etc/netplan/*.yaml

# Create minimal DHCP config
cat > /etc/netplan/00-recover.yaml << 'EOF'
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
EOF

# Apply
netplan apply
```

### Boot with Network Issues

At GRUB, edit kernel parameters:

```
net.ifnames=0 biosdevname=0
```

This uses classic naming (eth0) and may bypass configuration issues.
