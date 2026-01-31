# Netplan Property Reference

## Global Properties

### network

Top-level key for all network configuration.

```yaml
network:
  version: 2
  renderer: networkd
```

### version

Schema version. Always `2` for current netplan.

```yaml
network:
  version: 2
```

### renderer

Backend to use. Options: `networkd` (default on server), `NetworkManager` (default on desktop).

```yaml
network:
  version: 2
  renderer: networkd
```

## Common Interface Properties

These apply to all interface types.

### addresses

List of IP addresses with CIDR prefix.

```yaml
addresses:
  - 192.168.1.100/24
  - 10.0.0.100/24
  - "2001:db8::100/64"
```

With options:

```yaml
addresses:
  - 192.168.1.100/24:
      label: "eth0:0"
      lifetime: 0
```

### dhcp4 / dhcp6

Enable DHCP for IPv4/IPv6.

```yaml
dhcp4: true
dhcp6: true
```

### dhcp4-overrides / dhcp6-overrides

Customize DHCP behavior.

```yaml
dhcp4-overrides:
  use-dns: true
  use-ntp: true
  use-hostname: true
  use-mtu: true
  use-routes: true
  use-domains: true
  send-hostname: true
  hostname: myserver
  route-metric: 100
```

### routes

Static routes.

```yaml
routes:
  - to: default
    via: 192.168.1.1

  - to: 10.0.0.0/8
    via: 192.168.1.254
    metric: 100
    on-link: true
    table: 100
    type: unicast
    scope: global
    mtu: 1400
```

Route types: `unicast`, `blackhole`, `unreachable`, `prohibit`, `throw`

### routing-policy

Policy routing rules.

```yaml
routing-policy:
  - from: 10.0.0.0/8
    table: 100
    priority: 100

  - to: 8.8.8.8
    table: 200

  - mark: 1
    table: 300
```

### nameservers

DNS configuration.

```yaml
nameservers:
  search:
    - example.com
    - local
  addresses:
    - 1.1.1.1
    - 8.8.8.8
```

### mtu

Maximum transmission unit.

```yaml
mtu: 1500
# or
mtu: 9000  # Jumbo frames
```

### macaddress

Override MAC address.

```yaml
macaddress: "aa:bb:cc:dd:ee:ff"
```

### wakeonlan

Enable Wake-on-LAN.

```yaml
wakeonlan: true
```

### link-local

Link-local addresses to enable.

```yaml
link-local: [ipv4, ipv6]  # Both (default)
link-local: [ipv6]         # IPv6 only
link-local: []             # Disable
```

### optional

Don't wait for interface during boot.

```yaml
optional: true
```

### accept-ra

Accept Router Advertisements (IPv6).

```yaml
accept-ra: true
```

### ipv6-address-generation

IPv6 address generation mode.

```yaml
ipv6-address-generation: eui64
# or
ipv6-address-generation: stable-privacy
```

### ipv6-privacy

Enable IPv6 privacy extensions.

```yaml
ipv6-privacy: true
```

## Ethernet Properties

### match

Match criteria for interface.

```yaml
match:
  name: "en*"
  macaddress: "aa:bb:cc:dd:ee:ff"
  driver: "e1000*"
```

### set-name

Rename matched interface.

```yaml
match:
  macaddress: "aa:bb:cc:dd:ee:ff"
set-name: eth0
```

### Offload Features

```yaml
receive-checksum-offload: true
transmit-checksum-offload: true
tcp-segmentation-offload: true
generic-segmentation-offload: true
generic-receive-offload: true
large-receive-offload: false
```

## Bridge Properties

### interfaces

Member interfaces.

```yaml
bridges:
  br0:
    interfaces:
      - eth0
      - eth1
```

### parameters

Bridge-specific settings.

```yaml
parameters:
  stp: false
  forward-delay: 0
  hello-time: 2
  max-age: 20
  priority: 32768
  ageing-time: 300
  path-cost:
    eth0: 100
  port-priority:
    eth0: 32
```

### openvswitch

Use Open vSwitch.

```yaml
openvswitch: {}
```

## Bond Properties

### interfaces

