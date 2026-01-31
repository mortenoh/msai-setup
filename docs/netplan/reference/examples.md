# Complete Configuration Examples

## Desktop/Workstation

### Basic Desktop

```yaml
# Simple desktop with DHCP
network:
  version: 2
  renderer: NetworkManager

  ethernets:
    enp5s0:
      dhcp4: true
```

### Desktop with WiFi and Ethernet

```yaml
network:
  version: 2
  renderer: NetworkManager

  ethernets:
    enp5s0:
      dhcp4: true
      dhcp4-overrides:
        route-metric: 100    # Prefer wired

  wifis:
    wlp4s0:
      access-points:
        "HomeNetwork":
          password: "wifipassword"
      dhcp4: true
      dhcp4-overrides:
        route-metric: 200    # Fallback to WiFi
```

## Server Configurations

### Basic Web Server

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
        search: [local.domain]
        addresses:
          - 1.1.1.1
          - 8.8.8.8
```

### Database Server (Dual Network)

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Frontend network
    enp5s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]

    # Backend/replication network
    enp6s0:
      addresses:
        - 10.0.0.100/24
      mtu: 9000
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1
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
        - 203.0.113.50/24
      routes:
        - to: default
          via: 203.0.113.1
          metric: 100
      nameservers:
        addresses: [1.1.1.1]

    # Management interface
    enp2s0:
      addresses:
        - 10.10.10.50/24
      routes:
        - to: 10.0.0.0/8
          via: 10.10.10.1

    # Storage network
    enp3s0:
      addresses:
        - 10.20.0.50/24
      mtu: 9000
```

## Virtualization Hosts

### KVM Host with Bridge

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

### KVM Host with Bond + VLANs

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
    br-mgmt:
      interfaces:
        - bond0.10
      addresses:
        - 10.10.10.100/24
      routes:
        - to: default
          via: 10.10.10.1
      nameservers:
        addresses: [10.10.10.1]
      parameters:
        stp: false
        forward-delay: 0

    br-vms:
      interfaces:
        - bond0.20
      parameters:
        stp: false

    br-storage:
      interfaces:
        - bond0.100
      addresses:
        - 10.100.0.100/24
      mtu: 9000
      parameters:
        stp: false
```

### Docker Host

```yaml
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
        addresses: [1.1.1.1, 8.8.8.8]
      parameters:
        stp: false
        forward-delay: 0
```

## High Availability

### Active-Backup Bond

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
      nameservers:
        addresses: [1.1.1.1]
      parameters:
        mode: active-backup
        primary: enp5s0
        mii-monitor-interval: 100
```

### Dual ISP Failover

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Primary ISP
    enp1s0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1
          metric: 100
      nameservers:
        addresses: [203.0.113.1]

    # Backup ISP
    enp2s0:
      addresses:
        - 198.51.100.10/24
      routes:
        - to: default
          via: 198.51.100.1
          metric: 200
```

## VPN Configurations

### WireGuard VPN Server

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.1/24
      key: "SERVER_PRIVATE_KEY_BASE64"
      port: 51820
      peers:
        - keys:
            public: "CLIENT1_PUBLIC_KEY"
          allowed-ips:
            - 10.10.10.2/32
        - keys:
            public: "CLIENT2_PUBLIC_KEY"
          allowed-ips:
            - 10.10.10.3/32
```

### WireGuard VPN Client

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: true

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.2/24
      key: "CLIENT_PRIVATE_KEY_BASE64"
      routes:
        - to: 10.0.0.0/8
          via: 10.10.10.1
      peers:
        - keys:
            public: "SERVER_PUBLIC_KEY"
          allowed-ips:
            - 10.0.0.0/8
          endpoint: "vpn.example.com:51820"
          keepalive: 25
```

## Cloud/Provider Specific

### AWS EC2

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    ens5:
      dhcp4: true
      dhcp4-overrides:
        use-dns: true
        use-routes: true
```

### Azure VM

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      dhcp4: true
      dhcp4-overrides:
        use-routes: true
        use-dns: true
        use-hostname: true
```

### Google Cloud

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    ens4:
      dhcp4: true
```

### DigitalOcean

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Public interface
    eth0:
      addresses:
        - 1.2.3.4/20
      routes:
        - to: default
          via: 1.2.3.1
      nameservers:
        addresses: [67.207.67.2, 67.207.67.3]

    # Private interface
    eth1:
      addresses:
        - 10.132.0.2/16
```

## Advanced Configurations

### Policy Routing

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - 10.0.0.100/24
      routes:
        - to: default
          via: 192.168.1.1
          table: main
        - to: default
          via: 10.0.0.1
          table: 100

      routing-policy:
        - from: 10.0.0.0/8
          table: 100
```

### IPv6-Only with NAT64

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      accept-ra: true
      dhcp6: true
      link-local: [ipv6]
      nameservers:
        addresses:
          - "2001:db8::64"    # NAT64 DNS server
```

### Full Dual-Stack

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - "2001:db8::100/64"
      routes:
        - to: default
          via: 192.168.1.1
        - to: "::/0"
          via: "2001:db8::1"
      nameservers:
        addresses:
          - 1.1.1.1
          - "2606:4700:4700::1111"
          - 8.8.8.8
          - "2001:4860:4860::8888"
```

## Container/Microservices

### Kubernetes Node

```yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    # Node network
    enp5s0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]

    # Pod network (often managed by CNI)
    enp6s0:
      dhcp4: false
```

### LXD Host

```yaml
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
