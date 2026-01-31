# Netplan YAML Syntax

## YAML Fundamentals

### Indentation

YAML uses spaces for indentation (never tabs):

```yaml
# CORRECT - 2 spaces per level
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true

# WRONG - tabs
network:
	version: 2    # Tab character causes error!
```

### Data Types

```yaml
# Strings
network:
  version: 2

# Strings with special characters (quote them)
nameservers:
  search: ["example.com"]

# Booleans
dhcp4: true
dhcp6: false
optional: yes    # yes/no also work

# Integers
mtu: 1500
vlan:
  id: 100

# Lists (block style)
addresses:
  - 192.168.1.100/24
  - 192.168.1.101/24

# Lists (inline style)
addresses: [192.168.1.100/24, 192.168.1.101/24]

# Dictionaries/Maps (block style)
nameservers:
  addresses:
    - 1.1.1.1
    - 8.8.8.8
  search:
    - example.com

# Dictionaries (inline style)
nameservers: {addresses: [1.1.1.1], search: [example.com]}
```

### Comments

```yaml
network:
  version: 2
  # This is a comment
  ethernets:
    eth0:
      dhcp4: true  # Inline comment
```

## Netplan Schema

### Top-Level Structure

```yaml
network:
  version: 2          # Required: Schema version
  renderer: networkd  # Optional: Backend

  ethernets: {}       # Physical Ethernet
  bridges: {}         # Bridge devices
  bonds: {}           # Bond devices
  vlans: {}           # VLAN devices
  wifis: {}           # Wireless devices
  tunnels: {}         # Tunnel devices (VPN, etc.)
  vrfs: {}            # VRF devices
  nm-devices: {}      # NetworkManager-only devices
  modems: {}          # Mobile broadband modems
```

### Interface Definition

```yaml
ethernets:
  # Interface name as key
  eth0:
    # Configuration here

  # Or use match
  all-ethernet:
    match:
      name: "en*"
    # Configuration here
```

## Common Properties

### Addressing

```yaml
ethernets:
  eth0:
    # DHCP
    dhcp4: true
    dhcp6: true

    # Static addresses (list)
    addresses:
      - 192.168.1.100/24
      - "2001:db8::100/64"

    # Gateway (deprecated but still works)
    gateway4: 192.168.1.1

    # Routes (preferred way)
    routes:
      - to: default
        via: 192.168.1.1
```

### DHCP Options

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      use-dns: true           # Use DHCP-provided DNS
      use-ntp: true           # Use DHCP-provided NTP
      use-hostname: true      # Set hostname from DHCP
      use-mtu: true           # Use DHCP-provided MTU
      use-routes: true        # Use DHCP-provided routes
      use-domains: true       # Use DHCP search domains
      send-hostname: true     # Send hostname to DHCP server
      hostname: myserver      # Specific hostname to send
      route-metric: 100       # Route priority

    dhcp6-overrides:
      use-dns: true
      use-ntp: true
```

### DNS Configuration

```yaml
ethernets:
  eth0:
    nameservers:
      search:
        - example.com
        - local
      addresses:
        - 192.168.1.1
        - 1.1.1.1
        - "2001:4860:4860::8888"
```

### Routes

```yaml
ethernets:
  eth0:
    routes:
      # Default gateway
      - to: default
        via: 192.168.1.1

      # Specific network
      - to: 10.0.0.0/8
        via: 192.168.1.254

      # With options
      - to: 172.16.0.0/12
        via: 192.168.1.254
        metric: 200
        on-link: true

      # Table-based routing
      - to: 192.168.100.0/24
        via: 192.168.1.253
        table: 100
```

### Routing Policy

```yaml
ethernets:
  eth0:
    routing-policy:
      - from: 192.168.1.0/24
        table: 100
        priority: 100

      - to: 10.0.0.0/8
        table: 200

      - mark: 1
        table: 300
```

### Link Properties

```yaml
ethernets:
  eth0:
    mtu: 9000                    # Maximum transmission unit
    macaddress: "aa:bb:cc:dd:ee:ff"  # Override MAC
    wakeonlan: true              # Enable WoL
    link-local: [ipv4, ipv6]     # Link-local addresses
    optional: true               # Don't wait for this at boot
```

## Interface Types

### Ethernet

```yaml
ethernets:
  eth0:
    dhcp4: true

  # With match
  mainnic:
    match:
      macaddress: "aa:bb:cc:dd:ee:ff"
    set-name: eth0
    dhcp4: true
