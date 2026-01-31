# LXD/LXC Network Integration

## Overview

LXD provides container and VM management with its own network stack. Netplan configures the host, while LXD manages container networking.

```
┌──────────────────────────────────────────────────────────────────────┐
│                             Host System                               │
│                                                                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐              │
│  │ Container 1 │    │ Container 2 │    │ Container 3 │              │
│  │ 10.10.10.50 │    │ 10.10.10.51 │    │ 192.168.1.  │              │
│  │             │    │             │    │    150      │              │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘              │
│         │                  │                  │                      │
│         └─────────┬────────┘                  │                      │
│                   │                           │                      │
│            lxdbr0 (managed)             br0 (bridged)               │
│            10.10.10.1                   192.168.1.100               │
│                   │                           │                      │
│                   └───────────┬───────────────┘                      │
│                               │                                      │
│                          eth0 (netplan)                              │
│                          192.168.1.100                               │
└───────────────────────────────┼──────────────────────────────────────┘
                                │
                           Physical Network
```

## LXD Network Types

| Type | Description | Use Case |
|------|-------------|----------|
| lxdbr0 (managed) | LXD-managed NAT bridge | Default, isolated |
| bridged | Use host bridge | Direct network access |
| macvlan | Share physical interface | Direct IPs, no host-container |
| sriov | Hardware passthrough | High performance |
| ovn | Overlay network | Multi-host, advanced |

## Default LXD Network

LXD creates `lxdbr0` during initialization:

```bash
# Initialize LXD
lxd init

# Check LXD networks
lxc network list
lxc network show lxdbr0
```

Default provides:
- Bridge: `lxdbr0`
- Subnet: 10.x.x.x/24 (random)
- NAT to host
- Built-in DHCP/DNS

## Host Netplan for LXD

### Basic Host Configuration

```yaml
# /etc/netplan/00-lxd-host.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

LXD manages container networking independently.

## Bridged Containers

Containers get IPs directly from physical network.

### Create Host Bridge with Netplan

```yaml
# /etc/netplan/00-lxd-bridge.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
      parameters:
        stp: false
        forward-delay: 0
```

### Use Bridge in LXD

```bash
# Create LXD network using host bridge
lxc network create host-bridge \
  --type bridge \
  parent=br0

# Or attach existing bridge
lxc network attach-profile host-bridge default eth0
```

### Profile with Bridge

```bash
# Edit default profile
lxc profile edit default
```

```yaml
config: {}
description: Default LXD profile
devices:
  eth0:
    name: eth0
    nictype: bridged
    parent: br0
    type: nic
  root:
    path: /
    pool: default
    type: disk
name: default
```

### Launch Container on Bridge

```bash
# Create container using bridged network
lxc launch ubuntu:22.04 mycontainer

# Container gets IP from network DHCP
lxc exec mycontainer -- ip addr
```

## Multiple LXD Networks

### Separate Networks for Different Purposes

```yaml
# Netplan with multiple bridges
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: false
    eth1:
      dhcp4: false

  bridges:
    br-public:
      interfaces:
        - eth0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

    br-internal:
      interfaces:
        - eth1
      addresses:
        - 10.0.0.100/24
```

```bash
# Create LXD networks
lxc network create public parent=br-public
lxc network create internal parent=br-internal
```

### Container with Multiple NICs

```bash
# Add both networks to container
lxc config device add mycontainer eth0 nic nictype=bridged parent=br-public
lxc config device add mycontainer eth1 nic nictype=bridged parent=br-internal
```

## VLAN Integration

### Netplan VLANs with Bridges

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.10:
      id: 10
      link: eth0
    eth0.20:
      id: 20
      link: eth0

  bridges:
    br-mgmt:
      interfaces:
        - eth0.10
      addresses:
        - 10.10.0.100/24
      routes:
        - to: default
          via: 10.10.0.1

    br-app:
      interfaces:
        - eth0.20
```

```bash
# Use VLAN bridges in LXD
lxc network create mgmt parent=br-mgmt
lxc network create app parent=br-app
```

## Macvlan Networking

Containers get direct IPs without bridge:

