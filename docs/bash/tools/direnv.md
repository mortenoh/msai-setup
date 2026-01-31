# direnv

Load and unload environment variables based on the current directory.

## Overview

direnv provides:

- **Automatic loading** - Activates when entering directory
- **Security** - Explicit allow/deny for .envrc files
- **Shell integration** - Works with bash, zsh, fish
- **Tool integration** - Python venvs, Node versions, secrets
- **Unloading** - Cleans up when leaving directory

## Installation

### macOS

```bash
brew install direnv
```

### Linux

```bash
# Debian/Ubuntu
sudo apt install direnv

# Arch
sudo pacman -S direnv

# Or from binary
curl -sfL https://direnv.net/install.sh | bash
```

### Verify

```bash
direnv version
```

## Shell Integration

### Bash

Add to `~/.bashrc`:

```bash
eval "$(direnv hook bash)"
```

### Zsh

Add to `~/.zshrc`:

```bash
eval "$(direnv hook zsh)"
```

### Fish

Add to `~/.config/fish/config.fish`:

```fish
direnv hook fish | source
```

Restart your shell after adding the hook.

## Basic Usage

### Create .envrc

```bash
cd ~/project

# Create environment file
echo 'export PROJECT_NAME="my-project"' > .envrc

# Allow the file
direnv allow
```

### Automatic Loading

```bash
$ cd ~/project
direnv: loading ~/project/.envrc
direnv: export +PROJECT_NAME

$ echo $PROJECT_NAME
my-project

$ cd ~
direnv: unloading
```

### Edit and Reload

```bash
# Edit .envrc
direnv edit

# Manually reload
direnv reload

# Block current .envrc
direnv deny
```

## .envrc Patterns

### Basic Environment Variables

```bash
# .envrc
export DATABASE_URL="postgres://localhost/mydb"
export API_KEY="development-key"
export DEBUG=true
```

### Path Additions

```bash
# Add project bin to PATH
PATH_add bin
PATH_add scripts

# Or manually
export PATH="$PWD/bin:$PATH"
```

### Source Files

```bash
# Source other files
source_env .envrc.local
source_env_if_exists .envrc.secrets

# Dot files
dotenv
dotenv_if_exists .env.local
```

### Conditional Logic

```bash
# Only on specific OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    export MACOS=true
fi

# Check if command exists
if has docker; then
    export DOCKER_AVAILABLE=true
fi
```

## Python Virtual Environments

### With uv

```bash
# .envrc
layout python-venv

# Or specify Python version
layout python-venv python3.12

# Using uv (recommended)
if has uv; then
    # Create venv if needed
    if [ ! -d .venv ]; then
        uv venv
    fi
    source .venv/bin/activate
fi
```

### Custom Layout for uv

Add to `~/.config/direnv/direnvrc`:

```bash
layout_uv() {
    if [ ! -d .venv ]; then
        log_status "Creating venv with uv"
        uv venv
    fi
    source .venv/bin/activate
}
```

Use in project:

```bash
# .envrc
layout uv
```

### With pyenv

```bash
# .envrc
layout pyenv 3.12.0
```

### Poetry Projects

```bash
# .envrc
layout poetry
```

## Node.js Version Management

### With nvm

```bash
# .envrc
use nvm 20
```

Add to `~/.config/direnv/direnvrc`:

```bash
use_nvm() {
    local version="$1"
    local nvmrc_path="$PWD/.nvmrc"

    if [ -z "$version" ] && [ -e "$nvmrc_path" ]; then
        version=$(cat "$nvmrc_path")
    fi

    if [ -z "$version" ]; then
        log_error "No Node version specified"
        return 1
    fi

    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && source "$NVM_DIR/nvm.sh"

    nvm use "$version"
}
```

### With fnm

```bash
# .envrc
use fnm
```

Add to direnvrc:

```bash
use_fnm() {
    local version
    if [ -e .nvmrc ]; then
        version=$(cat .nvmrc)
    elif [ -e .node-version ]; then
        version=$(cat .node-version)
    else
        version="$1"
    fi

    eval "$(fnm env)"
    fnm use "$version"
}
```

### Direct Node Path

```bash
# .envrc
PATH_add node_modules/.bin
```

## Secrets Management

### From .env Files

```bash
# .envrc
dotenv

# Or from specific file
dotenv .env.development
```

### From 1Password

```bash
# .envrc
export DATABASE_PASSWORD="$(op read 'op://Development/Database/password')"
export API_KEY="$(op read 'op://Development/API/key')"
```

### From pass

```bash
# .envrc
export API_KEY="$(pass show project/api-key)"
```

### Local Secrets File

```bash
# .envrc
source_env_if_exists .envrc.local

# .gitignore
.envrc.local
```

Create `.envrc.local` for machine-specific secrets:

