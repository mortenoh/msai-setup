# Multi-Technology Conflicts

## The Challenge

Running Docker, KVM, and LXC on the same host creates complex iptables interactions:

```
                    iptables/nftables
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    ┌───────┐        ┌───────┐        ┌───────┐
    │ UFW   │        │Docker │        │libvirt│
    └───┬───┘        └───┬───┘        └───┬───┘
        │                │                │
        ▼                ▼                ▼
    ufw-*            DOCKER-*         LIBVIRT_*
    chains           chains           chains
```

Each tool assumes it has control over iptables.

## Common Conflicts

### Conflict 1: Chain Ordering

All tools insert chains into FORWARD:

```bash
sudo iptables -L FORWARD -n --line-numbers
```

```
1  DOCKER-USER
2  DOCKER-ISOLATION-STAGE-1
3  ACCEPT (established)
4  DOCKER
5  LIBVIRT_FWX
6  LIBVIRT_FWI
7  LIBVIRT_FWO
8  ufw-before-forward    # UFW rules come LAST
9  ufw-user-forward
10 ufw-after-forward
```

**Problem:** Docker and libvirt rules process before UFW.

### Conflict 2: Rule Overwrites

When services restart, they may re-create rules:

```bash
# Docker restart
systemctl restart docker
# Recreates DOCKER chains, may change order

# libvirt restart
systemctl restart libvirtd
# Recreates LIBVIRT chains

# UFW reload
ufw reload
# Doesn't touch Docker/libvirt chains
```

### Conflict 3: Bridge Filtering

Both Docker and libvirt create bridges. When `bridge-nf-call-iptables=1`:

- All bridge traffic goes through FORWARD
- Multiple sets of rules evaluate the same packet
- Unexpected blocks or allows

### Conflict 4: NAT Table Conflicts

Multiple POSTROUTING rules:

```bash
sudo iptables -t nat -L POSTROUTING -n
```

```
MASQUERADE  all  --  172.17.0.0/16   !172.17.0.0/16     # Docker
MASQUERADE  all  --  192.168.122.0/24 !192.168.122.0/24 # libvirt
MASQUERADE  all  --  10.10.10.0/24   !10.10.10.0/24     # LXD
```

Usually works, but can cause issues with routing.

## Symptoms of Conflicts

### Symptom: Service Works, Then Stops

After restarting another service:

```bash
systemctl restart docker
# Now VMs can't reach internet
```

**Cause:** Docker restart changed chain order.

### Symptom: Random Packet Drops

Intermittent connectivity issues.

**Cause:** Multiple rules matching, order-dependent behavior.

### Symptom: UFW Rules Don't Apply

Added UFW rule, traffic still passes.

**Cause:** Traffic matched by Docker/libvirt before reaching UFW.

### Symptom: Everything Blocked

After UFW change, all container/VM traffic stops.

**Cause:** UFW reload changed forwarding policy.

## Debugging Conflicts

### View Complete Rule Set

```bash
# All iptables
iptables-save > /tmp/iptables-full.txt
less /tmp/iptables-full.txt

# Focus on FORWARD
iptables -L FORWARD -n -v --line-numbers

# Focus on NAT
iptables -t nat -L -n -v
```

### Identify Rule Owners

```bash
# Docker rules contain "docker" or bridge names
iptables-save | grep -i docker

# libvirt rules contain "LIBVIRT" or "virbr"
iptables-save | grep -i libvirt

# LXD rules reference lxd bridge
iptables-save | grep lxdbr
```

### Trace Specific Traffic

```bash
# Enable tracing
iptables -t raw -A PREROUTING -s 172.17.0.2 -j TRACE

# Watch kernel log
dmesg -w | grep TRACE
```

### Check Chain Hit Counts

```bash
# Zero counters
iptables -Z

# Generate traffic

# Check which chains matched
iptables -L -n -v | grep -E "pkts|DOCKER|LIBVIRT|ufw"
```

## Resolution Strategies

### Strategy 1: Service Startup Order

Ensure consistent order:

```bash
# /etc/systemd/system/iptables-order.service
[Unit]
Description=Ensure iptables chain order
After=docker.service libvirtd.service lxd.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/fix-iptables-order.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

### Strategy 2: Single Point of Control

Use one tool for all firewall rules:

```bash
# Disable individual firewalls
# Docker
echo '{"iptables": false}' > /etc/docker/daemon.json

