# Configuration

Understanding and customizing LazyVim's configuration structure.

## Configuration Files

LazyVim's configuration lives in `~/.config/nvim/`:

```
lua/config/
├── autocmds.lua   # Auto commands
├── keymaps.lua    # Custom keybindings
├── lazy.lua       # Plugin manager config
└── options.lua    # Editor options
```

Files are loaded in order:
1. `options.lua` - Before plugins load
2. `lazy.lua` - Plugin manager and specs
3. `keymaps.lua` - After plugins (VeryLazy event)
4. `autocmds.lua` - After plugins (VeryLazy event)

## Options (options.lua)

Set Neovim options here. LazyVim defaults are loaded first, then your customizations.

```lua
-- lua/config/options.lua

-- Set indentation
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

-- Line numbers
vim.opt.relativenumber = true

-- Search
vim.opt.ignorecase = true
vim.opt.smartcase = true

-- Appearance
vim.opt.cursorline = true
vim.opt.scrolloff = 8

-- Disable word wrap
vim.opt.wrap = false

-- Configure Python LSP
vim.g.lazyvim_python_lsp = "pyright"
vim.g.lazyvim_python_ruff = "ruff"
```

### Common Options

| Option | Description | Default |
|--------|-------------|---------|
| `vim.opt.number` | Line numbers | `true` |
| `vim.opt.relativenumber` | Relative line numbers | `true` |
| `vim.opt.tabstop` | Tab width | `2` |
| `vim.opt.shiftwidth` | Indent width | `2` |
| `vim.opt.expandtab` | Spaces instead of tabs | `true` |
| `vim.opt.wrap` | Line wrapping | `false` |
| `vim.opt.cursorline` | Highlight current line | `true` |
| `vim.opt.termguicolors` | True color support | `true` |
| `vim.opt.scrolloff` | Min lines above/below cursor | `4` |
| `vim.opt.signcolumn` | Sign column | `"yes"` |

## Keymaps (keymaps.lua)

Add custom keybindings:

```lua
-- lua/config/keymaps.lua

local map = vim.keymap.set

-- Better window navigation
map("n", "<C-h>", "<C-w>h", { desc = "Go to left window" })
map("n", "<C-j>", "<C-w>j", { desc = "Go to lower window" })
map("n", "<C-k>", "<C-w>k", { desc = "Go to upper window" })
map("n", "<C-l>", "<C-w>l", { desc = "Go to right window" })

-- Stay in visual mode when indenting
map("v", "<", "<gv")
map("v", ">", ">gv")

-- Move lines up/down
map("v", "J", ":m '>+1<CR>gv=gv", { desc = "Move line down" })
map("v", "K", ":m '<-2<CR>gv=gv", { desc = "Move line up" })

-- Quick save
map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save file" })

-- Clear search highlight
map("n", "<Esc>", "<cmd>nohlsearch<CR>")
```

### Keymap Function Signature

```lua
vim.keymap.set(mode, key, action, opts)
```

| Parameter | Description |
|-----------|-------------|
| `mode` | `"n"` normal, `"i"` insert, `"v"` visual, `"x"` visual block |
| `key` | Key combination |
| `action` | Command or Lua function |
| `opts` | `{ desc = "...", silent = true, noremap = true }` |

### Delete LazyVim Keymaps

```lua
-- Remove a LazyVim keymap
vim.keymap.del("n", "<leader>l")
```

## Autocommands (autocmds.lua)

Create automatic behaviors:

```lua
-- lua/config/autocmds.lua

local autocmd = vim.api.nvim_create_autocmd
local augroup = vim.api.nvim_create_augroup

-- Highlight on yank
autocmd("TextYankPost", {
  group = augroup("highlight_yank", { clear = true }),
  callback = function()
    vim.highlight.on_yank({ higroup = "IncSearch", timeout = 200 })
  end,
})

-- Remove trailing whitespace on save
autocmd("BufWritePre", {
  pattern = "*",
  callback = function()
    local save_cursor = vim.fn.getpos(".")
    vim.cmd([[%s/\s\+$//e]])
    vim.fn.setpos(".", save_cursor)
  end,
})

-- Set filetype for specific extensions
autocmd({ "BufRead", "BufNewFile" }, {
  pattern = "*.mdx",
  command = "set filetype=markdown",
})

-- Auto-format on save for specific filetypes
autocmd("BufWritePre", {
  pattern = { "*.py", "*.rs", "*.lua" },
  callback = function()
    vim.lsp.buf.format({ async = false })
  end,
})
```

### Remove LazyVim Autocommands

```lua
-- Remove an autocommand group
vim.api.nvim_del_augroup_by_name("lazyvim_wrap_spell")
```

## lazy.lua

The plugin manager configuration:

```lua
-- lua/config/lazy.lua

local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  vim.fn.system({
    "git", "clone", "--filter=blob:none",
    "--branch=stable",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
  spec = {
    { "LazyVim/LazyVim", import = "lazyvim.plugins" },
    { import = "plugins" },  -- Your custom plugins
  },
  defaults = {
    lazy = false,  -- Lazy-load custom plugins?
    version = false,  -- Use latest commit
  },
  install = { colorscheme = { "tokyonight", "habamax" } },
  checker = {
    enabled = true,  -- Check for updates
    notify = false,  -- Notify on updates
  },
  performance = {
    rtp = {
      disabled_plugins = {
        "gzip",
        "tarPlugin",
        "tohtml",
        "tutor",
        "zipPlugin",
      },
    },
  },
})
```

## LazyVim Extras (lazyvim.json)

Enable LazyVim extras through the UI or `lazyvim.json`:

```json
{
  "extras": [
    "lazyvim.plugins.extras.lang.python",
    "lazyvim.plugins.extras.lang.rust",
    "lazyvim.plugins.extras.lang.docker",
    "lazyvim.plugins.extras.lang.json",
    "lazyvim.plugins.extras.lang.markdown"
  ],
  "version": 8
}
```

### Managing Extras

Enable/disable extras:

```vim
:LazyExtras
```

Navigate with `j`/`k`, toggle with `x`, and install with `I`.

### Available Extra Categories

| Category | Examples |
|----------|----------|
| `lang.*` | python, rust, go, typescript, java |
| `linting.*` | eslint, selene |
| `formatting.*` | prettier, black |
| `ui.*` | mini-animate, noice |
| `editor.*` | navic, aerial |
| `coding.*` | copilot, codeium, tabnine |

## Global Variables

LazyVim uses global variables for configuration:

```lua
-- Python LSP (pyright or basedpyright)
vim.g.lazyvim_python_lsp = "pyright"

-- Python linter (ruff or ruff_lsp)
vim.g.lazyvim_python_ruff = "ruff"

-- Disable root detection
vim.g.root_spec = { "cwd" }

-- Colorscheme
vim.g.lazyvim_colorscheme = "tokyonight"
```

## File-Type Configuration

Configure settings per file type:

```lua
-- lua/config/autocmds.lua

-- Python specific
vim.api.nvim_create_autocmd("FileType", {
  pattern = "python",
  callback = function()
    vim.opt_local.tabstop = 4
    vim.opt_local.shiftwidth = 4
    vim.opt_local.expandtab = true
  end,
})

-- Markdown specific
vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.wrap = true
    vim.opt_local.spell = true
  end,
})
```

## Environment Variables

Configure behavior through environment variables:

```bash
# Set config directory (default: ~/.config/nvim)
export XDG_CONFIG_HOME=~/.config

# Set data directory (default: ~/.local/share/nvim)
export XDG_DATA_HOME=~/.local/share

# Set cache directory (default: ~/.cache/nvim)
export XDG_CACHE_HOME=~/.cache
```
