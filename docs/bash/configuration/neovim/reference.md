# Quick Reference

Essential commands and keybindings for LazyVim.

## Commands

### Plugin Management

| Command | Description |
|---------|-------------|
| `:Lazy` | Open plugin manager |
| `:Lazy sync` | Install, clean, update plugins |
| `:Lazy update` | Update plugins |
| `:Lazy restore` | Restore from lockfile |
| `:Lazy profile` | Startup profile |
| `:LazyExtras` | Manage LazyVim extras |

### LSP

| Command | Description |
|---------|-------------|
| `:LspInfo` | Show active LSP clients |
| `:LspStart` | Start LSP |
| `:LspStop` | Stop LSP |
| `:LspRestart` | Restart LSP |
| `:Mason` | LSP server manager |

### Treesitter

| Command | Description |
|---------|-------------|
| `:TSInstall <lang>` | Install parser |
| `:TSUpdate` | Update all parsers |
| `:TSInstallInfo` | Show installed parsers |

### Diagnostics

| Command | Description |
|---------|-------------|
| `:checkhealth` | Run health check |
| `:checkhealth lazy` | Check lazy.nvim |
| `:checkhealth lsp` | Check LSP |

## Essential Keybindings

### Navigation

| Key | Action |
|-----|--------|
| ++space+space++ | Find files |
| ++space+slash++ | Search in files |
| ++space+comma++ | Switch buffer |
| ++space+e++ | File explorer |
| ++g+d++ | Go to definition |
| ++g+r++ | Go to references |

### Editing

| Key | Action |
|-----|--------|
| ++g+c+c++ | Toggle line comment |
| ++space+c+a++ | Code actions |
| ++space+c+r++ | Rename symbol |
| ++space+c+f++ | Format buffer |
| ++shift+k++ | Hover documentation |

### Buffers & Windows

| Key | Action |
|-----|--------|
| ++shift+h++ / ++shift+l++ | Previous/next buffer |
| ++space+b+d++ | Delete buffer |
| ++ctrl+h+j+k+l++ | Navigate windows |
| ++space+w+d++ | Delete window |
| ++space+bar++ | Split vertical |
| ++space+minus++ | Split horizontal |

### Git

| Key | Action |
|-----|--------|
| ++space+g+g++ | LazyGit |
| ++space+g+b++ | Git blame |
| ++bracket-left+h++ / ++bracket-right+h++ | Previous/next hunk |
| ++space+g+s++ | Stage hunk |
| ++space+g+r++ | Reset hunk |

### UI Toggles

| Key | Action |
|-----|--------|
| ++space+u+f++ | Toggle format on save |
| ++space+u+l++ | Toggle line numbers |
| ++space+u+w++ | Toggle word wrap |
| ++space+u+s++ | Toggle spell check |

## File Structure

```
~/.config/nvim/
├── init.lua                 # Entry point
├── lazy-lock.json           # Plugin versions
├── lazyvim.json             # Enabled extras
└── lua/
    ├── config/
    │   ├── autocmds.lua     # Auto commands
    │   ├── keymaps.lua      # Keybindings
    │   ├── lazy.lua         # Plugin manager
    │   └── options.lua      # Editor options
    └── plugins/
        └── *.lua            # Custom plugins
```

## Common Configuration

### options.lua

```lua
-- Indentation
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

-- Line numbers
vim.opt.relativenumber = true

-- Search
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- Python LSP
vim.g.lazyvim_python_lsp = "pyright"
vim.g.lazyvim_python_ruff = "ruff"
```

### keymaps.lua

```lua
local map = vim.keymap.set

map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save" })
map("v", "J", ":m '>+1<CR>gv=gv", { desc = "Move down" })
map("v", "K", ":m '<-2<CR>gv=gv", { desc = "Move up" })
```

### Adding Plugins

```lua
-- lua/plugins/example.lua
return {
  "username/plugin-name",
  event = "VeryLazy",
  opts = {
    -- configuration
  },
}
```

### Changing Colorscheme

```lua
-- lua/plugins/colorscheme.lua
return {
  { "catppuccin/nvim", name = "catppuccin" },
  {
    "LazyVim/LazyVim",
    opts = { colorscheme = "catppuccin" },
  },
}
```

### Disabling Plugins

```lua
-- lua/plugins/disabled.lua
return {
  { "plugin-name", enabled = false },
}
```

## LSP Configuration

```lua
-- lua/plugins/lsp.lua
return {
  "neovim/nvim-lspconfig",
  opts = {
    servers = {
      pyright = {
        settings = {
          python = {
            analysis = {
              typeCheckingMode = "basic",
            },
          },
        },
      },
    },
  },
}
```

## Telescope Controls

| Key | Action |
|-----|--------|
| ++ctrl+j++ / ++ctrl+k++ | Navigate |
| ++enter++ | Open |
| ++ctrl+x++ | Horizontal split |
| ++ctrl+v++ | Vertical split |
| ++tab++ | Toggle selection |
| ++ctrl+q++ | Send to quickfix |

## Neo-tree Controls

| Key | Action |
|-----|--------|
| ++enter++ | Open |
| ++a++ | Add file |
| ++d++ | Delete |
| ++r++ | Rename |
| ++y++ | Copy name |
| ++period++ | Toggle hidden |

## Vim Motions Cheatsheet

### Movement

| Key | Action |
|-----|--------|
| `h j k l` | Left, down, up, right |
| `w` / `b` | Next/previous word |
| `e` | End of word |
| `0` / `$` | Start/end of line |
| `gg` / `G` | Start/end of file |
| `{` / `}` | Previous/next paragraph |
| `%` | Matching bracket |

### Editing

| Key | Action |
|-----|--------|
| `i` / `a` | Insert before/after |
| `I` / `A` | Insert start/end of line |
| `o` / `O` | New line below/above |
| `x` | Delete character |
| `dd` | Delete line |
| `yy` | Yank line |
| `p` / `P` | Paste after/before |
| `u` | Undo |
| `Ctrl+r` | Redo |

### Text Objects

| Key | Description |
|-----|-------------|
| `iw` / `aw` | Inner/around word |
| `i"` / `a"` | Inner/around quotes |
| `i(` / `a(` | Inner/around parentheses |
| `i{` / `a{` | Inner/around braces |
| `if` / `af` | Inner/around function |
| `ic` / `ac` | Inner/around class |

### Operators

| Key | Action |
|-----|--------|
| `d` | Delete |
| `c` | Change |
| `y` | Yank (copy) |
| `>` / `<` | Indent |
| `=` | Auto-indent |

Combine: `diw` (delete inner word), `ci"` (change inside quotes), `yap` (yank around paragraph)