```bash
# Create macvlan network
lxc network create macvlan-net \
  ipv4.address=none \
  ipv6.address=none \
  nictype=macvlan \
  parent=eth0
```

Container config:

```bash
lxc config device add mycontainer eth0 nic \
  nictype=macvlan \
  parent=eth0
```

!!! warning "Host-Container Communication"
    Macvlan prevents direct host-to-container communication. Use a macvlan interface on host if needed.

## Proxy Devices (Port Forwarding)

Forward host ports to containers:

```bash
# Forward host port 80 to container port 80
lxc config device add mycontainer http proxy \
  listen=tcp:0.0.0.0:80 \
  connect=tcp:127.0.0.1:80

# Forward to specific container IP
lxc config device add mycontainer http proxy \
  listen=tcp:192.168.1.100:80 \
  connect=tcp:10.10.10.50:80
```

## Static IPs for Containers

### Using LXD DHCP Reservations

```bash
# Set static IP via LXD
lxc config device set mycontainer eth0 ipv4.address=10.10.10.50
```

### Container Static Config

Inside container:

```yaml
# /etc/netplan/50-cloud-init.yaml (in container)
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.150/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
```

## LXD Clustering with Netplan

### Fan Networking (Multi-Host)

For simple multi-host:

```bash
# Initialize with fan networking
lxd init --auto --network-address=192.168.1.100 --network-port=8443

# Create fan network
lxc network create fan0 \
  bridge.mode=fan \
  fan.underlay_subnet=192.168.1.0/24
```

### OVN Networking

For advanced multi-host:

```bash
# Install OVN
apt install ovn-host ovn-central

# Configure OVN network
lxc network create ovn-net --type=ovn
```

## DNS and Containers

### LXD DNS

LXD provides DNS for containers on managed networks:

```bash
# Check DNS
lxc network show lxdbr0 | grep dns

# Containers resolve each other
lxc exec container1 -- ping container2.lxd
```

### Host DNS Integration

Add LXD DNS to host resolver:

```ini
# /etc/systemd/resolved.conf.d/lxd.conf
[Resolve]
DNS=10.10.10.1
Domains=~lxd
```

## Troubleshooting

### Container Has No Network

```bash
# Check LXD network status
lxc network list
lxc network info lxdbr0

# Check container interface
lxc exec mycontainer -- ip addr
lxc exec mycontainer -- ip route

# Check host bridge
ip link show lxdbr0
bridge link show
```

### Container Can't Reach Internet

```bash
# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward

# Check NAT (for managed networks)
iptables -t nat -L -n -v | grep lxd

# Check default route in container
lxc exec mycontainer -- ip route show default
```

### Bridged Container Not Getting IP

```bash
# Check bridge exists and has interface
ip link show br0
bridge link show master br0

# Check container interface attached
lxc config show mycontainer | grep -A10 devices

# Check DHCP traffic
tcpdump -i br0 port 67 or port 68
```

### Name Resolution Failed

```bash
# Check container DNS config
lxc exec mycontainer -- cat /etc/resolv.conf

# Test DNS
lxc exec mycontainer -- dig google.com

# Check LXD DNS is running (managed networks)
ss -ulnp | grep dnsmasq
```

## Performance Tuning

### virtio for Better Performance

LXD uses virtio by default for containers.

### SR-IOV for VMs

```bash
# Create SR-IOV network
lxc network create sriov-net \
  nictype=sriov \
  parent=eth0
```

### Jumbo Frames

```yaml
# Netplan bridge with jumbo frames
bridges:
  br0:
    interfaces:
      - eth0
    mtu: 9000
    parameters:
      stp: false
```

## Best Practices

1. **Use managed networks for isolation** - LXD manages NAT and DHCP
2. **Use bridges for production** - Direct network access
3. **Plan IP addressing** - Avoid conflicts between LXD and host
4. **Use profiles** - Consistent network config across containers
5. **Consider security** - Containers share kernel with host
6. **Use proxy devices** - Preferred over manual iptables
7. **Document topology** - Complex setups need documentation
8. **Separate networks** - Different purposes = different bridges
