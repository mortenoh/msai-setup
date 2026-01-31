# Network Issues

This page covers diagnosing and resolving network connectivity problems on Ubuntu Server 24.04 LTS.

## Diagnostic Process

### Network Troubleshooting Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    1. Is interface up?                       │
│                    ip link show                              │
└─────────────────────────────────────────────────────────────┘
                              │ No → Fix interface
                              ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│                    2. Has IP address?                        │
│                    ip addr show                              │
└─────────────────────────────────────────────────────────────┘
                              │ No → Fix DHCP/static config
                              ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│                    3. Can reach gateway?                     │
│                    ping gateway-ip                           │
└─────────────────────────────────────────────────────────────┘
                              │ No → Check cable/switch/config
                              ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│                    4. Can reach internet?                    │
│                    ping 8.8.8.8                              │
└─────────────────────────────────────────────────────────────┘
                              │ No → Check routing
                              ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│                    5. DNS working?                           │
│                    ping google.com                           │
└─────────────────────────────────────────────────────────────┘
                              │ No → Fix DNS
                              ▼ Yes
┌─────────────────────────────────────────────────────────────┐
│                    6. Application issue                      │
│             Check firewall, service config                   │
└─────────────────────────────────────────────────────────────┘
```

## Basic Connectivity

### Check Interface Status

```bash
# List all interfaces
ip link show

# Detailed interface info
ip addr show

# Interface statistics
ip -s link show enp5s0
```

Interface states:

| State | Meaning |
|-------|---------|
| UP | Interface is up |
| DOWN | Interface is down |
| LOWER_UP | Physical link is up |
| NO-CARRIER | No cable/link |

### Bring Interface Up

```bash
# Using ip command
sudo ip link set enp5s0 up

# Using netplan
sudo netplan apply

# Check result
ip link show enp5s0
```

### Check Physical Connection

```bash
# Check link status
ethtool enp5s0 | grep "Link detected"

# Check speed/duplex
ethtool enp5s0 | grep -E "Speed|Duplex"

# If "Link detected: no"
# - Check cable
# - Check switch port
# - Try different port/cable
```

## IP Configuration

### DHCP Issues

```bash
# Release current lease
sudo dhclient -r enp5s0

# Request new lease
sudo dhclient enp5s0

# Check if got address
ip addr show enp5s0

