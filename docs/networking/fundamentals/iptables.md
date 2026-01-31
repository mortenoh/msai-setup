# iptables Deep Dive

## What is iptables?

iptables is the traditional userspace tool for configuring netfilter. Despite nftables being the modern replacement, iptables remains widely used and is essential to understand because:

- Docker uses iptables
- libvirt uses iptables
- UFW generates iptables rules
- Most documentation references iptables

## Command Structure

```bash
iptables [-t table] COMMAND chain [match] [target]
```

### Tables (-t)

| Table | Default | Purpose |
|-------|---------|---------|
| filter | Yes | Packet filtering |
| nat | No | Address translation |
| mangle | No | Packet modification |
| raw | No | Connection tracking bypass |

### Commands

| Command | Action |
|---------|--------|
| -A | Append rule to chain |
| -I | Insert rule at position |
| -D | Delete rule |
| -R | Replace rule |
| -L | List rules |
| -F | Flush (delete all rules) |
| -Z | Zero counters |
| -N | Create new chain |
| -X | Delete chain |
| -P | Set chain policy |

### Basic Examples

```bash
# List all rules with line numbers
iptables -L -n -v --line-numbers

# List specific table
iptables -t nat -L -n -v

# Append rule
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Insert at position 1
iptables -I INPUT 1 -p tcp --dport 80 -j ACCEPT

# Delete by specification
iptables -D INPUT -p tcp --dport 22 -j ACCEPT

# Delete by line number
iptables -D INPUT 3

# Set default policy
iptables -P INPUT DROP
```

## Match Extensions

### Protocol Matches

```bash
# TCP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --sport 1024: -j ACCEPT
iptables -A INPUT -p tcp --tcp-flags SYN,ACK SYN -j DROP

# UDP
iptables -A INPUT -p udp --dport 53 -j ACCEPT

# ICMP
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT
```

### State Matching (conntrack)

```bash
# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Only new connections to SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP
```

### Source/Destination

```bash
# By IP
iptables -A INPUT -s 192.168.1.100 -j ACCEPT
iptables -A INPUT -d 10.0.0.0/8 -j DROP

# By interface
iptables -A INPUT -i eth0 -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Negation
iptables -A INPUT ! -s 192.168.1.0/24 -j DROP
```

### Multiport

```bash
# Multiple ports
iptables -A INPUT -p tcp -m multiport --dports 80,443,8080 -j ACCEPT

# Port ranges
iptables -A INPUT -p tcp -m multiport --dports 6000:6100 -j ACCEPT
```

### IP Ranges

```bash
iptables -A INPUT -m iprange --src-range 192.168.1.100-192.168.1.200 -j ACCEPT
```

### MAC Address

```bash
iptables -A INPUT -m mac --mac-source AA:BB:CC:DD:EE:FF -j ACCEPT
```

### Time-Based

```bash
# Only during business hours
iptables -A INPUT -p tcp --dport 22 -m time \
    --timestart 09:00 --timestop 17:00 \
    --weekdays Mon,Tue,Wed,Thu,Fri -j ACCEPT
```

### Rate Limiting

```bash
# Limit new SSH connections
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m limit --limit 3/minute --limit-burst 3 -j ACCEPT

# Using hashlimit per source IP
iptables -A INPUT -p tcp --dport 80 -m hashlimit \
    --hashlimit-name http \
    --hashlimit-mode srcip \
    --hashlimit-above 100/sec \
    --hashlimit-burst 500 -j DROP
```

### Recent Module

```bash
# Track recent connections
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --set --name SSH

# Drop if too many recent attempts
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --update --seconds 60 --hitcount 4 --name SSH -j DROP
```

### String Matching

```bash
# Block requests containing pattern
iptables -A INPUT -p tcp --dport 80 \
    -m string --string "malicious" --algo bm -j DROP
```

### Comment

```bash
iptables -A INPUT -p tcp --dport 22 -m comment --comment "SSH access" -j ACCEPT
```

## NAT Operations

### Source NAT (SNAT)

```bash
# Static SNAT
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 \
    -j SNAT --to-source 203.0.113.1

# MASQUERADE (dynamic SNAT)
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE
```

### Destination NAT (DNAT)

```bash
# Port forwarding
iptables -t nat -A PREROUTING -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.1.10:80

# With interface restriction
iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 2222 \
    -j DNAT --to-destination 192.168.1.10:22
```

### Redirect

```bash
# Redirect to local port
iptables -t nat -A PREROUTING -p tcp --dport 80 \
    -j REDIRECT --to-ports 8080
```

### Hairpin NAT

When internal clients access internal services via external IP:

```bash
# Enable hairpin NAT
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -d 192.168.1.10 \
    -p tcp --dport 80 -j MASQUERADE
```

## Practical Configurations

### Basic Firewall

```bash
#!/bin/bash

# Flush existing rules
iptables -F
iptables -X
iptables -t nat -F
iptables -t nat -X

# Set default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# Allow loopback
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# Allow established connections
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Drop invalid packets
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Allow SSH
iptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW -j ACCEPT

# Allow ICMP (ping)
iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT

# Log dropped packets
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "iptables-dropped: "
```

