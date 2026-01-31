# Static Routes

## Understanding Routes

Routes tell the kernel where to send packets for different destinations. Each route specifies:

- **Destination** - Network or host to reach
- **Gateway** - Next hop to send packets through
- **Interface** - Which interface to use
- **Metric** - Priority when multiple routes exist

```
┌─────────────────────────────────────────────────────────────────┐
│                      Routing Table                               │
├─────────────────────────────────────────────────────────────────┤
│  Destination        Gateway           Interface    Metric       │
├─────────────────────────────────────────────────────────────────┤
│  default            192.168.1.1       eth0         100          │
│  192.168.1.0/24     0.0.0.0 (direct)  eth0         100          │
│  10.0.0.0/8         192.168.1.254     eth0         100          │
│  172.16.0.0/12      192.168.1.253     eth1         200          │
└─────────────────────────────────────────────────────────────────┘
```

## Default Gateway

### Single Default Route

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
```

### Alternative Syntax

```yaml
routes:
  - to: 0.0.0.0/0        # Same as "default"
    via: 192.168.1.1
```

### IPv6 Default

```yaml
routes:
  - to: default
    via: 192.168.1.1

  - to: "::/0"           # IPv6 default
    via: "2001:db8::1"
```

## Static Network Routes

### Route to Specific Network

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

        - to: 10.0.0.0/8
          via: 192.168.1.254

        - to: 172.16.0.0/12
          via: 192.168.1.253
```

### Host Routes

Route to a specific host:

```yaml
routes:
  - to: 10.10.10.50/32    # Single host
    via: 192.168.1.254
```

## Route Options

### Metric (Priority)

Lower metric = higher priority:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
          metric: 100          # Primary

    eth1:
      addresses:
        - 192.168.2.100/24
      routes:
        - to: default
          via: 192.168.2.1
          metric: 200          # Backup
```

### On-Link Routes

When gateway is directly connected (no routing lookup):

```yaml
routes:
  - to: 10.0.0.0/8
    via: 192.168.1.254
    on-link: true          # Gateway is on same segment
```

### Route Table

Use specific routing table:

```yaml
routes:
  - to: 10.0.0.0/8
    via: 192.168.1.254
    table: 100             # Custom table ID
```

### Route Type

```yaml
routes:
  # Blackhole - silently drop
  - to: 192.168.99.0/24
    type: blackhole

  # Unreachable - return ICMP unreachable
  - to: 192.168.98.0/24
    type: unreachable

  # Prohibit - return ICMP prohibited
  - to: 192.168.97.0/24
    type: prohibit

  # Throw - continue searching other tables
  - to: 192.168.96.0/24
    type: throw
```

### Route Scope

```yaml
routes:
  - to: 10.0.0.0/8
    via: 192.168.1.254
    scope: global          # Global route

  - to: 192.168.1.0/24
    scope: link            # Link-local (directly connected)
```

### MTU for Route

```yaml
routes:
  - to: 10.0.0.0/8
    via: 192.168.1.254
    mtu: 1400              # Set path MTU
```

### Congestion Window

```yaml
routes:
  - to: 10.0.0.0/8
    via: 192.168.1.254
    congestion-window: 10  # TCP initial congestion window
    advertised-receive-window: 10
```

## Multi-Path Routing

Load balancing across multiple gateways:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: 10.0.0.0/8
          via: 192.168.1.254
          weight: 1

        - to: 10.0.0.0/8
          via: 192.168.1.253
          weight: 1
```

!!! note "ECMP"
    Equal-Cost Multi-Path (ECMP) requires routes with same destination and metric but different gateways.

## Multiple Interfaces

### Different Networks

```yaml
network:
  version: 2
  ethernets:
    # Management network
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
        - to: 10.10.0.0/16
          via: 192.168.1.254

    # Storage network
    eth1:
      addresses:
        - 10.0.0.100/24
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1
```

### Dual Internet Links

```yaml
network:
  version: 2
  ethernets:
    # Primary ISP
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1
          metric: 100

    # Backup ISP
    eth1:
      addresses:
        - 198.51.100.10/24
      routes:
        - to: default
          via: 198.51.100.1
          metric: 200
```

