# Docker Compose

Define and run multi-container applications with YAML configuration.

## Overview

Docker Compose provides:

- **Declarative configuration** - Define services in YAML
- **Multi-container orchestration** - Manage related containers together
- **Networking** - Automatic service discovery
- **Volume management** - Persistent data across restarts
- **Development workflows** - Hot reload and overrides

## Installation

Docker Compose v2 is included with Docker Desktop and Docker Engine:

```bash
# Verify installation
docker compose version

# Or standalone (v1 style)
docker-compose --version
```

## Compose File Structure

### Basic Structure

```yaml
# docker-compose.yml
version: "3.8"  # Optional in modern Docker

services:
  web:
    image: nginx:alpine
    ports:
      - "8080:80"

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgres://db:5432/app

  db:
    image: postgres:16
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

### Service Definition

```yaml
services:
  app:
    # Image or build
    image: node:20-alpine
    # Or build from Dockerfile
    build:
      context: .
      dockerfile: Dockerfile
      args:
        NODE_ENV: production

    # Container name (optional)
    container_name: my-app

    # Command override
    command: npm start

    # Working directory
    working_dir: /app

    # User
    user: "node"

    # Restart policy
    restart: unless-stopped

    # Dependencies
    depends_on:
      - db
      - redis
```

## Environment Variables

### Inline Definition

```yaml
services:
  app:
    environment:
      - NODE_ENV=production
      - DEBUG=false
      - API_URL=http://api:3000
```

### Environment File

```yaml
services:
  app:
    env_file:
      - .env
      - .env.local
```

Create `.env`:

```bash
DATABASE_URL=postgres://user:pass@db:5432/app
REDIS_URL=redis://redis:6379
SECRET_KEY=your-secret-key
```

### Variable Substitution

```yaml
services:
  app:
    image: myapp:${VERSION:-latest}
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

```bash
# Run with variables
VERSION=1.2.3 docker compose up
```

## Networking

### Default Network

Services automatically join a default network:

```yaml
services:
  web:
    image: nginx
    # Can reach api at http://api:3000

  api:
    image: myapi
    # Can reach db at postgres://db:5432
```

### Custom Networks

```yaml
services:
  web:
    networks:
      - frontend
      - backend

  api:
    networks:
      - backend

  db:
    networks:
      - backend

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No external access
```

### Host Networking

```yaml
services:
  app:
    network_mode: host
```

### External Networks

```yaml
services:
  app:
    networks:
      - traefik_proxy

networks:
  traefik_proxy:
    external: true
```

## Volumes and Bind Mounts

### Named Volumes

```yaml
services:
  db:
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
    driver: local
```

### Bind Mounts

```yaml
services:
  app:
    volumes:
      # Source code
      - ./src:/app/src
      # Config file
      - ./config.json:/app/config.json:ro
      # Anonymous volume (not persisted)
      - /app/node_modules
```

### Volume Options

```yaml
volumes:
  db_data:
    driver: local
    driver_opts:
      type: none
      device: /data/postgres
      o: bind
```

## Port Mapping

### Basic Ports

```yaml
services:
  web:
    ports:
      - "8080:80"       # host:container
      - "443:443"
      - "3000"          # Random host port
```

### Specific Interface

```yaml
services:
  db:
    ports:
      - "127.0.0.1:5432:5432"  # localhost only
```

### Port Ranges

```yaml
services:
  app:
    ports:
      - "8000-8010:8000-8010"
```

## Health Checks

### Basic Health Check

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

### Health Check Types

```yaml
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
```

### Depend on Health

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
```

## Resource Limits

### Memory and CPU

```yaml
services:
  app:
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 2G
        reservations:
          cpus: "0.5"
          memory: 512M
```

### For docker-compose (v2)

```yaml
services:
  app:
    mem_limit: 2g
    cpus: 2.0
    memswap_limit: 4g
```

## Build Configuration

### Basic Build

```yaml
services:
  app:
    build: ./app