```bash
# .envrc.local (not committed)
export SECRET_KEY="actual-secret-value"
```

## Layout Commands

### Built-in Layouts

| Layout | Purpose |
|--------|---------|
| `layout python` | Python virtualenv |
| `layout python3` | Python 3 virtualenv |
| `layout ruby` | Ruby with rbenv/rvm |
| `layout go` | Go workspace |
| `layout node` | Node with nvm |

### Custom Layouts

Add to `~/.config/direnv/direnvrc`:

```bash
# Rust layout
layout_rust() {
    export CARGO_HOME="$PWD/.cargo"
    export RUSTUP_HOME="$PWD/.rustup"
    PATH_add "$CARGO_HOME/bin"
}

# Docker Compose layout
layout_docker() {
    export COMPOSE_PROJECT_NAME="$(basename "$PWD")"
    export COMPOSE_FILE="docker-compose.yml"
    if [ -e "docker-compose.override.yml" ]; then
        export COMPOSE_FILE="$COMPOSE_FILE:docker-compose.override.yml"
    fi
}
```

## Security

### Allow/Deny

```bash
# Allow current directory
direnv allow

# Deny (block) current directory
direnv deny

# Allow specific path
direnv allow /path/to/project
```

### Whitelist Patterns

Create `~/.config/direnv/direnv.toml`:

```toml
[whitelist]
prefix = [
    "~/dev",
    "~/work"
]

exact = [
    "~/dotfiles"
]
```

### Security Best Practices

1. Never commit `.envrc.local` with secrets
2. Use password managers for sensitive data
3. Review `.envrc` before allowing
4. Keep secrets in separate sourced files

```bash
# .envrc (committed)
source_env_if_exists .envrc.secrets
export APP_ENV="development"

# .envrc.secrets (not committed)
export API_KEY="sensitive-value"
```

## Integration Examples

### Full Python Project

```bash
# .envrc
# Python environment
layout uv

# Add local scripts to PATH
PATH_add scripts

# Load .env file
dotenv_if_exists

# Project configuration
export PYTHONPATH="$PWD/src"
export DJANGO_SETTINGS_MODULE="project.settings.local"

# Local secrets
source_env_if_exists .envrc.local
```

### Full Node.js Project

```bash
# .envrc
# Node version from .nvmrc
use nvm

# Add binaries to PATH
PATH_add node_modules/.bin

# Load environment
dotenv_if_exists .env.development

# Project name for Docker
export COMPOSE_PROJECT_NAME="$(basename "$PWD")"
```

### Full Docker Development

```bash
# .envrc
# Docker configuration
export COMPOSE_PROJECT_NAME="myproject"
export COMPOSE_FILE="docker-compose.yml:docker-compose.dev.yml"
export DOCKER_BUILDKIT=1

# Database for local dev
export DATABASE_URL="postgres://dev:dev@localhost:5432/myproject"

# Add helper scripts
PATH_add scripts
```

### Monorepo Setup

```bash
# .envrc (root)
export MONOREPO_ROOT="$PWD"
PATH_add scripts

# packages/api/.envrc
source_up
export SERVICE_NAME="api"
layout uv

# packages/web/.envrc
source_up
export SERVICE_NAME="web"
use nvm
```

## Troubleshooting

### Not Loading

```bash
# Check if allowed
direnv status

# Force reload
direnv reload

# Check hook is installed
type direnv
```

### Slow Loading

```bash
# Use cached operations
# Instead of:
export PATH="$(npm bin):$PATH"

# Use:
PATH_add node_modules/.bin
```

### Debug Mode

```bash
# Show verbose output
export DIRENV_LOG_FORMAT="%s"
direnv reload

# Or set in shell config
export DIRENV_LOG_FORMAT='direnv: %s'
```

### Common Errors

```bash
# "direnv: error .envrc is blocked"
direnv allow

# "direnv: command not found"
# Add hook to shell config and restart

# Variables not unloading
# Ensure hook is last in shell config
```

## Configuration Reference

### direnv.toml

Create `~/.config/direnv/direnv.toml`:

```toml
[global]
# Load .envrc from parent directories
load_dotenv = true

# Warn about changes
warn_timeout = "5s"

[whitelist]
prefix = [
    "~/dev",
    "~/work",
    "~/projects"
]
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `DIRENV_LOG_FORMAT` | Log output format |
| `DIRENV_BASH` | Path to bash for .envrc |
| `DIRENV_DIR` | Current .envrc directory |
| `DIRENV_WATCHES` | File watch list |

## See Also

- [chezmoi](chezmoi.md) - Dotfiles management
- [1Password CLI](1password-cli.md) - Secrets from 1Password
- [uv](uv.md) - Python package manager
- [Environment Configuration](../configuration/environment.md) - Shell environment