## DHCP with Static Routes

### Override DHCP Routes

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-routes: false      # Ignore DHCP routes
      routes:
        - to: default
          via: 192.168.1.1     # Use static gateway
        - to: 10.0.0.0/8
          via: 192.168.1.254
```

### Add to DHCP Routes

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-routes: true       # Keep DHCP routes
      routes:
        # Additional static routes
        - to: 172.16.0.0/12
          via: 192.168.1.253
```

## Routes Through VLANs

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.10:
      id: 10
      link: eth0
      addresses:
        - 10.10.0.100/24
      routes:
        - to: default
          via: 10.10.0.1

    eth0.20:
      id: 20
      link: eth0
      addresses:
        - 10.20.0.100/24
      routes:
        - to: 10.20.0.0/16
          via: 10.20.0.1
```

## Routes Through Bridges

```yaml
network:
  version: 2
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
        - to: 10.0.0.0/8
          via: 192.168.1.254
```

## Routes Through Tunnels

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
      local: 203.0.113.10
      remote: 198.51.100.20
      addresses:
        - 10.0.0.1/30
      routes:
        # Remote network via tunnel
        - to: 10.20.0.0/16
          via: 10.0.0.2

        # Another remote network
        - to: 172.16.0.0/16
          via: 10.0.0.2
```

## Verifying Routes

### View Routing Table

```bash
# All routes
ip route show

# Specific table
ip route show table 100

# Routes via specific interface
ip route show dev eth0

# Routes to specific network
ip route show to 10.0.0.0/8
```

### Route Lookup

```bash
# Which route matches destination
ip route get 10.10.10.50

# With source address
ip route get 10.10.10.50 from 192.168.1.100
```

### Route Cache

```bash
# Flush route cache (force new lookups)
ip route flush cache
```

## Troubleshooting Routes

### Route Not Applied

```bash
# Check netplan generation
sudo netplan generate

# Check systemd-networkd logs
journalctl -u systemd-networkd -f

# Verify configuration was generated
cat /run/systemd/network/*netplan*.network
```

### Wrong Gateway Used

```bash
# Check route metrics
ip route show | grep default

# Lower metric wins
# If both routes have same metric, first one wins
```

### Cannot Reach Network

```bash
# Check if route exists
ip route get 10.10.10.50

# Check gateway is reachable
ping 192.168.1.254

# Check interface is up
ip link show eth0

# Trace route
traceroute 10.10.10.50
```

### Asymmetric Routing

When packets go out one path and return another:

```bash
# Check return path
ip route get <source-of-incoming-packet>

# Verify both paths are configured
# May need policy routing
```

## Common Patterns

### Data Center Server

```yaml
network:
  version: 2
  ethernets:
    # Management
    eno1:
      addresses:
        - 10.10.10.50/24
      routes:
        - to: default
          via: 10.10.10.1
        - to: 10.10.0.0/16
          via: 10.10.10.1

    # Application network
    ens192:
      addresses:
        - 10.20.0.50/24
      routes:
        - to: 10.20.0.0/16
          via: 10.20.0.1
          metric: 100

    # Storage network
    ens224:
      addresses:
        - 10.30.0.50/24
      routes:
        - to: 10.30.0.0/24
          metric: 100
      mtu: 9000
```

### Multi-Homed Web Server

```yaml
network:
  version: 2
  ethernets:
    # Public interface
    eth0:
      addresses:
        - 203.0.113.50/24
      routes:
        - to: default
          via: 203.0.113.1
          metric: 100

    # Private backend
    eth1:
      addresses:
        - 10.0.0.50/24
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1
          metric: 100
        - to: 172.16.0.0/12
          via: 10.0.0.1
          metric: 100
```

### VPN Gateway

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.1/24
      routes:
        - to: default
          via: 192.168.1.254

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.1/24
      key: "PRIVATE_KEY"
      routes:
        # All VPN client networks
        - to: 10.10.0.0/16
        - to: 172.16.0.0/16
      peers:
        - keys:
            public: "PEER_KEY"
          allowed-ips:
            - 10.10.10.0/24
            - 172.16.0.0/16
```
