# nftables Introduction

## What is nftables?

nftables is the modern replacement for iptables, ip6tables, arptables, and ebtables. It provides:

- Unified framework for all protocols
- Better performance through atomic rule updates
- Simpler syntax
- Native sets and maps
- No kernel module dependencies for protocol matches

## Current State

As of Ubuntu 22.04/24.04:

- nftables is the default backend
- iptables commands use `iptables-nft` (translation layer)
- UFW uses nftables backend
- Docker still uses iptables compatibility layer
- libvirt uses iptables compatibility layer

```bash
# Check which iptables is in use
update-alternatives --query iptables
```

## Why Understand nftables?

Even if you use iptables commands, understanding nftables helps because:

1. Rules are actually stored in nftables format
2. Direct nftables rules can conflict with iptables-nft
3. Future tools will use nftables natively
4. Better debugging with nft commands

## Basic Concepts

### Address Families

| Family | Description |
|--------|-------------|
| ip | IPv4 |
| ip6 | IPv6 |
| inet | IPv4 and IPv6 |
| arp | ARP |
| bridge | Bridge filtering |
| netdev | Early packet processing |

### Tables

Tables are containers for chains:

```bash
# Create table
nft add table inet myfilter

# List tables
nft list tables

# Delete table
nft delete table inet myfilter
```

### Chains

Chains contain rules:

```bash
# Create base chain (attached to hook)
nft add chain inet myfilter input { type filter hook input priority 0 \; }

# Create regular chain (for jumping)
nft add chain inet myfilter ssh_check

# Delete chain
nft delete chain inet myfilter ssh_check
```

### Rules

```bash
# Add rule
nft add rule inet myfilter input tcp dport 22 accept

# Insert rule (at beginning)
nft insert rule inet myfilter input tcp dport 80 accept

# Add rule at position
nft add rule inet myfilter input position 3 tcp dport 443 accept

# Delete rule by handle
nft delete rule inet myfilter input handle 5
```

## Syntax Comparison

### iptables vs nftables

```bash
# iptables
iptables -A INPUT -p tcp --dport 22 -j ACCEPT
iptables -A INPUT -s 192.168.1.0/24 -j ACCEPT
iptables -A INPUT -m conntrack --ctstate ESTABLISHED -j ACCEPT

# nftables
nft add rule inet filter input tcp dport 22 accept
nft add rule inet filter input ip saddr 192.168.1.0/24 accept
nft add rule inet filter input ct state established accept
```

### Key Differences

| iptables | nftables |
|----------|----------|
| -p tcp | tcp |
| --dport 22 | dport 22 |
| -s 192.168.1.0/24 | ip saddr 192.168.1.0/24 |
| -j ACCEPT | accept |
| -m conntrack --ctstate | ct state |
| -A INPUT | add rule ... input |

## Complete Configuration

### File-Based Configuration

```bash
#!/usr/sbin/nft -f

# Clear existing rules
flush ruleset

# Main filter table
table inet filter {
    chain input {
        type filter hook input priority 0; policy drop;

        # Allow established/related
        ct state established,related accept

        # Drop invalid
        ct state invalid drop

        # Allow loopback
        iif lo accept

        # Allow ICMP
        ip protocol icmp accept
        ip6 nexthdr icmpv6 accept

        # Allow SSH
        tcp dport 22 accept

        # Allow HTTP/HTTPS
        tcp dport { 80, 443 } accept

        # Log and drop everything else
        log prefix "nft-drop: " counter drop
    }

    chain forward {
        type filter hook forward priority 0; policy drop;

        # Allow established
        ct state established,related accept

        # VM network forwarding
        iifname "virbr0" accept
        oifname "virbr0" ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}

# NAT table
table ip nat {
    chain prerouting {
        type nat hook prerouting priority -100;
    }

    chain postrouting {
        type nat hook postrouting priority 100;

        # Masquerade for VM network
        ip saddr 192.168.122.0/24 oifname "eth0" masquerade
    }
}
```

### Apply Configuration

```bash
# Apply rules
nft -f /etc/nftables.conf

# Enable on boot
systemctl enable nftables
```

## Sets and Maps

### Anonymous Sets

```bash
# Match multiple values
nft add rule inet filter input tcp dport { 22, 80, 443 } accept
nft add rule inet filter input ip saddr { 192.168.1.0/24, 10.0.0.0/8 } accept
```

### Named Sets

```bash
# Create set
nft add set inet filter allowed_ips { type ipv4_addr \; }

# Add elements
nft add element inet filter allowed_ips { 192.168.1.100 }
nft add element inet filter allowed_ips { 192.168.1.101, 192.168.1.102 }

# Use in rule
nft add rule inet filter input ip saddr @allowed_ips accept

# Delete element
nft delete element inet filter allowed_ips { 192.168.1.100 }
```

### Dynamic Sets

