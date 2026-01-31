# Neovim & LazyVim

Neovim is a hyperextensible text editor built for modern development workflows. LazyVim is a Neovim distribution that provides sensible defaults and a plugin management system out of the box.

## Why Neovim?

- **Performance**: Fast startup and editing, even with plugins
- **Lua Configuration**: Modern, powerful scripting language
- **LSP Native**: Built-in Language Server Protocol support
- **Treesitter**: Advanced syntax highlighting and code analysis
- **Extensibility**: Rich plugin ecosystem
- **Modal Editing**: Efficient Vim-style editing

## Why LazyVim?

LazyVim transforms Neovim from a text editor into a full-featured IDE while maintaining the speed and efficiency of Vim:

- **Pre-configured**: Sensible defaults for immediate productivity
- **Lazy Loading**: Plugins load only when needed
- **Modular**: Enable/disable features through "extras"
- **Well Documented**: Extensive documentation and community
- **Modern Stack**: Telescope, Treesitter, LSP, and more

## Current Setup

This configuration uses LazyVim with the following extras enabled:

| Extra | Purpose |
|-------|---------|
| `lang.docker` | Dockerfile support and container management |
| `lang.git` | Git integration and diff views |
| `lang.json` | JSON/JSONC editing with schemas |
| `lang.markdown` | Markdown preview and editing |
| `lang.python` | Python LSP, linting, formatting |
| `lang.rust` | Rust analyzer and tools |
| `lang.toml` | TOML file support |

## Key Features

### LSP Support

- **Pyright**: Python type checking and IntelliSense
- **Ruff**: Fast Python linting and formatting
- **Rust Analyzer**: Rust language support
- **JSON/YAML**: Schema validation

### Code Navigation

- **Telescope**: Fuzzy finding for files, grep, symbols
- **Neo-tree**: File explorer sidebar
- **Bufferline**: Tab-like buffer management

### Editor Enhancements

- **Treesitter**: Semantic syntax highlighting
- **Which-key**: Keybinding discovery
- **Mini.pairs**: Auto-closing brackets
- **Comments**: Easy code commenting

### Git Integration

- **Gitsigns**: Git status in gutter
- **LazyGit**: Terminal git UI integration
- **Fugitive**: Git commands in Vim

## Quick Start

```bash
# Alias vim to nvim (add to ~/.bashrc or ~/.zshrc)
alias vim='nvim'

# Open a file
vim file.py

# Open a directory
vim .

# Access LazyVim dashboard
vim
```

## Essential Commands

| Command | Action |
|---------|--------|
| `:LazyHealth` | Check plugin health |
| `:LazyExtras` | Manage LazyVim extras |
| `:Mason` | Manage LSP servers |
| `:Lazy` | Plugin manager UI |
| `:checkhealth` | Neovim health check |

## Documentation Structure

- [Installation](installation.md) - Installing Neovim and LazyVim
- [Configuration](configuration.md) - Config structure and basics
- [Keybindings](keybindings.md) - Essential keybindings
- [Plugins](plugins.md) - Core plugins overview
- [Language Support](language-support.md) - LSP and language extras
- [Customization](customization.md) - Customizing LazyVim
- [Troubleshooting](troubleshooting.md) - Common issues
- [Reference](reference.md) - Quick reference card
