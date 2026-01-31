# Ethernet Configuration

## Basic Configuration

### DHCP (Dynamic IP)

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
```

### Static IP

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
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
```

### Dual Stack (IPv4 + IPv6)

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp6: true
```

### Static Dual Stack

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - "2001:db8::100/64"
      routes:
        - to: default
          via: 192.168.1.1
        - to: default
          via: "2001:db8::1"
      nameservers:
        addresses:
          - 1.1.1.1
          - "2001:4860:4860::8888"
```

## Interface Identification

### By Device Name

Most common, uses predictable naming:

```yaml
ethernets:
  enp5s0:           # PCI bus 5, slot 0
    dhcp4: true

  eno1:             # Onboard port 1
    dhcp4: true

  ens192:           # VMware interface
    dhcp4: true
```

### By MAC Address

Identify specific hardware:

```yaml
ethernets:
  server-nic:
    match:
      macaddress: "aa:bb:cc:dd:ee:ff"
    dhcp4: true
```

### By Driver

Match all interfaces using a driver:

```yaml
ethernets:
  intel-nics:
    match:
      driver: "e1000*"
    dhcp4: true
```

### Rename Interface

```yaml
ethernets:
  main:
    match:
      macaddress: "aa:bb:cc:dd:ee:ff"
    set-name: eth0       # Rename to eth0
    dhcp4: true
```

## Multiple Addresses

### Primary and Secondary

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24    # Primary
      - 192.168.1.101/24    # Secondary
      - 192.168.1.102/24    # Another secondary
```

### Different Subnets

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24
      - 10.0.0.100/24
    routes:
      - to: default
        via: 192.168.1.1
```

### With Labels

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24:
          label: "eth0:0"
      - 192.168.1.101/24:
          label: "eth0:1"
```

## DHCP Options

### Basic DHCP Customization

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      use-dns: true         # Use DHCP DNS
      use-ntp: true         # Use DHCP NTP
      use-hostname: true    # Set hostname from DHCP
      use-mtu: true         # Use DHCP MTU
      use-routes: true      # Use DHCP routes
      use-domains: true     # Use DHCP search domains
      send-hostname: true   # Send hostname to server
```

### Route Metric

Control route priority:

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      route-metric: 100      # Lower = higher priority

  eth1:
    dhcp4: true
    dhcp4-overrides:
      route-metric: 200      # Backup route
```

### Custom Hostname

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      send-hostname: true
      hostname: myserver     # Send this hostname
```

### Ignore DHCP Options

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      use-dns: false        # Use static DNS instead
      use-routes: false     # Use static routes instead
    nameservers:
      addresses: [1.1.1.1]
    routes:
      - to: default
        via: 192.168.1.1
```

## DNS Configuration

### Static DNS Servers

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24
    nameservers:
      addresses:
        - 192.168.1.1       # Local
        - 1.1.1.1           # Cloudflare
        - 8.8.8.8           # Google
```

### Search Domains

```yaml
ethernets:
  eth0:
    dhcp4: true
    nameservers:
      search:
        - example.com
        - internal.example.com
      addresses:
        - 192.168.1.1
```

### DHCP with DNS Override

```yaml
ethernets:
  eth0:
    dhcp4: true
    dhcp4-overrides:
      use-dns: false        # Ignore DHCP DNS
    nameservers:
      addresses:
        - 1.1.1.1           # Use Cloudflare instead
```

## Routing

### Default Gateway

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24
    routes:
      - to: default
        via: 192.168.1.1
```

### Multiple Routes

```yaml
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

### Route Options

```yaml
ethernets:
  eth0:
    addresses:
      - 192.168.1.100/24
    routes:
      - to: 10.0.0.0/8
        via: 192.168.1.254
        metric: 100          # Priority
        on-link: true        # Gateway is on-link
        table: 100           # Routing table
```

## Link Properties

### MTU

```yaml
ethernets:
  eth0:
    dhcp4: true
    mtu: 1500            # Standard

  eth1:
    dhcp4: true
    mtu: 9000            # Jumbo frames
```

### MAC Address Override

```yaml
ethernets:
  eth0:
    macaddress: "aa:bb:cc:dd:ee:ff"
    dhcp4: true
```

### Wake-on-LAN

```yaml
ethernets:
  eth0:
    wakeonlan: true
    dhcp4: true
```

### Link-Local Addresses

```yaml
ethernets:
  eth0:
    dhcp4: true
    link-local: [ipv4, ipv6]   # Enable both

  eth1:
    dhcp4: true
    link-local: []              # Disable link-local
```

## Boot Behavior

### Optional Interface

Don't wait for this interface at boot:

```yaml
ethernets:
  eth0:
    dhcp4: true
    optional: true       # Boot continues without this
```

### Critical Interface

Default behavior - wait for interface:

```yaml
ethernets:
  eth0:
    dhcp4: true
    optional: false      # Wait for this (default)
```

### Activation Mode

```yaml
ethernets:
  eth0:
    dhcp4: true
    activation-mode: manual  # Don't auto-bring-up
```

## Hardware Settings

### Offloading

```yaml
ethernets:
  eth0:
    dhcp4: true
    receive-checksum-offload: true
    transmit-checksum-offload: true
    tcp-segmentation-offload: true
    generic-segmentation-offload: true
    generic-receive-offload: true
    large-receive-offload: true
```

### Ring Buffers

```yaml
ethernets:
  eth0:
    dhcp4: true
    ring:
      rx: 4096
      tx: 4096
```

## Multiple NICs

### Different Roles

```yaml
network:
  version: 2
  ethernets:
    # Management network
    eno1:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [192.168.1.1]

    # Storage network
    enp5s0:
      addresses:
        - 10.0.0.100/24
      mtu: 9000
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1

    # VM network (no IP on host)
    enp6s0:
      dhcp4: false
      dhcp6: false
```

### Failover with Metrics

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 100      # Primary

    eth1:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 200      # Failover
```

## Server Examples

### Basic Server

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        search: [home.local]
        addresses: [192.168.1.1, 1.1.1.1]
```

### Multi-Homed Server

```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    # Public interface
    enp1s0:
      addresses:
        - 203.0.113.100/24
      routes:
        - to: default
          via: 203.0.113.1
      nameservers:
        addresses: [1.1.1.1]

    # Private interface
    enp2s0:
      addresses:
        - 10.0.0.100/24
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1
          metric: 100
```

### DHCP Fallback to Static

```yaml
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true
      addresses:
        - 192.168.1.100/24    # Used if DHCP fails
```
