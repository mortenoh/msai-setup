# Complete before.rules Reference

## Production-Ready Configuration

This is a complete `/etc/ufw/before.rules` file that handles Docker, KVM/libvirt, and LXD.

```bash
#
# /etc/ufw/before.rules
#
# Production UFW configuration for multi-technology home server
# Supports: Docker, KVM/libvirt, LXD
#

# ============================================================
# NAT TABLE
# ============================================================
*nat
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# ------------------------------------------------------------
# NAT for container/VM networks
# ------------------------------------------------------------

# Docker (if using iptables: false in daemon.json)
# -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE
# -A POSTROUTING -s 172.18.0.0/16 ! -o br-xxx -j MASQUERADE

# libvirt default network
-A POSTROUTING -s 192.168.122.0/24 ! -d 192.168.122.0/24 -o eth0 -j MASQUERADE

# libvirt additional networks (uncomment as needed)
# -A POSTROUTING -s 192.168.123.0/24 ! -d 192.168.123.0/24 -o eth0 -j MASQUERADE

# LXD default network
-A POSTROUTING -s 10.10.10.0/24 ! -d 10.10.10.0/24 -o eth0 -j MASQUERADE

# ------------------------------------------------------------
# Port forwarding examples
# ------------------------------------------------------------

# Forward host:2222 to VM SSH
# -A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to-destination 192.168.122.10:22

# Forward host:8080 to VM web server
# -A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.122.10:80

# Forward host:3389 to Windows VM RDP
# -A PREROUTING -i eth0 -p tcp --dport 3389 -j DNAT --to-destination 192.168.122.20:3389

# Forward host:32400 to Plex (if in VM)
# -A PREROUTING -i eth0 -p tcp --dport 32400 -j DNAT --to-destination 192.168.122.30:32400

# Hairpin NAT (for internal access via external IP)
# -A POSTROUTING -s 192.168.122.0/24 -d 192.168.122.10 -p tcp --dport 80 -j MASQUERADE

COMMIT

# ============================================================
# FILTER TABLE
# ============================================================
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
:ufw-not-local - [0:0]

# ------------------------------------------------------------
# Loopback - allow all
# ------------------------------------------------------------
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-output -o lo -j ACCEPT

# ------------------------------------------------------------
# Established/Related - fast path
# ------------------------------------------------------------
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-output -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# ------------------------------------------------------------
# Invalid packets - drop
# ------------------------------------------------------------
-A ufw-before-input -m conntrack --ctstate INVALID -j ufw-logging-deny
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP

# ------------------------------------------------------------
# ICMP - allow common types
# ------------------------------------------------------------
# Ping
-A ufw-before-input -p icmp --icmp-type echo-request -j ACCEPT

# Error messages
-A ufw-before-input -p icmp --icmp-type destination-unreachable -j ACCEPT
-A ufw-before-input -p icmp --icmp-type time-exceeded -j ACCEPT
-A ufw-before-input -p icmp --icmp-type parameter-problem -j ACCEPT

# For forwarded traffic
-A ufw-before-forward -p icmp --icmp-type echo-request -j ACCEPT
-A ufw-before-forward -p icmp --icmp-type destination-unreachable -j ACCEPT
-A ufw-before-forward -p icmp --icmp-type time-exceeded -j ACCEPT

# ------------------------------------------------------------
# DHCP - allow client
# ------------------------------------------------------------
-A ufw-before-input -p udp --sport 67 --dport 68 -j ACCEPT

# ------------------------------------------------------------
# Container/VM Bridge Forwarding
# ------------------------------------------------------------

# Docker bridge (docker0)
-A ufw-before-forward -i docker0 -j ACCEPT
-A ufw-before-forward -o docker0 -j ACCEPT

# Docker custom networks (add as needed)
# -A ufw-before-forward -i br-xxx -j ACCEPT
# -A ufw-before-forward -o br-xxx -j ACCEPT

# libvirt default network (virbr0)
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# libvirt additional networks (uncomment as needed)
# -A ufw-before-forward -i virbr1 -j ACCEPT
# -A ufw-before-forward -o virbr1 -j ACCEPT

# LXD bridge (lxdbr0)
-A ufw-before-forward -i lxdbr0 -j ACCEPT
-A ufw-before-forward -o lxdbr0 -j ACCEPT

# Host bridge for bridged VMs (br0)
# -A ufw-before-forward -i br0 -j ACCEPT
# -A ufw-before-forward -o br0 -j ACCEPT

# ------------------------------------------------------------
# Port forwarding filter rules
# (Required for DNAT rules above)
# ------------------------------------------------------------

# Allow forwarded SSH to VM
# -A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT

# Allow forwarded HTTP to VM
# -A ufw-before-forward -p tcp -d 192.168.122.10 --dport 80 -j ACCEPT

# Allow forwarded RDP to Windows VM
# -A ufw-before-forward -p tcp -d 192.168.122.20 --dport 3389 -j ACCEPT

# ------------------------------------------------------------
# Internal network restrictions (optional)
# ------------------------------------------------------------

# Block VMs from accessing host-only services
# -A ufw-before-forward -i virbr0 -d 192.168.1.100 -p tcp --dport 22 -j DROP

# Block cross-network traffic
# -A ufw-before-forward -i virbr0 -o lxdbr0 -j DROP
# -A ufw-before-forward -i lxdbr0 -o virbr0 -j DROP

# ------------------------------------------------------------
# Not-local handling
# ------------------------------------------------------------
-A ufw-before-input -j ufw-not-local

-A ufw-not-local -m addrtype --dst-type LOCAL -j RETURN
-A ufw-not-local -m addrtype --dst-type MULTICAST -j RETURN
-A ufw-not-local -m addrtype --dst-type BROADCAST -j RETURN
-A ufw-not-local -m limit --limit 3/min --limit-burst 10 -j ufw-logging-deny
-A ufw-not-local -j DROP

# ------------------------------------------------------------
# Multicast/Broadcast services (optional)
# ------------------------------------------------------------

# mDNS (Avahi, Bonjour)
-A ufw-before-input -p udp -d 224.0.0.251 --dport 5353 -j ACCEPT

# UPnP/SSDP (DLNA, Plex discovery)
-A ufw-before-input -p udp -d 239.255.255.250 --dport 1900 -j ACCEPT

# IGMP (multicast management)
-A ufw-before-input -p igmp -j ACCEPT

COMMIT
```

