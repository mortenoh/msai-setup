# Authentik

Authentik is an open-source identity provider with support for OIDC, SAML, LDAP, and forward authentication.

## Docker Compose Setup

### docker-compose.yml

```yaml
services:
  postgresql:
    image: postgres:15-alpine
    container_name: authentik-db
    restart: unless-stopped
    volumes:
      - ./data/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_DB: authentik
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: ${PG_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U authentik"]
      interval: 30s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: authentik-redis
    restart: unless-stopped
    command: --save 60 1 --loglevel warning
    volumes:
      - ./data/redis:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 5s
      retries: 5

  server:
    image: ghcr.io/goauthentik/server:latest
    container_name: authentik-server
    restart: unless-stopped
    command: server
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASSWORD}
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
    volumes:
      - ./media:/media
      - ./custom-templates:/templates
    ports:
      - "9000:9000"
      - "9443:9443"
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - default
      - proxy

  worker:
    image: ghcr.io/goauthentik/server:latest
    container_name: authentik-worker
    restart: unless-stopped
    command: worker
    environment:
      AUTHENTIK_REDIS__HOST: redis
      AUTHENTIK_POSTGRESQL__HOST: postgresql
      AUTHENTIK_POSTGRESQL__USER: authentik
      AUTHENTIK_POSTGRESQL__NAME: authentik
      AUTHENTIK_POSTGRESQL__PASSWORD: ${PG_PASSWORD}
      AUTHENTIK_SECRET_KEY: ${AUTHENTIK_SECRET_KEY}
    volumes:
      - ./media:/media
      - ./custom-templates:/templates
    depends_on:
      postgresql:
        condition: service_healthy
      redis:
        condition: service_healthy

networks:
  proxy:
    external: true
```

### Environment Variables

```bash
# .env
PG_PASSWORD=$(openssl rand -base64 32)
AUTHENTIK_SECRET_KEY=$(openssl rand -base64 60)
```

### Initial Setup

```bash
# Create directories
mkdir -p data/postgres data/redis media custom-templates

# Start services
docker compose up -d

# Access setup at http://localhost:9000/if/flow/initial-setup/
```

## Traefik Integration

### Authentik Labels

```yaml
# Add to authentik server service
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.authentik.rule=Host(`auth.${DOMAIN}`)"
  - "traefik.http.routers.authentik.entrypoints=https"
  - "traefik.http.routers.authentik.tls.certresolver=letsencrypt"
  - "traefik.http.services.authentik.loadbalancer.server.port=9000"
```

### Forward Auth Middleware

Create an Outpost in Authentik UI, then configure Traefik:

```yaml
# In authentik docker-compose.yml, add to server labels
labels:
  # ... existing labels ...
  # Forward auth endpoint
  - "traefik.http.middlewares.authentik.forwardauth.address=http://authentik-server:9000/outpost.goauthentik.io/auth/traefik"
  - "traefik.http.middlewares.authentik.forwardauth.trustForwardHeader=true"
  - "traefik.http.middlewares.authentik.forwardauth.authResponseHeaders=X-authentik-username,X-authentik-groups,X-authentik-email,X-authentik-name,X-authentik-uid"
```

### Protected Service

```yaml
services:
  myapp:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.myapp.rule=Host(`myapp.${DOMAIN}`)"
      - "traefik.http.routers.myapp.entrypoints=https"
      - "traefik.http.routers.myapp.tls.certresolver=letsencrypt"
      - "traefik.http.routers.myapp.middlewares=authentik@docker"
```

## Configure Applications

### Forward Auth Provider

1. Go to **Applications** > **Providers** > **Create**
2. Select **Proxy Provider**
3. Configure:
   - Name: `Forward Auth`
   - Authorization flow: default
   - Mode: **Forward auth (single application)**
   - External host: `https://myapp.domain.com`

### OIDC Provider

1. Go to **Applications** > **Providers** > **Create**
2. Select **OAuth2/OpenID Provider**
3. Configure:
   - Name: App name
   - Authorization flow: default
   - Client ID: auto-generated (save this)
   - Client Secret: auto-generated (save this)
   - Redirect URIs: `https://app.domain.com/callback`

### LDAP Provider

1. Go to **Applications** > **Providers** > **Create**
2. Select **LDAP Provider**
3. Configure:
   - Name: `LDAP`
   - Bind DN: auto-generated
   - Search group: select user group

## Outpost Configuration

### Create Outpost

1. Go to **Applications** > **Outposts** > **Create**
2. Configure:
   - Name: `Embedded Outpost`
   - Type: **Proxy**
   - Integration: Select docker or kubernetes
   - Applications: Select your applications

### Embedded Outpost (Default)

The embedded outpost runs inside the server container. For forward auth:

```
http://authentik-server:9000/outpost.goauthentik.io/auth/traefik
```

## User Management

### Create Users

1. Go to **Directory** > **Users** > **Create**
2. Fill in user details
3. Set password or send invitation email

### Groups

1. Go to **Directory** > **Groups** > **Create**
2. Name the group (e.g., `admins`, `users`)
3. Add users to group

### Policies

Create policies to control access:

1. Go to **Flows & Stages** > **Policies** > **Create**
2. Policy types:
   - **Expression Policy**: Python expressions
   - **Group Membership**: Require group membership
   - **Password**: Password requirements

## Two-Factor Authentication

### Enable TOTP

1. Go to **Flows & Stages** > **Stages** > **Create**
2. Select **Authenticator Validation Stage**
3. Configure device classes (TOTP, WebAuthn)
4. Bind to authentication flow

### WebAuthn (Hardware Keys)

Supported by default when TOTP stage is configured.

## Customization

### Custom Branding

1. Go to **System** > **Brands**
2. Configure:
   - Logo
   - Favicon
   - Custom CSS

### Custom Templates

Mount templates directory and create custom HTML:

```
custom-templates/
└── login/
    └── login.html
```

## Backup

### Database Backup

```bash
docker exec authentik-db pg_dump -U authentik authentik > backup.sql
```

### Full Backup

```bash
# Stop services
docker compose stop

# Backup data directory
tar -czvf authentik-backup.tar.gz data/ media/

# Start services
docker compose start
```

## Troubleshooting

### Check Logs

```bash
docker logs authentik-server
docker logs authentik-worker
```

### Common Issues

1. **502 Bad Gateway**
   - Check if server is healthy
   - Verify network connectivity

2. **Forward auth not working**
   - Check outpost is running
   - Verify middleware URL is correct

3. **OIDC redirect issues**
   - Check redirect URIs match exactly
   - Verify client ID/secret

## See Also

- [Authentication Overview](index.md)
- [Traefik Integration](../reverse-proxy/traefik.md)
- [Authelia Alternative](authelia.md)