### NAT Router

```bash
#!/bin/bash

# Enable forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Flush rules
iptables -F
iptables -t nat -F

# Default policies
iptables -P INPUT DROP
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# NAT for internal network
iptables -t nat -A POSTROUTING -s 192.168.1.0/24 -o eth0 -j MASQUERADE

# Allow forwarding for established
iptables -A FORWARD -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Allow internal to external
iptables -A FORWARD -i eth1 -o eth0 -j ACCEPT

# Allow specific ports from external
iptables -A FORWARD -i eth0 -o eth1 -p tcp --dport 80 -j ACCEPT
```

### Docker-Aware Configuration

```bash
#!/bin/bash

# IMPORTANT: Run after Docker starts

# Allow Docker bridge
iptables -A INPUT -i docker0 -j ACCEPT

# Allow forwarding for Docker
iptables -A FORWARD -i docker0 -j ACCEPT
iptables -A FORWARD -o docker0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Block external access to unpublished ports
# Docker handles published ports via DOCKER chain
```

## Viewing and Debugging

### List Rules

```bash
# Basic list
iptables -L

# With packet counts
iptables -L -v

# With line numbers
iptables -L --line-numbers

# Numeric (no DNS lookups)
iptables -L -n

# All tables
iptables -L -n -v
iptables -t nat -L -n -v
iptables -t mangle -L -n -v
iptables -t raw -L -n -v
```

### Save and Restore

```bash
# Save current rules
iptables-save > /etc/iptables/rules.v4

# Restore rules
iptables-restore < /etc/iptables/rules.v4

# View saved rules (good for debugging)
iptables-save
```

### Packet Tracing

```bash
# Enable tracing for specific traffic
iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
iptables -t raw -A OUTPUT -p tcp --dport 80 -j TRACE

# View trace in kernel log
dmesg -w | grep TRACE

# Or with nfnetlink_log
modprobe nfnetlink_log
```

### Logging

```bash
# Log before dropping
iptables -A INPUT -j LOG --log-prefix "INPUT-DROP: " --log-level 4
iptables -A INPUT -j DROP

# Rate-limited logging
iptables -A INPUT -m limit --limit 5/min -j LOG --log-prefix "DROPPED: "

# View logs
journalctl -k | grep INPUT-DROP
```

## Rule Ordering

Order matters! Rules are processed top to bottom:

```bash
# WRONG: First rule matches everything
iptables -A INPUT -j DROP
iptables -A INPUT -p tcp --dport 22 -j ACCEPT  # Never reached

# CORRECT: Specific rules first
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -j DROP
```

### Optimization

Put frequently matched rules early:

```bash
# High-traffic established connections first
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
iptables -A INPUT -m conntrack --ctstate INVALID -j DROP

# Then specific services
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Default deny last
iptables -A INPUT -j DROP
```

## iptables vs Docker/libvirt

### Chain Priority

Both Docker and libvirt insert their chains early:

```bash
# Docker adds:
-A FORWARD -j DOCKER-USER       # User customization
-A FORWARD -j DOCKER-ISOLATION-STAGE-1
-A FORWARD -o docker0 -j DOCKER

# libvirt adds:
-A FORWARD -j LIBVIRT_FWI
-A FORWARD -j LIBVIRT_FWO
-A FORWARD -j LIBVIRT_FWX
```

### DOCKER-USER Chain

The only safe place for custom Docker rules:

```bash
# Block external access to container
iptables -I DOCKER-USER -i eth0 -p tcp --dport 8080 -j DROP

# Allow only from specific network
iptables -I DOCKER-USER -i eth0 -s 192.168.1.0/24 -j RETURN
iptables -I DOCKER-USER -i eth0 -j DROP
```

## Persistence

### Using iptables-persistent

```bash
# Install
sudo apt install iptables-persistent

# Save current rules
sudo netfilter-persistent save

# Rules are stored in:
# /etc/iptables/rules.v4
# /etc/iptables/rules.v6
```

### Manual systemd Service

```bash
# /etc/systemd/system/iptables-restore.service
[Unit]
Description=Restore iptables rules
Before=network-pre.target
Wants=network-pre.target

[Service]
Type=oneshot
ExecStart=/sbin/iptables-restore /etc/iptables/rules.v4
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### Interaction with Docker

!!! warning
    Docker recreates its rules on restart, potentially overwriting your rules.

Ensure your rules go in DOCKER-USER or run your script after Docker starts.

## IPv6 with ip6tables

Separate commands for IPv6:

```bash
# List IPv6 rules
ip6tables -L -n -v

# Add IPv6 rule
ip6tables -A INPUT -p tcp --dport 22 -j ACCEPT

# Save IPv6 rules
ip6tables-save > /etc/iptables/rules.v6
```

### Dual-Stack Considerations

```bash
# Block IPv6 if not needed
ip6tables -P INPUT DROP
ip6tables -P FORWARD DROP
ip6tables -P OUTPUT DROP

# Or allow loopback only
ip6tables -A INPUT -i lo -j ACCEPT
ip6tables -A OUTPUT -o lo -j ACCEPT
ip6tables -P INPUT DROP
ip6tables -P OUTPUT DROP
```
