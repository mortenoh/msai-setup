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

!!! warning "This build is not on the public internet by default"
    The `httpChallenge` above assumes a public domain name whose A/AAAA record
    points at this host and **ports 80/443 reachable from the internet**. That
    is not the default posture for this build: the MS-S1 MAX sits on the LAN
    and is managed over Tailscale, with nothing forwarded from the public
    internet (see `START.md` — "not directly on the public
    internet"). Public ACME issuance via HTTP-01 therefore requires you to
    **deliberately open 80/443** to the internet (router port-forward +
    firewall rule), which widens your attack surface.

    Alternatives that avoid a public-facing port:

    - **DNS-01 challenge** (see [DNS Challenge](#dns-challenge-wildcard-certificates)
      below) — issues public certs without exposing 80/443, using your DNS
      provider's API. Works for LAN/Tailscale-only services.
    - **Traefik `tls internal` / a private CA** for names you only reach over
      the LAN or Tailscale.
    - **[Tailscale Serve/Funnel](../../tailscale/features/funnel-serve.md)** — Serve exposes a
      service to your tailnet with a Tailscale-issued TLS cert (no open port);
      Funnel deliberately publishes it to the internet through Tailscale's
      relays if you actually want public access, without forwarding a port on
      your router.

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

Traefik can route raw TCP/UDP as well as HTTP. This is useful for the handful
of services that legitimately need a public TCP endpoint.

!!! danger "Do not expose a database this way"
    A previous version of this page routed Postgres (`:5432`) through a Traefik
    entrypoint with a wildcard `HostSNI("*")` rule, i.e. accepting connections
    from anything that reaches the entrypoint. That directly contradicts the
    port map in [services/index.md](../index.md#port-map), which requires
    Postgres to bind `127.0.0.1` only. Databases have no business on a shared,
    internet-facing entrypoint: a wildcard `HostSNI("*")` on a plain TCP router
    does no per-host filtering,
    and Postgres' own auth is your only remaining line of defense. Keep the DB
    on `127.0.0.1` (or a private Docker network) and let the app containers
    reach it internally; if you must reach it remotely, tunnel over Tailscale or
    SSH rather than publishing an entrypoint.

The example below instead shows a service that is actually meant to accept
external TCP — a self-hosted Git server's SSH endpoint — routed by SNI:

```yaml
# traefik.yml
entryPoints:
  gitssh:
    address: ":2222"

# docker-compose.yml
services:
  gitea:
    labels:
      - "traefik.enable=true"
      - "traefik.tcp.routers.gitssh.rule=HostSNI(`git.${DOMAIN}`)"
      - "traefik.tcp.routers.gitssh.entrypoints=gitssh"
      - "traefik.tcp.routers.gitssh.tls.passthrough=true"
      - "traefik.tcp.services.gitssh.loadbalancer.server.port=22"
```

Note that TCP entrypoints are subject to the same public-exposure caveat as
HTTPS above — only open the port to the internet deliberately, and prefer
Tailscale for anything that doesn't need to be public.

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
- [Docker Compose](../../docker/compose.md)
