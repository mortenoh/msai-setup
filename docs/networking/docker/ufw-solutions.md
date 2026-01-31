# Docker UFW Solutions

## Solution Overview

| Solution | Use When | Complexity | Security |
|----------|----------|------------|----------|
| Bind to localhost | Services behind reverse proxy | Low | Excellent |
| ufw-docker | General use | Medium | Good |
| DOCKER-USER rules | Need fine control | Medium | Good |
| Internal networks | Multi-container apps | Medium | Excellent |
| iptables: false | Full manual control | High | Depends |
| Host network mode | Need host networking | Low | Good |

## Solution 1: Bind to localhost (Recommended)

The simplest and most secure approach for services behind a reverse proxy.

### Implementation

```yaml
# docker-compose.yml
services:
  # Public: reverse proxy handles external traffic
  nginx:
    image: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf

  # Private: only accessible via nginx
  app:
    image: myapp
    ports:
      - "127.0.0.1:8080:8080"  # localhost only!

  # Private: only accessible via app
  db:
    image: postgres
    ports:
      - "127.0.0.1:5432:5432"  # localhost only!
```

### How It Works

```bash
# Check binding
docker port db
# 5432/tcp -> 127.0.0.1:5432

# External access blocked by kernel, not iptables
curl http://192.168.1.100:5432
# Connection refused (can't reach 127.0.0.1 from outside)
```

### nginx Reverse Proxy Config

```nginx
# /etc/nginx/nginx.conf
upstream app {
    server 127.0.0.1:8080;
}

server {
    listen 80;
    server_name example.com;

    location / {
        proxy_pass http://app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### UFW for the Proxy

```bash
# Only allow HTTP/HTTPS through UFW
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

### Pros and Cons

✅ **Pros:**
- Simple to understand
- No extra tools needed
- Works with standard UFW
- Kernel-level protection

❌ **Cons:**
- Requires reverse proxy for public services
- Can't access from other machines for debugging
- Need to remember for every container

## Solution 2: ufw-docker (Recommended for General Use)

A utility that modifies UFW to work correctly with Docker.

### Installation

```bash
# Download
sudo wget -O /usr/local/bin/ufw-docker \
    https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker

# Install (modifies UFW rules)
sudo ufw-docker install

# Restart UFW
sudo systemctl restart ufw
```

### How It Works

ufw-docker adds rules to `/etc/ufw/after.rules`:

```bash
# Added by ufw-docker
*filter
:DOCKER-USER - [0:0]
:ufw-user-forward - [0:0]

# Block all external access to Docker by default
-A DOCKER-USER -j ufw-user-forward

# Return if from internal networks
-A DOCKER-USER -j RETURN -s 10.0.0.0/8
-A DOCKER-USER -j RETURN -s 172.16.0.0/12
-A DOCKER-USER -j RETURN -s 192.168.0.0/16

# ... more rules ...
COMMIT
```

### Usage

```bash
# List container rules
sudo ufw-docker status

# Allow access to container port from anywhere
sudo ufw-docker allow nginx 80

# Allow from specific network
sudo ufw-docker allow nginx 80 192.168.1.0/24

# Allow multiple ports
sudo ufw-docker allow nginx 80/tcp
sudo ufw-docker allow nginx 443/tcp

# Delete rule
sudo ufw-docker delete allow nginx 80

# Block specific container
sudo ufw-docker deny nginx
```

### Example Workflow

```bash
# 1. Deploy services
docker run -d --name web -p 80:80 nginx
docker run -d --name db -p 5432:5432 postgres

# 2. Allow web server
sudo ufw-docker allow web 80

# 3. Database stays blocked (default)
# No ufw-docker allow = no external access

# 4. Verify
sudo ufw-docker status
```

### Pros and Cons

✅ **Pros:**
- Integrates with UFW workflow
- Easy to use
- Maintains UFW as single firewall interface

❌ **Cons:**
- External tool (not official)
- Must remember to allow new containers
- Rules reference container names (if container renamed, rules break)

## Solution 3: DOCKER-USER Chain Rules

Direct iptables manipulation for fine-grained control.

### Basic Setup

```bash
# Default deny for external interface
iptables -I DOCKER-USER -i eth0 -j DROP

# Allow established connections
iptables -I DOCKER-USER -i eth0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT
```

### Allow Specific Ports

```bash
# Allow port 80 from anywhere
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j ACCEPT

# Allow port 443 from anywhere
iptables -I DOCKER-USER -i eth0 -p tcp --dport 443 -j ACCEPT

# Allow port 8080 from local network only
iptables -I DOCKER-USER -i eth0 -s 192.168.1.0/24 -p tcp --dport 8080 -j ACCEPT
```

### Complete Script

