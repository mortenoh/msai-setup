# Virtual Interfaces

## Overview

Virtual interfaces are software-defined network interfaces that don't correspond to physical hardware. They're essential for:

- Tunneling (VPN, overlay networks)
- Container networking
- Testing and development
- Network isolation

## Tunnel Interfaces

### GRE Tunnel

Generic Routing Encapsulation for site-to-site connectivity:

```yaml
network:
  version: 2

  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1

  tunnels:
    gre1:
      mode: gre
      local: 203.0.113.10      # This server's public IP
      remote: 198.51.100.20    # Remote endpoint
      addresses:
        - 10.0.0.1/30          # Tunnel internal IP
      routes:
        - to: 10.10.0.0/16     # Remote network
          via: 10.0.0.2        # Via tunnel
```

### IP-in-IP Tunnel

Simpler than GRE:

```yaml
network:
  version: 2

  tunnels:
    ipip1:
      mode: ipip
      local: 203.0.113.10
      remote: 198.51.100.20
      addresses:
        - 10.0.0.1/30
```

### SIT Tunnel (IPv6 over IPv4)

```yaml
network:
  version: 2

  tunnels:
    sit1:
      mode: sit
      local: 203.0.113.10
      remote: 198.51.100.20
      addresses:
        - "2001:db8::1/64"
```

### IP6GRE Tunnel

GRE over IPv6:

```yaml
network:
  version: 2

  tunnels:
    ip6gre1:
      mode: ip6gre
      local: "2001:db8::10"
      remote: "2001:db8::20"
      addresses:
        - 10.0.0.1/30
```

### VXLAN Tunnel

Virtual Extensible LAN for overlay networks:

```yaml
network:
  version: 2

  tunnels:
    vxlan100:
      mode: vxlan
      id: 100
      local: 192.168.1.10
      remote: 192.168.1.20
      port: 4789
      addresses:
        - 10.100.0.1/24
```

### VXLAN with Multicast

For multi-node VXLAN:

```yaml
network:
  version: 2

  tunnels:
    vxlan100:
      mode: vxlan
      id: 100
      local: 192.168.1.10
      group: 239.1.1.1      # Multicast group
      port: 4789
      addresses:
        - 10.100.0.1/24
```

## WireGuard VPN

### Basic WireGuard

```yaml
network:
  version: 2

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.1/24
      key: "BASE64_PRIVATE_KEY_HERE"
      port: 51820
      peers:
        - keys:
            public: "PEER_PUBLIC_KEY_HERE"
          allowed-ips:
            - 10.10.10.2/32
            - 10.20.0.0/16
          endpoint: "peer.example.com:51820"
          keepalive: 25
```

### WireGuard Road Warrior

Client configuration:

```yaml
network:
  version: 2

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.2/24
      key: "CLIENT_PRIVATE_KEY"
      peers:
        - keys:
            public: "SERVER_PUBLIC_KEY"
          allowed-ips:
            - 0.0.0.0/0          # Route all traffic through VPN
          endpoint: "vpn.example.com:51820"
          keepalive: 25
```

### WireGuard Hub-and-Spoke

Central server with multiple clients:

```yaml
network:
  version: 2

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.1/24
      key: "SERVER_PRIVATE_KEY"
      port: 51820
      peers:
        # Client 1
        - keys:
            public: "CLIENT1_PUBLIC_KEY"
          allowed-ips:
            - 10.10.10.2/32

        # Client 2
        - keys:
            public: "CLIENT2_PUBLIC_KEY"
          allowed-ips:
            - 10.10.10.3/32

        # Site 2 network
        - keys:
            public: "SITE2_PUBLIC_KEY"
          allowed-ips:
            - 10.10.10.4/32
            - 10.20.0.0/24      # Entire site 2 subnet
          endpoint: "site2.example.com:51820"
```

## Dummy Interfaces

For testing or as anchor points:

```yaml
network:
  version: 2

  dummy-devices:
    dummy0:
      addresses:
        - 10.255.255.1/32      # Loopback-like address

    dummy1:
      addresses:
        - 192.168.100.1/24
```

## VRF (Virtual Routing and Forwarding)

Separate routing tables:

```yaml
network:
  version: 2

  vrfs:
    vrf-mgmt:
      table: 100
      interfaces:
        - eth0
      routes:
        - to: default
          via: 192.168.1.1
          table: 100

    vrf-customer:
      table: 200
      interfaces:
        - eth1
```

## TAP/TUN Interfaces

### Persistent TAP

For virtualization:

```yaml
network:
  version: 2

  bridges:
    br0:
      interfaces:
        - eth0
        # TAP interfaces are usually created by VMs
        # and added dynamically
      addresses:
        - 192.168.1.100/24
```

Create TAP manually:

```bash
# Create persistent TAP
ip tuntap add dev tap0 mode tap user libvirt-qemu

# Add to bridge
ip link set tap0 master br0
ip link set tap0 up
```

## MacVLAN

Multiple MAC addresses on one interface:

