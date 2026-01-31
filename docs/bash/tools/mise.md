# mise (formerly rtx)

mise is a modern polyglot tool version manager - a faster, more feature-rich alternative to asdf.

## Why mise?

- **Fast** - Written in Rust, significantly faster than asdf
- **Compatible** - Uses asdf plugins, drop-in replacement
- **Modern** - Better UX, more features
- **Task runner** - Built-in task execution
- **Env management** - Manages environment variables too

## Installation

### macOS

```bash
brew install mise
```

### Linux

```bash
curl https://mise.run | sh
```

### Cargo

```bash
cargo install mise
```

### Shell Integration

```bash
# Bash (~/.bashrc)
eval "$(mise activate bash)"

# Zsh (~/.zshrc)
eval "$(mise activate zsh)"

# Fish (~/.config/fish/config.fish)
mise activate fish | source
```

## Basic Usage

### Plugin/Tool Management

```bash
# mise uses "backends" (plugins)
# Most tools work without explicit plugin installation

# Install a tool
mise install node@20
mise install python@3.12
mise install go@1.21

# Install multiple at once
mise install node@20 python@3.12 go@1.21

# List installed
mise list

# Uninstall
mise uninstall node@18
```

### Setting Versions

```bash
# Global version
mise use --global node@20
mise use --global python@3.12

# Local version (creates .mise.toml)
mise use node@20
mise use python@3.12

# Current shell only
mise shell node@18
```

## Configuration Files

### .mise.toml (Preferred)

```toml
# .mise.toml
[tools]
node = "20"
python = "3.12"
go = "1.21"

[env]
NODE_ENV = "development"
DATABASE_URL = "postgres://localhost/mydb"

[tasks.dev]
run = "npm run dev"

[tasks.test]
run = "pytest"
```

### .tool-versions (asdf compatible)

```
# .tool-versions
node 20.10.0
python 3.12.0
go 1.21.5
```

mise reads both formats.

## Task Runner

### Define Tasks

```toml
# .mise.toml
[tasks.build]
run = "npm run build"
description = "Build the project"

[tasks.test]
run = "pytest -v"
description = "Run tests"

[tasks.dev]
run = "npm run dev"
description = "Start dev server"

[tasks.lint]
run = [
  "eslint src/",
  "prettier --check ."
]
description = "Run linters"
```

### Run Tasks

```bash
# Run a task
mise run build
mise run test

# List available tasks
mise tasks

# Run with arguments
mise run test -- -k "test_specific"
```

### Task Dependencies

```toml
[tasks.build]
depends = ["lint", "test"]
run = "npm run build"

[tasks.deploy]
depends = ["build"]
run = "npm run deploy"
```

## Environment Variables

### In .mise.toml

```toml
[env]
NODE_ENV = "development"
API_URL = "http://localhost:3000"

# Load from file
_.file = ".env"

# Conditional
[env.production]
NODE_ENV = "production"
```

### Directory-specific

```bash
# Set env for current directory
mise set NODE_ENV=development
mise set DATABASE_URL=postgres://localhost/db

# View current env
mise env
```

## Aliases

```toml
# ~/.config/mise/config.toml
[alias.node]
lts = "20.10.0"
current = "21.5.0"

[alias.python]
default = "3.12.0"
```

```bash
mise install node@lts
mise use node@lts
```

## Settings

### Global Configuration

```toml
# ~/.config/mise/config.toml
[settings]
experimental = true
verbose = false
asdf_compat = true  # Full asdf compatibility

[tools]
# Global defaults
node = "lts"
python = "3.12"
```

### Legacy Version Files

```toml
# ~/.config/mise/config.toml
[settings]
legacy_version_file = true  # Read .nvmrc, .python-version, etc.
```

## Hooks

```toml
# .mise.toml
[hooks]
# Run when entering directory
enter = "echo 'Entered project'"

# Run when changing tools
postinstall = "echo 'Tools updated'"
```

## Commands Reference

### Tools

```bash
# Install tools
mise install node@20
mise install node@20 python@3.12  # Multiple

# Use tools
mise use node@20              # Local (.mise.toml)
mise use --global node@20     # Global
mise shell node@18            # Current shell

# List
mise list                     # Installed tools
mise list node                # Specific tool versions
mise list --missing           # Missing from config

# Outdated
mise outdated                 # Check for updates
mise upgrade                  # Upgrade all
```

### Tasks

```bash
# Run tasks
mise run <task>
mise run build
mise run test -- --verbose

# List tasks
mise tasks
```

### Environment

```bash
# View environment
mise env
mise env --json

# Set variables
mise set KEY=value
mise unset KEY
```

### Info

```bash
# Current versions
mise current
mise current node

# Which binary
mise which node
mise where node@20

# Doctor (check setup)
mise doctor
```

## Migration from asdf

```bash
# mise is asdf-compatible
# Your .tool-versions files work as-is

# Install mise
brew install mise

# Remove asdf from shell config
# Replace with mise activation

# Install tools from .tool-versions
mise install
```

## IDE Integration

### VS Code

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "eslint.nodePath": "${env:HOME}/.local/share/mise/installs/node/20/lib/node_modules"
}
```

### Use in Scripts

```bash
#!/bin/bash
eval "$(mise activate bash)"

# Now tools are available
node --version
python --version
```

## Performance Comparison

| Operation | asdf | mise |
|-----------|------|------|
| Install node | 45s | 12s |
| Version switch | 200ms | 5ms |
| Shell startup | 300ms | 50ms |

## Best Practices

1. **Use .mise.toml** - More powerful than .tool-versions
2. **Define tasks** - Replace Makefiles for simple projects
3. **Set env in config** - Keep secrets in .env, track non-secrets
4. **Use hooks** - Automate setup on directory entry

## See Also

- [asdf](asdf.md) - Original tool
- [direnv](direnv.md) - Environment management
- [Node.js](nodejs.md) - Node-specific setup
