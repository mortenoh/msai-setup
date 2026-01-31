# Linux Networking Basics

## The Network Stack

Linux implements a full TCP/IP network stack in the kernel. Understanding how packets flow through this stack is essential for debugging and security.

```
┌─────────────────────────────────────────────────────────────┐
│                     User Space                               │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │  nginx  │  │  docker │  │ libvirt │  │   ssh   │        │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘        │
│       │            │            │            │              │
├───────┴────────────┴────────────┴────────────┴──────────────┤
│                    System Call Interface                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                       Socket Layer                           │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                     Transport Layer                          │
│                     (TCP, UDP, SCTP)                         │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                      Network Layer                           │
│                    (IP, ICMP, routing)                       │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│                      Link Layer                              │
│              (Ethernet, WiFi, bridges, bonds)                │
│                                                              │
├─────────────────────────────────────────────────────────────┤
│                     Device Drivers                           │
├─────────────────────────────────────────────────────────────┤
│                        Hardware                              │
│              (NICs, switches, cables)                        │
└─────────────────────────────────────────────────────────────┘
```

## Packet Reception (Ingress)

When a packet arrives at your network interface:

### 1. Hardware Interrupt

The NIC receives the packet and raises a hardware interrupt (IRQ).

```bash
# View interrupt assignments
cat /proc/interrupts | grep eth
```

### 2. Driver Processing

The device driver:

1. Copies packet to a kernel buffer (sk_buff)
2. Schedules softirq for further processing
3. Returns from interrupt handler quickly

### 3. Softirq Processing (NAPI)

The New API (NAPI) processes packets efficiently:

1. Disables further interrupts temporarily
2. Polls for additional packets
3. Processes packets in batches

```bash
# View softirq statistics
cat /proc/softirqs | grep NET
```

### 4. Network Layer Processing

For each packet:

1. **Netfilter PREROUTING** - First chance to filter/modify
2. **Routing decision** - Local delivery or forward?
3. **Netfilter INPUT** (if local) or **FORWARD** (if routing)
4. **Transport layer** - TCP/UDP processing
5. **Socket delivery** - Packet reaches application

## Packet Transmission (Egress)

When an application sends data:

### 1. Application Write

Application calls `send()` or `write()` on a socket.

### 2. Transport Layer

TCP/UDP adds headers and handles:

- Segmentation
- Sequence numbers (TCP)
- Congestion control (TCP)

### 3. Network Layer

IP layer:

1. Adds IP header
2. **Netfilter OUTPUT** - Filter/modify outgoing
3. Routing lookup
4. **Netfilter POSTROUTING** - Final modification (NAT)

### 4. Link Layer

- Adds Ethernet header
- ARP resolution if needed
- Queues for transmission

### 5. Driver and Hardware

- Driver sends to NIC
- NIC transmits on wire

## Forwarding (Routing)

When the host acts as a router:

```
Incoming                                                    Outgoing
Packet                                                      Packet
   │                                                           ▲
   ▼                                                           │
┌──────────────┐    ┌───────────────┐    ┌──────────────┐    ┌───────────────┐
│  PREROUTING  │───▶│ Route Decision│───▶│   FORWARD    │───▶│ POSTROUTING   │
│              │    │               │    │              │    │               │
└──────────────┘    └───────────────┘    └──────────────┘    └───────────────┘
                           │
                           ▼ (if local)
                    ┌───────────────┐
                    │    INPUT      │
                    │               │
                    └───────────────┘
                           │
                           ▼
                    ┌───────────────┐
                    │  Local Process│
                    └───────────────┘
```

### Enabling IP Forwarding

By default, Linux doesn't forward packets between interfaces.

```bash
# Check current setting
cat /proc/sys/net/ipv4/ip_forward

# Enable temporarily
echo 1 | sudo tee /proc/sys/net/ipv4/ip_forward

# Enable permanently
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-forward.conf
sudo sysctl -p /etc/sysctl.d/99-forward.conf
```

## Network Interfaces

### Physical Interfaces

```bash
# List all interfaces
ip link show

# Show interface details
ip addr show enp5s0

# Show interface statistics
ip -s link show enp5s0
```

### Virtual Interfaces

Linux supports many virtual interface types:

| Type | Description | Use Case |
|------|-------------|----------|
| lo | Loopback | Local-only communication |
| bridge | Software switch | VM/container networking |
| veth | Virtual ethernet pair | Container connectivity |
| tap | Layer 2 tunnel | VM networking |
| tun | Layer 3 tunnel | VPN connections |
| bond | Interface bonding | Redundancy/performance |
| vlan | 802.1Q VLAN | Network segmentation |
| macvlan | MAC-based virtual NIC | Container direct access |
| ipvlan | IP-based virtual NIC | Container networking |

### Bridge Interfaces

Bridges act as virtual switches:

```bash
# Create a bridge
sudo ip link add br0 type bridge

# Add interface to bridge
sudo ip link set enp5s0 master br0

# Show bridge info
bridge link show
bridge fdb show
```

### VETH Pairs

Virtual ethernet pairs connect network namespaces:

```bash
# Create veth pair
sudo ip link add veth0 type veth peer name veth1

# Move one end to a namespace
sudo ip link set veth1 netns container1

# The two ends can now communicate
```

## Routing

### Viewing Routes

```bash
# Show routing table
ip route show

# Show routing table with details
ip route show table all

# Show route for specific destination
ip route get 8.8.8.8
```

### Route Types

