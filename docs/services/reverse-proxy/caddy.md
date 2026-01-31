# Caddy

Caddy is a powerful, extensible web server with automatic HTTPS. Known for its simple configuration.

## Docker Compose Setup

### Basic Configuration

```yaml
# docker-compose.yml
services:
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
      - "443:443/udp"  # HTTP/3
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - ./data:/data
      - ./config:/config
    networks:
      - proxy
    environment:
      - DOMAIN=${DOMAIN}

networks:
  proxy:
    external: true
```

### Basic Caddyfile

```
# Caddyfile

# Global options
{
    email your@email.com
    acme_ca https://acme-v02.api.letsencrypt.org/directory
}

# Redirect www to non-www
www.{$DOMAIN} {
    redir https://{$DOMAIN}{uri}
}

# Main site
{$DOMAIN} {
    respond "Hello, world!"
}

# Reverse proxy example
app.{$DOMAIN} {
    reverse_proxy app:8080
}
```

## Reverse Proxy Configurations

### Basic Reverse Proxy

```
app.example.com {
    reverse_proxy app:8080
}
```

### With Health Checks

```
app.example.com {
    reverse_proxy app:8080 {
        health_uri /health
        health_interval 30s
        health_timeout 5s
    }
}
```

### Load Balancing

```
app.example.com {
    reverse_proxy app1:8080 app2:8080 app3:8080 {
        lb_policy round_robin
        health_uri /health
    }
}
```

### WebSocket Support

```
ws.example.com {
    reverse_proxy app:8080 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

### Path-Based Routing

```
example.com {
    handle /api/* {
        reverse_proxy api:3000
    }

    handle /app/* {
        reverse_proxy app:8080
    }

    handle {
        root * /srv
        file_server
    }
}
```

## Security

### Basic Authentication

```
admin.example.com {
    basicauth {
        # htpasswd -B -n admin
        admin $2a$14$hashed_password_here
    }
    reverse_proxy admin:8080
}
```

### IP Restriction

```
internal.example.com {
    @blocked not remote_ip 192.168.1.0/24 10.0.0.0/8
    respond @blocked "Access denied" 403

    reverse_proxy internal:8080
}
```

### Security Headers

```
example.com {
    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains; preload"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
        X-XSS-Protection "1; mode=block"
        Referrer-Policy "strict-origin-when-cross-origin"
    }
    reverse_proxy app:8080
}
```

### Rate Limiting

```
api.example.com {
    rate_limit {
        zone api_limit {
            key {remote_host}
            events 100
            window 1m
        }
    }
    reverse_proxy api:3000
}
```

## SSL/TLS Configuration

### Let's Encrypt (Default)

Automatic HTTPS is enabled by default. Just use a domain name.

### DNS Challenge (Cloudflare)

```yaml
# docker-compose.yml
services:
  caddy:
    image: caddy:2-alpine
    build:
      context: .
      dockerfile: Dockerfile.caddy
```

```dockerfile
# Dockerfile.caddy
FROM caddy:2-builder AS builder
RUN xcaddy build --with github.com/caddy-dns/cloudflare

FROM caddy:2-alpine
COPY --from=builder /usr/bin/caddy /usr/bin/caddy
```

```
# Caddyfile
{
    acme_dns cloudflare {env.CF_API_TOKEN}
}

*.example.com {
    tls {
        dns cloudflare {env.CF_API_TOKEN}
    }
    reverse_proxy app:8080
}
```

### Custom Certificates

```
example.com {
    tls /path/to/cert.pem /path/to/key.pem
    reverse_proxy app:8080
}
```

### Internal CA (No Public Certificate)

```
internal.local {
    tls internal
    reverse_proxy app:8080
}
```

## Common Service Configurations

### Jellyfin

```
jellyfin.example.com {
    reverse_proxy jellyfin:8096 {
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }
}
```

### Home Assistant

```
ha.example.com {
    reverse_proxy homeassistant:8123 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
    }
}
```

### Nextcloud

```
cloud.example.com {
    reverse_proxy nextcloud:80 {
        header_up Host {host}
        header_up X-Real-IP {remote_host}
        header_up X-Forwarded-For {remote_host}
        header_up X-Forwarded-Proto {scheme}
    }

    header {
        Strict-Transport-Security "max-age=31536000;"
    }

    redir /.well-known/carddav /remote.php/dav 301
    redir /.well-known/caldav /remote.php/dav 301
}
```

### Grafana

```
grafana.example.com {
    reverse_proxy grafana:3000 {
        header_up X-WEBAUTH-USER {http.request.header.X-WEBAUTH-USER}
    }
}
```

## Logging

### Access Logs

```
{
    log {
        output file /var/log/caddy/access.log {
            roll_size 100mb
            roll_keep 5
            roll_keep_for 720h
        }
        format json
    }
}
```

### Per-Site Logging

```
example.com {
    log {
        output file /var/log/caddy/example.log
    }
    reverse_proxy app:8080
}
```

## Snippets (Reusable Configurations)

```
# Caddyfile
(common_headers) {
    header {
        Strict-Transport-Security "max-age=31536000;"
        X-Content-Type-Options "nosniff"
        X-Frame-Options "DENY"
    }
}

(proxy_headers) {
    header_up Host {host}
    header_up X-Real-IP {remote_host}
    header_up X-Forwarded-For {remote_host}
    header_up X-Forwarded-Proto {scheme}
}

app1.example.com {
    import common_headers
    reverse_proxy app1:8080 {
        import proxy_headers
    }
}

app2.example.com {
    import common_headers
    reverse_proxy app2:8080 {
        import proxy_headers
    }
}
```

## Troubleshooting

### Check Configuration

```bash
# Validate Caddyfile
docker exec caddy caddy validate --config /etc/caddy/Caddyfile

# Reload configuration
docker exec caddy caddy reload --config /etc/caddy/Caddyfile

# Format Caddyfile
docker exec caddy caddy fmt --overwrite /etc/caddy/Caddyfile
```

### View Logs

```bash
docker logs caddy

# Follow logs
docker logs -f caddy
```

### Common Issues

1. **Certificate not generating**
   - Check DNS points to server
   - Ensure ports 80/443 are accessible
   - Check Let's Encrypt rate limits

2. **502 Bad Gateway**
   - Backend service not running
   - Wrong port or hostname
   - Container not on same network

3. **Redirect loops**
   - Check for conflicting redirects
   - Verify upstream isn't also redirecting

## See Also

- [Reverse Proxy Overview](index.md)
- [Traefik](traefik.md)
- [Docker Networking](../../docker/networking.md)
