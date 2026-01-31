# VLAN Configuration

## What are VLANs?

VLANs (Virtual LANs) segment a physical network into multiple logical networks at Layer 2. Each VLAN acts as a separate broadcast domain.

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Physical Interface (enp5s0)                      │
│                        Trunk Port (Tagged)                          │
│                                                                      │
│   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐           │
│   │  VLAN 10     │   │  VLAN 20     │   │  VLAN 30     │           │
│   │  Management  │   │  Servers     │   │  Storage     │           │
│   │ 10.10.10.0/24│   │ 10.10.20.0/24│   │ 10.10.30.0/24│           │
│   └──────────────┘   └──────────────┘   └──────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

## Use Cases

| Use Case | Description |
|----------|-------------|
| Network segmentation | Separate management, data, storage traffic |
| Multi-tenant | Isolate customer/department traffic |
| Security zones | Separate trusted/untrusted networks |
| VM networking | Provide multiple networks to hypervisors |

## Basic VLAN Configuration

### Single VLAN

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  vlans:
    vlan10:
      id: 10
      link: enp5s0
      addresses:
        - 10.10.10.100/24
      routes:
        - to: default
          via: 10.10.10.1
```

### Multiple VLANs

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false
      # No IP on physical interface

  vlans:
    vlan10:
      id: 10
      link: enp5s0
      addresses:
        - 10.10.10.100/24
      nameservers:
        addresses: [10.10.10.1]

    vlan20:
      id: 20
      link: enp5s0
      addresses:
        - 10.10.20.100/24

    vlan30:
      id: 30
      link: enp5s0
      addresses:
        - 10.10.30.100/24
      mtu: 9000  # Jumbo frames for storage
```

## VLAN Naming Conventions

### Interface.ID Format

```yaml
vlans:
  enp5s0.10:        # Traditional format
    id: 10
    link: enp5s0
    addresses:
      - 10.10.10.100/24
```

### Descriptive Names

```yaml
vlans:
  vlan-mgmt:        # Clear purpose
    id: 10
    link: enp5s0
    addresses:
      - 10.10.10.100/24

  vlan-storage:
    id: 30
    link: enp5s0
    addresses:
      - 10.10.30.100/24
```

### By Purpose

```yaml
vlans:
  management:
    id: 10
    link: enp5s0

  production:
    id: 20
    link: enp5s0

  backup:
    id: 100
    link: enp5s0
```

## VLAN with DHCP

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  vlans:
    vlan10:
      id: 10
      link: enp5s0
      dhcp4: true
      dhcp4-overrides:
        use-dns: true
        use-routes: true
```

## VLAN on Bond

Common in production servers:

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false
    enp6s0:
      dhcp4: false

  bonds:
    bond0:
      interfaces:
        - enp5s0
        - enp6s0
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4

  vlans:
    bond0.10:
      id: 10
      link: bond0
      addresses:
        - 10.10.10.100/24
      routes:
        - to: default
          via: 10.10.10.1

    bond0.20:
      id: 20
      link: bond0
      addresses:
        - 10.10.20.100/24

    bond0.30:
      id: 30
      link: bond0
      addresses:
        - 10.10.30.100/24
      mtu: 9000
```

## VLAN with Bridge

For VM networking:

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
    br-mgmt:
      interfaces:
        - enp5s0.10
      addresses:
        - 10.10.10.1/24
      parameters:
        stp: false

    br-vms:
      interfaces:
        - enp5s0.20
      addresses:
        - 10.10.20.1/24
      parameters:
        stp: false
```

## Full Stack: Bond + VLAN + Bridge

Production hypervisor setup:

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    enp5s0:
      dhcp4: false
    enp6s0:
      dhcp4: false

  bonds:
    bond0:
      interfaces:
        - enp5s0
        - enp6s0
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4

  vlans:
    bond0.10:
      id: 10
      link: bond0

    bond0.20:
      id: 20
      link: bond0

    bond0.100:
      id: 100
      link: bond0

  bridges:
    # Management bridge - host IP
    br-mgmt:
      interfaces:
        - bond0.10
      addresses:
        - 10.10.10.100/24
      routes:
        - to: default
          via: 10.10.10.1
      nameservers:
        addresses: [10.10.10.1, 1.1.1.1]
      parameters:
        stp: false
        forward-delay: 0

    # VM production network
    br-prod:
      interfaces:
        - bond0.20
      # No IP - VMs get IPs from DHCP
      parameters:
        stp: false

    # Storage/backup network
    br-storage:
      interfaces:
        - bond0.100
      addresses:
        - 10.10.100.100/24
      mtu: 9000
      parameters:
        stp: false
```

## Native VLAN (Untagged)

For hybrid tagged/untagged setup:

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false
      # Untagged traffic (native VLAN)
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

  vlans:
    # Tagged VLANs
    enp5s0.10:
      id: 10
      link: enp5s0
      addresses:
        - 10.10.10.100/24

    enp5s0.20:
      id: 20
      link: enp5s0
      addresses:
        - 10.10.20.100/24
```

## VLAN MTU

### Jumbo Frames for Storage VLAN

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false
      mtu: 9000  # Physical must support jumbo

  vlans:
    enp5s0.10:
      id: 10
      link: enp5s0
      mtu: 1500  # Standard for management
      addresses:
        - 10.10.10.100/24

    enp5s0.30:
      id: 30
      link: enp5s0
      mtu: 9000  # Jumbo for storage
      addresses:
        - 10.10.30.100/24
```