# LXD
lxc network set lxdbr0 ipv4.firewall false

# libvirt (edit network XML)
# Remove <forward> or set mode='route'

# Manage all in UFW before.rules
```

### Strategy 3: Use DOCKER-USER for Everything

Since DOCKER-USER processes first:

```bash
# /usr/local/bin/unified-firewall.sh
#!/bin/bash

# Clear DOCKER-USER (except RETURN)
iptables -F DOCKER-USER

# Default deny external to all containers/VMs
iptables -A DOCKER-USER -i eth0 -j DROP

# Allow established
iptables -I DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN

# Allow internal networks
iptables -I DOCKER-USER -s 10.0.0.0/8 -j RETURN
iptables -I DOCKER-USER -s 172.16.0.0/12 -j RETURN
iptables -I DOCKER-USER -s 192.168.0.0/16 -j RETURN

# Whitelist specific services
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j RETURN
iptables -I DOCKER-USER -i eth0 -p tcp --dport 443 -j RETURN
```

### Strategy 4: Separate Interfaces

Use different physical/virtual interfaces:

```
eth0 - Host management (UFW)
eth1 - Docker containers
eth2 - VMs
```

Each can have independent rules.

## Recommended Architecture

### For Home Server

```
┌─────────────────────────────────────────────────────────────┐
│                         Host                                 │
│                                                              │
│  UFW manages:                                                │
│  - Host services (SSH, management)                          │
│  - Simple allow/deny for public services                    │
│                                                              │
│  DOCKER-USER manages:                                        │
│  - All container external access                            │
│  - Rate limiting, IP restrictions                           │
│                                                              │
│  before.rules manages:                                       │
│  - VM NAT and forwarding                                    │
│  - LXD NAT and forwarding                                   │
│  - Cross-network restrictions                               │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                     │
│  │ Docker  │  │  KVM    │  │  LXD    │                     │
│  │ bridge  │  │ bridge  │  │ bridge  │                     │
│  └─────────┘  └─────────┘  └─────────┘                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Implementation

1. **Disable per-tool firewalls:**

```bash
# Docker daemon.json - keep iptables for networking
# but use DOCKER-USER for rules

# LXD
lxc network set lxdbr0 ipv4.firewall false

# libvirt
# Keep default, but add UFW integration
```

2. **UFW for basics:**

```bash
ufw default deny incoming
ufw default allow outgoing
ufw allow ssh
ufw enable
```

3. **before.rules for forwarding:**

```bash
# NAT for all
*nat
-A POSTROUTING -s 172.17.0.0/16 -o eth0 -j MASQUERADE  # Docker
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE  # KVM
-A POSTROUTING -s 10.10.10.0/24 -o eth0 -j MASQUERADE  # LXD
COMMIT

# Forwarding
*filter
-A ufw-before-forward -i docker0 -j ACCEPT
-A ufw-before-forward -o docker0 -j ACCEPT
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT
-A ufw-before-forward -i lxdbr0 -j ACCEPT
-A ufw-before-forward -o lxdbr0 -j ACCEPT
COMMIT
```

4. **DOCKER-USER for container access control:**

```bash
# Systemd service to apply after Docker
/usr/local/bin/docker-firewall.sh
```

## Testing Integration

### Test Matrix

| Source | Destination | Should Work? |
|--------|-------------|--------------|
| External | Host SSH | Yes (UFW) |
| External | Docker web | Yes (allowed) |
| External | Docker DB | No (blocked) |
| External | VM SSH | Yes (forwarded) |
| Docker | Internet | Yes |
| Docker | VM | Depends on config |
| VM | Internet | Yes |
| VM | Docker | Depends on config |
| LXC | Internet | Yes |

### Automated Test Script

```bash
#!/bin/bash
# test-firewall.sh

echo "Testing firewall rules..."

# Test SSH
nc -zv localhost 22 && echo "SSH: OK" || echo "SSH: FAIL"

# Test Docker web
curl -s http://localhost:80 > /dev/null && echo "Docker web: OK" || echo "Docker web: FAIL"

# Test Docker DB (should fail)
nc -zv localhost 3306 2>/dev/null && echo "Docker DB: EXPOSED!" || echo "Docker DB: OK (blocked)"

# Test VM via port forward
nc -zv localhost 2222 && echo "VM SSH: OK" || echo "VM SSH: FAIL"
```
