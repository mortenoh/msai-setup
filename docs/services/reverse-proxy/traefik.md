# Traefik

Traefik is a modern, Docker-native reverse proxy with automatic service discovery and SSL certificate management.

## Docker Compose Setup

### Basic Configuration

```yaml
# docker-compose.yml
services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    restart: unless-stopped
    security_opt:
      - no-new-privileges:true
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik.yml:/traefik.yml:ro
      - ./acme.json:/acme.json
      - ./config:/config
    networks:
      - proxy
    labels:
      - "traefik.enable=true"
      # Dashboard
      - "traefik.http.routers.traefik.rule=Host(`traefik.${DOMAIN}`)"
      - "traefik.http.routers.traefik.entrypoints=https"
      - "traefik.http.routers.traefik.tls.certresolver=letsencrypt"
      - "traefik.http.routers.traefik.service=api@internal"
      # Basic auth for dashboard
      - "traefik.http.routers.traefik.middlewares=auth"
      - "traefik.http.middlewares.auth.basicauth.users=${TRAEFIK_AUTH}"

networks:
  proxy:
    external: true
```

### Traefik Configuration

```yaml
# traefik.yml
api:
  dashboard: true
  insecure: false

entryPoints:
  http:
    address: ":80"
    http:
      redirections:
        entryPoint:
          to: https
          scheme: https
  https:
    address: ":443"

providers:
  docker:
    endpoint: "unix:///var/run/docker.sock"
    exposedByDefault: false
    network: proxy
  file:
    directory: /config
    watch: true

certificatesResolvers:
  letsencrypt:
    acme:
      email: your@email.com
      storage: acme.json
      httpChallenge:
        entryPoint: http
```

### Setup Steps

```bash
# Create network
docker network create proxy

# Create acme.json with proper permissions
touch acme.json
chmod 600 acme.json

# Generate basic auth password
htpasswd -nb admin yourpassword
# Add output to .env as TRAEFIK_AUTH

# Start
docker compose up -d
```

## Adding Services

### Service with Traefik Labels

```yaml
# Example: Whoami test service
services:
  whoami:
    image: traefik/whoami
    container_name: whoami
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.whoami.rule=Host(`whoami.${DOMAIN}`)"
      - "traefik.http.routers.whoami.entrypoints=https"
      - "traefik.http.routers.whoami.tls.certresolver=letsencrypt"
    networks:
      - proxy

networks:
  proxy:
    external: true
```

### Service with Custom Port

```yaml
services:
  myapp:
    image: myapp:latest
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.${DOMAIN}`)"
      - "traefik.http.routers.myapp.entrypoints=https"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
      - "traefik.http.services.myapp.loadbalancer.server.port=3000"
    networks:
      - proxy
```

### Path-Based Routing

```yaml
services:
  api:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`${DOMAIN}`) && PathPrefix(`/api`)"
      - "traefik.http.routers.api.entrypoints=https"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"
      - "traefik.http.middlewares.api-strip.stripprefix.prefixes=/api"
      - "traefik.http.routers.api.middlewares=api-strip"
```

## Middlewares

### Basic Authentication

```yaml
labels:
  - "traefik.http.middlewares.myauth.basicauth.users=admin:$$hashed$$password"
  - "traefik.http.routers.myapp.middlewares=myauth"
```

### Rate Limiting

```yaml
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=50"
  - "traefik.http.routers.myapp.middlewares=ratelimit"
```

### IP Whitelist

```yaml
labels:
  - "traefik.http.middlewares.local-only.ipwhitelist.sourcerange=192.168.1.0/24,10.0.0.0/8"
  - "traefik.http.routers.myapp.middlewares=local-only"
```

### Headers

```yaml
labels:
  - "traefik.http.middlewares.security.headers.browserXssFilter=true"
  - "traefik.http.middlewares.security.headers.contentTypeNosniff=true"
  - "traefik.http.middlewares.security.headers.frameDeny=true"
  - "traefik.http.middlewares.security.headers.stsIncludeSubdomains=true"
  - "traefik.http.middlewares.security.headers.stsSeconds=31536000"
  - "traefik.http.routers.myapp.middlewares=security"
```

### Redirect HTTP to HTTPS

Already configured in traefik.yml, but can also use:

```yaml
labels:
  - "traefik.http.middlewares.redirect-https.redirectscheme.scheme=https"
  - "traefik.http.routers.myapp-http.middlewares=redirect-https"
```

## DNS Challenge (Wildcard Certificates)

For internal services or wildcard certs:

```yaml
# traefik.yml
certificatesResolvers:
  letsencrypt-dns:
    acme:
      email: your@email.com
      storage: acme.json
      dnsChallenge:
        provider: cloudflare
        resolvers:
          - "1.1.1.1:53"
          - "8.8.8.8:53"
```

```yaml
# docker-compose.yml
services:
  traefik:
    environment:
      - CF_API_EMAIL=your@email.com
      - CF_DNS_API_TOKEN=your-token
```

## TCP/UDP Routing

### TCP Service (Database)

```yaml
# traefik.yml
entryPoints:
  postgres:
    address: ":5432"

# docker-compose.yml
services:
  postgres:
    labels:
      - "traefik.enable=true"
      - "traefik.tcp.routers.postgres.rule=HostSNI(`*`)"
      - "traefik.tcp.routers.postgres.entrypoints=postgres"
      - "traefik.tcp.services.postgres.loadbalancer.server.port=5432"
```

## File-Based Configuration

For non-Docker services:

```yaml
# config/external.yml
http:
  routers:
    external-router:
      rule: "Host(`external.domain.com`)"
      entryPoints:
        - https
      tls:
        certResolver: letsencrypt
      service: external-service

  services:
    external-service:
      loadBalancer:
        servers:
          - url: "http://192.168.1.100:8080"
```

## Monitoring

### Prometheus Metrics

```yaml
# traefik.yml
metrics:
  prometheus:
    entryPoint: metrics
    buckets:
      - 0.1
      - 0.3
      - 1.2
      - 5.0

entryPoints:
  metrics:
    address: ":8082"
```

### Access Logs

```yaml
# traefik.yml
accessLog:
  filePath: "/var/log/traefik/access.log"
  bufferingSize: 100
  filters:
    statusCodes:
      - "400-499"
      - "500-599"
```

## Troubleshooting

### Check Configuration

```bash
# View logs
docker logs traefik

# Check running routers
curl http://localhost:8080/api/http/routers

# Check services
curl http://localhost:8080/api/http/services
```

### Common Issues

1. **Certificate not generating**
   - Check acme.json permissions (600)
   - Verify DNS is pointing to your server
   - Check Let's Encrypt rate limits

2. **Service not discovered**
   - Ensure `traefik.enable=true` label
   - Check service is on the `proxy` network
   - Verify Docker socket is mounted

3. **503 Service Unavailable**
   - Check backend service is running
   - Verify port in loadbalancer.server.port

## See Also

- [Reverse Proxy Overview](index.md)
- [Authentication with Authentik](../authentication/authentik.md)
- [Docker Networking](../../docker/networking.md)
