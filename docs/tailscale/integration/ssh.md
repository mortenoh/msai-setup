# Tailscale SSH

## Overview

Tailscale SSH provides secure, passwordless SSH access using Tailscale identities instead of traditional SSH keys.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Traditional SSH vs Tailscale SSH                          │
│                                                                              │
│   Traditional SSH                       Tailscale SSH                       │
│   ─────────────────                     ──────────────                      │
│                                                                              │
│   • Manage SSH keys                     • Use Tailscale identity            │
│   • Configure authorized_keys           • No key management                 │
│   • Handle key rotation                 • Automatic authentication          │
│   • Port 22 exposure                    • No port exposure                  │
│   • Password or key auth                • Identity-based auth               │
│                                                                              │
│   ssh -i key user@host                  ssh user@host (via Tailscale)      │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Enabling Tailscale SSH

### On the Server

```bash
sudo tailscale up --ssh
```

Or persistently:

```bash
sudo tailscale set --ssh
```

### Verify SSH is Running

```bash
tailscale status
# Shows "ssh" in capabilities

tailscale status --json | jq '.Self.Capabilities'
```

## Connecting via Tailscale SSH

### Basic Connection

```bash
# Using Tailscale hostname
ssh user@my-server

# Using Tailscale IP
ssh user@100.100.100.2

# Using full DNS name
ssh user@my-server.tailnet.ts.net
```

### Using tailscale ssh Command

```bash
tailscale ssh user@my-server
```

This uses Tailscale's SSH client which provides additional features.

## SSH Check Mode

Validate SSH configuration without connecting:

```bash
tailscale ssh --check user@my-server
```

## Access Control with ACLs

Control SSH access via Tailscale ACLs:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["tag:server:*"],
      "users": ["root", "admin"]
    },
    {
      "action": "accept",
      "src": ["group:developers"],
      "dst": ["tag:dev-server:*"],
      "users": ["autogroup:nonroot"]
    }
  ],
  "ssh": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["tag:server"],
      "users": ["root", "admin"]
    },
    {
      "action": "accept",
      "src": ["autogroup:members"],
      "dst": ["autogroup:self"],
      "users": ["autogroup:nonroot"]
    }
  ]
}
```

### SSH ACL Options

| Field | Description |
|-------|-------------|
| `action` | `accept` or `check` |
| `src` | Source users/groups |
| `dst` | Destination devices |
| `users` | Unix users allowed |
| `checkPeriod` | Re-check interval |

### Special Values

| Value | Meaning |
|-------|---------|
| `autogroup:members` | All tailnet members |
| `autogroup:self` | User's own devices |
| `autogroup:nonroot` | Any non-root user |
| `root` | Root user specifically |

## Session Recording

Record SSH sessions for audit:

```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["group:employees"],
      "dst": ["tag:production"],
      "users": ["ubuntu"],
      "recorder": ["tag:recorder"]
    }
  ]
}
```

### Setting Up Recorder

```bash
# On recorder device
sudo tailscale up --advertise-tags=tag:recorder

# Sessions stored in /var/log/tailscale/
```

## SSH vs Traditional SSH

### When to Use Tailscale SSH

| Scenario | Use Tailscale SSH |
|----------|-------------------|
| Key management burden | ✓ |
| Identity-based access | ✓ |
| Audit/compliance needs | ✓ |
| Quick, secure access | ✓ |
| Existing SSH workflows | Consider both |

### Running Both

You can run traditional SSH alongside Tailscale SSH:

```bash
# Tailscale SSH on Tailscale interface
# Traditional SSH on regular interface

# sshd still listens on port 22
# Tailscale SSH uses Tailscale network
```

## SSH Configuration

### Client SSH Config

Configure SSH client to use Tailscale:

```bash
# ~/.ssh/config
Host *.tailnet.ts.net
    # Uses standard SSH through Tailscale network

Host my-server
    HostName my-server.tailnet.ts.net
    User admin
```

### ProxyCommand (Optional)

Force traffic through Tailscale:

```bash
Host my-server
    HostName my-server.tailnet.ts.net
    ProxyCommand tailscale nc %h %p
```

## SCP and SFTP

Tailscale SSH supports file transfer:

```bash
# SCP
scp file.txt user@my-server:/path/

# SFTP
sftp user@my-server
```

## Port Forwarding

SSH port forwarding works through Tailscale:

```bash
# Local forward
ssh -L 8080:localhost:80 user@my-server

# Remote forward
ssh -R 9090:localhost:3000 user@my-server
```

## SSH Agent Forwarding

```bash
# Forward SSH agent
ssh -A user@my-server

# Or in config
Host my-server
    ForwardAgent yes
```

!!! warning "Security"
    Agent forwarding has security implications. Use judiciously.

## Disabling Tailscale SSH

### On Specific Device

```bash
sudo tailscale up --ssh=false
```

### Via ACLs

Block SSH in ACLs:

```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["tag:server"],
      "users": ["*"]
    }
    // No rule for other users = denied
  ]
}
```

## Troubleshooting

### Connection Refused

```bash
# Check SSH is enabled
tailscale status --json | jq '.Self.Capabilities'

# Verify SSH daemon
sudo tailscale set --ssh

# Check ACLs allow connection
```

### Permission Denied

```bash
# Check ACL allows your user
# Verify Unix user exists on target
id username

# Check ACL ssh section
```

### Can't Login as Root

ACLs must explicitly allow root:

```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["group:admins"],
      "dst": ["*"],
      "users": ["root"]  // Explicit root access
    }
  ]
}
```

### Debugging

```bash
# Verbose SSH
ssh -v user@my-server

# Check Tailscale logs
journalctl -u tailscaled -f

# Test connectivity
tailscale ping my-server
```

## Security Benefits

1. **No exposed ports**: SSH not accessible from internet
2. **No key management**: Tailscale handles authentication
3. **Identity-based**: Know who's connecting
4. **Centralized ACLs**: Single point of access control
5. **Session recording**: Audit capability
6. **MFA support**: Through identity provider

## Integration Examples

### VS Code Remote SSH

```json
// settings.json
{
  "remote.SSH.configFile": "~/.ssh/config"
}
```

```bash
# ~/.ssh/config
Host my-server
    HostName my-server.tailnet.ts.net
    User developer
```

### Ansible

```yaml
# inventory.yml
all:
  hosts:
    web:
      ansible_host: web.tailnet.ts.net
    db:
      ansible_host: db.tailnet.ts.net
  vars:
    ansible_user: deploy
```

### GitHub Actions

```yaml
- name: SSH to server
  run: |
    tailscale up --auth-key=${{ secrets.TS_AUTHKEY }}
    ssh user@server.tailnet.ts.net "deploy.sh"
```