```

### Bridge

```yaml
bridges:
  br0:
    interfaces:
      - eth0
      - eth1
    addresses:
      - 192.168.1.100/24
    routes:
      - to: default
        via: 192.168.1.1
    parameters:
      stp: false
      forward-delay: 0
      max-age: 0
      hello-time: 0
      priority: 32768
```

### Bond

```yaml
bonds:
  bond0:
    interfaces:
      - eth0
      - eth1
    addresses:
      - 192.168.1.100/24
    parameters:
      mode: 802.3ad
      lacp-rate: fast
      mii-monitor-interval: 100
      transmit-hash-policy: layer3+4
      primary: eth0
```

### VLAN

```yaml
vlans:
  vlan100:
    id: 100
    link: eth0
    addresses:
      - 192.168.100.1/24

  vlan-mgmt:
    id: 10
    link: bond0
    addresses:
      - 10.10.10.1/24
```

### WiFi

```yaml
wifis:
  wlan0:
    access-points:
      "NetworkName":
        password: "secret"

      "OpenNetwork": {}

      "EnterpriseNetwork":
        auth:
          key-management: eap
          method: peap
          identity: "user@example.com"
          password: "secret"

    dhcp4: true
```

### Tunnel

```yaml
tunnels:
  gre1:
    mode: gre
    remote: 203.0.113.1
    local: 192.168.1.100
    addresses:
      - 10.0.0.1/30

  wg0:
    mode: wireguard
    addresses:
      - 10.10.10.1/24
    key: "private-key-here"
    peers:
      - keys:
          public: "peer-public-key"
        allowed-ips: [10.10.10.0/24]
        endpoint: "peer.example.com:51820"
```

## Match Patterns

### By Name

```yaml
ethernets:
  alleth:
    match:
      name: "eth*"        # Glob pattern
    dhcp4: true

  specific:
    match:
      name: "enp[0-9]s0"  # Regex-like
    dhcp4: true
```

### By MAC Address

```yaml
ethernets:
  mymac:
    match:
      macaddress: "aa:bb:cc:dd:ee:ff"
    set-name: eth0
    dhcp4: true
```

### By Driver

```yaml
ethernets:
  virtio-nics:
    match:
      driver: virtio*
    dhcp4: true
```

### Combined Match

```yaml
ethernets:
  specific:
    match:
      name: "en*"
      driver: "e1000"
    dhcp4: true
```

## Advanced Features

### Multiple Files

```yaml
# /etc/netplan/00-base.yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true

# /etc/netplan/10-bridge.yaml
network:
  version: 2
  bridges:
    br0:
      interfaces: [eth0]
```

### Renderer-Specific Options

```yaml
ethernets:
  eth0:
    dhcp4: true

    # For networkd
    networkd:
      RequiredForOnline: no

    # For NetworkManager
    networkmanager:
      passthrough:
        connection.autoconnect-priority: "100"
```

### Openvswitch

```yaml
bridges:
  ovs-br0:
    openvswitch: {}
    interfaces:
      - eth0
```

### SR-IOV

```yaml
ethernets:
  enp5s0:
    embedded-switch-mode: switchdev
    sriov-link: enp5s0f0

  enp5s0f0v0:
    dhcp4: true
```

## Validation

### Check Syntax

```bash
# Parse and validate
sudo netplan generate

# With debug output
sudo netplan --debug generate

# Dry run (show what would be generated)
sudo netplan generate --mapping
```

### Common Errors

```yaml
# ERROR: Missing version
network:
  ethernets:
    eth0:
      dhcp4: true

# ERROR: Address without CIDR
addresses:
  - 192.168.1.100    # Missing /24

# ERROR: Tabs instead of spaces
network:
	version: 2       # Tab!

# ERROR: Wrong indentation
network:
  version: 2
 ethernets:          # Only 1 space
```

## Best Practices

### Use Explicit Version

```yaml
network:
  version: 2  # Always include
```

### Use Explicit Renderer

```yaml
network:
  version: 2
  renderer: networkd  # Don't rely on default
```

### Quote Special Values

```yaml
# Quote MAC addresses
macaddress: "aa:bb:cc:dd:ee:ff"

# Quote SSIDs with spaces
access-points:
  "My Network":
    password: "secret"
```

### Use Meaningful Names

```yaml
bridges:
  br-vms:        # Clear purpose
    interfaces: [enp5s0]

vlans:
  vlan-mgmt:     # Clear purpose
    id: 10
```