```bash
# Auto-populated set (like ipset)
nft add set inet filter blocklist { type ipv4_addr \; timeout 1h \; }

# Add entries dynamically
nft add element inet filter blocklist { 10.0.0.1 }

# Rule can auto-add
nft add rule inet filter input tcp dport 22 \
    meter ssh-limit { ip saddr limit rate over 10/minute } \
    add @blocklist { ip saddr timeout 1h } drop
```

### Maps

```bash
# Create map
nft add map inet filter port_redirect { type inet_service : inet_service \; }

# Add mappings
nft add element inet filter port_redirect { 80 : 8080, 443 : 8443 }

# Use in rule
nft add rule inet nat prerouting dnat to tcp dport map @port_redirect
```

## Viewing Rules

```bash
# List all rules
nft list ruleset

# List specific table
nft list table inet filter

# List specific chain
nft list chain inet filter input

# With handles (for deletion)
nft -a list ruleset

# As commands (for scripting)
nft list ruleset -s
```

## Interaction with iptables-nft

When you run iptables on a modern system, it uses iptables-nft:

```bash
# This iptables command
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Creates nftables rules in a compatibility table
nft list table ip filter
```

### Viewing Translated Rules

```bash
# See what iptables-nft created
nft list ruleset

# You'll see tables named:
# - table ip filter
# - table ip nat
# - table ip mangle
```

### Potential Conflicts

!!! warning
    Don't mix direct nftables rules with iptables-nft rules in the same tables.

Best practices:

1. Use only iptables commands, or
2. Use only nft commands, or
3. Put custom nft rules in separate tables

## nftables for Container Networking

### Docker Bridge Rules

Docker creates rules like:

```
table ip filter {
    chain DOCKER {
        iifname "docker0" counter packets 0 bytes 0 return
        iifname != "docker0" meta l4proto tcp ip daddr 172.17.0.2 tcp dport 80 counter accept
    }
    chain DOCKER-ISOLATION-STAGE-1 {
        iifname "docker0" oifname != "docker0" counter jump DOCKER-ISOLATION-STAGE-2
        counter return
    }
}
```

### Adding Custom Rules

```bash
# Create your own table to avoid conflicts
nft add table inet custom

nft add chain inet custom input { type filter hook input priority -100 \; }

# This runs before Docker's rules due to lower priority
nft add rule inet custom input tcp dport 8080 drop
```

## Practical Examples

### Rate Limiting

```bash
nft add rule inet filter input tcp dport 22 \
    ct state new \
    limit rate 10/minute \
    accept
```

### Port Knocking

```bash
table inet portknock {
    set clients_ipv4 {
        type ipv4_addr
        timeout 10s
    }

    chain input {
        type filter hook input priority -10;

        tcp dport 1234 add @clients_ipv4 { ip saddr }
        tcp dport 22 ip saddr @clients_ipv4 accept
    }
}
```

### Geo-blocking (with sets)

```bash
# Create set for blocked countries
nft add set inet filter blocked_countries { type ipv4_addr \; flags interval \; }

# Add IP ranges (from geo IP database)
nft add element inet filter blocked_countries { 1.0.0.0/8 }

# Use in rule
nft add rule inet filter input ip saddr @blocked_countries drop
```

## Migration from iptables

### Export iptables Rules

```bash
# Save iptables rules
iptables-save > iptables-rules.txt

# Convert to nftables (basic translation)
iptables-restore-translate -f iptables-rules.txt > nftables-rules.nft
```

### Gradual Migration

1. Start with nftables daemon
2. Keep using iptables commands (via iptables-nft)
3. Gradually add native nftables rules
4. Eventually remove iptables-nft dependency

## Debugging

```bash
# Trace packets
nft add rule inet filter input meta nftrace set 1

# Monitor trace
nft monitor trace

# Count packets
nft add rule inet filter input counter

# View counters
nft list chain inet filter input

# Reset counters
nft reset counters
```

## Performance Tips

### Use Sets

```bash
# Instead of multiple rules
nft add rule inet filter input ip saddr 192.168.1.1 drop
nft add rule inet filter input ip saddr 192.168.1.2 drop
nft add rule inet filter input ip saddr 192.168.1.3 drop

# Use a set
nft add set inet filter blocklist { type ipv4_addr \; }
nft add element inet filter blocklist { 192.168.1.1, 192.168.1.2, 192.168.1.3 }
nft add rule inet filter input ip saddr @blocklist drop
```

### Atomic Updates

```bash
# Load entire ruleset atomically
nft -f /etc/nftables.conf

# Better than individual commands
```

### Early Filtering

```bash
# Use netdev family for early drops
table netdev filter {
    chain ingress {
        type filter hook ingress device eth0 priority -500;

        # Drop before full stack processing
        ip saddr 10.0.0.0/8 drop
    }
}
```
