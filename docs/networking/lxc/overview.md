# LXD Network Overview

## LXC vs LXD

- **LXC** - Low-level container runtime
- **LXD** - High-level management layer for LXC
- This guide focuses on LXD (the common way to use LXC)

## Network Types

### Managed Bridge (Default)

LXD manages a bridge with NAT:

```
┌─────────────────────────────────────────────────────────────┐
│                          Host                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              lxdbr0 bridge                           │   │
│   │              10.10.10.1/24                           │   │
│   │              (managed by LXD)                        │   │
│   │                                                      │   │
│   │    ┌────────┐  ┌────────┐                           │   │
│   │    │ veth0  │  │ veth1  │                           │   │
│   └────┴───┬────┴──┴───┬────┴───────────────────────────┘   │
│            │           │                                     │
│   ┌────────▼────────┐ ┌▼───────────────┐                    │
│   │   Container 1   │ │  Container 2   │                    │
│   │   10.10.10.10   │ │  10.10.10.11   │                    │
│   └─────────────────┘ └────────────────┘                    │
│                                                              │
│   eth0 ─────────────────────────────────▶ Internet          │
│   NAT: 10.10.10.0/24 masquerade                            │
└─────────────────────────────────────────────────────────────┘
```

### External Bridge

Using a pre-existing bridge:

```bash
lxc network attach-profile br0 default eth0
```

### macvlan

Direct network access with separate MAC:

```yaml
config:
  nictype: macvlan
  parent: eth0
```

### Physical NIC

Dedicated NIC for container:

```yaml
config:
  nictype: physical
  parent: eth1
```

## Initial Setup

### Install LXD

```bash
sudo snap install lxd
sudo lxd init
```

### Default Network Configuration

During `lxd init`:

```
Would you like to create a new local network bridge? (yes/no) [default=yes]: yes
What should the new bridge be called? [default=lxdbr0]: lxdbr0
What IPv4 address should be used? (CIDR subnet notation, "auto" or "none") [default=auto]: auto
What IPv6 address should be used? (CIDR subnet notation, "auto" or "none") [default=auto]: none
```

### View Network

```bash
lxc network list
lxc network show lxdbr0
```

```yaml
config:
  ipv4.address: 10.10.10.1/24
  ipv4.nat: "true"
  ipv6.address: none
description: ""
name: lxdbr0
type: bridge
managed: true
status: Created
```

## Managing Networks

### Create Network

```bash
# Managed bridge
lxc network create mynet

# With specific config
lxc network create mynet \
    ipv4.address=10.20.0.1/24 \
    ipv4.nat=true \
    ipv6.address=none
```

### Edit Network

```bash
# Interactive edit
lxc network edit lxdbr0

# Set specific option
lxc network set lxdbr0 ipv4.address 10.10.10.1/24
```

### Delete Network

```bash
lxc network delete mynet
```

## Network Options

### IPv4 Configuration

```bash
lxc network set lxdbr0 ipv4.address 10.10.10.1/24
lxc network set lxdbr0 ipv4.nat true
lxc network set lxdbr0 ipv4.dhcp true
lxc network set lxdbr0 ipv4.dhcp.ranges 10.10.10.100-10.10.10.200
```

### DNS Configuration

```bash
lxc network set lxdbr0 dns.domain lxd.local
lxc network set lxdbr0 dns.mode managed
```

### Firewall

```bash
# Enable LXD firewall management
lxc network set lxdbr0 ipv4.firewall true

# Or disable (manage manually)
lxc network set lxdbr0 ipv4.firewall false
```

## Container Network Configuration

### Attach to Network

```bash
# At creation
lxc launch ubuntu:22.04 mycontainer --network lxdbr0

# Or add device
lxc network attach lxdbr0 mycontainer eth0
```

### Static IP

```bash
lxc config device override mycontainer eth0 ipv4.address=10.10.10.50
```

### Multiple NICs

```bash
# Add second interface
lxc config device add mycontainer eth1 nic network=mynet
```

## Profiles

### Default Profile

```bash
lxc profile show default
```

```yaml
config: {}
description: Default LXD profile
devices:
  eth0:
    name: eth0
    network: lxdbr0
    type: nic
  root:
    path: /
    pool: default
    type: disk
name: default
```

### Custom Profile

```bash
# Create profile
lxc profile create isolated

# Add network device
lxc profile device add isolated eth0 nic network=isolated-net

# Apply to container
lxc profile add mycontainer isolated
```

## Proxy Devices

Expose container ports via host.

### TCP Proxy

```bash
# Forward host:8080 to container:80
lxc config device add mycontainer myproxy proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80
```

### With bind=host

```bash
# Proxy runs on host (UFW applies!)
lxc config device add mycontainer myproxy proxy \
    listen=tcp:0.0.0.0:8080 \
    connect=tcp:127.0.0.1:80 \
    bind=host
```

### Remove Proxy

```bash
lxc config device remove mycontainer myproxy
```

## DNS Resolution

### Container to Container

Containers can resolve each other by name:

```bash
# From container1
ping container2.lxd.local
ping container2  # Short name works too
```

### From Host

```bash
# Add to host's resolv.conf
# Or use:
dig @10.10.10.1 container1.lxd.local
```

## Troubleshooting

### Container Has No Network

```bash
# Check container's devices
lxc config show mycontainer | grep -A5 devices

# Check network is running
lxc network list

# Check in container
lxc exec mycontainer -- ip addr
lxc exec mycontainer -- ip route
```

### DNS Not Working

```bash
# Check dnsmasq
ps aux | grep dnsmasq | grep lxd

# Check DNS config
lxc network get lxdbr0 dns.mode
```

### NAT Not Working

```bash
# Check NAT setting
lxc network get lxdbr0 ipv4.nat

# Check iptables
sudo iptables -t nat -L -n | grep 10.10.10
```