!!! warning "MTU Considerations"
    VLAN MTU cannot exceed parent interface MTU. Set physical MTU to the largest needed value.

## VLAN MAC Address

Override the VLAN interface MAC:

```yaml
vlans:
  vlan10:
    id: 10
    link: enp5s0
    macaddress: "aa:bb:cc:dd:ee:ff"
    addresses:
      - 10.10.10.100/24
```

## QinQ (VLAN Stacking)

Double-tagged VLANs for service providers:

```yaml
network:
  version: 2

  ethernets:
    enp5s0:
      dhcp4: false

  vlans:
    # Outer VLAN (S-VLAN)
    enp5s0.100:
      id: 100
      link: enp5s0

    # Inner VLAN (C-VLAN) on outer VLAN
    enp5s0.100.10:
      id: 10
      link: enp5s0.100
      addresses:
        - 10.10.10.100/24
```

## Verifying VLAN Configuration

### Check VLAN Interfaces

```bash
# List VLAN interfaces
ip -d link show type vlan

# Specific VLAN details
ip -d link show enp5s0.10
```

Output:

```
5: enp5s0.10@enp5s0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    link/ether aa:bb:cc:dd:ee:ff brd ff:ff:ff:ff:ff:ff
    vlan protocol 802.1Q id 10 <REORDER_HDR>
```

### Check IP Addresses

```bash
ip addr show enp5s0.10
```

### Check Routing

```bash
# Routes via VLAN interface
ip route show dev enp5s0.10
```

### VLAN Statistics

```bash
# Traffic statistics
ip -s link show enp5s0.10

# Kernel VLAN info
cat /proc/net/vlan/enp5s0.10
```

## Troubleshooting VLANs

### VLAN Not Getting Traffic

```bash
# Check switch configuration
# - Port must be trunk or access with correct VLAN

# Check VLAN is up
ip link show enp5s0.10 | grep "state UP"

# Check parent interface is up
ip link show enp5s0 | grep "state UP"

# Check 802.1Q module
lsmod | grep 8021q
```

### Wrong VLAN ID

```bash
# Verify VLAN ID
ip -d link show enp5s0.10 | grep "vlan.*id"
```

### MTU Issues

```bash
# Check MTU on VLAN
ip link show enp5s0.10 | grep mtu

# Check parent MTU
ip link show enp5s0 | grep mtu

# VLAN MTU must be <= parent MTU
```

### No Connectivity Between VLANs

VLANs are isolated by design. For inter-VLAN routing:

```bash
# Option 1: Router on a stick (external router)
# Configure switch to send all VLANs to router

# Option 2: Linux routing (this host)
# Enable IP forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# Add routes between VLANs (or use firewall rules)
```

## Switch Configuration Reference

### Cisco IOS Trunk Port

```
interface GigabitEthernet0/1
  switchport mode trunk
  switchport trunk allowed vlan 10,20,30
  switchport trunk native vlan 1
```

### Juniper Trunk Port

```
set interfaces ge-0/0/0 unit 0 family ethernet-switching port-mode trunk
set interfaces ge-0/0/0 unit 0 family ethernet-switching vlan members [vlan10 vlan20 vlan30]
```

### Linux Bridge VLAN Filtering

```bash
# Enable VLAN filtering on bridge
ip link set br0 type bridge vlan_filtering 1

# Add VLAN to bridge port
bridge vlan add dev enp5s0 vid 10

# Show VLAN configuration
bridge vlan show
```

## Server Network Design Example

### Multi-Role Server

```yaml
# /etc/netplan/00-server-vlans.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Main trunk interface
    enp5s0:
      dhcp4: false

    # Dedicated management (could be separate NIC)
    eno1:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]

  vlans:
    # Application network
    vlan-app:
      id: 10
      link: enp5s0
      addresses:
        - 10.10.10.100/24

    # Database network
    vlan-db:
      id: 20
      link: enp5s0
      addresses:
        - 10.10.20.100/24

    # Backup network
    vlan-backup:
      id: 100
      link: enp5s0
      addresses:
        - 10.10.100.100/24
      mtu: 9000

    # Monitoring network
    vlan-mon:
      id: 200
      link: enp5s0
      addresses:
        - 10.10.200.100/24
```

### Hypervisor with Guest VLANs

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    enp5s0:
      dhcp4: false
    enp6s0:
      dhcp4: false

  bonds:
    bond0:
      interfaces: [enp5s0, enp6s0]
      parameters:
        mode: 802.3ad
        lacp-rate: fast

  vlans:
    # Host management
    bond0.10:
      id: 10
      link: bond0

    # Guest network 1
    bond0.100:
      id: 100
      link: bond0

    # Guest network 2
    bond0.200:
      id: 200
      link: bond0

  bridges:
    # Host uses this bridge
    br-mgmt:
      interfaces: [bond0.10]
      addresses:
        - 10.10.10.50/24
      routes:
        - to: default
          via: 10.10.10.1
      parameters:
        stp: false

    # VMs connect to these bridges
    br-guest1:
      interfaces: [bond0.100]
      parameters:
        stp: false

    br-guest2:
      interfaces: [bond0.200]
      parameters:
        stp: false
```
