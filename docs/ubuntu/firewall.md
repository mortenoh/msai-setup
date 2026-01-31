# Firewall

!!! info "Comprehensive Guide Available"
    This page provides a quick start for UFW. For in-depth coverage of firewall configuration, Docker/KVM/LXC integration, and troubleshooting, see the [Networking & Firewall](../networking/index.md) section.

## Why Firewalls Matter

A firewall is your first line of defense against unauthorized network access. Even on a home network behind a router, a host-level firewall is essential:

- **Defense in depth** - Router firewalls can be misconfigured or bypassed
- **Lateral movement protection** - Limits damage if another device on your network is compromised
- **Service isolation** - Prevents accidental exposure of development/test services
- **Audit trail** - Logs connection attempts for security analysis

Without a firewall, every listening service is potentially accessible to anyone who can reach your network.

## Linux Firewall Architecture

Understanding the layers is critical before configuring anything:

```
┌─────────────────────────────────────────────────────────────┐
│                      User Space                              │
├─────────────────────────────────────────────────────────────┤
│  UFW          │  Docker        │  libvirt      │  LXC       │
│  (frontend)   │  (iptables)    │  (iptables)   │  (varies)  │
├─────────────────────────────────────────────────────────────┤
│                    iptables / nftables                       │
│                    (netfilter frontend)                      │
├─────────────────────────────────────────────────────────────┤
│                       netfilter                              │
│                    (kernel module)                           │
└─────────────────────────────────────────────────────────────┘
```

### The Problem

**Multiple tools manipulate the same underlying system (netfilter) without coordinating with each other.**

- UFW adds rules to manage host traffic
- Docker adds rules for container networking
- libvirt adds rules for VM networking
- LXC may add rules depending on configuration

These rules can conflict, override each other, or create security holes.

## UFW Fundamentals

### What UFW Actually Does

UFW (Uncomplicated Firewall) is a frontend for iptables/nftables. It:

1. Manages chains in the `filter` table
2. Provides a simple syntax for common operations
3. Persists rules across reboots
4. Integrates with systemd

### Default Chains

UFW creates its own chains within iptables:

```
ufw-before-input
ufw-user-input
ufw-after-input
ufw-before-forward
ufw-user-forward
ufw-after-forward
ufw-before-output
ufw-user-output
ufw-after-output
```

Your rules go in `ufw-user-*` chains. The `before` and `after` chains handle special cases.

### Basic Setup

```bash
# Check current status
sudo ufw status verbose

# Set default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (critical - do this before enabling!)
sudo ufw allow ssh

# Enable firewall
sudo ufw enable
```

### Rule Syntax

```bash
# Allow by service name
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Allow by port
sudo ufw allow 8080/tcp
sudo ufw allow 53/udp

# Allow port ranges
sudo ufw allow 6000:6100/tcp

# Allow from specific IP
sudo ufw allow from 192.168.1.100

# Allow from subnet to specific port
sudo ufw allow from 192.168.1.0/24 to any port 22

# Allow to specific interface
sudo ufw allow in on eth0 to any port 80

# Deny specific traffic
sudo ufw deny from 10.0.0.0/8

# Delete rules
sudo ufw delete allow 8080/tcp
sudo ufw delete 5  # by rule number

# Show numbered rules
sudo ufw status numbered
```

### Logging

```bash
# Enable logging
sudo ufw logging on

# Set log level (off, low, medium, high, full)
sudo ufw logging medium

# View logs
sudo journalctl -f | grep UFW
# or
sudo tail -f /var/log/ufw.log
```

---

## Docker and UFW: The Fundamental Conflict

!!! danger "Critical Issue"
    By default, Docker completely bypasses UFW. Published container ports are accessible from anywhere, regardless of your UFW rules.

### Why This Happens

Docker manipulates iptables directly to enable container networking:

1. Creates the `DOCKER` chain
2. Inserts rules into the `FORWARD` chain
3. Adds NAT rules for port publishing
4. These rules are processed **before** UFW rules

Example: You run `docker run -p 8080:80 nginx`

