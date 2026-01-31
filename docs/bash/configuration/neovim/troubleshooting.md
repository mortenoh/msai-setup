# Troubleshooting

Common issues and solutions for Neovim and LazyVim.

## Diagnostic Commands

### Health Check

Run comprehensive diagnostics:

```vim
:checkhealth
```

Check specific components:

```vim
:checkhealth lazy
:checkhealth lsp
:checkhealth mason
:checkhealth nvim-treesitter
```

### Plugin Information

```vim
:Lazy          " Plugin manager UI
:Lazy log      " View update log
:Lazy profile  " Startup profile
```

### LSP Information

```vim
:LspInfo       " Active LSP clients
:LspLog        " LSP debug log
:Mason         " LSP server manager
```

## Plugin Issues

### Plugins Not Loading

1. **Check lazy-lock.json**: Ensure it exists and is valid JSON
2. **Sync plugins**: Run `:Lazy sync`
3. **Check for errors**: Run `:Lazy`

```vim
" Force reinstall all plugins
:Lazy restore
```

### Plugin Conflicts

Disable conflicting plugins:

```lua
-- lua/plugins/disabled.lua
return {
  { "conflicting-plugin", enabled = false },
}
```

### Startup Errors

Check startup profile:

```vim
:Lazy profile
```

Run Neovim without config to isolate:

```bash
nvim --clean
nvim -u NONE
```

## LSP Issues

### LSP Not Starting

1. **Check if installed**: `:Mason`
2. **Check LspInfo**: `:LspInfo`
3. **Check logs**: `:LspLog`

### Install Missing Server

```vim
:MasonInstall pyright
```

Or automatically:

```lua
-- lua/plugins/lsp.lua
return {
  "williamboman/mason-lspconfig.nvim",
  opts = {
    ensure_installed = { "pyright", "ruff" },
  },
}
```

### Wrong LSP Server

Check active servers:

```vim
:LspInfo
```

Disable unwanted server:

```lua
-- lua/plugins/lsp.lua
return {
  "neovim/nvim-lspconfig",
  opts = {
    servers = {
      tsserver = { enabled = false },
    },
  },
}
```

### LSP Slow or Hanging

1. Check file size and complexity
2. Exclude large directories from analysis
3. Increase timeout:

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
              diagnosticMode = "openFilesOnly",
            },
          },
        },
      },
    },
  },
}
```

### Python Virtual Environment Not Detected

Set path manually:

```vim
:PyrightSetPythonPath /path/to/.venv/bin/python
```

Or configure in `pyproject.toml`:

```toml
[tool.pyright]
venvPath = "."
venv = ".venv"
```

## Treesitter Issues

### Parser Errors

Update parsers:

```vim
:TSUpdate
```

Reinstall specific parser:

```vim
:TSInstall! python
```

### Missing Syntax Highlighting

1. Check if parser installed: `:TSInstallInfo`
2. Install parser: `:TSInstall <language>`
3. Check highlight status: `:TSBufToggle highlight`

### Treesitter Slow

Disable for large files:

```lua
-- lua/plugins/treesitter.lua
return {
  "nvim-treesitter/nvim-treesitter",
  opts = {
    highlight = {
      disable = function(lang, buf)
        local max_filesize = 100 * 1024  -- 100 KB
        local ok, stats = pcall(vim.loop.fs_stat, vim.api.nvim_buf_get_name(buf))
        if ok and stats and stats.size > max_filesize then
          return true
        end
      end,
    },
  },
}
```

## Keybinding Issues

### Keybinding Not Working

Check if keymap exists:

```vim
:Telescope keymaps
```

Or search directly:

```vim
:verbose nmap <leader>f
```

### Keybinding Conflict

List all mappings for a key:

```vim
:verbose map <key>
```

### Which-key Not Showing

Press key and wait (default 300ms). Adjust timeout:

```lua
-- lua/config/options.lua
vim.opt.timeoutlen = 500
```

## Display Issues

### Icons Not Displaying

Install a Nerd Font:

```bash
brew install --cask font-jetbrains-mono-nerd-font
```

Configure terminal to use the font.

### Colors Wrong

Enable true colors:

```lua
-- lua/config/options.lua
vim.opt.termguicolors = true
```

Check terminal supports true color:

```bash
echo $TERM  # Should include 256color or truecolor
```

### Cursor Shape Not Changing

Set cursor shape in terminal settings or:

```lua
-- lua/config/options.lua
vim.opt.guicursor = "n-v-c:block,i-ci-ve:ver25,r-cr:hor20,o:hor50"
```

## Performance Issues

### Slow Startup

Profile startup:

```vim
:Lazy profile
```

Identify slow plugins and lazy-load them:

```lua
return {
  "slow-plugin",
  event = "VeryLazy",  -- Load after startup
}
```

### Slow Editing

1. Disable heavy features:

```lua
-- lua/plugins/disabled.lua
return {
  { "echasnovski/mini.animate", enabled = false },
}
```

2. Reduce update frequency:

```lua
-- lua/config/options.lua
vim.opt.updatetime = 300
```

### High CPU Usage

Check running LSP servers:

```vim
:LspInfo
```

Disable diagnostics temporarily:

```vim
:lua vim.diagnostic.disable()
```

## Common Error Messages

### "module not found"

Plugin not installed. Run:

```vim
:Lazy sync
```

### "Invalid character"

Likely copy-paste issue with special characters. Check for:
- Smart quotes instead of regular quotes
- Non-breaking spaces
- Hidden Unicode characters

### "E5108: Error executing lua"

Syntax error in Lua config. Check:

```vim
:lua require("plugins.myconfig")
```

### "No information available"

LSP not attached. Check:

```vim
:LspInfo
```

## Reset Configuration

### Soft Reset

Remove plugin state:

```bash
rm -rf ~/.local/share/nvim
rm -rf ~/.local/state/nvim
rm -rf ~/.cache/nvim
```

### Hard Reset

Backup and remove everything:

```bash
mv ~/.config/nvim ~/.config/nvim.bak
mv ~/.local/share/nvim ~/.local/share/nvim.bak
```

Then reinstall LazyVim:

```bash
git clone https://github.com/LazyVim/starter ~/.config/nvim
```

## Getting Help

### Documentation

```vim
:help <topic>
:Telescope help_tags
```

### LazyVim Resources

- [LazyVim Documentation](https://www.lazyvim.org/)
- [GitHub Discussions](https://github.com/LazyVim/LazyVim/discussions)
- [LazyVim Discord](https://discord.gg/LazyVim)

### Debug Output

Enable verbose logging:

```bash
nvim -V10log.txt
```

Check the log file after reproducing the issue.
