# Debugging Netplan

## Diagnostic Commands

### netplan Commands

```bash
# Validate syntax
sudo netplan generate

# Verbose generation
sudo netplan --debug generate

# Show effective configuration
sudo netplan get

# Try configuration with rollback
sudo netplan try

# Show what will be applied
sudo netplan apply --debug
```

### System Information

```bash
# Network interfaces
ip link show
ip addr show

# Routes
ip route show
ip -6 route show

# DNS
resolvectl status

# Bridge details
bridge link show
bridge vlan show
```

## Validation

### Check YAML Syntax

```bash
# Using netplan
sudo netplan generate
# No output = valid syntax

# Using Python
python3 -c "import yaml; yaml.safe_load(open('/etc/netplan/config.yaml'))"

# Using yamllint
yamllint /etc/netplan/config.yaml
```

### Verbose Output

```bash
# Full debug output
sudo netplan --debug generate 2>&1 | less

# Shows:
# - Files being processed
# - Keys being parsed
# - Generated backend configs
```

## Backend Configuration

### Check Generated Files

For systemd-networkd:

```bash
# View generated network files
ls -la /run/systemd/network/

# Content of specific file
cat /run/systemd/network/10-netplan-eth0.network
cat /run/systemd/network/10-netplan-eth0.link
```

For NetworkManager:

```bash
# View generated connections
ls -la /run/NetworkManager/system-connections/

# nmcli view
nmcli connection show
```

### Compare Configuration

```bash
# What netplan will generate
sudo netplan generate --mapping

# What's currently running
networkctl status eth0
```

## Service Status

### systemd-networkd

```bash
# Service status
systemctl status systemd-networkd

# Detailed network status
networkctl status
networkctl status eth0

# View logs
journalctl -u systemd-networkd -f
journalctl -u systemd-networkd --since "10 minutes ago"
```

### NetworkManager

```bash
# Service status
systemctl status NetworkManager

# Connection status
nmcli general status
nmcli device status
nmcli connection show

# Logs
journalctl -u NetworkManager -f
```

### systemd-resolved (DNS)

```bash
# DNS status
resolvectl status
resolvectl statistics

# DNS logs
journalctl -u systemd-resolved -f
```

## Network Diagnostics

### Interface Status

```bash
# Link state
ip -s link show eth0

# Driver info
ethtool -i eth0

# Hardware status
ethtool eth0
```

### Address Assignment

```bash
# Check addresses
ip -4 addr show eth0
ip -6 addr show eth0

# Check DHCP lease
cat /var/lib/dhcp/dhclient.eth0.leases 2>/dev/null
journalctl -u systemd-networkd | grep DHCP
```

### Routing

```bash
# Full routing table
ip route show table all

# Specific destination
ip route get 8.8.8.8
ip route get 8.8.8.8 from 192.168.1.100

# Policy rules
ip rule show
```

### DNS Resolution

```bash
# Test resolution
resolvectl query google.com
dig google.com
host google.com

# DNS configuration
resolvectl status eth0
cat /run/systemd/resolve/resolv.conf
```

## Live Debugging

### Watch Interface Changes

```bash
# Monitor network events
ip monitor all

# Watch specific interface
ip monitor link dev eth0

# Watch addresses
ip monitor address
```

### Packet Capture

```bash
# Capture all traffic on interface
tcpdump -i eth0 -n

# DHCP traffic
tcpdump -i eth0 port 67 or port 68 -n

# ARP traffic
tcpdump -i eth0 arp -n

# Specific host
tcpdump -i eth0 host 192.168.1.1 -n
```

### Connection Testing

```bash
# Layer 2 - Check link
ip link show eth0

# Layer 3 - Check IP/routing
ping -c 3 192.168.1.1

# Layer 4 - Check ports
nc -vz 192.168.1.1 22
curl http://192.168.1.1/

# MTU testing
ping -M do -s 1472 192.168.1.1
```

## Debug Specific Issues

### DHCP Debugging

