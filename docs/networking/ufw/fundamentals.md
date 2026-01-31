# UFW Fundamentals

## What is UFW?

UFW (Uncomplicated Firewall) is a user-friendly frontend for managing netfilter firewall rules. It's designed to make firewall configuration accessible without requiring deep iptables knowledge.

## How UFW Works

```
┌────────────────────────────────────────────────────────────┐
│                     User Commands                           │
│         ufw allow 22, ufw deny from 10.0.0.0/8             │
├────────────────────────────────────────────────────────────┤
│                         UFW                                 │
│    Translates commands → iptables/nftables rules           │
├────────────────────────────────────────────────────────────┤
│                    iptables-nft                             │
│    (iptables compatibility layer using nftables)           │
├────────────────────────────────────────────────────────────┤
│                      nftables                               │
│              (netfilter configuration)                      │
├────────────────────────────────────────────────────────────┤
│                      netfilter                              │
│                (kernel packet filtering)                    │
└────────────────────────────────────────────────────────────┘
```

### UFW Components

| Component | Location | Purpose |
|-----------|----------|---------|
| ufw | /usr/sbin/ufw | Command-line tool |
| ufw.conf | /etc/ufw/ufw.conf | Main configuration |
| before.rules | /etc/ufw/before.rules | Rules processed first |
| after.rules | /etc/ufw/after.rules | Rules processed last |
| user.rules | /etc/ufw/user.rules | Your custom rules |
| applications.d/ | /etc/ufw/applications.d/ | Application profiles |

## UFW Chain Architecture

UFW creates its own chains within iptables:

```
                    Built-in Chain
                    ┌─────────────────────────────────────────┐
                    │                 INPUT                    │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │          ufw-before-logging-input        │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │            ufw-before-input              │
                    │    (from /etc/ufw/before.rules)         │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │             ufw-user-input               │
                    │        (your ufw allow/deny rules)       │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │            ufw-after-input               │
                    │     (from /etc/ufw/after.rules)         │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │          ufw-after-logging-input         │
                    └────────────────────┬────────────────────┘
                                         │
                    ┌────────────────────▼────────────────────┐
                    │           ufw-reject-input               │
                    │    (applies default policy: DROP)        │
                    └─────────────────────────────────────────┘
```

The same pattern exists for FORWARD and OUTPUT chains.

## Rule Processing Order

1. **before.rules** - System rules (ICMP, DHCP, multicast)
2. **user rules** - Your `ufw allow/deny` commands
3. **after.rules** - Cleanup and logging
4. **Default policy** - DROP or REJECT remaining

### Why Order Matters

```bash
# Rule in before.rules ALWAYS runs first
# Even if you add a deny rule, before.rules can accept

# Example: before.rules accepts established connections
# Your "deny from badip" won't block established sessions
```

## Installation and Status

```bash
# UFW is pre-installed on Ubuntu
# Verify installation
which ufw

# Check status
sudo ufw status
# Status: inactive

# Enable UFW
sudo ufw enable

# Disable UFW
sudo ufw disable

# Check verbose status
sudo ufw status verbose
```

## Default Policies

```bash
# View current defaults
sudo ufw status verbose
# Default: deny (incoming), allow (outgoing), disabled (routed)

# Set defaults
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw default deny routed  # For forwarded traffic
```

### Policy Options

| Policy | Effect |
|--------|--------|
| allow | Accept all traffic |
| deny | Silently drop traffic |
| reject | Drop with ICMP unreachable |

## What UFW Does and Doesn't Protect

### UFW Protects

- Direct incoming connections to the host
- Host-generated outgoing connections (if policy set)
- Traffic explicitly routed through the host (with forward rules)

### UFW Does NOT Protect (by default)

- Docker container published ports
- KVM VM NAT traffic
- LXC container NAT traffic
- Bridged VM/container traffic

This is the critical issue we'll address in later sections.

## UFW vs Raw iptables

### Advantages of UFW

| Feature | UFW | iptables |
|---------|-----|----------|
| Syntax | Simple | Complex |
| Persistence | Automatic | Requires scripts |
| Profiles | Built-in | Manual |
| Integration | systemd service | None |
| Learning curve | Gentle | Steep |

### When to Use Raw iptables

- Complex NAT scenarios
- Custom chain logic
- Performance-critical rules
- Integration with Docker/libvirt

### Mixing UFW and iptables

!!! warning
    Don't add rules directly to iptables when using UFW unless you know what you're doing.

If you need custom iptables rules:

1. Put them in `/etc/ufw/before.rules` or `/etc/ufw/after.rules`
2. Use `ufw reload` to apply
3. Never modify UFW's generated chains directly

## The before.rules File

Located at `/etc/ufw/before.rules`, this file contains:

- NAT table rules
- Filter rules that run before user rules
- System essentials (loopback, established connections, ICMP)

### Structure

```bash
# NAT rules (for routing/forwarding)
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
# NAT rules here
COMMIT

# Filter rules
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
# Filter rules here
COMMIT
```

### Default Contents (Critical Rules)

```bash
# Allow loopback
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-output -o lo -j ACCEPT

# Allow established connections (CRITICAL)
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-output -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Drop invalid
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP

# Allow ICMP
-A ufw-before-input -p icmp --icmp-type echo-request -j ACCEPT
```

## The after.rules File

Located at `/etc/ufw/after.rules`:

- Runs after user rules
- Usually contains logging
- Good place for "catch-all" rules

## Application Profiles

UFW includes profiles for common applications:

```bash
# List available profiles
sudo ufw app list

# View profile details
sudo ufw app info OpenSSH

# Use profile
sudo ufw allow OpenSSH

# Use profile with specificity
sudo ufw allow from 192.168.1.0/24 to any app OpenSSH
```

### Creating Custom Profiles

```ini
# /etc/ufw/applications.d/myapp
[MyApp]
title=My Application
description=My custom application
ports=8080/tcp|8443/tcp
```

```bash
# Reload profiles
sudo ufw app update MyApp

# Use profile
sudo ufw allow MyApp
```

## IPv6 Support

UFW handles IPv6 automatically:

```bash
# Check if IPv6 is enabled
grep IPV6 /etc/default/ufw
# IPV6=yes

# Rules apply to both v4 and v6
sudo ufw allow 22  # Allows both IPv4 and IPv6

# IPv6-specific rule
sudo ufw allow from 2001:db8::/32
```

### Disable IPv6

```bash
# /etc/default/ufw
IPV6=no

# Reload
sudo ufw reload
```

## Reset UFW

```bash
# Complete reset (removes all rules)
sudo ufw reset

# This deletes:
# - All user rules
# - Custom before/after.rules
# - Resets to defaults
```

## Relationship with Systemd

UFW is a systemd service:

```bash
# Check service status
systemctl status ufw

# UFW starts at boot when enabled
sudo ufw enable

# The service loads rules from /etc/ufw/
```

### Boot Order

```
network.target
    └── ufw.service (loads firewall rules)
            └── docker.service (may add its own rules)
            └── libvirtd.service (may add its own rules)
```

!!! warning "Race Condition"
    Docker and libvirt may add rules that conflict with or bypass UFW.

## UFW Limitations

1. **No direct nftables support** - Uses iptables-nft translation
2. **Limited NAT support** - Complex NAT needs before.rules
3. **No connection tracking tuning** - Can't adjust timeouts
4. **Docker bypass** - Doesn't protect Docker by default
5. **No support for ipset** - Large blocklists are inefficient
