# Language Support

Configuring LSP servers and language-specific features in LazyVim.

## LazyVim Extras

LazyVim provides pre-configured language support through "extras". Enable them via:

```vim
:LazyExtras
```

Navigate with ++j++ / ++k++, toggle with ++x++.

### Available Language Extras

| Extra | Languages/Tools |
|-------|-----------------|
| `lang.python` | Python (pyright, ruff) |
| `lang.rust` | Rust (rust-analyzer) |
| `lang.go` | Go (gopls, gofumpt) |
| `lang.typescript` | TypeScript/JavaScript |
| `lang.java` | Java (jdtls) |
| `lang.clangd` | C/C++ |
| `lang.json` | JSON with schemas |
| `lang.yaml` | YAML with schemas |
| `lang.markdown` | Markdown |
| `lang.docker` | Dockerfile, compose |
| `lang.terraform` | Terraform/HCL |
| `lang.sql` | SQL |
| `lang.toml` | TOML |

### Current Configuration

Enabled extras in `lazyvim.json`:

```json
{
  "extras": [
    "lazyvim.plugins.extras.lang.docker",
    "lazyvim.plugins.extras.lang.git",
    "lazyvim.plugins.extras.lang.json",
    "lazyvim.plugins.extras.lang.markdown",
    "lazyvim.plugins.extras.lang.python",
    "lazyvim.plugins.extras.lang.rust",
    "lazyvim.plugins.extras.lang.toml"
  ]
}
```

## Mason: LSP Server Manager

Mason manages installation of LSP servers, linters, and formatters.

### Opening Mason

```vim
:Mason
```

### Installing Servers

In Mason UI:

1. Navigate to the package
2. Press ++i++ to install
3. Press ++shift+x++ to uninstall

Or via command:

```vim
:MasonInstall pyright ruff rust-analyzer
```

### Installed Tools Location

```
~/.local/share/nvim/mason/bin/
```

## Python Configuration

### LSP: Pyright

Pyright provides type checking and IntelliSense.

```lua
-- lua/config/options.lua
vim.g.lazyvim_python_lsp = "pyright"
```

Or use `basedpyright` for stricter checking:

```lua
vim.g.lazyvim_python_lsp = "basedpyright"
```

### Linting/Formatting: Ruff

Ruff handles linting and formatting (replaces black, isort, flake8).

```lua
-- lua/config/options.lua
vim.g.lazyvim_python_ruff = "ruff"
```

### pyproject.toml Configuration

```toml
[tool.pyright]
typeCheckingMode = "basic"
pythonVersion = "3.12"
venvPath = "."
venv = ".venv"

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP"]
ignore = ["E501"]

[tool.ruff.format]
quote-style = "double"
```

### Virtual Environment

LazyVim auto-detects virtual environments. Set manually if needed:

```vim
:PyrightSetPythonPath /path/to/.venv/bin/python
```

## Rust Configuration

### LSP: rust-analyzer

Enable the Rust extra:

```vim
:LazyExtras
```

Select `lang.rust`.

### Cargo.toml

rust-analyzer reads configuration from Cargo.toml and .cargo/config.toml.

### Features

- Inline type hints
- Macro expansion
- Cargo commands
- Test runner integration

### Keybindings

| Key | Action |
|-----|--------|
| ++space+c+r++ | Cargo run |
| ++space+c+t++ | Cargo test |
| ++space+c+c++ | Cargo check |

## TypeScript/JavaScript

Enable the TypeScript extra:

```vim
:LazyExtras
```

Select `lang.typescript`.

### Servers

- **typescript-language-server**: LSP for TS/JS
- **eslint**: Linting
- **prettier**: Formatting

### Configuration

For formatting, use prettier with:

```lua
-- lua/plugins/formatting.lua
return {
  "stevearc/conform.nvim",
  opts = {
    formatters_by_ft = {
      javascript = { "prettier" },
      typescript = { "prettier" },
      typescriptreact = { "prettier" },
      javascriptreact = { "prettier" },
    },
  },
}
```

## Go Configuration

Enable the Go extra:

```vim
:LazyExtras
```

Select `lang.go`.

### Servers