```yaml
network:
  version: 2

  # Parent interface
  ethernets:
    eth0:
      dhcp4: false

  # MacVLAN sub-interfaces (manual setup)
  # Netplan doesn't directly support macvlan
  # Use networkd directly or bridges
```

Manual MacVLAN setup:

```bash
# Create macvlan interface
ip link add macvlan0 link eth0 type macvlan mode bridge
ip addr add 192.168.1.200/24 dev macvlan0
ip link set macvlan0 up
```

## IPvlan

Similar to MacVLAN but shares MAC:

```bash
# L2 mode (same as macvlan but shared MAC)
ip link add ipvlan0 link eth0 type ipvlan mode l2

# L3 mode (routing mode)
ip link add ipvlan0 link eth0 type ipvlan mode l3
```

## Network Namespaces

Isolated network stacks (used by containers):

```bash
# Create namespace
ip netns add ns1

# Create veth pair
ip link add veth0 type veth peer name veth1

# Move one end to namespace
ip link set veth1 netns ns1

# Configure host side
ip addr add 10.0.0.1/24 dev veth0
ip link set veth0 up

# Configure namespace side
ip netns exec ns1 ip addr add 10.0.0.2/24 dev veth1
ip netns exec ns1 ip link set veth1 up
ip netns exec ns1 ip link set lo up
```

## Tunnel Configuration Examples

### Site-to-Site VPN

```
Site A (203.0.113.10)          Site B (198.51.100.20)
┌──────────────────┐          ┌──────────────────┐
│  10.10.0.0/24    │          │  10.20.0.0/24    │
│                  │   GRE    │                  │
│    eth0 ─────────┼──────────┼───── eth0        │
│    gre1 (10.0.0.1/30)       (10.0.0.2/30) gre1 │
└──────────────────┘          └──────────────────┘
```

Site A configuration:

```yaml
network:
  version: 2

  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24
        - 10.10.0.1/24
      routes:
        - to: default
          via: 203.0.113.1

  tunnels:
    gre1:
      mode: gre
      local: 203.0.113.10
      remote: 198.51.100.20
      addresses:
        - 10.0.0.1/30
      routes:
        - to: 10.20.0.0/24
          via: 10.0.0.2
```

### WireGuard Full Tunnel

Route all traffic through VPN:

```yaml
network:
  version: 2

  ethernets:
    eth0:
      dhcp4: true

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.2/24
      key: "PRIVATE_KEY"
      routes:
        # Route all traffic through WireGuard
        - to: 0.0.0.0/0
          via: 10.10.10.1
      routing-policy:
        # Ensure VPN endpoint is reachable via eth0
        - from: 0.0.0.0/0
          to: vpn.example.com
          table: main
      peers:
        - keys:
            public: "SERVER_PUBLIC_KEY"
          allowed-ips:
            - 0.0.0.0/0
            - "::/0"
          endpoint: "vpn.example.com:51820"
          keepalive: 25
```

## Verifying Virtual Interfaces

### List All Interfaces

```bash
# Show all interfaces with type
ip -d link show

# Show tunnels
ip tunnel show

# Show WireGuard
wg show

# Show bridges and their ports
bridge link show
```

### Check Tunnel Status

```bash
# GRE tunnel
ip tunnel show gre1

# WireGuard
wg show wg0

# VXLAN
ip -d link show vxlan100
```

### Debug Connectivity

```bash
# Ping through tunnel
ping -I gre1 10.0.0.2

# Check tunnel traffic
tcpdump -i gre1

# Check encapsulated traffic
tcpdump -i eth0 proto gre
```

## Troubleshooting

### Tunnel Not Coming Up

```bash
# Check kernel modules
lsmod | grep -E "gre|vxlan|wireguard"

# Load if missing
modprobe ip_gre
modprobe vxlan
modprobe wireguard

# Check interface state
ip link show gre1
```

### No Traffic Through Tunnel

```bash
# Check routes
ip route show

# Check firewall
iptables -L -n -v | grep -E "gre|51820"

# Verify remote endpoint is reachable
ping 198.51.100.20

# Check GRE protocol (47) is allowed
```

### WireGuard Handshake Fails

```bash
# Check WireGuard status
wg show

# Verify keys match
# Server's public key should be in client config
# Client's public key should be in server's peer list

# Check endpoint is correct
# Check firewall allows UDP 51820

# Check time sync (important for handshake)
date
```

### MTU Issues

```bash
# Check MTU
ip link show gre1

# Tunnel overhead reduces effective MTU
# GRE: 24 bytes overhead (1500-24=1476)
# WireGuard: 60 bytes overhead (1500-60=1440)

# Set appropriate MTU
ip link set gre1 mtu 1476
```

## Best Practices

1. **Use WireGuard** for new VPN deployments - it's faster and more secure
2. **Set appropriate MTU** - tunnels have overhead
3. **Use keepalive** for NAT traversal with WireGuard
4. **Monitor tunnel state** - tunnels can silently fail
5. **Secure private keys** - restrict file permissions
6. **Use dedicated interfaces** for tunnel endpoints when possible
7. **Plan IP addressing** - tunnel networks should not overlap
