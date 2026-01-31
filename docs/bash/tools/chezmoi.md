# chezmoi

Manage dotfiles across multiple machines with templates, secrets, and version control.

## Overview

chezmoi provides:

- **Templates** - Machine-specific configurations with Go templates
- **Secrets** - Integration with 1Password, Bitwarden, pass
- **Multi-machine** - Different configs per hostname/OS
- **Version control** - Git-based source of truth
- **Encryption** - Optional file encryption

## Installation

### macOS

```bash
brew install chezmoi
```

### Linux

```bash
# Script install
sh -c "$(curl -fsLS get.chezmoi.io)"

# Or with package manager
sudo apt install chezmoi  # Debian/Ubuntu
sudo pacman -S chezmoi    # Arch
```

### Verify

```bash
chezmoi --version
```

## Quick Start

### Initialize

```bash
# Create new source directory
chezmoi init

# Or init from existing repo
chezmoi init https://github.com/username/dotfiles.git
```

### Add Files

```bash
# Add dotfiles
chezmoi add ~/.bashrc
chezmoi add ~/.gitconfig
chezmoi add ~/.config/starship.toml

# Add entire directory
chezmoi add ~/.config/nvim
```

### Apply Changes

```bash
# See what would change
chezmoi diff

# Apply changes
chezmoi apply

# Apply with verbose output
chezmoi apply -v
```

### Edit Files

```bash
# Edit source file
chezmoi edit ~/.bashrc

# Edit and apply
chezmoi edit --apply ~/.bashrc
```

## Directory Structure

```
~/.local/share/chezmoi/
├── .chezmoi.toml.tmpl       # Config template
├── .chezmoiignore           # Files to ignore
├── .chezmoiexternal.toml    # External files
├── dot_bashrc               # ~/.bashrc
├── dot_gitconfig.tmpl       # ~/.gitconfig (template)
├── private_dot_ssh/         # ~/.ssh (private)
│   └── config.tmpl
├── run_once_install.sh      # Run once script
└── dot_config/              # ~/.config
    └── nvim/
        └── init.lua
```

### Naming Conventions

| Prefix | Meaning |
|--------|---------|
| `dot_` | Becomes `.` |
| `private_` | File mode 0600 |
| `empty_` | Empty file |
| `executable_` | File mode 0755 |
| `readonly_` | Read-only |
| `exact_` | Remove extra files |
| `.tmpl` | Template file |

## Templates

### Basic Template Syntax

Create `dot_gitconfig.tmpl`:

```
[user]
    name = {{ .name }}
    email = {{ .email }}

[core]
    editor = {{ .editor | default "vim" }}
```

### Configuration Data

Create `~/.config/chezmoi/chezmoi.toml`:

```toml
[data]
    name = "Your Name"
    email = "you@example.com"
    editor = "nvim"
```

### Conditional Templates

```
{{ if eq .chezmoi.os "darwin" -}}
# macOS-specific
alias ls="ls -G"
{{ else if eq .chezmoi.os "linux" -}}
# Linux-specific
alias ls="ls --color=auto"
{{ end -}}
```

### Hostname-Based Config

```
{{ if eq .chezmoi.hostname "work-laptop" -}}
export COMPANY_EMAIL="{{ .work_email }}"
{{ end -}}

{{ if eq .chezmoi.hostname "home-desktop" -}}
export GAMING_MODE=true
{{ end -}}
```

### Template Variables

Built-in variables:

| Variable | Description |
|----------|-------------|
| `.chezmoi.os` | Operating system |
| `.chezmoi.arch` | Architecture |
| `.chezmoi.hostname` | Machine hostname |
| `.chezmoi.username` | Current user |
| `.chezmoi.homeDir` | Home directory |
| `.chezmoi.sourceDir` | Source directory |

## Secrets Management

### 1Password Integration

Install 1Password CLI, then in template:

```
{{ onepasswordRead "op://Personal/GitHub/token" }}
```

Or with item reference:

```toml
# chezmoi.toml
[onepassword]
    command = "op"

[data]
    github_token = {{ onepasswordRead "op://Personal/GitHub/token" | quote }}
```

### Bitwarden Integration

```bash
# Login first
bw login
bw unlock
export BW_SESSION="..."
```

In template:

```
{{ (bitwarden "item" "github-token").login.password }}
```

### pass Integration

```
{{ (pass "github/token") }}
```

### Environment Variables

```
{{ env "GITHUB_TOKEN" }}
```

### Encrypted Files

```bash
# Initialize encryption
chezmoi init --config-path ~/.config/chezmoi/chezmoi.toml

# Add encryption key
chezmoi age key add
```

In `chezmoi.toml`:

```toml
encryption = "age"
[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age1..."
```

Add encrypted files:

```bash
chezmoi add --encrypt ~/.ssh/id_ed25519
```

## Multi-Machine Configuration

### OS-Specific Files

```
~/.local/share/chezmoi/
├── dot_bashrc.tmpl                # All systems
├── dot_bashrc_darwin.tmpl         # macOS only (not built-in)
└── .chezmoiignore
```

Using `.chezmoiignore`:

```
{{ if ne .chezmoi.os "darwin" }}
.config/karabiner
{{ end }}

{{ if ne .chezmoi.os "linux" }}
.config/i3
{{ end }}
```