- Docker adds a DNAT rule to forward port 8080 to the container
- This rule is in the `nat` table's `PREROUTING` chain
- Traffic is redirected before it ever reaches UFW's `filter` rules
- **Your UFW rules are never evaluated for this traffic**

### Demonstrating the Problem

```bash
# UFW is enabled with default deny
sudo ufw status
# Status: active
# Default: deny (incoming)

# Run a container with published port
docker run -d -p 8080:80 nginx

# From another machine, this WORKS despite UFW:
curl http://your-server:8080
# Returns nginx welcome page

# UFW shows no rules for 8080
sudo ufw status | grep 8080
# (nothing)
```

### Solution 1: Disable Docker's iptables Management

Edit `/etc/docker/daemon.json`:

```json
{
  "iptables": false
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

**Consequences:**

- Container-to-container networking breaks
- Container-to-internet networking breaks
- You must manually configure all networking

**Manual NAT setup required:**

```bash
# Enable IP forwarding
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# Add NAT for container network
sudo iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

# Allow forwarding for Docker
sudo iptables -A FORWARD -i docker0 -o eth0 -j ACCEPT
sudo iptables -A FORWARD -i eth0 -o docker0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

This approach is complex and error-prone. Not recommended unless you have specific requirements.

### Solution 2: Use ufw-docker (Recommended)

The `ufw-docker` utility modifies UFW to work correctly with Docker.

**Install:**

```bash
sudo wget -O /usr/local/bin/ufw-docker \
  https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
```

**Initialize:**

```bash
sudo ufw-docker install
sudo systemctl restart ufw
```

This modifies `/etc/ufw/after.rules` to handle Docker traffic properly.

**Usage:**

```bash
# Allow access to container port from anywhere
sudo ufw-docker allow nginx 80

# Allow from specific network
sudo ufw-docker allow nginx 80 192.168.1.0/24

# List container rules
sudo ufw-docker status

# Delete rule
sudo ufw-docker delete allow nginx 80
```

### Solution 3: Bind to localhost Only

If a service only needs to be accessed locally or through a reverse proxy:

```yaml
# docker-compose.yml
services:
  app:
    ports:
      - "127.0.0.1:8080:80"  # Only accessible from localhost
```

Then use a reverse proxy (nginx, Caddy, Traefik) on the host to expose it with proper access control.

### Solution 4: Use Host Network Mode Selectively

For services that need full network access:

```yaml
services:
  plex:
    network_mode: host
```

Now the service uses the host's network stack directly, and UFW rules apply normally. However:

- Port conflicts with host services possible
- Less isolation
- Container sees all host network interfaces

### Solution 5: Docker Networks Without Publishing

For internal-only services:

```yaml
# No ports published - only accessible from other containers
services:
  database:
    image: postgres
    # No 'ports:' section
    networks:
      - internal

  app:
    image: myapp
    networks:
      - internal
      - external
    ports:
      - "127.0.0.1:8080:80"

networks:
  internal:
    internal: true  # No external access
  external:
```

### Docker and UFW: Summary

| Approach | Complexity | Security | Recommended For |
|----------|------------|----------|-----------------|
| Do nothing | Low | Poor | Never in production |
| `iptables: false` | High | Good | Advanced users only |
| ufw-docker | Medium | Good | Most users |
| Bind to localhost | Low | Good | Services behind reverse proxy |
| Host network | Low | Medium | Services needing full network |
| Internal networks | Medium | Excellent | Multi-container apps |

---

## KVM/libvirt and UFW

### How libvirt Manages Networking

libvirt creates virtual networks for VMs, typically using NAT. It manages this through:

1. **dnsmasq** - DHCP and DNS for VMs
2. **iptables rules** - NAT and forwarding
3. **bridge interfaces** - virbr0, etc.

### Default NAT Network

When you install libvirt, it creates a default network:

```bash
virsh net-list
# Name      State    Autostart   Persistent
# default   active   yes         yes

virsh net-dumpxml default
```

```xml
<network>
  <name>default</name>
  <forward mode='nat'/>
  <bridge name='virbr0'/>
  <ip address='192.168.122.1' netmask='255.255.255.0'>
    <dhcp>
      <range start='192.168.122.2' end='192.168.122.254'/>
    </dhcp>
  </ip>
</network>
```

