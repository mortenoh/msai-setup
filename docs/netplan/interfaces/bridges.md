# Bridge Configuration

## What is a Bridge?

A bridge is a software switch that connects multiple network interfaces at Layer 2 (Ethernet). It's essential for:

- **VM networking** - Connect VMs to physical network
- **Container networking** - Docker, LXC bridges
- **Network aggregation** - Combine interfaces logically

```
┌─────────────────────────────────────────────────────────────┐
│                    Bridge (br0)                              │
│                   192.168.1.100/24                          │
│                                                              │
│   ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│   │  enp5s0  │  │  vnet0   │  │  vnet1   │  │  veth0   │  │
│   │(physical)│  │  (VM1)   │  │  (VM2)   │  │(container)│  │
│   └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
└────────┼─────────────┼─────────────┼─────────────┼─────────┘
         │             │             │             │
    To Network        VM1           VM2        Container
```

## Basic Bridge

### Simple Bridge with DHCP

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
      dhcp4: true
```

### Bridge with Static IP

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses:
          - 1.1.1.1
```

## Bridge Parameters

### Spanning Tree Protocol (STP)

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    addresses:
      - 192.168.1.100/24
    parameters:
      stp: true              # Enable STP
      forward-delay: 15      # Seconds before forwarding
      hello-time: 2          # Seconds between hello packets
      max-age: 20            # Maximum age of information
```

### Disable STP (Recommended for Single Bridge)

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    addresses:
      - 192.168.1.100/24
    parameters:
      stp: false             # Disable STP
      forward-delay: 0       # No delay
```

!!! tip "When to Disable STP"
    If you have only one bridge with one uplink, disable STP for faster interface activation.

### Bridge Priority

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    parameters:
      stp: true
      priority: 32768        # Default is 32768, lower = preferred root
```

### Ageing Time

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    parameters:
      ageing-time: 300       # MAC address table timeout (seconds)
```

## Multiple Interfaces

### Combining Physical Interfaces

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false
    enp6s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
        - enp6s0
      addresses:
        - 192.168.1.100/24
```

!!! warning "Not Bonding"
    This creates a bridge (switch), not a bond. Traffic isn't load-balanced. Use bonds for redundancy/performance.

### Physical + Virtual Interfaces

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
        # Virtual interfaces (vnet*, veth*) are added dynamically by:
        # - libvirt for VMs
        # - Docker for containers
        # - LXD for containers
      addresses:
        - 192.168.1.100/24
```

## VM Networking Bridge

### For KVM/libvirt

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
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

Then in libvirt:

```xml
<network>
  <name>host-bridge</name>
  <forward mode="bridge"/>
  <bridge name="br0"/>
</network>
```

### For Docker

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br-docker:
      interfaces:
        - enp5s0
      addresses:
        - 192.168.1.100/24
      parameters:
        stp: false
```

Docker macvlan using the bridge:

```bash
docker network create -d macvlan \
  --subnet=192.168.1.0/24 \
  --gateway=192.168.1.1 \
  -o parent=br-docker \
  macvlan-net
```

## Multiple Bridges

### Separate Networks

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false
    enp6s0:
      dhcp4: false

  bridges:
    # Management network
    br-mgmt:
      interfaces:
        - enp5s0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

    # VM network (different subnet)
    br-vms:
      interfaces:
        - enp6s0
      addresses:
        - 10.0.0.1/24
```

### VLAN-Based Bridges

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  vlans:
    enp5s0.10:
      id: 10
      link: enp5s0
    enp5s0.20:
      id: 20
      link: enp5s0

  bridges:
    br-vlan10:
      interfaces:
        - enp5s0.10
      addresses:
        - 192.168.10.1/24

    br-vlan20:
      interfaces:
        - enp5s0.20
      addresses:
        - 192.168.20.1/24
```

## Bridge without IP

For bridges that only forward traffic:

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  bridges:
    br0:
      interfaces:
        - enp5s0
      # No addresses - bridge only forwards traffic
      # VMs/containers get IPs from external DHCP
```

## Bridge MTU

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    addresses:
      - 192.168.1.100/24
    mtu: 1500              # Standard MTU

    # Or for jumbo frames
    mtu: 9000
```

!!! note "MTU Consistency"
    All interfaces on the bridge should have the same MTU. Set MTU on physical interfaces too.

```yaml
ethernets:
  enp5s0:
    dhcp4: false
    mtu: 9000

bridges:
  br0:
    interfaces:
      - enp5s0
    mtu: 9000
```

## Bridge MAC Address

```yaml
bridges:
  br0:
    interfaces:
      - enp5s0
    macaddress: "aa:bb:cc:dd:ee:ff"
    addresses:
      - 192.168.1.100/24
```

By default, the bridge uses the MAC of the first interface.

## Isolated Bridge

Bridge without external connectivity:

```yaml
network:
  version: 2

  bridges:
    br-isolated:
      addresses:
        - 10.10.0.1/24
      # No interfaces listed
      # VMs/containers can communicate with each other
      # but not external network
```

## OpenVSwitch Bridge

For advanced software-defined networking:

```yaml
network:
  version: 2

  bridges:
    ovs-br0:
      openvswitch: {}
      interfaces:
        - enp5s0
      addresses:
        - 192.168.1.100/24
```

Requires Open vSwitch installed:

```bash
sudo apt install openvswitch-switch
```

## Troubleshooting Bridges

### Verify Bridge Creation

```bash
# Check bridge exists
ip link show br0

# Show bridge details
bridge link show

# Show forwarding database
bridge fdb show br0

# Show VLAN info
bridge vlan show
```

### Check Interface Membership

```bash
# Show which interfaces are in bridge
bridge link show master br0

# Alternative
brctl show br0  # Legacy tool
```

### Common Issues

**Bridge has no IP:**

```bash
# Check IP
ip addr show br0

# Verify configuration
cat /etc/netplan/*.yaml | grep -A 10 "br0"
```

**Interface not joining bridge:**

```bash
# Check interface exists
ip link show enp5s0

# Check interface state
ip link show enp5s0 | grep state

# Ensure physical interface has no IP
# (IP should be on bridge, not interface)
```

**Network unreachable after bridge:**

```bash
# Check routes
ip route show

# Verify default gateway is via bridge
# NOT via physical interface
```

## Complete Server Example

```yaml
# /etc/netplan/00-bridge-config.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Physical NIC - no IP, just enslaved to bridge
    enp5s0:
      dhcp4: false
      dhcp6: false

  bridges:
    # Main bridge for VMs and containers
    br0:
      interfaces:
        - enp5s0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        search: [home.local]
        addresses:
          - 192.168.1.1
          - 1.1.1.1
      mtu: 1500
      parameters:
        stp: false
        forward-delay: 0
```

## Migration from Interface to Bridge

### Before (Direct Interface)

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
```

### After (Bridge)

```yaml
network:
  version: 2
  ethernets:
    enp5s0:
      dhcp4: false    # Remove IP config

  bridges:
    br0:
      interfaces:
        - enp5s0      # Add interface to bridge
      addresses:
        - 192.168.1.100/24    # Move IP to bridge
      routes:
        - to: default
          via: 192.168.1.1
```

### Safe Migration

```bash
# 1. Test new config
sudo netplan try

# 2. If connectivity lost, wait for rollback

# 3. If working, confirm
# Press ENTER
```
