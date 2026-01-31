# asdf

asdf is a tool version manager that supports multiple languages and tools with a single CLI.

## Why asdf?

- **One tool for everything** - Python, Node.js, Ruby, Go, etc.
- **Per-project versions** - Different versions per directory
- **Plugin ecosystem** - Hundreds of supported tools
- **Consistent interface** - Same commands for all tools

## Installation

### macOS

```bash
brew install asdf
```

### Linux

```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
```

### Shell Integration

```bash
# Bash (~/.bashrc)
. "$HOME/.asdf/asdf.sh"
. "$HOME/.asdf/completions/asdf.bash"

# Zsh (~/.zshrc)
. "$HOME/.asdf/asdf.sh"
fpath=(${ASDF_DIR}/completions $fpath)
autoload -Uz compinit && compinit

# Fish (~/.config/fish/config.fish)
source ~/.asdf/asdf.fish
```

## Basic Usage

### Plugin Management

```bash
# List available plugins
asdf plugin list all

# Add a plugin
asdf plugin add nodejs
asdf plugin add python
asdf plugin add golang

# List installed plugins
asdf plugin list

# Update plugins
asdf plugin update --all

# Remove plugin
asdf plugin remove nodejs
```

### Version Management

```bash
# List available versions
asdf list all nodejs
asdf list all python

# Install a version
asdf install nodejs 20.10.0
asdf install python 3.12.0

# List installed versions
asdf list nodejs
asdf list python

# Uninstall a version
asdf uninstall nodejs 18.0.0
```

### Setting Versions

```bash
# Set global version (default)
asdf global nodejs 20.10.0
asdf global python 3.12.0

# Set local version (per-project)
cd my-project
asdf local nodejs 18.19.0
asdf local python 3.11.0

# Set shell version (current session only)
asdf shell nodejs 16.20.0

# Check current version
asdf current nodejs
asdf current  # All tools
```

## .tool-versions File

Per-project version control:

```bash
# .tool-versions
nodejs 20.10.0
python 3.12.0
golang 1.21.5
```

```bash
# Create from current versions
asdf local nodejs 20.10.0
asdf local python 3.12.0

# Or edit manually
echo "nodejs 20.10.0" >> .tool-versions
```

## Common Plugins

### Node.js

```bash
asdf plugin add nodejs

# Install LTS
asdf install nodejs lts

# Install specific version
asdf install nodejs 20.10.0
asdf install nodejs 18.19.0

# Set default
asdf global nodejs 20.10.0
```

### Python

```bash
asdf plugin add python

# Install latest
asdf install python latest

# Install specific
asdf install python 3.12.0
asdf install python 3.11.0

# Set default
asdf global python 3.12.0
```

### Go

```bash
asdf plugin add golang

asdf install golang 1.21.5
asdf global golang 1.21.5
```

### Java

```bash
asdf plugin add java

# List available distributions
asdf list all java

# Install specific distribution
asdf install java temurin-21.0.1+12.0.LTS
asdf global java temurin-21.0.1+12.0.LTS
```

### Ruby

```bash
asdf plugin add ruby

asdf install ruby 3.3.0
asdf global ruby 3.3.0
```

### Rust

```bash
asdf plugin add rust

asdf install rust 1.75.0
asdf global rust 1.75.0
```

## Configuration

### .asdfrc

```bash
# ~/.asdfrc
legacy_version_file = yes  # Support .nvmrc, .python-version, etc.
```

### Environment Variables

```bash
# Plugin-specific settings
export ASDF_NODEJS_LEGACY_FILE_DYNAMIC_STRATEGY=latest_installed
export ASDF_PYTHON_DEFAULT_PACKAGES_FILE=~/.default-python-packages
```

## Workflow Examples

### Project Setup

```bash
# Clone project
git clone https://github.com/user/project.git
cd project

# Install all tools from .tool-versions
asdf install

# Verify versions
asdf current
```

### Updating Versions

```bash
# Check for new versions
asdf list all nodejs | tail -20

# Install and switch
asdf install nodejs 20.11.0
asdf local nodejs 20.11.0

# Update .tool-versions
git add .tool-versions
git commit -m "chore: update Node.js to 20.11.0"
```

### Team Consistency

```bash
# Team member clones project
git clone project.git
cd project

# .tool-versions is committed
cat .tool-versions
# nodejs 20.10.0
# python 3.12.0

# Install exact versions
asdf install
```

## Migration

### From nvm

```bash
# Get current nvm version
nvm current
# v18.19.0

# Install same version with asdf
asdf plugin add nodejs
asdf install nodejs 18.19.0
asdf global nodejs 18.19.0

# Remove nvm (optional)
rm -rf ~/.nvm
# Remove nvm lines from .bashrc/.zshrc
```

### From pyenv

```bash
# Get current pyenv versions
pyenv versions

# Install with asdf
asdf plugin add python
asdf install python 3.12.0
asdf global python 3.12.0

# Remove pyenv (optional)
rm -rf ~/.pyenv
```

## Troubleshooting

### Reshim

```bash
# After installing packages globally
pip install some-package
asdf reshim python

npm install -g typescript
asdf reshim nodejs
```

### Check Shims

```bash
# Verify which version is used
which node
# ~/.asdf/shims/node

asdf which node
# ~/.asdf/installs/nodejs/20.10.0/bin/node
```

### Plugin Not Found

```bash
# Update plugin repository
asdf plugin update --all

# Or add specific plugin
asdf plugin add nodejs https://github.com/asdf-vm/asdf-nodejs.git
```

### Version Not Installing

```bash
# Check dependencies
# For Python:
# - macOS: xcode-select --install
# - Linux: build-essential, libssl-dev, etc.

# For Node.js (uses node-build):
asdf plugin update nodejs
```

## Best Practices

1. **Commit .tool-versions** - Ensure team consistency
2. **Use specific versions** - Not `latest` in production
3. **Pin in CI** - Match versions in CI/CD pipelines
4. **Reshim after global installs** - Keep shims updated

## Alternatives

- **mise** - Modern rewrite, faster, additional features
- **rtx** - Renamed to mise
- **fnm** - Node.js only, very fast
- **pyenv** - Python only

## See Also

- [mise](mise.md) - Modern alternative
- [Node.js with nvm](nodejs.md)
- [Python with uv](../../../ai/coding-tools/python-uv.md)
