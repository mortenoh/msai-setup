# User Management

## Identity Providers

Tailscale authenticates users through identity providers (IdPs):

| Provider | Features |
|----------|----------|
| Google | Workspace, personal accounts |
| Microsoft | Azure AD, Microsoft 365, personal |
| GitHub | Organizations, personal |
| Okta | Enterprise SSO |
| OneLogin | Enterprise SSO |
| OIDC | Custom OpenID Connect |

## User Types

### Owner

- Full administrative access
- Can manage billing
- Can delete tailnet
- Cannot be removed

### Admin

- Manage devices and users
- Configure ACLs
- Manage DNS and settings
- Cannot manage billing

### Member

- Connect devices
- Access based on ACLs
- Cannot manage tailnet

### Network Admin (Personal+)

- Subset of admin permissions
- Configured via admin console

## User Roles Configuration

### Admin Console

1. Go to **Users**
2. Click on user
3. Select role: Owner, Admin, Member

### Via ACLs

Grant specific capabilities:

```json
{
  "grants": [
    {
      "src": ["alice@example.com"],
      "dst": ["*"],
      "app": {
        "tailscale.com/cap/admin-api-access": [{
          "endpoints": ["devices", "dns"]
        }]
      }
    }
  ]
}
```

## User Invitations

### Invite New Users

1. Go to **Users** → **Invite users**
2. Enter email addresses
3. Users receive invitation email
4. They authenticate with their IdP

### Domain-Wide Access

For Google Workspace or Microsoft 365:

1. **Settings** → **User access**
2. Enable "Allow any user with a @domain.com email"
3. No individual invitations needed

## Device Limits

### Per-User Limits

Configure maximum devices per user:

1. **Settings** → **User access**
2. Set "Device limit per user"

### Personal vs Shared Devices

| Type | Ownership | Expiry |
|------|-----------|--------|
| Personal | Tied to user | With user |
| Tagged | Organization-owned | Never (unless key expires) |

## User Provisioning

### SCIM (Enterprise)

Automatic user provisioning:

```
Identity Provider ──► SCIM ──► Tailscale
                              (creates/removes users)
```

Supported:
- Okta
- Azure AD
- OneLogin

### Manual

Invite/remove users through admin console.

## Removing Users

### Remove User Access

1. Go to **Users**
2. Click user → **Remove access**
3. User's devices disconnected

### Remove Devices Only

1. Go to **Machines**
2. Select user's devices
3. Remove individually

## Multi-User Tailnets

### Personal Accounts

Single user tailnet, invite others as needed.

### Organization/Team

- Multiple admins
- Group management
- SCIM provisioning
- SSO enforcement

## Guest Access

### Temporary Access

Use auth keys with expiry:

1. Create reusable auth key with short expiry
2. Share with guest
3. Key expires, access ends

### Shared Devices

Tag devices for shared access:

```bash
sudo tailscale up --advertise-tags=tag:shared
```

ACL controls who accesses shared devices.

## User Activity

### View Active Sessions

**Machines** tab shows:
- Which users are connected
- Device names
- Last seen times

### Audit Logs (Enterprise)

**Logs** tab shows:
- Authentication events
- Device registrations
- Configuration changes

## Best Practices

1. **Use groups** in ACLs, not individual users
2. **Regular audits**: Remove inactive users
3. **SSO enforcement**: For compliance
4. **Device tagging**: For shared/service devices
5. **Least privilege**: Grant minimum needed access
6. **Document roles**: Who has admin access and why
