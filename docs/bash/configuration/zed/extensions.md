# Extensions

Language support and extensions in Zed.

## Extension System

Zed uses extensions to provide language support, themes, and additional features. Extensions are written in Rust/WebAssembly for performance.

## Installing Extensions

### Via Command Palette

1. Press ++cmd+shift+p++
2. Search "zed: extensions"
3. Browse and install

### Via Settings

Enable specific language support:

```json
{
  "languages": {
    "Python": {
      "language_servers": ["pyright", "ruff"]
    }
  }
}
```

## Language Support

### Python

Required tools:

```bash
pip install pyright ruff
# Or via pipx
pipx install pyright ruff
```

Configuration:

```json
{
  "languages": {
    "Python": {
      "language_servers": ["pyright", "ruff"],
      "format_on_save": "on",
      "formatter": [
        { "code_action": "source.organizeImports.ruff" },
        { "code_action": "source.fixAll.ruff" },
        { "language_server": { "name": "ruff" } }
      ]
    }
  },
  "lsp": {
    "pyright": {
      "settings": {
        "python.analysis": {
          "typeCheckingMode": "basic",
          "autoImportCompletions": true
        }
      }
    }
  }
}
```

### Rust

Rust support is built-in via rust-analyzer:

```json
{
  "languages": {
    "Rust": {
      "format_on_save": "on"
    }
  },
  "lsp": {
    "rust-analyzer": {
      "initialization_options": {
        "checkOnSave": {
          "command": "clippy"
        },
        "cargo": {
          "features": "all"
        }
      }
    }
  }
}
```

### TypeScript/JavaScript

Install tools:

```bash
npm install -g typescript typescript-language-server prettier eslint
```

Configuration:

```json
{
  "languages": {
    "TypeScript": {
      "language_servers": ["typescript-language-server", "eslint"],
      "format_on_save": "on",
      "formatter": {
        "external": {
          "command": "prettier",
          "arguments": ["--stdin-filepath", "{buffer_path}"]
        }
      }
    },
    "JavaScript": {
      "language_servers": ["typescript-language-server", "eslint"],
      "format_on_save": "on"
    },
    "TSX": {
      "language_servers": ["typescript-language-server", "eslint"],
      "format_on_save": "on"
    },
    "JSX": {
      "language_servers": ["typescript-language-server", "eslint"],
      "format_on_save": "on"
    }
  }
}
```

### Go

Install gopls:

```bash
go install golang.org/x/tools/gopls@latest
```

Configuration:

```json
{
  "languages": {
    "Go": {
      "language_servers": ["gopls"],
      "format_on_save": "on",
      "hard_tabs": true,
      "tab_size": 4
    }
  },
  "lsp": {
    "gopls": {
      "initialization_options": {
        "hints": {
          "assignVariableTypes": true,
          "compositeLiteralFields": true,
          "functionTypeParameters": true,
          "parameterNames": true
        }
      }
    }
  }
}
```

### C/C++

Install clangd:

```bash
# macOS
brew install llvm

# Ubuntu
sudo apt install clangd
```

Configuration:

```json
{
  "languages": {
    "C": {
      "language_servers": ["clangd"],
      "format_on_save": "on"
    },
    "C++": {
      "language_servers": ["clangd"],
      "format_on_save": "on"
    }
  }
}
```

### JSON

```json
{
  "languages": {
    "JSON": {
      "format_on_save": "on",
      "tab_size": 2
    },
    "JSONC": {
      "format_on_save": "on",
      "tab_size": 2
    }
  }
}
```

### YAML

```json
{
  "languages": {
    "YAML": {
      "format_on_save": "on",
      "tab_size": 2
    }
  }
}
```

### Markdown

```json
{
  "languages": {
    "Markdown": {
      "soft_wrap": "preferred_line_length",
      "preferred_line_length": 80,
      "format_on_save": "off",
      "show_whitespaces": "none"
    }
  }
}
```

### HTML/CSS

```json
{
  "languages": {
    "HTML": {
      "format_on_save": "on",
      "formatter": {
        "external": {
          "command": "prettier",
          "arguments": ["--stdin-filepath", "{buffer_path}"]
        }
      }
    },
    "CSS": {
      "format_on_save": "on"
    },
    "SCSS": {
      "format_on_save": "on"
    }
  }
}
```

### Docker

```json
{
  "languages": {
    "Dockerfile": {
      "format_on_save": "off"
    }
  }
}
```

### Shell Scripts

Install shellcheck and shfmt:

```bash
brew install shellcheck shfmt
```

Configuration:

```json
{
  "languages": {
    "Shell Script": {
      "format_on_save": "on",
      "formatter": {
        "external": {
          "command": "shfmt",
          "arguments": ["-i", "2", "-"]
        }
      }
    }
  }
}
```

### Lua

Install lua-language-server:

```bash
brew install lua-language-server
```

Configuration:

```json
{
  "languages": {
    "Lua": {
      "language_servers": ["lua-language-server"],
      "format_on_save": "on"
    }
  },
  "lsp": {
    "lua-language-server": {
      "initialization_options": {
        "settings": {
          "Lua": {
            "diagnostics": {
              "globals": ["vim"]
            }
          }
        }
      }
    }
  }
}
```

## Themes

### Installing Themes

Themes are available as extensions:

1. ++cmd+shift+p++ > "extensions"
2. Search for theme name
3. Install and set in settings

### Popular Themes

```json
{
  "theme": "One Dark Pro"
}
```

Available themes:

- `One Dark Pro`
- `Tokyo Night`
- `Catppuccin Mocha` / `Catppuccin Latte`
- `Gruvbox Dark` / `Gruvbox Light`
- `Dracula`
- `GitHub Dark` / `GitHub Light`
- `Solarized Dark` / `Solarized Light`
- `Nord`
- `Rose Pine`

### Theme Switching

Quick switch with Command Palette:

1. ++cmd+shift+p++
2. Search "theme"
3. Select theme

## Icons

```json
{
  "icon_theme": "VSCode Icons for Zed (Dark)"
}
```

## Multiple Language Servers

Run multiple servers for a language:

```json
{
  "languages": {
    "Python": {
      "language_servers": ["pyright", "ruff"]
    }
  }
}
```

## Disable Language Server

```json
{
  "languages": {
    "Markdown": {
      "enable_language_server": false
    }
  }
}
```

## Custom Formatters

### External Formatter

```json
{
  "languages": {
    "Python": {
      "formatter": {
        "external": {
          "command": "black",
          "arguments": ["-"]
        }
      }
    }
  }
}
```

### Code Actions as Formatter

```json
{
  "languages": {
    "Python": {
      "formatter": [
        { "code_action": "source.organizeImports.ruff" },
        { "language_server": { "name": "ruff" } }
      ]
    }
  }
}
```

## Extension Development

Zed extensions use WebAssembly. See the [Zed Extension API](https://zed.dev/docs/extensions) for development details.

## Troubleshooting

### Language Server Not Starting

1. Verify tool is installed: `which pyright`
2. Check Zed logs: Command Palette > "zed: open log"
3. Restart language server: Command Palette > "lsp: restart server"

### Formatting Not Working

1. Verify formatter is installed
2. Check `format_on_save` is `"on"`
3. Check formatter configuration
4. Try manual format: ++shift+alt+f++
