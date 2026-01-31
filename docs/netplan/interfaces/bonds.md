# Bond Configuration

## What is Bonding?

Bonding (also called link aggregation or NIC teaming) combines multiple physical interfaces into one logical interface for:

- **Redundancy** - Failover if one link fails
- **Increased bandwidth** - Aggregate throughput
- **Load balancing** - Distribute traffic across links

```
┌─────────────────────────────────────────────────────────────┐
│                    Bond (bond0)                              │
│                   192.168.1.100/24                          │
│                                                              │
│   ┌──────────────────┐      ┌──────────────────┐           │
│   │      enp5s0      │      │      enp6s0      │           │
│   │   (1 Gbps NIC)   │      │   (1 Gbps NIC)   │           │
│   └────────┬─────────┘      └────────┬─────────┘           │
└────────────┼─────────────────────────┼─────────────────────┘
             │                         │
             └───────────┬─────────────┘
                         │
                    To Switch
                  (2 Gbps combined)
```

## Bond Modes

| Mode | Name | Description | Requires |
|------|------|-------------|----------|
| 0 | balance-rr | Round-robin | Switch support (EtherChannel) |
| 1 | active-backup | Failover only | Nothing |
| 2 | balance-xor | XOR hash balancing | Switch support |
| 3 | broadcast | Send on all slaves | Switch support |
| 4 | 802.3ad | LACP | Switch LACP support |
| 5 | balance-tlb | Adaptive transmit | Nothing |
| 6 | balance-alb | Adaptive load | Nothing |

### Mode Recommendations

| Use Case | Recommended Mode |
|----------|------------------|
| Simple failover | active-backup (1) |
| Maximum throughput with LACP switch | 802.3ad (4) |
| Load balance without switch support | balance-alb (6) |
| Server-to-server direct connect | balance-rr (0) |

## Basic Bond Configuration

### Active-Backup (Failover)

Simplest and most compatible:

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
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        mode: active-backup
        primary: enp5s0
        mii-monitor-interval: 100
```

### LACP (802.3ad)

For managed switches with LACP:

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
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        mode: 802.3ad
        lacp-rate: fast
        mii-monitor-interval: 100
        transmit-hash-policy: layer3+4
```

### Balance-ALB (No Switch Config Needed)

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
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        mode: balance-alb
        mii-monitor-interval: 100
```

## Bond Parameters

### MII Monitor

Link health monitoring:

```yaml
parameters:
  mii-monitor-interval: 100    # Check every 100ms
  up-delay: 200                # Wait 200ms before marking up
  down-delay: 200              # Wait 200ms before marking down
```

### ARP Monitor

Alternative to MII monitoring:

```yaml
parameters:
  arp-interval: 1000           # Check every 1000ms
  arp-ip-targets:
    - 192.168.1.1              # Ping gateway
    - 192.168.1.2              # Ping another host
  arp-validate: all            # Validate on all slaves
  arp-all-targets: all         # All targets must respond
```

### Primary Interface

For active-backup mode:

```yaml
parameters:
  mode: active-backup
  primary: enp5s0              # Preferred active interface
  primary-reselect-policy: always  # Reselect when primary returns
```

Reselect policies:
- `always` - Switch back when primary returns
- `better` - Switch back if primary is better
- `failure` - Only switch on failure

### Hash Policy

For 802.3ad and balance-xor:

```yaml
parameters:
  mode: 802.3ad
  transmit-hash-policy: layer3+4  # Hash by IP + port
```

Hash policies:
- `layer2` - Source/dest MAC
- `layer2+3` - MAC + IP
- `layer3+4` - IP + port (recommended for most cases)
- `encap2+3` - Encapsulated layer 2+3
- `encap3+4` - Encapsulated layer 3+4

### LACP Rate

```yaml
parameters:
  mode: 802.3ad
  lacp-rate: fast    # LACPDUs every 1 second
  # lacp-rate: slow  # LACPDUs every 30 seconds (default)
