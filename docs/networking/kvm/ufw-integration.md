# KVM UFW Integration

## The Conflict

libvirt and UFW both manipulate iptables, leading to potential conflicts:

1. **UFW default forward policy** blocks VM traffic
2. **libvirt rules** may not persist across UFW reloads
3. **Port forwarding** requires manual configuration

## How libvirt Uses iptables

### NAT Rules

```bash
sudo iptables -t nat -L -n | grep -A 10 LIBVIRT
```

Typical rules:

```
Chain LIBVIRT_PRT (1 references)
target     prot opt source               destination
RETURN     all  --  192.168.122.0/24     224.0.0.0/24
RETURN     all  --  192.168.122.0/24     255.255.255.255
MASQUERADE tcp  --  192.168.122.0/24    !192.168.122.0/24     masq ports: 1024-65535
MASQUERADE udp  --  192.168.122.0/24    !192.168.122.0/24     masq ports: 1024-65535
MASQUERADE all  --  192.168.122.0/24    !192.168.122.0/24
```

### Filter Rules

```bash
sudo iptables -L -n | grep -A 20 LIBVIRT
```

```
Chain LIBVIRT_FWI (1 references)
target     prot opt source               destination
ACCEPT     all  --  0.0.0.0/0            192.168.122.0/24     ctstate RELATED,ESTABLISHED
REJECT     all  --  0.0.0.0/0            0.0.0.0/0            reject-with icmp-port-unreachable

Chain LIBVIRT_FWO (1 references)
target     prot opt source               destination
ACCEPT     all  --  192.168.122.0/24     0.0.0.0/0
REJECT     all  --  0.0.0.0/0            0.0.0.0/0            reject-with icmp-port-unreachable

Chain LIBVIRT_FWX (1 references)
target     prot opt source               destination
ACCEPT     all  --  0.0.0.0/0            0.0.0.0/0
```

### Chain Order in FORWARD

```bash
sudo iptables -L FORWARD -n --line-numbers
```

```
num  target     prot opt source    destination
1    LIBVIRT_FWX  all --  anywhere  anywhere
2    LIBVIRT_FWI  all --  anywhere  anywhere
3    LIBVIRT_FWO  all --  anywhere  anywhere
4    ufw-before-forward all -- anywhere anywhere
...
```

libvirt chains process before UFW!

## Problem 1: UFW Blocks VM Traffic

### Symptom

VMs can't reach the internet despite libvirt network working.

### Cause

UFW's default forward policy is DROP:

```bash
# /etc/default/ufw
DEFAULT_FORWARD_POLICY="DROP"
```

### Solution 1: Change Default Policy

```bash
# /etc/default/ufw
DEFAULT_FORWARD_POLICY="ACCEPT"

# Reload
sudo ufw reload
```

!!! warning
    This allows all forwarded traffic. Use with other restrictions.

### Solution 2: Add Specific Rules (Recommended)

Edit `/etc/ufw/before.rules`:

```bash
# Before the *filter section ends (before COMMIT)

# Allow VM network forwarding
-A ufw-before-forward -s 192.168.122.0/24 -j ACCEPT
-A ufw-before-forward -d 192.168.122.0/24 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
```

## Problem 2: NAT Not Working

### Symptom

VMs can ping the host but not external IPs.

### Cause

Missing MASQUERADE rule or IP forwarding disabled.

### Solution

Check IP forwarding:

```bash
cat /proc/sys/net/ipv4/ip_forward
# Should be 1
```

Add NAT to before.rules:

```bash
# At the very beginning of the file
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# NAT for VM network
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE

COMMIT

# Then the *filter section...
```

## Problem 3: Rules Disappear on UFW Reload

### Symptom

After `ufw reload`, VM networking breaks.

### Cause

libvirt rules are in iptables but not in UFW's rule files.

### Solution

Restart libvirtd after UFW changes:

```bash
sudo ufw reload
sudo systemctl restart libvirtd
```

Or create a hook:

```bash
# /etc/ufw/after.init
#!/bin/bash
systemctl restart libvirtd
```

## Complete UFW Configuration for KVM

### /etc/ufw/before.rules

```bash
#
# UFW before.rules for KVM/libvirt
#

# NAT table
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# NAT for default VM network
-A POSTROUTING -s 192.168.122.0/24 ! -d 192.168.122.0/24 -o eth0 -j MASQUERADE

# Port forwarding examples (uncomment and modify as needed)
# Forward host:2222 to VM:22
# -A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to-destination 192.168.122.10:22

COMMIT

# Filter table
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
:ufw-not-local - [0:0]

# Allow loopback
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-output -o lo -j ACCEPT

# Established connections
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-output -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Invalid packets
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP

# ICMP
-A ufw-before-input -p icmp --icmp-type echo-request -j ACCEPT

# DHCP
-A ufw-before-input -p udp --sport 67 --dport 68 -j ACCEPT

# VM bridge forwarding - IMPORTANT
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# For additional VM networks, add similar rules:
# -A ufw-before-forward -i virbr1 -j ACCEPT
# -A ufw-before-forward -o virbr1 -j ACCEPT

# Allow forwarded traffic for port forwarding
# -A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT

# ufw-not-local
-A ufw-before-input -j ufw-not-local
-A ufw-not-local -m addrtype --dst-type LOCAL -j RETURN
-A ufw-not-local -m addrtype --dst-type MULTICAST -j RETURN
-A ufw-not-local -m addrtype --dst-type BROADCAST -j RETURN
-A ufw-not-local -j DROP

COMMIT
```

### /etc/default/ufw

```bash
# Can stay as DROP with before.rules handling forwarding
DEFAULT_FORWARD_POLICY="DROP"

# Enable IPv4 forwarding
IPV4_FORWARD=yes
```

### /etc/ufw/sysctl.conf

```bash
# Enable forwarding
net/ipv4/ip_forward=1
```

## Verification

### Check UFW Status

```bash
sudo ufw status verbose
```

### Check iptables Rules

```bash
# NAT rules
sudo iptables -t nat -L -n -v

# Forward rules
sudo iptables -L FORWARD -n -v

# Verify libvirt chains exist
sudo iptables -L | grep LIBVIRT
```

### Test VM Connectivity

```bash
# From VM
ping 192.168.122.1     # Gateway
ping 8.8.8.8           # External
ping google.com        # DNS
```

## Startup Order

Ensure proper service order:

```
1. Network (netplan/networkd)
2. UFW
3. libvirtd (recreates its iptables rules)
```

libvirtd must start after UFW to insert its chains in the right place.

### Systemd Dependencies

libvirtd already depends on network, but may need UFW dependency:

```bash
# /etc/systemd/system/libvirtd.service.d/ufw.conf
[Unit]
After=ufw.service
```

## Multiple VM Networks

For additional networks, add rules for each:

```bash
# /etc/ufw/before.rules

# Network 1: default (192.168.122.0/24)
-A POSTROUTING -s 192.168.122.0/24 ! -d 192.168.122.0/24 -o eth0 -j MASQUERADE
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# Network 2: internal (10.0.0.0/24)
-A POSTROUTING -s 10.0.0.0/24 ! -d 10.0.0.0/24 -o eth0 -j MASQUERADE
-A ufw-before-forward -i virbr1 -j ACCEPT
-A ufw-before-forward -o virbr1 -j ACCEPT
```

## Firewall Inside VMs

Even with host firewall configured, VMs should have their own:

```bash
# Inside VM
sudo ufw enable
sudo ufw default deny incoming
sudo ufw allow ssh
```

This provides defense in depth.
