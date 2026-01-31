# Access Controls (ACLs)

## Overview

Tailscale Access Control Lists (ACLs) define who can connect to what on your tailnet.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    ACL Concept                                               │
│                                                                              │
│   Source (who)                       Destination (what)                     │
│   ─────────────                      ─────────────────                      │
│   • Users                            • Devices                              │
│   • Groups                           • Tags                                 │
│   • Devices                          • Ports                                │
│   • Autogroups                       • Services                             │
│                                                                              │
│   ACL Rules:                                                                 │
│   "group:dev" ──────► CAN ACCESS ──────► "tag:dev-server:22"               │
│   "group:ops" ──────► CAN ACCESS ──────► "tag:server:*"                    │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Default Behavior

Without custom ACLs, the default policy is:

```json
{
  "acls": [
    {"action": "accept", "src": ["*"], "dst": ["*:*"]}
  ]
}
```

Everyone can access everything - suitable only for small, trusted networks.

## ACL Structure

### Basic Format

```json
{
  "groups": { ... },
  "tagOwners": { ... },
  "acls": [ ... ],
  "ssh": [ ... ],
  "autoApprovers": { ... },
  "tests": [ ... ]
}
```

## Groups

Define user groups:

```json
{
  "groups": {
    "group:admins": ["alice@example.com", "bob@example.com"],
    "group:developers": ["dev1@example.com", "dev2@example.com"],
    "group:ops": ["ops@example.com"]
  }
}
```

### Group Naming

- Must start with `group:`
- Use lowercase
- Descriptive names

## Tags

Tags identify devices by role:

```json
{
  "tagOwners": {
    "tag:server": ["group:ops"],
    "tag:dev-server": ["group:developers"],
    "tag:prod": ["group:ops"]
  }
}
```

### Applying Tags

```bash
# When connecting
sudo tailscale up --advertise-tags=tag:server

# Or via admin console
# Machines → Select device → Edit tags
```

### Tag Ownership

`tagOwners` defines who can use a tag:

```json
{
  "tagOwners": {
    "tag:server": ["group:ops"],      // Only ops can tag devices as "server"
    "tag:dev": ["group:developers"]    // Only devs can tag devices as "dev"
  }
}
```

## ACL Rules