### libvirt's iptables Rules

libvirt adds rules to multiple tables:

```bash
# View libvirt's NAT rules
sudo iptables -t nat -L -n | grep -A5 LIBVIRT

# View libvirt's filter rules
sudo iptables -L -n | grep -A5 LIBVIRT
```

Typical rules include:

- MASQUERADE for outbound VM traffic
- ACCEPT for traffic on virbr0
- REJECT for forwarded traffic not matching VM networks

### The Conflict

UFW's default configuration blocks forwarded traffic:

```bash
# /etc/default/ufw
DEFAULT_FORWARD_POLICY="DROP"
```

This can break VM networking because:

1. VM sends packet to external network
2. Packet hits the FORWARD chain
3. UFW's default DROP policy blocks it
4. VM has no network connectivity

### Solution: Allow Forwarding for VM Networks

**Option 1: Change default forward policy**

Edit `/etc/default/ufw`:

```bash
DEFAULT_FORWARD_POLICY="ACCEPT"
```

Then reload:

```bash
sudo ufw reload
```

!!! warning
    This allows all forwarded traffic. Use with caution.

**Option 2: Specific rules for VM network (Recommended)**

Add to `/etc/ufw/before.rules` (before the `*filter` line):

```bash
# NAT table rules for libvirt
*nat
:POSTROUTING ACCEPT [0:0]
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE
COMMIT
```

Add to the `*filter` section:

```bash
# Allow VM network forwarding
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -m state --state RELATED,ESTABLISHED -j ACCEPT
```

Reload UFW:

```bash
sudo ufw reload
```

### Bridged Networking

For VMs that need to be on the same network as the host:

**1. Create bridge in Netplan:**

```yaml
# /etc/netplan/00-installer-config.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: no
  bridges:
    br0:
      interfaces: [enp5s0]
      dhcp4: true
      parameters:
        stp: false
        forward-delay: 0
```

Apply:

```bash
sudo netplan apply
```

**2. Create libvirt network using the bridge:**

```xml
<!-- bridged-network.xml -->
<network>
  <name>bridged</name>
  <forward mode="bridge"/>
  <bridge name="br0"/>
</network>
```

```bash
virsh net-define bridged-network.xml
virsh net-start bridged
virsh net-autostart bridged
```

**3. UFW considerations for bridged mode:**

With bridged networking, VMs appear as separate hosts on your network. UFW on the host doesn't filter their traffic (it bypasses the host's IP stack).

The VM needs its own firewall, or use iptables `FORWARD` chain rules:

```bash
# In /etc/ufw/before.rules, filter section
# Block VM from accessing host-only services
-A ufw-before-forward -i br0 -d 192.168.1.100 -p tcp --dport 22 -j DROP
```

### Exposing VM Services

**NAT mode - Port forwarding:**

```bash
# Forward host port 2222 to VM's SSH
sudo iptables -t nat -A PREROUTING -p tcp --dport 2222 -j DNAT --to-destination 192.168.122.10:22
sudo iptables -A FORWARD -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT

# Make persistent in /etc/ufw/before.rules
```

**Or use UFW:**

```bash
# /etc/ufw/before.rules (in *nat section)
-A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to-destination 192.168.122.10:22

# (in *filter section)
-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT
```

---

## LXC/LXD and UFW

### LXC Networking Modes

LXC containers can use several networking modes:

| Mode | Description | UFW Interaction |
|------|-------------|-----------------|
| NAT (lxdbr0) | Default, similar to Docker | Bypasses UFW like Docker |
| Bridged | Container on host network | Bypasses host UFW |
| macvlan | Direct network access | Bypasses host UFW |
| none | No networking | N/A |

### Default LXD Bridge (lxdbr0)

LXD creates a NAT bridge similar to libvirt:

```bash
lxc network show lxdbr0
```

```yaml
config:
  ipv4.address: 10.10.10.1/24
  ipv4.nat: "true"
  ipv6.address: fd42:474b:622d:259d::1/64
  ipv6.nat: "true"
```