```bash
# Default route (gateway)
default via 192.168.1.1 dev enp5s0

# Network route
192.168.1.0/24 dev enp5s0 proto kernel scope link src 192.168.1.100

# Host route
192.168.122.10 via 192.168.122.1 dev virbr0
```

### Policy Routing

Multiple routing tables for advanced scenarios:

```bash
# Add custom routing table
echo "100 custom" | sudo tee -a /etc/iproute2/rt_tables

# Add route to custom table
sudo ip route add default via 10.0.0.1 table custom

# Add rule to use custom table
sudo ip rule add from 10.0.0.0/24 table custom
```

## DNS Resolution

### systemd-resolved

Ubuntu uses systemd-resolved for DNS:

```bash
# Check resolver status
resolvectl status

# Query DNS
resolvectl query google.com

# Flush cache
resolvectl flush-caches
```

### Configuration

```bash
# View resolved.conf
cat /etc/systemd/resolved.conf

# DNS servers from DHCP are in
ls /run/systemd/resolve/
```

### The /etc/resolv.conf Situation

```bash
# Usually a symlink
ls -la /etc/resolv.conf
# -> ../run/systemd/resolve/stub-resolv.conf

# Contains 127.0.0.53 (local resolver)
cat /etc/resolv.conf
```

## Network Namespaces

Namespaces provide network isolation:

```bash
# List namespaces
ip netns list

# Create namespace
sudo ip netns add test

# Execute command in namespace
sudo ip netns exec test ip addr

# Delete namespace
sudo ip netns delete test
```

### Namespace Networking

```bash
# Create namespace with connectivity
sudo ip netns add isolated

# Create veth pair
sudo ip link add veth-host type veth peer name veth-ns

# Move one end to namespace
sudo ip link set veth-ns netns isolated

# Configure addresses
sudo ip addr add 10.0.0.1/24 dev veth-host
sudo ip link set veth-host up

sudo ip netns exec isolated ip addr add 10.0.0.2/24 dev veth-ns
sudo ip netns exec isolated ip link set veth-ns up
sudo ip netns exec isolated ip link set lo up

# Test connectivity
sudo ip netns exec isolated ping 10.0.0.1
```

## Sockets and Ports

### Viewing Sockets

```bash
# All TCP sockets
ss -t

# Listening sockets with process info
ss -tlnp

# UDP sockets
ss -u

# Unix sockets
ss -x

# All sockets with state
ss -a
```

### Socket States

| State | Meaning |
|-------|---------|
| LISTEN | Waiting for connections |
| ESTABLISHED | Active connection |
| TIME_WAIT | Waiting to close |
| CLOSE_WAIT | Remote closed, local hasn't |
| SYN_SENT | Connection initiating |
| SYN_RECV | Connection received |

### Port Ranges

```bash
# View ephemeral port range
cat /proc/sys/net/ipv4/ip_local_port_range

# Reserved ports (< 1024) require root
# Well-known ports: 0-1023
# Registered ports: 1024-49151
# Dynamic/ephemeral: 49152-65535
```

## ARP and Neighbor Discovery

### ARP Cache

```bash
# View ARP cache
ip neigh show

# Add static entry
sudo ip neigh add 192.168.1.50 lladdr aa:bb:cc:dd:ee:ff dev enp5s0

# Delete entry
sudo ip neigh del 192.168.1.50 dev enp5s0
```

### Neighbor States

| State | Meaning |
|-------|---------|
| REACHABLE | Recently confirmed |
| STALE | Needs revalidation |
| DELAY | Pending revalidation |
| PROBE | Actively probing |
| FAILED | Resolution failed |

## MTU and Fragmentation

### Maximum Transmission Unit

```bash
# View MTU
ip link show enp5s0 | grep mtu

# Change MTU
sudo ip link set enp5s0 mtu 9000

# Find path MTU
tracepath google.com
```

### Common MTU Values

| MTU | Use Case |
|-----|----------|
| 1500 | Standard Ethernet |
| 1492 | PPPoE |
| 1400 | Common VPN overhead |
| 9000 | Jumbo frames (local network) |

## Network Configuration with Netplan

### Basic Configuration

```yaml
# /etc/netplan/00-config.yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: true
```

### Static IP

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
```

### Bridge Configuration

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false
  bridges:
    br0:
      interfaces: [enp5s0]
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

### Applying Changes

```bash
# Test configuration
sudo netplan try

# Apply configuration
sudo netplan apply

# Debug issues
sudo netplan --debug apply
```

## Kernel Parameters

### Important Network Sysctls

```bash
# View all network parameters
sysctl net.

# Common parameters
sysctl net.ipv4.ip_forward
sysctl net.ipv4.conf.all.rp_filter
sysctl net.core.somaxconn
sysctl net.ipv4.tcp_max_syn_backlog
```

### Setting Parameters

```bash
# Temporary
sudo sysctl -w net.ipv4.ip_forward=1

# Permanent
echo "net.ipv4.ip_forward = 1" | sudo tee /etc/sysctl.d/99-custom.conf
sudo sysctl -p /etc/sysctl.d/99-custom.conf
```

### Security-Related Parameters

```bash
# Prevent IP spoofing
net.ipv4.conf.all.rp_filter = 1

# Ignore ICMP redirects
net.ipv4.conf.all.accept_redirects = 0

# Don't send ICMP redirects
net.ipv4.conf.all.send_redirects = 0

# Log martian packets
net.ipv4.conf.all.log_martians = 1

# Ignore broadcast pings
net.ipv4.icmp_echo_ignore_broadcasts = 1
```
