# Docker Compose Networking

## Network Basics in Compose

Docker Compose creates a default network for each project:

```yaml
# docker-compose.yml
services:
  web:
    image: nginx
  db:
    image: postgres
```

```bash
docker compose up -d
# Creates network: myproject_default
# Both services connected automatically
```

## Default Network Behavior

### Automatic DNS

Services can reach each other by name:

```bash
# From web container
ping db        # Works
ping database  # Doesn't work (unless aliased)
```

### Automatic Network Naming

```
projectname_default
└── projectname_web_1
└── projectname_db_1
```

### Network Isolation

Each compose project is isolated:

```
project1_default ←→ project1 services only
project2_default ←→ project2 services only
```

## Custom Networks

### Define Networks

```yaml
services:
  web:
    networks:
      - frontend

  api:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend

networks:
  frontend:
  backend:
```

### Network Options

```yaml
networks:
  frontend:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.name: br-frontend

  backend:
    driver: bridge
    internal: true  # No external access
    ipam:
      driver: default
      config:
        - subnet: 10.0.1.0/24
          gateway: 10.0.1.1
```

### Use External Network

```yaml
networks:
  shared:
    external: true
    name: my-shared-network
```

```bash
# Create external network first
docker network create my-shared-network
```

## Port Publishing in Compose

### Basic Syntax

```yaml
services:
  web:
    ports:
      # Long syntax
      - target: 80
        published: 8080
        protocol: tcp
        mode: host

      # Short syntax
      - "80:80"
      - "443:443"
```

### Localhost Binding

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"
```

### Random Port

```yaml
services:
  app:
    ports:
      - "3000"  # Random host port, container 3000
```

```bash
docker compose port app 3000
# Shows assigned port
```

## Network Aliases

```yaml
services:
  db:
    networks:
      backend:
        aliases:
          - database
          - postgres

  legacy-api:
    networks:
      backend:
        aliases:
          - api  # Multiple services can share an alias
```

## Static IPs

```yaml
services:
  web:
    networks:
      backend:
        ipv4_address: 10.0.1.10

networks:
  backend:
    ipam:
      config:
        - subnet: 10.0.1.0/24
```

## DNS Configuration

### Custom DNS

```yaml
services:
  web:
    dns:
      - 1.1.1.1
      - 8.8.8.8
    dns_search:
      - example.com
```

### Extra Hosts

```yaml
services:
  web:
    extra_hosts:
      - "somehost:192.168.1.100"
      - "otherhost:192.168.1.101"
```

## Network Patterns

### Frontend/Backend Pattern

```yaml
services:
  nginx:
    image: nginx
    ports:
      - "80:80"
      - "443:443"
    networks:
      - frontend
    depends_on:
      - app

  app:
    image: myapp
    networks:
      - frontend
      - backend
    depends_on:
      - db
      - redis

  db:
    image: postgres
    networks:
      - backend
    volumes:
      - db-data:/var/lib/postgresql/data

  redis:
    image: redis
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true

volumes:
  db-data:
```

### Microservices Pattern

```yaml
services:
  gateway:
    image: kong
    ports:
      - "80:8000"
      - "443:8443"
    networks:
      - public
      - services

  auth:
    image: auth-service
    networks:
      - services
      - data

  users:
    image: users-service
    networks:
      - services
      - data

  orders:
    image: orders-service
    networks:
      - services
      - data

  postgres:
    image: postgres
    networks:
      - data

  redis:
    image: redis
    networks:
      - data

networks:
  public:
  services:
    internal: true
  data:
    internal: true
```

### Shared Network Pattern

For services across multiple compose files:

```yaml
# File: network.yml (run first)
networks:
  shared:
    name: app-network
```

```yaml
# File: app1/docker-compose.yml
services:
  web:
    networks:
      - shared

networks:
  shared:
    external: true
    name: app-network
```

```yaml
# File: app2/docker-compose.yml
services:
  api:
    networks:
      - shared

networks:
  shared:
    external: true
    name: app-network
```

## Security Considerations

### Minimize Published Ports

```yaml
# BAD: Everything exposed
services:
  web:
    ports:
      - "80:80"
  db:
    ports:
      - "5432:5432"  # Unnecessary!
  redis:
    ports:
      - "6379:6379"  # Unnecessary!
```

```yaml
# GOOD: Only what's needed
services:
  web:
    ports:
      - "80:80"
  db:
    # No ports - only network access
  redis:
    # No ports - only network access
```

### Use Internal Networks

```yaml
networks:
  backend:
    internal: true  # Services can't reach internet
```

### Localhost for Development

```yaml
# Development override
# docker-compose.override.yml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"  # Localhost only
```

## UFW Integration

### With ufw-docker

```bash
# After docker compose up
sudo ufw-docker allow myproject-web-1 80
```

### With DOCKER-USER

```bash
# Allow compose services
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j ACCEPT
# Block database port explicitly
iptables -I DOCKER-USER -i eth0 -p tcp --dport 5432 -j DROP
```

## Debugging Compose Networks

### View Networks

```bash
docker compose ps
docker network ls | grep myproject
docker network inspect myproject_default
```

### Test Connectivity

```bash
# Enter container
docker compose exec web sh

# Test DNS
nslookup db
ping db

# Test port
nc -zv db 5432
```

### View Container IPs

```bash
docker compose exec web ip addr
docker inspect myproject-web-1 -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'
```

## Environment-Specific Configuration

### Development

```yaml
# docker-compose.yml
services:
  web:
    ports:
      - "80:80"
```

```yaml
# docker-compose.override.yml (auto-loaded)
services:
  web:
    ports:
      - "8080:80"  # Different port for dev
  db:
    ports:
      - "127.0.0.1:5432:5432"  # Expose for debugging
```

### Production

```yaml
# docker-compose.prod.yml
services:
  web:
    ports:
      - "80:80"
      - "443:443"
  db:
    # No ports exposed

# Use with:
# docker compose -f docker-compose.yml -f docker-compose.prod.yml up
```