Member interfaces.

```yaml
bonds:
  bond0:
    interfaces:
      - eth0
      - eth1
```

### parameters

Bond-specific settings.

```yaml
parameters:
  mode: 802.3ad
  lacp-rate: fast
  mii-monitor-interval: 100
  min-links: 1
  transmit-hash-policy: layer3+4
  ad-select: stable
  all-slaves-active: false
  arp-interval: 0
  arp-ip-targets: []
  arp-validate: none
  arp-all-targets: any
  up-delay: 0
  down-delay: 0
  fail-over-mac-policy: none
  gratuitious-arp: 1
  packets-per-slave: 1
  primary: eth0
  primary-reselect-policy: always
  resend-igmp: 1
  learn-packet-interval: 1
```

Bond modes:
- `balance-rr` (0)
- `active-backup` (1)
- `balance-xor` (2)
- `broadcast` (3)
- `802.3ad` (4)
- `balance-tlb` (5)
- `balance-alb` (6)

## VLAN Properties

### id

VLAN ID (1-4094).

```yaml
vlans:
  vlan100:
    id: 100
    link: eth0
```

### link

Parent interface.

```yaml
vlans:
  eth0.100:
    id: 100
    link: eth0
```

## WiFi Properties

### access-points

WiFi networks to connect.

```yaml
wifis:
  wlan0:
    access-points:
      "NetworkName":
        password: "secret"
        hidden: false
        band: 5GHz
        bssid: "aa:bb:cc:dd:ee:ff"
        mode: infrastructure
```

### auth

Enterprise authentication.

```yaml
access-points:
  "Enterprise":
    auth:
      key-management: eap
      method: peap
      identity: "user@domain"
      password: "secret"
      anonymous-identity: "anon"
      ca-certificate: /path/to/ca.pem
      client-certificate: /path/to/client.pem
      client-key: /path/to/key.pem
      client-key-password: "keypass"
```

## Tunnel Properties

### mode

Tunnel type.

```yaml
tunnels:
  tun0:
    mode: gre
```

Modes: `gre`, `gretap`, `ip6gre`, `ip6gretap`, `ipip`, `ipip6`, `ip6ip6`, `sit`, `vti`, `vti6`, `vxlan`, `wireguard`

### local / remote

Tunnel endpoints.

```yaml
tunnels:
  gre1:
    mode: gre
    local: 192.168.1.100
    remote: 192.168.2.100
```

### WireGuard

```yaml
tunnels:
  wg0:
    mode: wireguard
    key: "BASE64_PRIVATE_KEY"
    port: 51820
    mark: 0
    peers:
      - keys:
          public: "PEER_PUBLIC_KEY"
        allowed-ips:
          - 10.0.0.0/8
        endpoint: "peer.example.com:51820"
        keepalive: 25
```

### VXLAN

```yaml
tunnels:
  vxlan100:
    mode: vxlan
    id: 100
    local: 192.168.1.100
    remote: 192.168.1.101
    port: 4789
    ageing: 300
    limit: 0
    type-of-service: inherit
    mac-learning: true
    short-circuit: false
    notifications:
      - l2-miss
      - l3-miss
```

## VRF Properties

```yaml
vrfs:
  vrf-mgmt:
    table: 100
    interfaces:
      - eth0
    routes:
      - to: default
        via: 192.168.1.1
        table: 100
    routing-policy:
      - from: 192.168.1.0/24
        table: 100
```

## Dummy Devices

```yaml
dummy-devices:
  dummy0:
    addresses:
      - 10.255.255.1/32
```

## Backend-Specific Options

### networkd

```yaml
networkd:
  RequiredForOnline: no
```

### NetworkManager

```yaml
networkmanager:
  uuid: "12345678-1234-1234-1234-123456789abc"
  name: "My Connection"
  passthrough:
    connection.autoconnect-priority: "100"
    wifi.powersave: "2"
```

## SR-IOV

```yaml
ethernets:
  enp5s0:
    embedded-switch-mode: switchdev
    delay-virtual-functions-rebind: true
    virtual-function-count: 4
    link: enp5s0f0
```
