# Customization

Extending and customizing LazyVim to fit your workflow.

## Adding Custom Plugins

Create plugin spec files in `lua/plugins/`:

```lua
-- lua/plugins/example.lua
return {
  -- Simple plugin
  "username/plugin-name",

  -- Plugin with options
  {
    "username/plugin-name",
    opts = {
      -- Plugin configuration
    },
  },

  -- Plugin with lazy loading
  {
    "username/plugin-name",
    event = "VeryLazy",  -- Load after startup
    keys = {
      { "<leader>p", "<cmd>PluginCommand<cr>", desc = "Plugin action" },
    },
  },
}
```

### Plugin Spec Options

| Option | Description |
|--------|-------------|
| `opts` | Plugin configuration (merged with defaults) |
| `config` | Custom config function |
| `event` | Load on event (BufRead, VeryLazy, etc.) |
| `cmd` | Load on command |
| `keys` | Load on keybinding |
| `ft` | Load for filetypes |
| `dependencies` | Required plugins |
| `enabled` | Enable/disable plugin |
| `priority` | Load order (higher = earlier) |

### Loading Events

| Event | When |
|-------|------|
| `VeryLazy` | After startup |
| `BufRead` | When opening a file |
| `BufReadPre` | Before opening a file |
| `InsertEnter` | Entering insert mode |
| `CmdlineEnter` | Entering command line |

## Extending LazyVim Plugins

Override or extend default plugin configurations:

```lua
-- lua/plugins/telescope.lua
return {
  "nvim-telescope/telescope.nvim",
  opts = {
    defaults = {
      layout_strategy = "horizontal",
      layout_config = {
        horizontal = {
          preview_width = 0.5,
        },
      },
    },
  },
}
```

### Using a Config Function

```lua
-- lua/plugins/telescope.lua
return {
  "nvim-telescope/telescope.nvim",
  opts = function(_, opts)
    -- Modify existing opts
    opts.defaults.layout_strategy = "horizontal"
    return opts
  end,
}
```

## Colorschemes

### Change Colorscheme

```lua
-- lua/plugins/colorscheme.lua
return {
  -- Add the colorscheme
  { "folke/tokyonight.nvim" },

  -- Set as default
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "tokyonight",
    },
  },
}
```

### Popular Colorschemes

```lua
-- lua/plugins/colorscheme.lua
return {
  -- Tokyo Night (default)
  { "folke/tokyonight.nvim" },

  -- Catppuccin
  { "catppuccin/nvim", name = "catppuccin" },

  -- One Dark
  { "navarasu/onedark.nvim" },

  -- Gruvbox
  { "ellisonleao/gruvbox.nvim" },

  -- Rose Pine
  { "rose-pine/neovim", name = "rose-pine" },

  -- Set one as default
  {
    "LazyVim/LazyVim",
    opts = {
      colorscheme = "catppuccin",
    },
  },
}
```

### Customize Colorscheme

```lua
-- lua/plugins/colorscheme.lua
return {
  {
    "folke/tokyonight.nvim",
    opts = {
      style = "night",  -- storm, moon, night, day
      transparent = false,
      terminal_colors = true,
      styles = {
        comments = { italic = true },
        keywords = { italic = true },
      },
    },
  },
}
```

## Custom Keymaps

### Add Keymaps

```lua
-- lua/config/keymaps.lua
local map = vim.keymap.set

-- Quick save
map("n", "<leader>w", "<cmd>w<cr>", { desc = "Save file" })

-- Better movement
map("n", "J", "mzJ`z")  -- Join lines, keep cursor
map("n", "<C-d>", "<C-d>zz")  -- Scroll down, center
map("n", "<C-u>", "<C-u>zz")  -- Scroll up, center

-- Move lines
map("v", "J", ":m '>+1<CR>gv=gv", { desc = "Move down" })
map("v", "K", ":m '<-2<CR>gv=gv", { desc = "Move up" })

-- Stay in visual mode when indenting
map("v", "<", "<gv")
map("v", ">", ">gv")
```

### Plugin-Specific Keymaps

```lua
-- lua/plugins/telescope.lua
return {
  "nvim-telescope/telescope.nvim",
  keys = {
    { "<leader>fp", "<cmd>Telescope projects<cr>", desc = "Projects" },
  },
}
```

### Delete Default Keymaps

```lua
-- lua/config/keymaps.lua
vim.keymap.del("n", "<leader>l")  -- Remove default keymap
```

## Custom Autocommands

```lua
-- lua/config/autocmds.lua
local autocmd = vim.api.nvim_create_autocmd
local augroup = vim.api.nvim_create_augroup

-- Auto-save on focus lost
autocmd("FocusLost", {
  pattern = "*",
  command = "silent! wa",
})

-- Return to last edit position
autocmd("BufReadPost", {
  pattern = "*",
  callback = function()
    local mark = vim.api.nvim_buf_get_mark(0, '"')
    local lcount = vim.api.nvim_buf_line_count(0)
    if mark[1] > 0 and mark[1] <= lcount then
      pcall(vim.api.nvim_win_set_cursor, 0, mark)
    end
  end,
})

-- Highlight yanked text
autocmd("TextYankPost", {
  group = augroup("highlight_yank", { clear = true }),
  callback = function()
    vim.highlight.on_yank({ timeout = 200 })
  end,
})

