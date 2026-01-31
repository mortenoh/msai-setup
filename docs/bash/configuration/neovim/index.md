# Neovim & LazyVim

Neovim is a hyperextensible text editor built for modern development workflows. LazyVim is a Neovim distribution that provides sensible defaults and a plugin management system out of the box.

## Norwegian Keyboard Layout

Neovim works well with Norwegian keyboards, but some default keybindings may need adjustment:

**Potential Issues:**

- Square brackets `[]` require ++alt+8++ and ++alt+9++ (used for navigation)
- Backtick requires ++shift+backslash++ (marks and jumps)
- Backslash `\` requires ++alt+shift+7++ (leader key on some configs)
- Curly braces `{}` require ++alt+shift+8++ and ++alt+shift+9++

**Recommended Settings:**

Add to `~/.config/nvim/lua/config/keymaps.lua`:

```lua
-- Norwegian keyboard-friendly mappings

-- Easier access to [ and ] for navigation
vim.keymap.set("n", "ø", "[", { remap = true })
vim.keymap.set("n", "æ", "]", { remap = true })

-- Or use leader key alternatives
vim.keymap.set("n", "<leader>[", "[", { remap = true })
vim.keymap.set("n", "<leader>]", "]", { remap = true })

-- Navigate diagnostics without brackets
vim.keymap.set("n", "<leader>dp", vim.diagnostic.goto_prev, { desc = "Previous diagnostic" })
vim.keymap.set("n", "<leader>dn", vim.diagnostic.goto_next, { desc = "Next diagnostic" })

-- Navigate hunks without brackets
vim.keymap.set("n", "<leader>hp", function()
  require("gitsigns").prev_hunk()
end, { desc = "Previous hunk" })
vim.keymap.set("n", "<leader>hn", function()
  require("gitsigns").next_hunk()
end, { desc = "Next hunk" })
```

**Space as Leader Key**: LazyVim uses ++space++ as the leader key by default, which works perfectly with Norwegian keyboards.

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
