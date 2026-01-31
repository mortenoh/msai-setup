# Plugins

Overview of core LazyVim plugins and their functionality.

## Plugin Manager: lazy.nvim

[lazy.nvim](https://github.com/folke/lazy.nvim) manages all plugins with lazy-loading support.

### Plugin UI

Open the plugin manager:

```vim
:Lazy
```

### Keybindings in Lazy UI

| Key | Action |
|-----|--------|
| ++i++ | Install missing plugins |
| ++shift+u++ | Update plugins |
| ++shift+s++ | Sync (install, clean, update) |
| ++shift+x++ | Clean unused plugins |
| ++c++ | Check for updates |
| ++l++ | View log |
| ++r++ | Restore from lockfile |
| ++p++ | Profile startup time |
| ++q++ | Close |

### Lockfile

Plugin versions are locked in `lazy-lock.json`. Commit this file to ensure reproducible setups.

```bash
# Restore plugins to lockfile versions
:Lazy restore
```

## Fuzzy Finder: Telescope

[telescope.nvim](https://github.com/nvim-telescope/telescope.nvim) provides fuzzy finding for everything.

### Common Pickers

| Command | Keybinding | Description |
|---------|------------|-------------|
| `:Telescope find_files` | ++space+space++ | Find files |
| `:Telescope live_grep` | ++space+slash++ | Search in files |
| `:Telescope buffers` | ++space+comma++ | Switch buffer |
| `:Telescope oldfiles` | ++space+f+r++ | Recent files |
| `:Telescope git_files` | ++space+f+g++ | Git tracked files |
| `:Telescope help_tags` | ++space+s+h++ | Search help |
| `:Telescope keymaps` | ++space+s+k++ | Search keymaps |

### Telescope Controls

| Key | Action |
|-----|--------|
| ++ctrl+j++ / ++ctrl+k++ | Navigate results |
| ++enter++ | Open selection |
| ++ctrl+x++ | Open in horizontal split |
| ++ctrl+v++ | Open in vertical split |
| ++ctrl+u++ | Scroll preview up |
| ++ctrl+d++ | Scroll preview down |
| ++tab++ | Toggle selection |
| ++ctrl+q++ | Send to quickfix |

## File Explorer: Neo-tree

[neo-tree.nvim](https://github.com/nvim-neo-tree/neo-tree.nvim) provides a sidebar file explorer.

### Commands

| Command | Keybinding | Description |
|---------|------------|-------------|
| `:Neotree toggle` | ++space+e++ | Toggle explorer |
| `:Neotree focus` | ++space+f+e++ | Focus explorer |
| `:Neotree git_status` | - | Git status view |
| `:Neotree buffers` | - | Buffer view |

### Neo-tree Controls

| Key | Action |
|-----|--------|
| ++enter++ / ++o++ | Open file |
| ++a++ | Add file/directory |
| ++d++ | Delete |
| ++r++ | Rename |
| ++c++ | Copy |
| ++m++ | Move |
| ++y++ | Copy name |
| ++shift+y++ | Copy path |
| ++period++ | Toggle hidden |
| ++question++ | Show help |

## Syntax Highlighting: Treesitter

[nvim-treesitter](https://github.com/nvim-treesitter/nvim-treesitter) provides advanced syntax highlighting.

### Install Parsers

```vim
:TSInstall python rust lua javascript typescript
```

### Commands

| Command | Description |
|---------|-------------|
| `:TSInstall <lang>` | Install parser |
| `:TSUpdate` | Update all parsers |
| `:TSInstallInfo` | Show installed parsers |
| `:TSModuleInfo` | Show module info |

### Features

- **Highlighting**: Semantic, context-aware highlighting
- **Indentation**: Smart indentation
- **Folding**: Code folding based on syntax
- **Text objects**: Function and class text objects

## Buffer Line: bufferline.nvim

[bufferline.nvim](https://github.com/akinsho/bufferline.nvim) shows open buffers as tabs.

### Navigation

| Key | Action |
|-----|--------|
| ++shift+h++ | Previous buffer |
| ++shift+l++ | Next buffer |
| ++space+b+d++ | Close buffer |
| ++space+b+o++ | Close other buffers |
| ++space+b+p++ | Toggle pin |

## Status Line: lualine.nvim

[lualine.nvim](https://github.com/nvim-lualine/lualine.nvim) provides the status line at the bottom.

Displays:
- Mode indicator
- Git branch
- File info
- LSP status
- Diagnostics
- Cursor position

## Keybinding Help: which-key.nvim

[which-key.nvim](https://github.com/folke/which-key.nvim) shows available keybindings.

Press ++space++ and wait to see all leader key combinations.

### Configuration

```lua
-- lua/plugins/which-key.lua
return {
  "folke/which-key.nvim",
  opts = {
    delay = 200,  -- Delay before showing (ms)
  },
}
```

## Git Signs: gitsigns.nvim

[gitsigns.nvim](https://github.com/lewis6991/gitsigns.nvim) shows git status in the gutter.

### Signs

| Sign | Meaning |
|------|---------|
| `|` (green) | Added lines |
| `|` (blue) | Changed lines |
| `_` (red) | Deleted lines |

### Commands

| Key | Action |
|-----|--------|
| ++bracket-right+h++ | Next hunk |
| ++bracket-left+h++ | Previous hunk |
| ++space+g+s++ | Stage hunk |
| ++space+g+r++ | Reset hunk |
| ++space+g+shift+s++ | Stage buffer |
| ++space+g+u++ | Undo stage hunk |
| ++space+g+p++ | Preview hunk |
| ++space+g+b++ | Blame line |

## Commenting: Comment.nvim

Built-in commenting functionality.

| Key | Action |
|-----|--------|
| ++g+c+c++ | Toggle line comment |
| ++g+c++ (visual) | Toggle selection comment |
| ++g+b+c++ | Toggle block comment |

## Auto Pairs: mini.pairs

Automatically closes brackets, quotes, etc.

| Type | Inserts |
|------|---------|
| `(` | `()` |
| `[` | `[]` |
| `{` | `{}` |
| `"` | `""` |
| `'` | `''` |

## Surround: mini.surround

Add, delete, replace surroundings.

| Key | Action |
|-----|--------|
| `gza` + motion + char | Add surrounding |
| `gzd` + char | Delete surrounding |
| `gzr` + old + new | Replace surrounding |

Examples:

- `gzaiw"` - Surround word with quotes
- `gzd"` - Delete surrounding quotes
- `gzr"'` - Replace double quotes with single

## LSP: nvim-lspconfig

Built-in LSP support with [nvim-lspconfig](https://github.com/neovim/nvim-lspconfig).

### Commands

| Command | Description |
|---------|-------------|
| `:LspInfo` | Show active LSP clients |
| `:LspStart` | Start LSP |
| `:LspStop` | Stop LSP |
| `:LspRestart` | Restart LSP |

## Completion: nvim-cmp

[nvim-cmp](https://github.com/hrsh7th/nvim-cmp) provides auto-completion.

### Controls

| Key | Action |
|-----|--------|
| ++ctrl+space++ | Trigger completion |
| ++ctrl+n++ | Next item |
| ++ctrl+p++ | Previous item |
| ++enter++ | Accept |
| ++ctrl+e++ | Close menu |
| ++ctrl+d++ | Scroll docs down |
| ++ctrl+f++ | Scroll docs up |

### Sources

Completion sources (in priority order):

1. LSP
2. Luasnip (snippets)
3. Buffer
4. Path

## Snippets: LuaSnip

[LuaSnip](https://github.com/L3MON4D3/LuaSnip) provides snippet expansion.

| Key | Action |
|-----|--------|
| ++tab++ | Expand or jump forward |
| ++shift+tab++ | Jump backward |

## Mason: LSP Server Manager

[mason.nvim](https://github.com/williamboman/mason.nvim) manages LSP servers, linters, formatters.

### Commands

| Command | Description |
|---------|-------------|
| `:Mason` | Open Mason UI |
| `:MasonInstall <pkg>` | Install package |
| `:MasonUninstall <pkg>` | Uninstall package |
| `:MasonUpdate` | Update packages |

### Mason UI

| Key | Action |
|-----|--------|
| ++i++ | Install |
| ++shift+x++ | Uninstall |
| ++u++ | Update |
| ++ctrl+c++ | Cancel |

## Diagnostics: trouble.nvim

[trouble.nvim](https://github.com/folke/trouble.nvim) shows diagnostics in a list.

| Key | Action |
|-----|--------|
| ++space+x+x++ | Document diagnostics |
| ++space+x+shift+x++ | Workspace diagnostics |
| ++space+x+l++ | Location list |
| ++space+x+q++ | Quickfix list |

## Terminal: toggleterm

Integrated terminal support.

| Key | Action |
|-----|--------|
| ++ctrl+slash++ | Toggle terminal |
| ++space+f+t++ | Float terminal (root) |
| ++space+f+shift+t++ | Float terminal (cwd) |

Inside terminal, press ++esc+esc++ or ++ctrl+backslash+backslash++ to exit terminal mode.

## Indent Guides: indent-blankline

Shows vertical indent guides.

Customize:

```lua
-- lua/plugins/indent.lua
return {
  "lukas-reineke/indent-blankline.nvim",
  opts = {
    indent = {
      char = "|",
    },
    scope = {
      enabled = true,
    },
  },
}
```