### Basic Rule Structure

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["source"],
      "dst": ["destination:port"]
    }
  ]
}
```

### Examples

```json
{
  "acls": [
    // Admins can access everything
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["*:*"]
    },
    // Developers can SSH to dev servers
    {
      "action": "accept",
      "src": ["group:developers"],
      "dst": ["tag:dev-server:22"]
    },
    // Everyone can access web servers on 80/443
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["tag:webserver:80,443"]
    },
    // Users can access their own devices
    {
      "action": "accept",
      "src": ["autogroup:members"],
      "dst": ["autogroup:self:*"]
    }
  ]
}
```

## Autogroups

Built-in dynamic groups:

| Autogroup | Description |
|-----------|-------------|
| `autogroup:members` | All users in the tailnet |
| `autogroup:self` | Devices owned by the connecting user |
| `autogroup:tagged` | All tagged devices |
| `autogroup:internet` | Internet access (for exit nodes) |
| `autogroup:nonroot` | Non-root Unix users (SSH) |

### Examples

```json
{
  "acls": [
    // Users can access their own devices
    {
      "action": "accept",
      "src": ["autogroup:members"],
      "dst": ["autogroup:self:*"]
    },
    // Allow exit node usage
    {
      "action": "accept",
      "src": ["group:employees"],
      "dst": ["autogroup:internet:*"]
    }
  ]
}
```

## Port Specifications

```json
{
  "acls": [
    // Single port
    {"dst": ["tag:server:22"]},

    // Multiple ports
    {"dst": ["tag:server:22,80,443"]},

    // Port range
    {"dst": ["tag:server:8000-9000"]},

    // All ports
    {"dst": ["tag:server:*"]}
  ]
}
```

## SSH ACLs

Control Tailscale SSH access:

```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["tag:server"],
      "users": ["root", "admin"]
    },
    {
      "action": "accept",
      "src": ["group:developers"],
      "dst": ["tag:dev"],
      "users": ["autogroup:nonroot"]
    },
    {
      "action": "check",
      "src": ["*"],
      "dst": ["tag:prod"],
      "users": ["*"],
      "checkPeriod": "12h"
    }
  ]
}
```

### SSH Action Types

| Action | Behavior |
|--------|----------|
| `accept` | Allow access |
| `check` | Require periodic re-authentication |

## Auto Approvers

Automatically approve routes and exit nodes:

```json
{
  "autoApprovers": {
    "routes": {
      "192.168.1.0/24": ["tag:router"],
      "10.0.0.0/8": ["group:ops"]
    },
    "exitNode": ["tag:exit"]
  }
}
```

## Host Aliases

Create named aliases for IP ranges:

```json
{
  "hosts": {
    "homelab": "192.168.1.0/24",
    "office": "10.0.0.0/8",
    "databases": "10.10.0.0/16"
  },
  "acls": [
    {
      "action": "accept",
      "src": ["group:ops"],
      "dst": ["homelab:*", "office:*"]
    }
  ]
}
```

## Testing ACLs

Add tests to validate your ACLs:

```json
{
  "tests": [
    {
      "src": "alice@example.com",
      "accept": ["server1:22", "server2:80"],
      "deny": ["database:5432"]
    },
    {
      "src": "tag:dev",
      "accept": ["tag:dev-db:5432"],
      "deny": ["tag:prod-db:5432"]
    }
  ]
}
```

Run tests in the admin console ACL editor.

## Complete Example

```json
{
  "groups": {
    "group:admins": ["admin@example.com"],
    "group:developers": ["dev1@example.com", "dev2@example.com"],
    "group:ops": ["ops@example.com"]
  },

  "tagOwners": {
    "tag:server": ["group:ops"],
    "tag:dev-server": ["group:developers"],
    "tag:router": ["group:ops"],
    "tag:exit": ["group:ops"]
  },

  "hosts": {
    "internal": "192.168.0.0/16"
  },

  "acls": [
    // Admins: full access
    {"action": "accept", "src": ["group:admins"], "dst": ["*:*"]},

    // Developers: dev servers and internal network
    {"action": "accept", "src": ["group:developers"], "dst": ["tag:dev-server:*"]},
    {"action": "accept", "src": ["group:developers"], "dst": ["internal:*"]},

    // Ops: all servers
    {"action": "accept", "src": ["group:ops"], "dst": ["tag:server:*"]},

    // Everyone: own devices
    {"action": "accept", "src": ["autogroup:members"], "dst": ["autogroup:self:*"]},

    // Exit node access
    {"action": "accept", "src": ["autogroup:members"], "dst": ["autogroup:internet:*"]}
  ],

  "ssh": [
    {"action": "accept", "src": ["group:admins"], "dst": ["*"], "users": ["*"]},
    {"action": "accept", "src": ["group:developers"], "dst": ["tag:dev-server"], "users": ["autogroup:nonroot"]}
  ],

  "autoApprovers": {
    "routes": {
      "192.168.0.0/16": ["tag:router"]
    },
    "exitNode": ["tag:exit"]
  },

  "tests": [
    {"src": "admin@example.com", "accept": ["tag:server:22", "tag:dev-server:80"]},
    {"src": "dev1@example.com", "accept": ["tag:dev-server:22"], "deny": ["tag:server:22"]}
  ]
}
```

## Best Practices

1. **Start restrictive**: Begin with deny-all, add specific allows
2. **Use groups**: Easier to manage than individual users
3. **Tag devices**: Role-based access is clearer
4. **Write tests**: Validate ACLs before applying
5. **Document rules**: Add comments (HuJSON supports `//`)
6. **Review regularly**: Remove stale rules
7. **Use autogroups**: Leverage built-in dynamic groups
