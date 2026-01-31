# LXD UFW Integration

## The Same Problem as Docker

LXD with NAT networking has similar UFW bypass issues as Docker:

1. LXD manages its own iptables rules
2. NAT rules bypass UFW filter chains
3. Published ports may be accessible despite UFW

## How LXD Uses iptables

### NAT Rules

```bash
sudo iptables -t nat -L -n | grep -A5 10.10.10
```

```
Chain POSTROUTING (policy ACCEPT)
MASQUERADE  all  --  10.10.10.0/24  !10.10.10.0/24
```

### Filter Rules

```bash
sudo iptables -L -n | grep -A10 lxd
```

LXD creates rules for:
- Bridge forwarding
- DHCP/DNS access
- Inter-container communication

### LXD's Firewall Mode

```bash
# Check current setting
lxc network get lxdbr0 ipv4.firewall
```

When `ipv4.firewall=true`:
- LXD manages iptables for the network
- Rules auto-created for containers
- May conflict with UFW

## Solution: Disable LXD Firewall

Let UFW manage all rules:

```bash
lxc network set lxdbr0 ipv4.firewall false
lxc network set lxdbr0 ipv6.firewall false
```

Then configure UFW manually.

## UFW Configuration for LXD

### /etc/ufw/before.rules

```bash
# NAT table
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# LXD NAT
-A POSTROUTING -s 10.10.10.0/24 ! -d 10.10.10.0/24 -o eth0 -j MASQUERADE

COMMIT

# Filter table
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
:ufw-not-local - [0:0]

# ... standard rules ...

# LXD bridge forwarding
-A ufw-before-forward -i lxdbr0 -j ACCEPT
-A ufw-before-forward -o lxdbr0 -j ACCEPT

# ... rest of rules ...
COMMIT
```

### Apply

```bash
sudo ufw reload
```

## Proxy Devices with UFW

### The Recommended Approach

Use proxy devices with `bind=host`:

```bash
lxc config device add mycontainer web proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80 \
    bind=host
```

With `bind=host`:
- Proxy runs in host's network namespace
- UFW rules apply to incoming traffic
- You control access with standard UFW rules

### UFW Rules for Proxy

```bash
# Allow from anywhere
sudo ufw allow 8080/tcp

# Or restrict
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

## Direct Exposure (Without Proxy)

If container binds to host port (network_mode equivalent):

```yaml
# Container profile
config:
  security.privileged: "true"
devices:
  eth0:
    name: eth0
    nictype: p2p  # Or bridged
    type: nic
```

UFW rules apply normally in this case.

## Multiple Networks

### Internal Network (No External Access)

```bash
# Create internal network
lxc network create internal \
    ipv4.address=10.20.0.1/24 \
    ipv4.nat=false

# No NAT = containers can't reach internet
```

### Isolated Containers

```bash
# Network with no routing
lxc network create isolated \
    ipv4.address=10.30.0.1/24 \
    ipv4.nat=false \
    ipv4.routing=false
```

## Complete Example

### Network Setup

```bash
# Main network (NAT)
lxc network set lxdbr0 ipv4.firewall false

# Internal network
lxc network create backend \
    ipv4.address=10.20.0.1/24 \
    ipv4.nat=false \
    ipv4.firewall=false
```

### /etc/ufw/before.rules

```bash
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# NAT only for lxdbr0
-A POSTROUTING -s 10.10.10.0/24 ! -d 10.10.10.0/24 -o eth0 -j MASQUERADE

COMMIT

*filter
# ... standard rules ...

# lxdbr0 forwarding
-A ufw-before-forward -i lxdbr0 -j ACCEPT
-A ufw-before-forward -o lxdbr0 -j ACCEPT

# backend (internal) - only between containers
-A ufw-before-forward -i backend -o backend -j ACCEPT
-A ufw-before-forward -i backend -j DROP  # No external access

COMMIT
```

### Container Configuration

```bash
# Web server (public facing)
lxc launch ubuntu:22.04 webserver
lxc network attach lxdbr0 webserver eth0
lxc config device add webserver http proxy \
    listen=tcp:0.0.0.0:80 connect=tcp:127.0.0.1:80 bind=host

# Database (internal only)
lxc launch ubuntu:22.04 database
lxc network attach backend database eth0
# No proxy = not accessible from outside
```

### UFW Rules

```bash
sudo ufw allow 80/tcp    # Web server
sudo ufw allow 443/tcp   # HTTPS
# Database not exposed
```

## Troubleshooting

### Container Can't Reach Internet

```bash
# Check NAT
lxc network get lxdbr0 ipv4.nat

# Check iptables
sudo iptables -t nat -L POSTROUTING -n

# Check forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check UFW forward rules
sudo iptables -L ufw-before-forward -n
```

### Proxy Not Working

```bash
# Check proxy device
lxc config device show mycontainer | grep proxy

# Check listening
sudo ss -tlnp | grep 8080

# Check UFW
sudo ufw status | grep 8080
```

### UFW Blocks Container Traffic

```bash
# Check FORWARD chain
sudo iptables -L FORWARD -n -v

# Ensure LXD bridge rules in before.rules
grep lxdbr0 /etc/ufw/before.rules
```
