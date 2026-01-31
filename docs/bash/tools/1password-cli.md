# 1Password CLI

Access 1Password secrets from the command line with biometric authentication.

## Overview

1Password CLI (op) provides:

- **Secret access** - Read passwords, API keys, credentials
- **SSH agent** - Use 1Password as SSH key storage
- **Biometric unlock** - Touch ID, Windows Hello
- **Script integration** - Inject secrets into scripts
- **chezmoi integration** - Templated dotfiles with secrets

## Installation

### macOS

```bash
brew install --cask 1password-cli

# Or download from 1Password
```

### Linux

```bash
# Debian/Ubuntu
curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
  sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
  sudo tee /etc/apt/sources.list.d/1password.list

sudo apt update && sudo apt install 1password-cli
```

### Verify

```bash
op --version
```

## Initial Setup

### Sign In

```bash
# Interactive signin
op signin

# With account shorthand
op signin my.1password.com

# First time setup
op account add --address my.1password.com --email you@example.com
```

### Biometric Unlock (macOS)

1. Open 1Password app
2. Go to Settings > Developer
3. Enable "Integrate with 1Password CLI"
4. Enable "Touch ID for 1Password CLI"

Test biometric:

```bash
op read "op://Personal/GitHub/token"
# Should prompt for Touch ID
```

### Session Management

```bash
# Get session token (without biometric)
eval $(op signin)

# Check current session
op account get

# Sign out
op signout
```

## Reading Secrets

### Secret Reference Format

```
op://vault/item/field
```

Examples:

| Reference | Description |
|-----------|-------------|
| `op://Personal/GitHub/token` | Token field from GitHub item |
| `op://Personal/GitHub/password` | Password field |
| `op://Personal/GitHub/username` | Username field |
| `op://Work/AWS/access_key_id` | Custom field |

### Read Command

```bash
# Read single secret
op read "op://Personal/GitHub/token"

# Read with vault specified
op read "op://Personal/GitHub/token"

# Output to variable
TOKEN=$(op read "op://Personal/GitHub/token")
```

### Get Full Item

```bash
# JSON output
op item get "GitHub" --format json

# Specific field
op item get "GitHub" --fields password

# Multiple fields
op item get "GitHub" --fields username,password
```

### List Items

```bash
# List all items
op item list

# List in vault
op item list --vault Personal

# List with tags
op item list --tags development
```

## SSH Agent Integration

### Enable SSH Agent

1. Open 1Password app
2. Go to Settings > Developer
3. Enable "Use the SSH Agent"

### Configure SSH

Add to `~/.ssh/config`:

```
Host *
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```

For Linux:

```
Host *
    IdentityAgent ~/.1password/agent.sock
```

### Add SSH Key to 1Password

1. Open 1Password
2. Create new item: SSH Key
3. Either import existing key or generate new one
4. The key appears in ssh-add -l

### Verify SSH Agent

```bash
# List keys from 1Password
ssh-add -l

# Test connection
ssh -T git@github.com
```

### Per-Host Key Selection

In `~/.ssh/config`:

```
Host github.com
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
    IdentitiesOnly yes

Host work-server
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
    IdentitiesOnly yes
```

## Environment Variable Injection

### Using op run

```bash
# Run command with secrets injected
op run --env-file .env.template -- python app.py
```

Create `.env.template`:

```bash
DATABASE_URL=op://Development/Database/url
API_KEY=op://Development/API/key
SECRET_KEY=op://Development/App/secret
```

### In Scripts

```bash
#!/bin/bash
# script.sh

export DATABASE_URL="$(op read 'op://Development/Database/url')"
export API_KEY="$(op read 'op://Development/API/key')"

python app.py
```

### Docker Compose

```yaml
# docker-compose.yml
services:
  app:
    image: myapp
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

Run with:

```bash
op run --env-file .env.template -- docker-compose up
```

## chezmoi Integration

### Basic Template

In chezmoi template file (`.tmpl`):

```
# .gitconfig.tmpl
[user]
    name = {{ .name }}
    email = {{ .email }}
    signingkey = {{ onepasswordRead "op://Personal/GPG/key_id" }}

[github]
    token = {{ onepasswordRead "op://Personal/GitHub/token" }}
```

### chezmoi Configuration

In `~/.config/chezmoi/chezmoi.toml`:

```toml
[onepassword]
    command = "op"
```

### Complex Templates

```
# .envrc.tmpl
export DATABASE_URL="{{ onepasswordRead "op://Development/Database/url" }}"
export AWS_ACCESS_KEY_ID="{{ onepasswordRead "op://Work/AWS/access_key_id" }}"
export AWS_SECRET_ACCESS_KEY="{{ onepasswordRead "op://Work/AWS/secret_access_key" }}"
```

### Conditional Secrets

```
{{ if eq .chezmoi.hostname "work-laptop" -}}
export WORK_API_KEY="{{ onepasswordRead "op://Work/API/key" }}"
{{ end -}}
```

## Script Integration

### Bash Script Example

```bash
#!/bin/bash
# deploy.sh