# Check DHCP client logs
sudo journalctl -u systemd-networkd | grep DHCP
```

### Static IP Issues

Check Netplan configuration:

```bash
cat /etc/netplan/*.yaml
```

Common issues:

```yaml
# Wrong: Missing addresses as list
addresses: 192.168.1.100/24

# Correct: Addresses as list
addresses:
  - 192.168.1.100/24

# Wrong: gateway4 (deprecated)
gateway4: 192.168.1.1

# Correct: routes
routes:
  - to: default
    via: 192.168.1.1
```

Validate and apply:

```bash
# Check syntax
sudo netplan generate

# Apply (use --debug for verbose)
sudo netplan --debug apply

# If locked out, revert in 2 minutes
sudo netplan try
```

### Check IP Configuration

```bash
# Current IP addresses
ip addr show

# Current routes
ip route show

# Default gateway
ip route show default
```

## Routing Problems

### Check Default Route

```bash
# View routing table
ip route show

# Should have default route like:
# default via 192.168.1.1 dev enp5s0 proto static

# If missing, add temporarily:
sudo ip route add default via 192.168.1.1 dev enp5s0
```

### Multiple Default Routes

```bash
# Check for duplicate defaults
ip route show | grep default

# Remove extra route
sudo ip route del default via 192.168.1.2

# Fix in Netplan for persistence
```

### Test Routing

```bash
# Trace route to destination
traceroute 8.8.8.8
# or
tracepath 8.8.8.8

# Check which interface is used
ip route get 8.8.8.8
```

## DNS Problems

### Check Current DNS

```bash
# Using systemd-resolved
resolvectl status

# Or check resolv.conf
cat /etc/resolv.conf
```

### Test DNS Resolution

```bash
# Test specific DNS server
dig @8.8.8.8 google.com

# Test system resolution
dig google.com

# Simple test
nslookup google.com

# Check response
host google.com
```

### Fix DNS

```bash
# Temporary fix - direct resolv.conf edit
sudo nano /etc/resolv.conf
# Add: nameserver 8.8.8.8

# Better - configure systemd-resolved
sudo nano /etc/systemd/resolved.conf
```

```ini
[Resolve]
DNS=8.8.8.8 1.1.1.1
FallbackDNS=8.8.4.4
```

```bash
sudo systemctl restart systemd-resolved
```

### Or via Netplan

```yaml
network:
  ethernets:
    enp5s0:
      addresses:
        - 192.168.1.100/24
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

## Firewall Issues

### Check UFW Status

```bash
# Status
sudo ufw status verbose

# Check specific port
sudo ufw status | grep 22

# Temporarily disable for testing
sudo ufw disable

# Re-enable after testing
sudo ufw enable
```

### Check iptables

```bash
# List all rules
sudo iptables -L -n -v

# List NAT rules
sudo iptables -t nat -L -n -v

# Check if packet would be dropped
sudo iptables -C INPUT -p tcp --dport 22 -j ACCEPT
```

### Allow Traffic

```bash
# Allow port via UFW
sudo ufw allow 22/tcp

# Allow from specific network
sudo ufw allow from 192.168.1.0/24 to any port 22

# Reload UFW
sudo ufw reload
```

## Service-Specific Issues

### SSH Connection Refused

```bash
# Check SSH is running
systemctl status ssh

# Check SSH is listening
sudo ss -tlnp | grep 22

# Check firewall allows SSH
sudo ufw status | grep 22

# Check sshd config
sudo sshd -t

# Check auth log
sudo tail -f /var/log/auth.log
```

### Web Server Not Responding

```bash
# Check service is running
systemctl status nginx

# Check listening ports
sudo ss -tlnp | grep -E ":80|:443"

# Check firewall
sudo ufw status | grep -E "80|443"

# Test locally
curl -I http://localhost

# Check error logs
sudo tail -f /var/log/nginx/error.log
```

## Network Manager vs Netplan

### Check What's Managing Network

```bash
# Check if NetworkManager is active
systemctl status NetworkManager

# Check if systemd-networkd is active
systemctl status systemd-networkd

# Check Netplan renderer
grep renderer /etc/netplan/*.yaml
```

### Switch to NetworkManager

```yaml
# /etc/netplan/01-network-manager-all.yaml
network:
  version: 2
  renderer: NetworkManager
```

### Switch to systemd-networkd

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: true
```

## Advanced Diagnostics

### Packet Capture

```bash
# Capture on interface
sudo tcpdump -i enp5s0 -n

# Capture specific traffic
sudo tcpdump -i enp5s0 port 80

# Capture to file
sudo tcpdump -i enp5s0 -w capture.pcap

# Analyze with Wireshark (if GUI available)
wireshark capture.pcap
```

### Network Statistics

```bash
# Connection states
ss -s

# All connections
ss -ant

# Listening ports
ss -tlnp

# Interface statistics
ip -s link

# Network errors
netstat -i
```

### ARP Issues

```bash
# View ARP table
ip neigh show

# Clear ARP cache
sudo ip neigh flush all

# Check for duplicate IPs
arping -D -I enp5s0 192.168.1.100
```

## Common Problems

### "Network is Unreachable"

```bash
# No default route
ip route show
# Add route:
sudo ip route add default via 192.168.1.1

# Fix in Netplan for persistence
```

### "Host is Unreachable"

```bash
# Target not on network or ARP failure
# Check if on same subnet
ip addr show
# Check ARP
ip neigh show | grep target-ip
# Try ping with explicit interface
ping -I enp5s0 target-ip
```

### "Connection Refused"

```bash
# Service not running or not listening
# Check service
systemctl status service-name
# Check listening
ss -tlnp | grep port
# Check firewall
sudo ufw status
```

### "Connection Timed Out"

```bash
# Firewall or routing issue
# Check route
ip route get destination
# Check firewall
sudo iptables -L -n
# Trace path
traceroute destination
```

### Slow Network

```bash
# Check for errors
ip -s link show enp5s0 | grep -E "errors|dropped"

# Check duplex mismatch
ethtool enp5s0 | grep -E "Speed|Duplex"

# Check for packet loss
ping -c 100 gateway | tail -2

# Check MTU issues
ping -M do -s 1472 destination
```

## Quick Reference

### Diagnostic Commands

```bash
# Interface
ip link show              # Interface status
ip addr show              # IP addresses
ethtool enp5s0            # Physical link

# Connectivity
ping gateway              # Test gateway
ping 8.8.8.8              # Test internet
ping google.com           # Test DNS

# DNS
resolvectl status         # DNS status
dig google.com            # DNS lookup
nslookup google.com       # Simple lookup

# Routing
ip route show             # Routing table
traceroute 8.8.8.8        # Path to destination

# Ports
ss -tlnp                  # Listening ports
ss -ant                   # All connections

# Firewall
sudo ufw status           # UFW status
sudo iptables -L -n       # Raw rules
```

### Quick Fixes

```bash
# Restart networking
sudo netplan apply
# or
sudo systemctl restart systemd-networkd

# Get new DHCP lease
sudo dhclient -r enp5s0 && sudo dhclient enp5s0

# Add default route
sudo ip route add default via GATEWAY

# Add DNS
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf
```

## Next Steps

If network issues are resolved but you suspect security problems, see [Security Incidents](security-incidents.md).