```

### Fail Over MAC

For active-backup:

```yaml
parameters:
  mode: active-backup
  fail-over-mac-policy: active  # Use active slave's MAC
```

Policies:
- `none` - Bond uses fixed MAC (default)
- `active` - Bond uses active slave's MAC
- `follow` - Each slave uses bond's MAC

## Bond with DHCP

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
      dhcp4: true
      parameters:
        mode: active-backup
        mii-monitor-interval: 100
```

## Bond + Bridge

Common for VM hosts:

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
      # No IP here - IP goes on bridge

  bridges:
    br0:
      interfaces:
        - bond0
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      parameters:
        stp: false
```

## Bond + VLAN

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

  vlans:
    bond0.100:
      id: 100
      link: bond0
      addresses:
        - 192.168.100.1/24

    bond0.200:
      id: 200
      link: bond0
      addresses:
        - 192.168.200.1/24
```

## Bond + VLAN + Bridge

Full stack:

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
    bond0.20:
      id: 20
      link: bond0

  bridges:
    br-mgmt:
      interfaces:
        - bond0.10
      addresses:
        - 192.168.10.100/24
      routes:
        - to: default
          via: 192.168.10.1

    br-vms:
      interfaces:
        - bond0.20
      addresses:
        - 192.168.20.1/24
```

## Verifying Bond Status

```bash
# Check bond status
cat /proc/net/bonding/bond0

# networkctl status
networkctl status bond0

# ip link
ip link show bond0
ip link show enp5s0
ip link show enp6s0

# Check LACP
cat /proc/net/bonding/bond0 | grep -A5 "802.3ad"
```

### Example Bond Status

```
Ethernet Channel Bonding Driver: v5.x

Bonding Mode: IEEE 802.3ad Dynamic link aggregation
Transmit Hash Policy: layer3+4 (1)
MII Status: up
MII Polling Interval (ms): 100
Up Delay (ms): 0
Down Delay (ms): 0

802.3ad info
LACP rate: fast
Min links: 0
Aggregator selection policy (ad_select): stable
System priority: 65535

Slave Interface: enp5s0
MII Status: up
Speed: 1000 Mbps
Duplex: full
Link Failure Count: 0
Aggregator ID: 1

Slave Interface: enp6s0
MII Status: up
Speed: 1000 Mbps
Duplex: full
Link Failure Count: 0
Aggregator ID: 1
```

## Troubleshooting

### Bond Not Forming

```bash
# Check interfaces exist
ip link show

# Check interfaces aren't in use
ip addr show enp5s0
# Should show no IP

# Check kernel module
lsmod | grep bonding
```

### LACP Not Negotiating

```bash
# Check LACP status
cat /proc/net/bonding/bond0 | grep -A10 "802.3ad"

# Verify switch config
# - Port-channel/LAG configured
# - Same LACP mode (active/passive)
# - Same speed on all ports
```

### Failover Not Working

```bash
# Test failover
# Physically disconnect one cable

# Watch bond status
watch cat /proc/net/bonding/bond0

# Check MII status
ip link show enp5s0
```

### Performance Issues

```bash
# Check hash policy
cat /proc/net/bonding/bond0 | grep "Transmit Hash"

# Monitor traffic distribution
# (Requires iftop or similar)
iftop -i bond0
```

## Switch Configuration Reference

### Cisco IOS LACP

```
interface range GigabitEthernet0/1-2
  channel-group 1 mode active
  channel-protocol lacp

interface Port-channel1
  switchport mode trunk
```

### Juniper LACP

```
set interfaces ae0 aggregated-ether-options lacp active
set interfaces ge-0/0/0 ether-options 802.3ad ae0
set interfaces ge-0/0/1 ether-options 802.3ad ae0
```

### Linux Bridge (No Config Needed for balance-alb)

For `balance-alb` mode, no switch configuration needed.