```bash
#!/bin/bash
# /usr/local/bin/docker-firewall.sh

# Flush existing DOCKER-USER rules (except RETURN)
iptables -F DOCKER-USER
iptables -A DOCKER-USER -j RETURN

# Allow established connections
iptables -I DOCKER-USER -m conntrack --ctstate ESTABLISHED,RELATED -j RETURN

# Allow from local networks
iptables -I DOCKER-USER -s 10.0.0.0/8 -j RETURN
iptables -I DOCKER-USER -s 172.16.0.0/12 -j RETURN
iptables -I DOCKER-USER -s 192.168.0.0/16 -j RETURN

# Allow specific services from external
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j RETURN
iptables -I DOCKER-USER -i eth0 -p tcp --dport 443 -j RETURN

# Drop everything else from external
iptables -A DOCKER-USER -i eth0 -j DROP

echo "Docker firewall rules applied"
```

### Persistence

```bash
# Create systemd service
cat > /etc/systemd/system/docker-firewall.service << 'EOF'
[Unit]
Description=Docker DOCKER-USER firewall rules
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-firewall.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

# Enable
systemctl daemon-reload
systemctl enable docker-firewall
systemctl start docker-firewall
```

### Pros and Cons

✅ **Pros:**
- Full control
- Works with any Docker setup
- Efficient (iptables native)

❌ **Cons:**
- Manual management
- Separate from UFW
- Need to maintain script

## Solution 4: Internal Networks

Prevent external access at the Docker network level.

### Implementation

```yaml
# docker-compose.yml
services:
  web:
    image: nginx
    ports:
      - "80:80"
    networks:
      - frontend
      - backend

  app:
    image: myapp
    networks:
      - backend  # No frontend = no external access

  db:
    image: postgres
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # KEY: No external access
```

### How Internal Networks Work

```bash
# Internal network has no gateway
docker network inspect backend
# "Internal": true
# No MASQUERADE rule = no outbound
# No DNAT rule = no inbound from host ports
```

### Combined with Localhost Binding

```yaml
services:
  web:
    ports:
      - "80:80"  # Public
    networks:
      - frontend
      - backend

  admin:
    ports:
      - "127.0.0.1:9090:9090"  # Localhost only
    networks:
      - backend

  db:
    # No ports - only network access
    networks:
      - backend

networks:
  backend:
    internal: true
```

### Pros and Cons

✅ **Pros:**
- Docker-native solution
- Clear network boundaries
- No iptables manipulation

❌ **Cons:**
- Internal containers can't reach internet
- More complex compose files
- Need to plan network topology

## Solution 5: Disable Docker iptables

Complete manual control by disabling Docker's iptables management.

### Configuration

```json
// /etc/docker/daemon.json
{
  "iptables": false
}
```

```bash
sudo systemctl restart docker
```

### Manual Network Setup

```bash
#!/bin/bash
# Complete manual Docker networking

# Enable forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# NAT for container network
iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

# Basic forwarding
iptables -A FORWARD -i docker0 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o docker0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Port publishing (per container)
# Example: nginx on 172.17.0.2
iptables -t nat -A PREROUTING -p tcp --dport 80 -j DNAT --to-destination 172.17.0.2:80
iptables -A FORWARD -p tcp -d 172.17.0.2 --dport 80 -j ACCEPT
```

### Pros and Cons

✅ **Pros:**
- Complete control
- UFW works normally
- No surprises

❌ **Cons:**
- Very complex
- Must manually manage every container
- Container networking features break
- Not recommended for most users

## Solution 6: Host Network Mode

Container uses host's network directly.

### Implementation

```yaml
services:
  plex:
    image: plexinc/pms-docker
    network_mode: host
    # No ports needed - binds directly to host
```

### UFW Works Normally

```bash
# UFW rules apply to host network services
sudo ufw allow 32400/tcp  # Plex
```

### Pros and Cons

✅ **Pros:**
- UFW works as expected
- Best performance
- Simple to understand

❌ **Cons:**
- No network isolation
- Port conflicts possible
- Container sees all host interfaces
- Not suitable for multi-instance services

## Recommended Architecture

For a typical home server:

```yaml
# docker-compose.yml
version: '3.8'

services:
  # Reverse proxy - only public-facing service
  traefik:
    image: traefik:v2.10
    ports:
      - "80:80"
      - "443:443"
    networks:
      - proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock

  # Web app - behind proxy
  app:
    image: myapp
    networks:
      - proxy
      - internal
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.app.rule=Host(`app.example.com`)"

  # Database - internal only
  db:
    image: postgres
    networks:
      - internal
    volumes:
      - db-data:/var/lib/postgresql/data

networks:
  proxy:
    driver: bridge
  internal:
    driver: bridge
    internal: true

volumes:
  db-data:
```

### UFW Configuration

```bash
# Only HTTP/HTTPS allowed
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

This architecture:
- Only Traefik is exposed
- All other services are internal
- UFW protects the host
- Database has no network exposure