```

### Advanced Build

```yaml
services:
  app:
    build:
      context: .
      dockerfile: Dockerfile.prod
      args:
        - NODE_ENV=production
        - BUILD_DATE=${BUILD_DATE}
      target: production
      cache_from:
        - myapp:cache
      labels:
        - "com.example.version=1.0"
```

### Multi-Stage Build

```dockerfile
# Dockerfile
FROM node:20 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine AS production
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
CMD ["node", "dist/main.js"]
```

```yaml
services:
  app:
    build:
      context: .
      target: production
```

## Override Files

### Development Override

`docker-compose.yml`:

```yaml
services:
  app:
    image: myapp
    environment:
      - NODE_ENV=production
```

`docker-compose.override.yml` (auto-loaded):

```yaml
services:
  app:
    build: .
    volumes:
      - ./src:/app/src
    environment:
      - NODE_ENV=development
      - DEBUG=true
```

### Multiple Override Files

```bash
# Production
docker compose -f docker-compose.yml -f docker-compose.prod.yml up

# Staging
docker compose -f docker-compose.yml -f docker-compose.staging.yml up
```

## Common Commands

### Start Services

```bash
# Start all services
docker compose up

# Start in background
docker compose up -d

# Start specific service
docker compose up api

# Rebuild and start
docker compose up --build
```

### Stop Services

```bash
# Stop services
docker compose stop

# Stop and remove containers
docker compose down

# Remove volumes too
docker compose down -v

# Remove images too
docker compose down --rmi all
```

### Service Management

```bash
# View running services
docker compose ps

# View logs
docker compose logs

# Follow logs
docker compose logs -f api

# Execute command
docker compose exec api sh

# Run one-off command
docker compose run api npm test
```

### Build

```bash
# Build all images
docker compose build

# Build without cache
docker compose build --no-cache

# Build specific service
docker compose build api
```

## Profiles

### Define Profiles

```yaml
services:
  app:
    image: myapp
    profiles: []  # Always started

  debug:
    image: busybox
    profiles: ["debug"]

  test:
    image: myapp-test
    profiles: ["test"]
```

### Use Profiles

```bash
# Start default services
docker compose up

# Start with debug profile
docker compose --profile debug up

# Multiple profiles
docker compose --profile debug --profile test up
```

## Logging

### Configure Logging

```yaml
services:
  app:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

### Available Drivers

| Driver | Description |
|--------|-------------|
| `json-file` | Default, JSON logs |
| `local` | Optimized local storage |
| `syslog` | Syslog server |
| `journald` | systemd journal |
| `none` | Disable logging |

## Security

### Read-Only Container

```yaml
services:
  app:
    read_only: true
    tmpfs:
      - /tmp
```

### Capabilities

```yaml
services:
  app:
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

### Secrets

```yaml
services:
  app:
    secrets:
      - db_password

secrets:
  db_password:
    file: ./secrets/db_password.txt
```

## Complete Example

```yaml
# docker-compose.yml
version: "3.8"

services:
  web:
    build: ./web
    ports:
      - "3000:3000"
    environment:
      - API_URL=http://api:8080
    depends_on:
      api:
        condition: service_healthy
    networks:
      - frontend
      - backend

  api:
    build: ./api
    environment:
      - DATABASE_URL=postgres://user:${DB_PASSWORD}@db:5432/app
      - REDIS_URL=redis://redis:6379
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 10s
      timeout: 5s
      retries: 3
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    networks:
      - backend
    deploy:
      resources:
        limits:
          memory: 1G

  db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_DB=app
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d app"]
      interval: 5s
      timeout: 5s
      retries: 5
    networks:
      - backend

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - backend

networks:
  frontend:
  backend:
    internal: true

volumes:
  db_data:
  redis_data:
```

## See Also

- [Docker Setup](setup.md) - Docker installation
- [Development Stacks](development-stacks.md) - Ready-to-use stacks
- [Ollama Stack](ollama-stack.md) - Local AI stack
- [Resource Limits](resources.md) - Container resources
