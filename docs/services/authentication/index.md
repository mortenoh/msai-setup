# Authentication Services

Centralized authentication and Single Sign-On (SSO) for your homelab services.

## Why Centralized Auth?

- **Single Sign-On** - Log in once, access all services
- **Centralized management** - One place for user accounts
- **Security** - 2FA, session management, audit logs
- **Access control** - Role-based permissions

## Options Comparison

| Feature | Authentik | Authelia | Keycloak |
|---------|-----------|----------|----------|
| Complexity | Medium | Low | High |
| Resources | Higher | Lower | Highest |
| UI | Modern | Basic | Enterprise |
| SAML | Yes | No | Yes |
| OIDC | Yes | Yes | Yes |
| LDAP | Yes | Backend | Yes |
| 2FA | Yes | Yes | Yes |
| Best for | Full-featured SSO | Simple forward auth | Enterprise |

## In This Section

| Document | Description |
|----------|-------------|
| [Authentik](authentik.md) | Full-featured identity provider |
| [Authelia](authelia.md) | Lightweight authentication server |

## Quick Decision

- **Authentik** - Need SAML, LDAP, or full IdP features
- **Authelia** - Simple forward auth, lower resources

## Authentication Concepts

### Forward Authentication

Reverse proxy checks auth before forwarding request:

```
User Request
    │
    v
┌─────────────┐     ┌─────────────┐
│   Traefik   │────>│  Authentik  │
└─────────────┘     └─────────────┘
    │                     │
    │<── Auth OK ─────────┘
    │
    v
┌─────────────┐
│   App       │
└─────────────┘
```

### OpenID Connect (OIDC)

Application redirects to IdP for login:

```
User ──> App ──redirect──> Authentik ──> Login
                              │
                              v
User <── App <──callback<── Auth Token
```

### LDAP

Directory service for user lookup:

```
App ──> LDAP Query ──> Authentik ──> User Info
```

## Integration with Reverse Proxy

### Traefik + Authentik

```yaml
# Traefik middleware
labels:
  - "traefik.http.middlewares.authentik.forwardauth.address=http://authentik:9000/outpost.goauthentik.io/auth/traefik"
  - "traefik.http.middlewares.authentik.forwardauth.trustForwardHeader=true"
  - "traefik.http.middlewares.authentik.forwardauth.authResponseHeaders=X-authentik-username,X-authentik-groups,X-authentik-email"
```

### Caddy + Authelia

```
app.example.com {
    forward_auth authelia:9091 {
        uri /api/verify?rd=https://auth.example.com
        copy_headers Remote-User Remote-Groups Remote-Email
    }
    reverse_proxy app:8080
}
```

## See Also

- [Authentik Setup](authentik.md)
- [Authelia Setup](authelia.md)
- [Traefik](../reverse-proxy/traefik.md)