```bash
# Monitor DHCP
journalctl -u systemd-networkd -f | grep -i dhcp

# Manual DHCP request
dhclient -v eth0

# Check DHCP server responses
tcpdump -i eth0 port 67 or port 68 -n -v
```

### Bridge Debugging

```bash
# Bridge status
bridge link show
bridge fdb show
bridge vlan show

# Spanning tree
bridge stp status br0

# Check forwarding
cat /proc/sys/net/ipv4/ip_forward
```

### Bond Debugging

```bash
# Bond status
cat /proc/net/bonding/bond0

# Individual slave status
cat /proc/net/bonding/bond0 | grep -A10 "Slave Interface"

# LACP status
cat /proc/net/bonding/bond0 | grep -A10 "802.3ad"
```

### VLAN Debugging

```bash
# VLAN details
ip -d link show eth0.10

# VLAN statistics
cat /proc/net/vlan/eth0.10

# Check 8021q module
lsmod | grep 8021q
```

## Log Analysis

### Important Log Files

```bash
# System messages
journalctl -b | grep -i network
journalctl -b | grep -i eth0

# Specific services
journalctl -u systemd-networkd
journalctl -u NetworkManager
journalctl -u systemd-resolved

# Kernel messages
dmesg | grep -i eth0
dmesg | grep -i link
```

### Common Log Patterns

```bash
# DHCP success
journalctl -u systemd-networkd | grep "DHCPv4 address"

# DHCP failure
journalctl -u systemd-networkd | grep -i "dhcp" | grep -i -E "fail|error|timeout"

# Interface up/down
journalctl -u systemd-networkd | grep -i "gained\|lost"
```

## Testing Changes Safely

### netplan try

```bash
# Apply with automatic rollback
sudo netplan try

# Custom timeout
sudo netplan try --timeout 30

# The changes revert if you don't confirm
```

### Manual Testing

```bash
# Backup current config
sudo cp /etc/netplan/config.yaml /etc/netplan/config.yaml.backup

# Make changes
sudo nano /etc/netplan/config.yaml

# Validate
sudo netplan generate

# Apply
sudo netplan apply

# If broken, restore
sudo cp /etc/netplan/config.yaml.backup /etc/netplan/config.yaml
sudo netplan apply
```

## Debugging Script

Complete diagnostic script:

```bash
#!/bin/bash
# /usr/local/bin/netplan-debug.sh

echo "=== Netplan Configuration ==="
ls -la /etc/netplan/
cat /etc/netplan/*.yaml

echo -e "\n=== Validation ==="
sudo netplan generate && echo "Syntax: OK" || echo "Syntax: FAILED"

echo -e "\n=== Interfaces ==="
ip -br link show
ip -br addr show

echo -e "\n=== Routing ==="
ip route show

echo -e "\n=== DNS ==="
resolvectl status | head -30

echo -e "\n=== Generated Config ==="
ls -la /run/systemd/network/

echo -e "\n=== Service Status ==="
systemctl is-active systemd-networkd
systemctl is-active systemd-resolved

echo -e "\n=== Recent Logs ==="
journalctl -u systemd-networkd --since "5 minutes ago" --no-pager | tail -20

echo -e "\n=== Connectivity Test ==="
ping -c 1 8.8.8.8 > /dev/null && echo "Internet: OK" || echo "Internet: FAILED"
ping -c 1 google.com > /dev/null && echo "DNS: OK" || echo "DNS: FAILED"
```

```bash
chmod +x /usr/local/bin/netplan-debug.sh
```

## Getting Help

### Collect Information for Support

```bash
# System info
uname -a
lsb_release -a

# Netplan version
netplan --version

# All configs
cat /etc/netplan/*.yaml

# Network state
ip addr
ip route
resolvectl status

# Logs
journalctl -u systemd-networkd --since "1 hour ago"
```

### Resources

- [Netplan Documentation](https://netplan.io/reference)
- [Ubuntu Netplan](https://ubuntu.com/server/docs/network-configuration)
- Ubuntu Forums / Ask Ubuntu for specific issues