### The Same Problems as Docker

LXD with NAT mode has the same UFW bypass issues:

1. Container binds to port 80
2. LXD adds iptables rules for NAT
3. External traffic reaches container without UFW evaluation

### LXD Proxy Devices

LXD's recommended way to expose container ports:

```bash
# Add proxy device to container
lxc config device add mycontainer myproxy proxy \
  listen=tcp:0.0.0.0:8080 \
  connect=tcp:127.0.0.1:80

# Bind to specific interface
lxc config device add mycontainer myproxy proxy \
  listen=tcp:192.168.1.100:8080 \
  connect=tcp:127.0.0.1:80 \
  bind=host
```

With `bind=host`, the proxy runs on the host's network stack, so UFW rules apply:

```bash
sudo ufw allow 8080/tcp
```

### Solution: Firewall Rules in LXD

LXD can manage its own firewall rules:

```bash
# View current rules
lxc network show lxdbr0

# Add firewall rules to network
lxc network set lxdbr0 ipv4.firewall=true
lxc network set lxdbr0 ipv6.firewall=true
```

### Bridge Mode for LXC

Attach container directly to host bridge:

```bash
# Create profile for bridged networking
lxc profile create bridged
lxc profile device add bridged eth0 nic \
  nictype=bridged \
  parent=br0

# Launch container with profile
lxc launch ubuntu:22.04 mycontainer -p bridged
```

Container gets IP from your network's DHCP. Host UFW doesn't filter its traffic.

### LXC Security Best Practices

1. **Use proxy devices with `bind=host`** for services that need external access
2. **Run firewall inside containers** for bridged/macvlan mode
3. **Use LXD's built-in firewall** for network-level rules
4. **Avoid exposing containers directly** - use a reverse proxy on the host

---

## Comprehensive UFW Configuration

### Complete `/etc/ufw/before.rules`

This configuration handles Docker, libvirt, and LXD:

```bash
#
# /etc/ufw/before.rules
#

# NAT table rules
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# Docker NAT (if using iptables: false)
# -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

# libvirt NAT
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE

# LXD NAT (if not using LXD's built-in)
# -A POSTROUTING -s 10.10.10.0/24 -o eth0 -j MASQUERADE

# Port forwarding examples
# -A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to 192.168.122.10:22

COMMIT

# Filter table rules
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
:ufw-not-local - [0:0]

# Accept all on loopback
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-output -o lo -j ACCEPT

# Quickly process established connections
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-output -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Drop invalid packets
-A ufw-before-input -m conntrack --ctstate INVALID -j ufw-logging-deny
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP

# Accept ICMP (ping)
-A ufw-before-input -p icmp --icmp-type echo-request -j ACCEPT

# libvirt bridge forwarding
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# LXD bridge forwarding (if needed)
# -A ufw-before-forward -i lxdbr0 -j ACCEPT
# -A ufw-before-forward -o lxdbr0 -j ACCEPT

# Docker bridge forwarding (if using iptables: false)
# -A ufw-before-forward -i docker0 -j ACCEPT
# -A ufw-before-forward -o docker0 -j ACCEPT

# Allow DHCP client
-A ufw-before-input -p udp --sport 67 --dport 68 -j ACCEPT

# ufw-not-local chain
-A ufw-before-input -j ufw-not-local
-A ufw-not-local -m addrtype --dst-type LOCAL -j RETURN
-A ufw-not-local -m addrtype --dst-type MULTICAST -j RETURN
-A ufw-not-local -m addrtype --dst-type BROADCAST -j RETURN
-A ufw-not-local -m limit --limit 3/min --limit-burst 10 -j ufw-logging-deny
-A ufw-not-local -j DROP

# Allow mDNS (optional, for local network discovery)
-A ufw-before-input -p udp --dport 5353 -d 224.0.0.251 -j ACCEPT

# Allow UPnP (optional, for DLNA/media servers)
-A ufw-before-input -p udp --dport 1900 -d 239.255.255.250 -j ACCEPT

COMMIT
```

### `/etc/ufw/after.rules` for ufw-docker

