# Docker Network Overview

## Docker Networking Basics

Docker provides several network drivers to handle container connectivity:

```
┌─────────────────────────────────────────────────────────────┐
│                         Host                                 │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Docker Engine                      │    │
│  │                                                      │    │
│  │   ┌─────────┐   ┌─────────┐   ┌─────────┐          │    │
│  │   │ bridge  │   │  host   │   │  none   │          │    │
│  │   │ network │   │ network │   │ network │          │    │
│  │   └─────────┘   └─────────┘   └─────────┘          │    │
│  │                                                      │    │
│  │   ┌─────────────────────────────────────────────┐   │    │
│  │   │              Custom Networks                 │   │    │
│  │   │   bridge | overlay | macvlan | ipvlan       │   │    │
│  │   └─────────────────────────────────────────────┘   │    │
│  │                                                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Network Drivers

### Bridge (Default)

The default network for containers:

```bash
# Default bridge (docker0)
docker run nginx
# Container gets IP in 172.17.0.0/16

# Custom bridge
docker network create mynetwork
docker run --network mynetwork nginx
```

**Characteristics:**

- Containers can communicate via IP
- NAT for outbound traffic
- Port publishing for inbound traffic
- Isolated from host network

### Host

Container shares host's network namespace:

```bash
docker run --network host nginx
# nginx binds directly to host ports
```

**Characteristics:**

- No network isolation
- No NAT overhead
- Container uses host IP
- Port conflicts with host services possible
- UFW rules apply normally

### None

No networking:

```bash
docker run --network none alpine
# Only loopback interface
```

### Macvlan

Container gets MAC address on physical network:

```bash
docker network create -d macvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    macvlan_net

docker run --network macvlan_net nginx
# Container appears as separate host on network
```

**Characteristics:**

- Container has unique MAC address
- Direct network access (no NAT)
- Can get DHCP lease
- Host cannot communicate with container directly

### IPvlan

Similar to macvlan but shares MAC address:

```bash
docker network create -d ipvlan \
    --subnet=192.168.1.0/24 \
    --gateway=192.168.1.1 \
    -o parent=eth0 \
    ipvlan_net
```

### Overlay

Multi-host networking (Docker Swarm):

```bash
docker network create -d overlay myoverlay
```

## Default Bridge Network

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                          Host                                │
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │              docker0 bridge                          │   │
│   │              172.17.0.1/16                           │   │
│   │                                                      │   │
│   │    ┌────────┐  ┌────────┐  ┌────────┐              │   │
│   │    │veth123 │  │veth456 │  │veth789 │              │   │
│   └────┴───┬────┴──┴───┬────┴──┴───┬────┴──────────────┘   │
│            │           │           │                        │
│   ┌────────▼───────┐  ┌▼──────────▼────────┐               │
│   │  Container A   │  │   Container B       │               │
│   │  eth0          │  │   eth0              │               │
│   │  172.17.0.2    │  │   172.17.0.3        │               │
│   └────────────────┘  └────────────────────┘               │
│                                                              │
│   eth0 (host) ─────────────────────────────▶ Internet       │
│   NAT: 172.17.0.0/16 → host IP (masquerade)                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Default Network Properties

```bash
# Inspect default bridge
docker network inspect bridge

# Key properties:
# - Subnet: 172.17.0.0/16
# - Gateway: 172.17.0.1
# - Driver: bridge
# - Scope: local
```

### Limitations of Default Bridge

- No automatic DNS resolution between containers
- Must use --link (deprecated) or IP addresses
- All containers share the same network

## Custom Bridge Networks

### Create Network

```bash
# Basic custom network
docker network create myapp

# With specific subnet
docker network create \
    --subnet=10.0.0.0/24 \
    --gateway=10.0.0.1 \
    myapp

# With IP range for containers
docker network create \
    --subnet=10.0.0.0/24 \
    --ip-range=10.0.0.128/25 \
    --gateway=10.0.0.1 \
    myapp
```

### Advantages Over Default

- DNS resolution by container name
- Better isolation
- Configurable subnet
- Network-scoped aliases

### Container DNS

```bash
# On custom network
docker network create myapp
docker run -d --name db --network myapp postgres
docker run -d --name web --network myapp nginx

# 'web' can resolve 'db' by name
docker exec web ping db
```

## Port Publishing

### Publish Ports

```bash
# Publish to all interfaces
docker run -p 8080:80 nginx
# Host:8080 → Container:80

# Publish to specific interface
docker run -p 127.0.0.1:8080:80 nginx
# Only localhost:8080 → Container:80

# Publish to specific IP
docker run -p 192.168.1.100:8080:80 nginx

# Random host port
docker run -p 80 nginx
docker port <container>  # Shows assigned port

# UDP port
docker run -p 53:53/udp dns-server
```

### How Port Publishing Works

When you publish a port, Docker:

1. Creates iptables NAT rules (DNAT)
2. Creates filter rules to allow traffic
3. Sets up userland proxy (docker-proxy)

```bash
# View Docker's NAT rules
sudo iptables -t nat -L DOCKER -n

# Example output:
# DNAT tcp -- 0.0.0.0/0 0.0.0.0/0 tcp dpt:8080 to:172.17.0.2:80
```

## Container Communication

### Same Network

Containers on the same network can communicate:

```bash
# Create network
docker network create myapp

# Start containers
docker run -d --name db --network myapp postgres
docker run -d --name web --network myapp -p 80:80 nginx

# Communication is direct (no NAT)
docker exec web curl http://db:5432
```

### Different Networks

Containers on different networks cannot communicate by default:

```bash
docker network create frontend
docker network create backend

docker run -d --name web --network frontend nginx
docker run -d --name db --network backend postgres

# web cannot reach db (different networks)
```

### Connect to Multiple Networks

```bash
docker run -d --name app --network frontend nginx

# Add to additional network
docker network connect backend app

# Now 'app' can reach both networks
```

## Network Inspection

```bash
# List networks
docker network ls

# Inspect network
docker network inspect bridge

# Show container's networks
docker inspect <container> -f '{{json .NetworkSettings.Networks}}'

# Show container IP
docker inspect <container> -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

## Internal Networks

Create networks without external access:

```bash
docker network create --internal isolated

docker run -d --network isolated myapp
# Container has no internet access
# Can only communicate with other containers on 'isolated'
```

## Network Configuration in Compose

```yaml
version: '3.8'

services:
  web:
    image: nginx
    networks:
      - frontend
    ports:
      - "80:80"

  api:
    image: myapi
    networks:
      - frontend
      - backend

  db:
    image: postgres
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

## Network Troubleshooting

### Check Connectivity

```bash
# Enter container
docker exec -it container sh

# Check interfaces
ip addr

# Check routes
ip route

# Test connectivity
ping other-container
curl http://other-container:port
```

### DNS Issues

```bash
# Check DNS resolution
docker exec container nslookup other-container

# Check /etc/resolv.conf
docker exec container cat /etc/resolv.conf
# Should show 127.0.0.11 (Docker's embedded DNS)
```

### Network Isolation Issues

```bash
# Verify networks
docker network ls

# Check container's networks
docker inspect container -f '{{json .NetworkSettings.Networks}}'

# Verify containers are on same network
docker network inspect mynetwork
```
