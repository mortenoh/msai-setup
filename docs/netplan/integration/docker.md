# Docker Network Integration

## Overview

Docker creates its own network infrastructure that interacts with netplan-managed interfaces. Understanding this interaction is crucial for:

- Exposing container services
- Container-to-host communication
- Multi-host container networking
- Avoiding conflicts

```
┌────────────────────────────────────────────────────────────────────┐
│                           Host System                               │
│                                                                     │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐          │
│  │ Container 1 │     │ Container 2 │     │ Container 3 │          │
│  │ 172.17.0.2  │     │ 172.17.0.3  │     │ 10.0.1.2    │          │
│  └──────┬──────┘     └──────┬──────┘     └──────┬──────┘          │
│         │                   │                   │                  │
│         └─────────┬─────────┘                   │                  │
│                   │                             │                  │
│            docker0 (bridge)              br-custom                 │
│            172.17.0.1                    10.0.1.1                  │
│                   │                             │                  │
│                   └──────────┬──────────────────┘                  │
│                              │                                     │
│                         eth0 (netplan)                             │
│                         192.168.1.100                              │
└──────────────────────────────┼─────────────────────────────────────┘
                               │
                          Physical Network
```

## Default Docker Networking

Docker creates `docker0` bridge automatically:

```bash
# View Docker networks
docker network ls

# Inspect default bridge
docker network inspect bridge
```

Default configuration:
- Bridge: `docker0`
- Subnet: `172.17.0.0/16`
- Gateway: `172.17.0.1`

## Host Network Prerequisites

### Basic Netplan for Docker Host

```yaml
# /etc/netplan/00-docker-host.yaml
network:
  version: 2
  renderer: networkd

  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1, 8.8.8.8]
```

### Enable IP Forwarding

Required for container networking:

```bash
# /etc/sysctl.d/99-docker.conf
net.ipv4.ip_forward = 1
net.bridge.bridge-nf-call-iptables = 1
```

## Docker with Host Bridge

### Create Bridge in Netplan

```yaml
# /etc/netplan/00-docker-bridge.yaml
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

### Use Bridge with Docker

```bash
# Create Docker network using host bridge
docker network create \
  --driver bridge \
  --subnet 192.168.1.0/24 \
  --gateway 192.168.1.100 \
  --opt "com.docker.network.bridge.name"="br0" \
  host-bridge
```

## Macvlan Network

Containers get IPs directly on physical network:

### Netplan Configuration

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

### Create Macvlan Network

```bash
# Create macvlan network
docker network create \
  --driver macvlan \
  --subnet 192.168.1.0/24 \
  --gateway 192.168.1.1 \
  --ip-range 192.168.1.192/26 \
  -o parent=eth0 \
  macvlan-net

# Run container with macvlan
docker run -d \
  --network macvlan-net \
  --ip 192.168.1.200 \
  nginx
```

### Host-to-Container Communication

Macvlan prevents host-container direct communication. Create a macvlan interface on host:

```bash
# Create macvlan interface for host
ip link add macvlan0 link eth0 type macvlan mode bridge
ip addr add 192.168.1.101/24 dev macvlan0
ip link set macvlan0 up

# Now host can reach containers via macvlan0
```

## IPvlan Network

Alternative to macvlan (works with some switches that reject multiple MACs):

```bash
# Create ipvlan network
docker network create \
  --driver ipvlan \
  --subnet 192.168.1.0/24 \
  --gateway 192.168.1.1 \
  -o parent=eth0 \
  -o ipvlan_mode=l2 \
  ipvlan-net
```

## Docker Compose Integration

### Custom Networks

```yaml
# docker-compose.yml
version: "3.8"

services:
  web:
    image: nginx
    networks:
      - frontend
      - backend

  api:
    image: myapi
    networks:
      - backend

  db:
    image: postgres
    networks:
      - backend

networks:
  frontend:
    driver: bridge
    ipam:
      config:
        - subnet: 10.1.0.0/24

  backend:
    driver: bridge
    internal: true  # No external access
    ipam:
      config:
        - subnet: 10.2.0.0/24
```

### External Networks

```yaml
# docker-compose.yml
version: "3.8"

services:
  web:
    image: nginx
    networks:
      - host-bridge