If using ufw-docker, it adds to this file. Don't edit manually.

### Testing Your Configuration

```bash
# Reload UFW
sudo ufw reload

# Check iptables rules
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v

# Test from another machine
nmap -p 1-1000 your-server-ip

# Test specific services
nc -zv your-server-ip 22
nc -zv your-server-ip 8080

# Check what's listening
sudo ss -tlnp
```

---

## Debugging Firewall Issues

### Traffic Not Reaching Service

```bash
# 1. Check if service is listening
sudo ss -tlnp | grep :8080

# 2. Check UFW status
sudo ufw status verbose

# 3. Check raw iptables
sudo iptables -L -n -v --line-numbers
sudo iptables -t nat -L -n -v

# 4. Watch for blocked packets
sudo journalctl -f | grep UFW

# 5. Trace packet path
sudo iptables -t raw -A PREROUTING -p tcp --dport 8080 -j TRACE
sudo dmesg -w
```

### VM Has No Network

```bash
# 1. Check VM can reach gateway
# (from inside VM)
ping 192.168.122.1

# 2. Check IP forwarding on host
cat /proc/sys/net/ipv4/ip_forward
# Should be 1

# 3. Check libvirt network is active
virsh net-list

# 4. Check virbr0 interface
ip addr show virbr0

# 5. Check forwarding rules
sudo iptables -L FORWARD -n -v
```

### Container Published Port Not Accessible

```bash
# 1. Verify container is running
docker ps

# 2. Check Docker's iptables rules
sudo iptables -t nat -L DOCKER -n
sudo iptables -L DOCKER -n

# 3. Test from localhost
curl localhost:8080

# 4. Test from container network
docker exec -it container curl localhost:80

# 5. Check if bound to 127.0.0.1
docker port container
```

### Rule Order Issues

```bash
# List rules with numbers
sudo iptables -L -n --line-numbers

# UFW rules are in ufw-user-* chains
sudo iptables -L ufw-user-input -n --line-numbers

# Check rule hit counts
sudo iptables -L -n -v
# The 'pkts' column shows how many packets matched
```

---

## Security Recommendations

### Minimal Exposure

```bash
# Default deny everything
sudo ufw default deny incoming
sudo ufw default deny outgoing  # Optional, breaks most things
sudo ufw default deny routed    # For forwarded traffic

# Only allow what's needed
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 8080
```

### Rate Limiting

```bash
# Limit SSH connections (6 per 30 seconds)
sudo ufw limit ssh

# Custom rate limit in before.rules
-A ufw-before-input -p tcp --dport 22 -m state --state NEW -m recent --set
-A ufw-before-input -p tcp --dport 22 -m state --state NEW -m recent --update --seconds 30 --hitcount 6 -j DROP
```

### Logging Strategy

```bash
# Log all blocked incoming
sudo ufw logging medium

# In /etc/ufw/before.rules, add logging for specific traffic:
-A ufw-before-input -p tcp --dport 22 -j LOG --log-prefix "[UFW SSH] "
```

### Regular Audits

```bash
# Review open ports
sudo ss -tlnp

# Review UFW rules
sudo ufw status numbered

# Review raw iptables
sudo iptables-save > /tmp/iptables-audit.txt

# Scan yourself from outside
nmap -sS -O your-external-ip
```

---

## Quick Reference

### Start Fresh

```bash
sudo ufw reset
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### Common Services

```bash
sudo ufw allow ssh           # 22/tcp
sudo ufw allow http          # 80/tcp
sudo ufw allow https         # 443/tcp
sudo ufw allow 'Nginx Full'  # 80,443/tcp
sudo ufw allow Samba         # Samba ports
sudo ufw allow 32400/tcp     # Plex
```

### Troubleshooting Commands

```bash
# UFW
sudo ufw status verbose
sudo ufw show raw
sudo ufw show added

# iptables
sudo iptables -L -n -v
sudo iptables -t nat -L -n -v
sudo iptables -t mangle -L -n -v

# Connection tracking
sudo conntrack -L

# Network
sudo ss -tlnp
sudo netstat -tlnp
ip route show
```