set -e

# Get secrets
DB_PASSWORD=$(op read "op://Production/Database/password")
DEPLOY_TOKEN=$(op read "op://Production/Deploy/token")

# Use in deployment
curl -X POST \
  -H "Authorization: Bearer $DEPLOY_TOKEN" \
  -d "db_password=$DB_PASSWORD" \
  https://api.example.com/deploy
```

### Git Hooks

```bash
#!/bin/bash
# .git/hooks/pre-push

# Verify no secrets in code
if grep -r "$(op read 'op://Personal/GitHub/token')" .; then
    echo "Error: Found secret in code!"
    exit 1
fi
```

### Cron Jobs

```bash
# Use with launchd or systemd for scheduled tasks
# Biometric won't work - use service account or session

# crontab
0 * * * * /path/to/script-with-op.sh
```

For unattended access, use service accounts.

## direnv Integration

```bash
# .envrc
export DATABASE_URL="$(op read 'op://Development/Database/url')"
export API_KEY="$(op read 'op://Development/API/key')"

# Or with dotenv template
# .env.template
# DATABASE_URL=op://Development/Database/url
# API_KEY=op://Development/API/key

# .envrc
op run --env-file .env.template --no-masking -- direnv allow
```

## Service Accounts

For CI/CD and automated systems without biometric:

### Create Service Account

1. Go to 1Password.com > Settings > Service Accounts
2. Create new service account
3. Grant vault access
4. Save token securely

### Use in CI/CD

```yaml
# GitHub Actions
env:
  OP_SERVICE_ACCOUNT_TOKEN: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}

steps:
  - name: Get secrets
    run: |
      DATABASE_URL=$(op read "op://Vault/Item/field")
```

## Common Operations

### Create Items

```bash
# Create login
op item create --category login \
  --title "New Service" \
  --vault Personal \
  username=admin \
  password=secretpassword

# Create with generated password
op item create --category login \
  --title "New Service" \
  --vault Personal \
  --generate-password
```

### Edit Items

```bash
# Edit field
op item edit "GitHub" password=newpassword

# Edit with vault
op item edit "GitHub" --vault Personal token=newtoken
```

### Delete Items

```bash
# Delete item
op item delete "Old Service"

# Delete with confirmation skip
op item delete "Old Service" --force
```

## Security Best Practices

1. **Use biometric** - Enable Touch ID/Windows Hello
2. **Limit vault access** - Only grant necessary vaults
3. **Audit access** - Review 1Password audit logs
4. **Short sessions** - Sign out when not needed
5. **Service accounts** - Use for CI/CD, not personal tokens

### Prevent Secrets in History

```bash
# Good - no secret in command
op read "op://Personal/GitHub/token" | pbcopy

# Bad - secret visible in history
curl -H "Authorization: $(op read 'op://...')" https://api.example.com
# Better
TOKEN=$(op read "op://Personal/API/token")
curl -H "Authorization: Bearer $TOKEN" https://api.example.com
unset TOKEN
```

## Troubleshooting

### Biometric Not Working

```bash
# Verify 1Password app settings
# Developer > Integrate with 1Password CLI

# Check agent is running
op signin --help  # Should not ask for master password if biometric enabled
```

### Session Expired

```bash
# Re-authenticate
eval $(op signin)

# Or with biometric
op read "op://Personal/Test/password"  # Triggers biometric
```

### SSH Agent Issues

```bash
# Verify socket exists
ls -la ~/Library/Group\ Containers/2BUA8C4S2C.com.1password/t/agent.sock

# Test agent
SSH_AUTH_SOCK="$HOME/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock" ssh-add -l
```

### Item Not Found

```bash
# List items to find correct name
op item list --vault Personal

# Search for item
op item list | grep -i github
```

## Reference

### Useful Commands

| Command | Description |
|---------|-------------|
| `op signin` | Authenticate |
| `op signout` | End session |
| `op account get` | Current account info |
| `op vault list` | List vaults |
| `op item list` | List items |
| `op item get` | Get item details |
| `op read` | Read single field |
| `op run` | Run with injected secrets |

### Environment Variables

| Variable | Description |
|----------|-------------|
| `OP_SERVICE_ACCOUNT_TOKEN` | Service account auth |
| `OP_BIOMETRIC_UNLOCK_ENABLED` | Biometric status |
| `OP_ACCOUNT` | Default account |

## See Also

- [chezmoi](chezmoi.md) - Dotfiles with secrets
- [direnv](direnv.md) - Environment management
- [SSH Configuration](../../ssh/client/configuration.md) - SSH setup
- [Secrets Management](../../operations/secrets-management.md) - Secret storage overview