## Usage Notes

### Replace Interface Names

- `eth0` - Your external interface (check with `ip link`)
- Adjust subnet ranges to match your configuration

### Uncomment as Needed

Sections marked with comments (`#`) need to be uncommented and customized for your setup.

### After Editing

```bash
# Test syntax
sudo ufw --dry-run reload

# Apply
sudo ufw reload

# Verify
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v
```

## Companion /etc/default/ufw

```bash
# /etc/default/ufw

# Set to yes to apply rules to support IPv6
IPV6=yes

# Set the default input policy
DEFAULT_INPUT_POLICY="DROP"

# Set the default output policy
DEFAULT_OUTPUT_POLICY="ACCEPT"

# Set the default forward policy
# IMPORTANT: Keep DROP, we handle forwarding in before.rules
DEFAULT_FORWARD_POLICY="DROP"

# Set the default application policy
DEFAULT_APPLICATION_POLICY="SKIP"

# IPT_SYSCTL is deprecated, use /etc/sysctl.d/ instead
IPT_SYSCTL=/etc/ufw/sysctl.conf

# Additional modules for connection tracking
IPT_MODULES="nf_conntrack_ftp nf_conntrack_tftp"
```

## Companion sysctl Settings

```bash
# /etc/sysctl.d/99-ufw-forward.conf

# Enable IPv4 forwarding (required for VMs/containers)
net.ipv4.ip_forward = 1

# Enable IPv6 forwarding (if using IPv6)
# net.ipv6.conf.all.forwarding = 1

# Bridge filtering (apply iptables to bridged traffic)
net.bridge.bridge-nf-call-iptables = 1
net.bridge.bridge-nf-call-ip6tables = 1
```

Apply:

```bash
sudo sysctl -p /etc/sysctl.d/99-ufw-forward.conf
```