### Machine Classes

In `chezmoi.toml.tmpl`:

```toml
{{ $isWork := eq .chezmoi.hostname "work-laptop" -}}
{{ $isPersonal := or (eq .chezmoi.hostname "home-desktop") (eq .chezmoi.hostname "personal-laptop") -}}

[data]
    isWork = {{ $isWork }}
    isPersonal = {{ $isPersonal }}
```

Use in templates:

```
{{ if .isWork -}}
# Work configuration
source ~/.work-aliases
{{ end -}}
```

### Interactive Prompts

In `chezmoi.toml.tmpl`:

```toml
{{- $email := promptStringOnce . "email" "Email address" -}}
{{- $isWork := promptBoolOnce . "isWork" "Is this a work machine" -}}

[data]
    email = {{ $email | quote }}
    isWork = {{ $isWork }}
```

## Scripts

### Run Once Scripts

Create `run_once_install-packages.sh`:

```bash
#!/bin/bash

# Only runs once per machine

if command -v brew &> /dev/null; then
    brew install fzf ripgrep bat
fi
```

### Run on Change Scripts

Create `run_onchange_configure-nvim.sh.tmpl`:

```bash
#!/bin/bash

# hash: {{ include "dot_config/nvim/init.lua" | sha256sum }}

# Runs when init.lua changes
nvim --headless "+Lazy! sync" +qa
```

### Run After Apply

Create `run_after_reload-shell.sh`:

```bash
#!/bin/bash

# Runs after every apply
exec $SHELL -l
```

### Script Ordering

Scripts run in alphabetical order. Use prefixes:

```
run_once_01-install-brew.sh
run_once_02-install-packages.sh
run_onchange_03-configure-app.sh
```

## External Files

Download files from URLs.

Create `.chezmoiexternal.toml`:

```toml
[".config/nvim/lazy-lock.json"]
    type = "file"
    url = "https://raw.githubusercontent.com/user/dotfiles/main/nvim/lazy-lock.json"
    refreshPeriod = "168h"  # Weekly

[".local/bin/starship"]
    type = "file"
    url = "https://starship.rs/install.sh"
    executable = true

[".oh-my-zsh"]
    type = "archive"
    url = "https://github.com/ohmyzsh/ohmyzsh/archive/master.tar.gz"
    exact = true
    stripComponents = 1
```

## Migration from Bare Git

### Export Current Setup

```bash
# Backup current dotfiles
cd ~
tar -cvf dotfiles-backup.tar .bashrc .gitconfig .config/nvim

# Initialize chezmoi
chezmoi init

# Add files one by one
chezmoi add ~/.bashrc
chezmoi add ~/.gitconfig
chezmoi add ~/.config/nvim
```

### Convert to Templates

```bash
# Edit to add template logic
chezmoi edit ~/.gitconfig

# Test changes
chezmoi diff

# Apply
chezmoi apply
```

### Setup Git Remote

```bash
# Initialize git in source dir
chezmoi cd
git init
git add .
git commit -m "Initial commit"
git remote add origin git@github.com:user/dotfiles.git
git push -u origin main
```

## Common Workflows

### New Machine Setup

```bash
# One-liner setup
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply username
```

### Update from Remote

```bash
# Pull and apply
chezmoi update

# Or pull without applying
chezmoi git pull
chezmoi diff
chezmoi apply
```

### Push Changes

```bash
chezmoi cd
git add .
git commit -m "Update configs"
git push
```

### Dry Run

```bash
# See what would change
chezmoi diff

# Apply verbosely
chezmoi apply -v --dry-run
```

## Configuration Reference

### Full chezmoi.toml Example

```toml
# Source directory
sourceDir = "~/.dotfiles"

# Use 1Password
[onepassword]
    command = "op"

# Use age encryption
encryption = "age"
[age]
    identity = "~/.config/chezmoi/key.txt"
    recipient = "age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Template data
[data]
    name = "Your Name"
    email = "you@example.com"
    editor = "nvim"

# Git configuration
[git]
    autoCommit = true
    autoPush = true

# Diff tool
[diff]
    command = "delta"
    pager = "delta"

# Merge tool
[merge]
    command = "nvim"
    args = ["-d"]
```

## Troubleshooting

### Debug Templates

```bash
# Execute template and see output
chezmoi execute-template '{{ .chezmoi.hostname }}'

# Debug a file template
chezmoi execute-template < ~/.local/share/chezmoi/dot_bashrc.tmpl
```

### Verify State

```bash
# Check status
chezmoi status

# Managed files
chezmoi managed

# Unmanaged in home
chezmoi unmanaged
```

### Reset File

```bash
# Forget a file
chezmoi forget ~/.bashrc

# Re-add
chezmoi add ~/.bashrc
```

### Common Errors

```bash
# Template error
chezmoi execute-template --init < ~/.local/share/chezmoi/.chezmoi.toml.tmpl

# Permission issues
chezmoi doctor
```

## See Also

- [direnv](direnv.md) - Per-directory environments
- [1Password CLI](1password-cli.md) - Secrets management
- [Dotfiles Configuration](../configuration/dotfiles.md) - Shell configuration
