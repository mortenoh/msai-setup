# Key Management

## Key Types

### Auth Keys

Pre-authentication keys for automated device registration.

```bash
# Use auth key instead of browser login
sudo tailscale up --auth-key=tskey-auth-xxxxx
```

### API Keys

Keys for Tailscale API access.

```bash
# API requests
curl -H "Authorization: Bearer tskey-api-xxxxx" \
  https://api.tailscale.com/api/v2/tailnet/-/devices
```

## Auth Keys

### Creating Auth Keys

1. **Admin Console** → **Settings** → **Keys**
2. Click **Generate auth key**
3. Configure options:
   - **Reusable**: Use for multiple devices
   - **Ephemeral**: Devices removed when offline
   - **Pre-authorized**: Skip admin approval
   - **Expiration**: 1 day to 90 days
   - **Tags**: Apply tags automatically

### Auth Key Options

| Option | Description | Use Case |
|--------|-------------|----------|
| **One-time** | Single use, then expires | Single server setup |
| **Reusable** | Multiple devices | Fleet deployment |
| **Ephemeral** | Device removed when offline | Temporary/CI jobs |
| **Pre-authorized** | No admin approval needed | Automated setup |

### Auth Key Expiration

- Minimum: 1 day
- Maximum: 90 days
- Default: 90 days
- Expired keys stop working for new registrations

### Auth Key with Tags

```bash
# Key configured with tag:server in admin console
sudo tailscale up --auth-key=tskey-auth-xxxxx

# Device automatically tagged as "server"
```

Or specify tags at registration:

```bash
sudo tailscale up --auth-key=tskey-auth-xxxxx --advertise-tags=tag:webserver
```

## API Keys

### Creating API Keys

1. **Admin Console** → **Settings** → **Keys**
2. Click **Generate API key**
3. Select scopes
4. Set expiration

### API Scopes

| Scope | Permissions |
|-------|-------------|
| `all:read` | Read all resources |
| `devices:read` | Read device list |
| `devices:write` | Modify devices |
| `dns:read` | Read DNS config |
| `dns:write` | Modify DNS |
| `routes:read` | Read routes |
| `routes:write` | Modify routes |
| `acl:read` | Read ACL |
| `acl:write` | Modify ACL |

### Using API Keys

```bash
# List devices
curl -s \
  -H "Authorization: Bearer tskey-api-xxxxx" \
  "https://api.tailscale.com/api/v2/tailnet/-/devices" | jq

# Delete a device
curl -X DELETE \
  -H "Authorization: Bearer tskey-api-xxxxx" \
  "https://api.tailscale.com/api/v2/device/{deviceID}"

# Get ACL
curl -s \
  -H "Authorization: Bearer tskey-api-xxxxx" \
  "https://api.tailscale.com/api/v2/tailnet/-/acl"
```

## OAuth Clients

For applications and integrations:

### Creating OAuth Clients

1. **Admin Console** → **Settings** → **OAuth clients**
2. Click **Create OAuth client**
3. Configure:
   - Name
   - Scopes
   - Redirect URIs (if applicable)

### OAuth Scopes

| Scope | Description |
|-------|-------------|
| `devices` | Device management |
| `routes` | Route management |
| `dns` | DNS configuration |
| `acl` | ACL management |
| `auth_keys` | Auth key management |

### Using OAuth

```bash
# Get access token
curl -X POST \
  -d "client_id=xxx&client_secret=xxx&grant_type=client_credentials" \
  https://api.tailscale.com/oauth/token

# Use access token
curl -H "Authorization: Bearer <access_token>" \
  https://api.tailscale.com/api/v2/tailnet/-/devices
```

## Device Keys

### Key Expiry

By default, device keys expire and require re-authentication.

**Disable expiry** for servers:
1. **Machines** → Select device
2. **Disable key expiry**

### Re-authentication

```bash
# Force re-authentication
sudo tailscale up --force-reauth
```

### Key Rotation

Device keys automatically rotate. Manual rotation:

1. Remove device from admin console
2. Re-authenticate: `sudo tailscale up`

## Best Practices

### Auth Keys

1. **Use short expiration** for one-time keys
2. **Use ephemeral** for temporary workloads
3. **Tag at key creation** for consistent tagging
4. **Rotate regularly** for long-lived deployments
5. **Don't commit to git** - use secrets management

### API Keys

1. **Minimum scopes** - only what's needed
2. **Short expiration** when possible
3. **Separate keys** for different services
4. **Audit usage** - who uses which key
5. **Rotate compromised keys** immediately

## Secrets Management

### Environment Variables

```bash
# Never hardcode
export TS_AUTHKEY=tskey-auth-xxxxx
sudo tailscale up --auth-key=$TS_AUTHKEY
```

### CI/CD Secrets

```yaml
# GitHub Actions
- name: Setup Tailscale
  env:
    TS_AUTHKEY: ${{ secrets.TAILSCALE_AUTHKEY }}
  run: |
    tailscale up --auth-key=$TS_AUTHKEY
```

### Kubernetes Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: tailscale-auth
type: Opaque
stringData:
  authkey: tskey-auth-xxxxx
```

### HashiCorp Vault

```bash
# Store
vault kv put secret/tailscale authkey=tskey-auth-xxxxx

# Retrieve
export TS_AUTHKEY=$(vault kv get -field=authkey secret/tailscale)
```

## Revoking Keys

### Auth Keys

1. **Settings** → **Keys**
2. Find key → **Revoke**
3. Existing devices stay connected
4. New registrations fail

### API Keys

1. **Settings** → **Keys**
2. Find API key → **Revoke**
3. API calls with key fail immediately

### Device Keys

1. **Machines** → Select device
2. **Remove** or **Expire key**
3. Device disconnects

## Monitoring Key Usage

### Admin Console

- View active auth keys
- See which devices used which key
- Monitor API key usage

### Audit Logs

Enterprise plans show:
- Key creation/revocation events
- API calls per key
- Authentication attempts