-- Filetype-specific settings
autocmd("FileType", {
  pattern = "python",
  callback = function()
    vim.opt_local.tabstop = 4
    vim.opt_local.shiftwidth = 4
  end,
})
```

## Disabling Features

### Disable a Plugin

```lua
-- lua/plugins/disabled.lua
return {
  { "plugin-name", enabled = false },

  -- Disable multiple
  { "nvim-neo-tree/neo-tree.nvim", enabled = false },
  { "folke/flash.nvim", enabled = false },
}
```

### Disable LazyVim Module

```lua
-- lua/plugins/disabled.lua
return {
  -- Disable animations
  { "echasnovski/mini.animate", enabled = false },

  -- Disable indent guides
  { "lukas-reineke/indent-blankline.nvim", enabled = false },
}
```

## UI Customization

### Dashboard

```lua
-- lua/plugins/dashboard.lua
return {
  "nvimdev/dashboard-nvim",
  opts = function(_, opts)
    local logo = [[
      ██╗      █████╗ ███████╗██╗   ██╗
      ██║     ██╔══██╗╚══███╔╝╚██╗ ██╔╝
      ██║     ███████║  ███╔╝  ╚████╔╝
      ██║     ██╔══██║ ███╔╝    ╚██╔╝
      ███████╗██║  ██║███████╗   ██║
      ╚══════╝╚═╝  ╚═╝╚══════╝   ╚═╝
    ]]
    opts.config.header = vim.split(logo, "\n")
    return opts
  end,
}
```

### Status Line (lualine)

```lua
-- lua/plugins/lualine.lua
return {
  "nvim-lualine/lualine.nvim",
  opts = {
    options = {
      theme = "tokyonight",
      component_separators = { left = "", right = "" },
      section_separators = { left = "", right = "" },
    },
  },
}
```

### Buffer Line

```lua
-- lua/plugins/bufferline.lua
return {
  "akinsho/bufferline.nvim",
  opts = {
    options = {
      mode = "buffers",
      show_buffer_close_icons = false,
      show_close_icon = false,
      separator_style = "thin",
    },
  },
}
```

## Editor Options

### Common Customizations

```lua
-- lua/config/options.lua

-- Indentation
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true

-- Line numbers
vim.opt.number = true
vim.opt.relativenumber = true

-- Search
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.hlsearch = true

-- Display
vim.opt.wrap = false
vim.opt.cursorline = true
vim.opt.scrolloff = 8
vim.opt.sidescrolloff = 8
vim.opt.signcolumn = "yes"
vim.opt.colorcolumn = "88"

-- Split behavior
vim.opt.splitright = true
vim.opt.splitbelow = true

-- Clipboard
vim.opt.clipboard = "unnamedplus"

-- Performance
vim.opt.updatetime = 200
vim.opt.timeoutlen = 300
```

## File Type Configuration

### Per-Filetype Settings

```lua
-- lua/config/autocmds.lua
vim.api.nvim_create_autocmd("FileType", {
  pattern = "markdown",
  callback = function()
    vim.opt_local.wrap = true
    vim.opt_local.spell = true
    vim.opt_local.textwidth = 80
  end,
})

vim.api.nvim_create_autocmd("FileType", {
  pattern = { "go", "rust" },
  callback = function()
    vim.opt_local.tabstop = 4
    vim.opt_local.shiftwidth = 4
    vim.opt_local.expandtab = false
  end,
})
```

### ftplugin Directory

Create `ftplugin/<filetype>.lua` for per-filetype config:

```lua
-- ftplugin/python.lua
vim.opt_local.tabstop = 4
vim.opt_local.shiftwidth = 4
```

## Popular Plugin Additions

### File Navigation

```lua
-- lua/plugins/harpoon.lua
return {
  "ThePrimeagen/harpoon",
  branch = "harpoon2",
  dependencies = { "nvim-lua/plenary.nvim" },
  keys = {
    { "<leader>ha", function() require("harpoon"):list():add() end, desc = "Harpoon add" },
    { "<leader>hh", function() require("harpoon").ui:toggle_quick_menu(require("harpoon"):list()) end, desc = "Harpoon menu" },
    { "<leader>1", function() require("harpoon"):list():select(1) end, desc = "Harpoon 1" },
    { "<leader>2", function() require("harpoon"):list():select(2) end, desc = "Harpoon 2" },
    { "<leader>3", function() require("harpoon"):list():select(3) end, desc = "Harpoon 3" },
    { "<leader>4", function() require("harpoon"):list():select(4) end, desc = "Harpoon 4" },
  },
}
```

### Undo History

```lua
-- lua/plugins/undotree.lua
return {
  "mbbill/undotree",
  keys = {
    { "<leader>u", "<cmd>UndotreeToggle<cr>", desc = "Toggle undotree" },
  },
}
```

### Code Outline

```lua
-- lua/plugins/outline.lua
return {
  "hedyhli/outline.nvim",
  keys = {
    { "<leader>o", "<cmd>Outline<cr>", desc = "Toggle outline" },
  },
  opts = {},
}
```

## Debugging Configuration

Check your config for errors:

```vim
:checkhealth lazy
:Lazy profile
```

View log:

```vim
:Lazy log
```