- **gopls**: LSP
- **gofumpt**: Formatting
- **golines**: Line length
- **goimports**: Import management

## JSON/YAML Configuration

Enable JSON extra:

```vim
:LazyExtras
```

Select `lang.json` and/or `lang.yaml`.

### Schema Support

JSON and YAML files get schema validation from SchemaStore.

### Associate Files with Schemas

```json
// .vscode/settings.json (works with many tools)
{
  "json.schemas": [
    {
      "fileMatch": ["package.json"],
      "url": "https://json.schemastore.org/package"
    }
  ]
}
```

## Docker Configuration

Enable Docker extra:

```vim
:LazyExtras
```

Select `lang.docker`.

### Servers

- **dockerfile-language-server**: Dockerfile LSP
- **docker-compose-language-service**: Compose LSP

## Custom LSP Configuration

### Override LSP Settings

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
              typeCheckingMode = "strict",
              autoImportCompletions = true,
              diagnosticMode = "workspace",
            },
          },
        },
      },
    },
  },
}
```

### Add New LSP Server

```lua
-- lua/plugins/lsp.lua
return {
  "neovim/nvim-lspconfig",
  opts = {
    servers = {
      -- Add a new server
      gleam = {},
      -- With custom config
      lua_ls = {
        settings = {
          Lua = {
            workspace = {
              checkThirdParty = false,
            },
          },
        },
      },
    },
  },
}
```

### Disable LSP Server

```lua
-- lua/plugins/lsp.lua
return {
  "neovim/nvim-lspconfig",
  opts = {
    servers = {
      tsserver = {
        enabled = false,
      },
    },
  },
}
```

## Formatting

### conform.nvim

LazyVim uses conform.nvim for formatting.

```lua
-- lua/plugins/formatting.lua
return {
  "stevearc/conform.nvim",
  opts = {
    formatters_by_ft = {
      python = { "ruff_format" },
      rust = { "rustfmt" },
      lua = { "stylua" },
      javascript = { "prettier" },
      typescript = { "prettier" },
      json = { "prettier" },
      yaml = { "prettier" },
      markdown = { "prettier" },
    },
    format_on_save = {
      timeout_ms = 3000,
      lsp_fallback = true,
    },
  },
}
```

### Toggle Format on Save

```vim
:lua vim.g.autoformat = false
```

Or use keybinding ++space+u+f++.

## Linting

### nvim-lint

For additional linting beyond LSP:

```lua
-- lua/plugins/linting.lua
return {
  "mfussenegger/nvim-lint",
  opts = {
    linters_by_ft = {
      python = { "ruff" },
      javascript = { "eslint" },
      typescript = { "eslint" },
    },
  },
}
```

## Treesitter

Install parsers for syntax highlighting:

```vim
:TSInstall python rust lua javascript typescript go
```

### Ensure Parsers Installed

```lua
-- lua/plugins/treesitter.lua
return {
  "nvim-treesitter/nvim-treesitter",
  opts = {
    ensure_installed = {
      "bash",
      "dockerfile",
      "go",
      "json",
      "lua",
      "markdown",
      "python",
      "rust",
      "toml",
      "typescript",
      "yaml",
    },
  },
}
```

## Debugging (DAP)

Enable debugging support:

```vim
:LazyExtras
```

Select `dap.core` and language-specific adapters like `dap.python`.

### Keybindings

| Key | Action |
|-----|--------|
| ++space+d+b++ | Toggle breakpoint |
| ++space+d+c++ | Continue |
| ++space+d+s++ | Step over |
| ++space+d+i++ | Step into |
| ++space+d+o++ | Step out |
| ++space+d+t++ | Terminate |

## LSP Keybindings Reference

| Key | Action |
|-----|--------|
| ++g+d++ | Go to definition |
| ++g+r++ | Go to references |
| ++g+i++ | Go to implementation |
| ++g+y++ | Go to type definition |
| ++shift+k++ | Hover documentation |
| ++space+c+a++ | Code actions |
| ++space+c+r++ | Rename symbol |
| ++space+c+f++ | Format buffer |
| ++space+c+l++ | LSP info |
| ++bracket-left+d++ | Previous diagnostic |
| ++bracket-right+d++ | Next diagnostic |