networks:
  host-bridge:
    external: true
    name: macvlan-net
```

## Port Publishing

### Map Container to Host Port

```bash
# Basic port mapping
docker run -d -p 80:80 nginx

# Specific interface
docker run -d -p 192.168.1.100:80:80 nginx

# All interfaces
docker run -d -p 0.0.0.0:80:80 nginx
```

### Netplan for Multiple IPs

Different services on different IPs:

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24    # Main
        - 192.168.1.101/24    # Web
        - 192.168.1.102/24    # API
      routes:
        - to: default
          via: 192.168.1.1
```

```bash
# Web container on 192.168.1.101
docker run -d -p 192.168.1.101:80:80 nginx

# API container on 192.168.1.102
docker run -d -p 192.168.1.102:80:80 api
```

## DNS Configuration

### Docker DNS

Containers use Docker's embedded DNS (127.0.0.11):

```bash
# Check container DNS
docker exec container cat /etc/resolv.conf
```

### Custom DNS via Host

```yaml
# Netplan with DNS
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      nameservers:
        search: [internal.local]
        addresses: [192.168.1.1, 1.1.1.1]
```

Docker daemon config:

```json
{
  "dns": ["192.168.1.1", "1.1.1.1"],
  "dns-search": ["internal.local"]
}
```

## Multi-Host Networking

### Overlay Network with Swarm

Netplan on each Docker host:

```yaml
# Same on all hosts
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.10X/24    # Different on each host
      routes:
        - to: default
          via: 192.168.1.1
```

Create overlay network:

```bash
# On swarm manager
docker network create \
  --driver overlay \
  --subnet 10.10.0.0/16 \
  --attachable \
  my-overlay
```

### VXLAN for Multi-Host

Manual VXLAN overlay:

```yaml
# /etc/netplan/50-vxlan.yaml
network:
  version: 2
  tunnels:
    vxlan100:
      mode: vxlan
      id: 100
      local: 192.168.1.100
      remote: 192.168.1.101
      port: 4789
      addresses:
        - 10.100.0.1/24
```

## Docker and VLANs

### VLAN-Aware Docker Networks

```yaml
# Netplan VLANs
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false

  vlans:
    eth0.10:
      id: 10
      link: eth0

    eth0.20:
      id: 20
      link: eth0
```

Create networks per VLAN:

```bash
# VLAN 10 network
docker network create \
  --driver macvlan \
  --subnet 10.10.0.0/24 \
  --gateway 10.10.0.1 \
  -o parent=eth0.10 \
  vlan10-net

# VLAN 20 network
docker network create \
  --driver macvlan \
  --subnet 10.20.0.0/24 \
  --gateway 10.20.0.1 \
  -o parent=eth0.20 \
  vlan20-net
```

## Troubleshooting

### Container Can't Reach Internet

```bash
# Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
# Should be 1

# Check NAT rules
iptables -t nat -L POSTROUTING -n -v

# Check Docker daemon is running
systemctl status docker

# Check container DNS
docker exec container ping 8.8.8.8
docker exec container ping google.com
```

### Port Not Accessible

```bash
# Check port is published
docker port container_name

# Check host firewall
iptables -L INPUT -n -v | grep 80
ufw status

# Check nothing else using port
ss -tlnp | grep :80
```

### Container-to-Container Communication

```bash
# Check both on same network
docker network inspect bridge

# Try by container name (needs user network)
docker exec container1 ping container2

# Check network connectivity
docker exec container1 ip route
```

### Macvlan Not Working

```bash
# Check promiscuous mode
ip link show eth0 | grep PROMISC

# Enable if needed (some cloud providers block this)
ip link set eth0 promisc on

# Check switch allows multiple MACs
# (managed switches may need config)
```

## Best Practices

1. **Use user-defined networks** - Don't rely on default bridge
2. **Isolate sensitive containers** - Use internal networks
3. **Plan IP ranges** - Avoid conflicts with host networks
4. **Use macvlan for direct access** - When containers need real IPs
5. **Document port mappings** - Keep track of what's exposed
6. **Consider security** - Docker bypasses host firewall (see networking section)
7. **Use DNS names** - Don't hardcode container IPs
