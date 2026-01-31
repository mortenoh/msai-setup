# Authelia

Authelia is a lightweight authentication server providing two-factor authentication and single sign-on for applications via forward authentication.

## Docker Compose Setup

### docker-compose.yml

```yaml
services:
  authelia:
    image: authelia/authelia:latest
    container_name: authelia
    restart: unless-stopped
    volumes:
      - ./config:/config
    environment:
      TZ: Europe/Oslo
    ports:
      - "9091:9091"
    networks:
      - proxy

networks:
  proxy:
    external: true
```

### Configuration Files

Create `config/configuration.yml`:

```yaml
# config/configuration.yml
theme: dark
default_redirection_url: https://home.example.com

server:
  host: 0.0.0.0
  port: 9091

log:
  level: info
  format: text

totp:
  issuer: example.com
  period: 30
  skew: 1

authentication_backend:
  file:
    path: /config/users_database.yml
    password:
      algorithm: argon2id
      iterations: 3
      memory: 65536
      parallelism: 4
      key_length: 32
      salt_length: 16

access_control:
  default_policy: deny
  rules:
    # Public endpoints
    - domain: public.example.com
      policy: bypass

    # Single factor for basic apps
    - domain: app.example.com
      policy: one_factor

    # Two factor for sensitive apps
    - domain: admin.example.com
      policy: two_factor

    # Admin-only with 2FA
    - domain: secure.example.com
      policy: two_factor
      subject:
        - "group:admins"

session:
  name: authelia_session
  domain: example.com
  expiration: 3600
  inactivity: 300
  remember_me_duration: 1M
  secret: your-session-secret

regulation:
  max_retries: 3
  find_time: 2m
  ban_time: 5m

storage:
  local:
    path: /config/db.sqlite3

notifier:
  filesystem:
    filename: /config/notification.txt
  # Or use SMTP:
  # smtp:
  #   host: smtp.example.com
  #   port: 587
  #   username: authelia@example.com
  #   password: your-password
  #   sender: "Authelia <authelia@example.com>"
```

### Users Database

Create `config/users_database.yml`:

```yaml
# config/users_database.yml
users:
  admin:
    displayname: "Admin User"
    # Password: admin (change this!)
    # Generate with: docker run authelia/authelia:latest authelia crypto hash generate argon2
    password: "$argon2id$v=19$m=65536,t=3,p=4$hash_here"
    email: admin@example.com
    groups:
      - admins
      - users

  user:
    displayname: "Regular User"
    password: "$argon2id$v=19$m=65536,t=3,p=4$hash_here"
    email: user@example.com
    groups:
      - users
```

### Generate Password Hash

```bash
docker run --rm authelia/authelia:latest authelia crypto hash generate argon2 --password 'your-password'
```

## Traefik Integration

### Authelia Labels

```yaml
services:
  authelia:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.authelia.rule=Host(`auth.example.com`)"
      - "traefik.http.routers.authelia.entrypoints=https"
      - "traefik.http.routers.authelia.tls.certresolver=letsencrypt"
      - "traefik.http.services.authelia.loadbalancer.server.port=9091"
      # Middleware for other services
      - "traefik.http.middlewares.authelia.forwardauth.address=http://authelia:9091/api/verify?rd=https://auth.example.com"
      - "traefik.http.middlewares.authelia.forwardauth.trustForwardHeader=true"
      - "traefik.http.middlewares.authelia.forwardauth.authResponseHeaders=Remote-User,Remote-Groups,Remote-Name,Remote-Email"
```

### Protected Service

```yaml
services:
  myapp:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.example.com`)"
      - "traefik.http.routers.myapp.entrypoints=https"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
      - "traefik.http.routers.myapp.middlewares=authelia@docker"
```

## Caddy Integration

### Caddyfile

```
auth.example.com {
    reverse_proxy authelia:9091
}

app.example.com {
    forward_auth authelia:9091 {
        uri /api/verify?rd=https://auth.example.com
        copy_headers Remote-User Remote-Groups Remote-Email Remote-Name
    }
    reverse_proxy app:8080
}
```

## Access Control Policies

### Policy Types

| Policy | Description |
|--------|-------------|
| bypass | No authentication required |
| one_factor | Username/password only |
| two_factor | Username/password + TOTP/WebAuthn |
| deny | Block access |

### Rule Examples

```yaml
access_control:
  default_policy: deny

  rules:
    # Public API
    - domain: api.example.com
      resources:
        - "^/public.*$"
      policy: bypass

    # Require 2FA for admin paths
    - domain: app.example.com
      resources:
        - "^/admin.*$"
      policy: two_factor

    # Allow specific users
    - domain: secret.example.com
      policy: two_factor
      subject:
        - "user:admin"
        - "group:admins"

    # Network-based rules
    - domain: internal.example.com
      policy: one_factor
      networks:
        - 192.168.1.0/24

    # Require specific methods
    - domain: api.example.com
      resources:
        - "^/api/write.*$"
      methods:
        - POST
        - PUT
        - DELETE
      policy: two_factor
```

## Two-Factor Authentication

### TOTP Setup

Users can register TOTP at:
```
https://auth.example.com
```

### WebAuthn (Hardware Keys)

Add to configuration:

```yaml
webauthn:
  disable: false
  display_name: Authelia
  attestation_conveyance_preference: indirect
  user_verification: preferred
  timeout: 60s
```

## Database Backends

### SQLite (Default)

```yaml
storage:
  local:
    path: /config/db.sqlite3
```

### PostgreSQL

```yaml
storage:
  postgres:
    host: postgres
    port: 5432
    database: authelia
    username: authelia
    password: your-password
```

### MySQL/MariaDB

```yaml
storage:
  mysql:
    host: mysql
    port: 3306
    database: authelia
    username: authelia
    password: your-password
```

## Session Storage

### In-Memory (Default)

Good for single instance.

### Redis

```yaml
session:
  redis:
    host: redis
    port: 6379
    # password: your-password
```

## Email Notifications

### SMTP

```yaml
notifier:
  smtp:
    host: smtp.example.com
    port: 587
    username: authelia@example.com
    password: your-password
    sender: "Authelia <authelia@example.com>"
    startup_check_address: test@example.com
```

### File (Development)

```yaml
notifier:
  filesystem:
    filename: /config/notification.txt
```

## Secrets Management

Use environment variables for secrets:

```yaml
# configuration.yml
session:
  secret:
    file: /config/secrets/session

storage:
  encryption_key:
    file: /config/secrets/storage

# Or use environment variables
# AUTHELIA_SESSION_SECRET_FILE=/config/secrets/session
```

## Troubleshooting

### Check Logs

```bash
docker logs authelia
```

### Validate Configuration

```bash
docker exec authelia authelia validate-config --config /config/configuration.yml
```

### Common Issues

1. **Redirect loops**
   - Check domain in session config matches your domains
   - Ensure forward auth URL is correct

2. **Cookie issues**
   - Session domain must be parent of app domains
   - Check browser accepts cookies

3. **502 errors**
   - Verify Authelia is running
   - Check network connectivity

## See Also

- [Authentication Overview](index.md)
- [Authentik Alternative](authentik.md)
- [Traefik Integration](../reverse-proxy/traefik.md)
