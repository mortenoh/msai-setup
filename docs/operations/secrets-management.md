# Secrets Management

Overview of storing and managing sensitive data across development and production.

## Overview

Secrets management addresses:

- **Where to store** - Different solutions for different contexts
- **Access control** - Who can access what
- **Rotation** - Changing secrets without downtime
- **Audit** - Tracking secret access

## Secret Types

| Type | Examples | Storage |
|------|----------|---------|
| API keys | GitHub tokens, cloud APIs | Password manager, env vars |
| Database credentials | Connection strings | Environment, secrets manager |
| SSH keys | Server access, Git auth | SSH agent, 1Password |
| TLS certificates | HTTPS, mTLS | Let's Encrypt, cloud provider |
| Encryption keys | Data at rest | HSM, KMS |

## Local Development

### Environment Variables

For local-only, non-sensitive development config:

```bash
# .envrc (with direnv)
export DATABASE_URL="postgres://localhost/dev"
export API_URL="http://localhost:3000"
```

### .env Files

For project-specific environment:

```bash
# .env (committed - non-sensitive defaults)
NODE_ENV=development
API_URL=http://localhost:3000

# .env.local (not committed - sensitive)
DATABASE_PASSWORD=localpass
API_KEY=dev-key-123
```

`.gitignore`:
```
.env.local
.env.*.local
```

### Password Managers (1Password CLI)

For actual secrets:

```bash
# Read secret at runtime
export API_KEY="$(op read 'op://Development/API/key')"

# Or with direnv
# .envrc
export API_KEY="$(op read 'op://Development/API/key')"
```

See [1Password CLI](../bash/tools/1password-cli.md) for setup.

## SSH Keys Management

### Generate Keys

```bash
# Ed25519 (recommended)
ssh-keygen -t ed25519 -C "you@example.com"

# RSA (legacy compatibility)
ssh-keygen -t rsa -b 4096 -C "you@example.com"
```

### Key Locations

| Key | Path | Permission |
|-----|------|------------|
| Private | `~/.ssh/id_ed25519` | 600 |
| Public | `~/.ssh/id_ed25519.pub` | 644 |
| Config | `~/.ssh/config` | 600 |

### SSH Agent

```bash
# Start agent
eval "$(ssh-agent -s)"

# Add key
ssh-add ~/.ssh/id_ed25519

# List keys
ssh-add -l
```

### 1Password SSH Agent

Better approach - store keys in 1Password:

1. Store SSH key in 1Password
2. Enable SSH agent in 1Password settings
3. Configure `~/.ssh/config`:

```
Host *
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```

See [1Password CLI SSH Setup](../bash/tools/1password-cli.md#ssh-agent-integration).

## CI/CD Secrets

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Deploy
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: ./deploy.sh
```

Set secrets in: Repository Settings > Secrets and variables > Actions

### Environment-Specific

```yaml
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production  # Uses production environment secrets
    steps:
      - name: Deploy
        env:
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
```

### OIDC for Cloud Access

Avoid long-lived credentials:

```yaml
jobs:
  deploy:
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/github-deploy
          aws-region: us-east-1
```

## Docker Secrets

### Docker Compose (Development)

```yaml
services:
  app:
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

With `.env` file:
```
DATABASE_URL=postgres://user:pass@db:5432/app
```

### Docker Swarm Secrets

```bash
# Create secret
echo "mypassword" | docker secret create db_password -

# Use in service
docker service create \
  --name app \
  --secret db_password \
  myapp
```

```yaml
# docker-compose.yml (swarm mode)
services:
  app:
    secrets:
      - db_password

secrets:
  db_password:
    external: true
```

Access in container: `/run/secrets/db_password`

### Build-Time Secrets

```dockerfile
# Dockerfile
# syntax=docker/dockerfile:1.2

FROM node:20
RUN --mount=type=secret,id=npmrc,target=/root/.npmrc \
    npm ci
```

```bash
docker build --secret id=npmrc,src=$HOME/.npmrc .
```

## Git Safety

### .gitignore

Essential patterns:

```gitignore
# Environment files
.env
.env.local
.env.*.local
.envrc.local

# Credentials
*.pem
*.key
credentials.json
secrets.json
.secrets/

# IDE
.idea/
.vscode/settings.json

# OS
.DS_Store
```

### Pre-commit Hooks

Using [git-secrets](https://github.com/awslabs/git-secrets):

```bash
# Install
brew install git-secrets

# Initialize in repo
cd repo
git secrets --install

# Add AWS patterns
git secrets --register-aws

# Add custom patterns
git secrets --add 'password\s*=\s*.+'
git secrets --add --literal 'AKIAIOSFODNN7EXAMPLE'
```

### Gitleaks

```bash
# Install
brew install gitleaks

# Scan repo
gitleaks detect --source .

# Pre-commit hook
gitleaks protect --staged
```

### Pre-commit Framework

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.18.0
    hooks:
      - id: gitleaks

  - repo: https://github.com/awslabs/git-secrets
    rev: master
    hooks:
      - id: git-secrets
```

## Secret Rotation

### Database Credentials

```bash
# 1. Create new credentials
# 2. Update application config
# 3. Deploy with new credentials
# 4. Verify application works
# 5. Revoke old credentials
```

### API Keys

```bash
# In 1Password, store both old and new keys during rotation
# Update references
# Verify
# Remove old key
```

### SSH Keys

```bash
# 1. Generate new key
ssh-keygen -t ed25519 -C "you@example.com" -f ~/.ssh/id_ed25519_new

# 2. Add new key to services
# 3. Update 1Password / SSH agent
# 4. Test access
# 5. Remove old key from services
```

## Best Practices

### Do

- Use password managers for all secrets
- Use SSH agent (preferably 1Password)
- Use OIDC in CI/CD when possible
- Rotate secrets regularly
- Audit secret access
- Use environment-specific secrets

### Don't

- Commit secrets to git (even private repos)
- Log secrets
- Share secrets via chat/email
- Use the same secret across environments
- Store secrets in code comments
- Use weak passwords for any credential

### Secret Hierarchy

| Priority | Solution | Use Case |
|----------|----------|----------|
| 1 | OIDC/Workload Identity | Cloud CI/CD |
| 2 | Cloud Secrets Manager | Production |
| 3 | 1Password/Bitwarden | Development |
| 4 | Environment variables | Local only, non-sensitive |

## Emergency Response

### If Secret is Exposed

1. **Rotate immediately** - Generate new secret
2. **Revoke old secret** - Disable exposed credential
3. **Audit access** - Check for unauthorized use
4. **Update all references** - Deploy with new secret
5. **Document** - Record incident for review

### Git History Cleanup

If secret was committed:

```bash
# Using git-filter-repo (recommended)
pip install git-filter-repo
git filter-repo --invert-paths --path secrets.json

# Force push (coordinate with team)
git push --force-with-lease
```

Note: Anyone with a clone still has the secret. Always rotate.

## See Also

- [1Password CLI](../bash/tools/1password-cli.md) - Password manager CLI
- [chezmoi](../bash/tools/chezmoi.md) - Dotfiles with secrets
- [direnv](../bash/tools/direnv.md) - Environment management
- [SSH Fundamentals](../ssh/fundamentals/keys.md) - SSH key management
