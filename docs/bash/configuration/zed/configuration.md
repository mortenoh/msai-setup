# Configuration

Understanding and customizing Zed's settings.

## Settings File

Settings are stored in `~/.config/zed/settings.json`. Open with ++cmd+comma++ or via Command Palette.

## Basic Settings

### Font Configuration

```json
{
  "buffer_font_family": "JetBrains Mono",
  "buffer_font_size": 14,
  "buffer_font_weight": 400,
  "buffer_line_height": { "custom": 1.6 },
  "ui_font_family": "JetBrains Mono",
  "ui_font_size": 14
}
```

### Theme

```json
{
  "theme": "One Dark Pro"
}
```

Popular themes:

- `One Dark Pro`
- `Tokyo Night`
- `Catppuccin Mocha`
- `Gruvbox Dark`
- `Dracula`
- `GitHub Dark`
- `Solarized Dark`

### Editor Appearance

```json
{
  "cursor_blink": false,
  "cursor_shape": "block",
  "relative_line_numbers": true,
  "show_whitespaces": "selection",
  "vertical_scroll_margin": 5,
  "scrollbar": {
    "show": "auto"
  },
  "gutter": {
    "line_numbers": true,
    "code_actions": true,
    "folds": true
  }
}
```

### Cursor Shapes

- `bar` - Thin vertical line
- `block` - Full character block
- `underline` - Underscore
- `hollow` - Outlined block

## Editor Behavior

### Indentation

```json
{
  "tab_size": 4,
  "hard_tabs": false,
  "soft_wrap": "none"
}
```

Soft wrap options:

- `none` - No wrapping
- `editor_width` - Wrap at editor width
- `preferred_line_length` - Wrap at specified width

### File Handling

```json
{
  "format_on_save": "on",
  "remove_trailing_whitespace_on_save": true,
  "ensure_final_newline_on_save": true,
  "autosave": {
    "after_delay": { "milliseconds": 1000 }
  }
}
```

Format on save options:

- `on` - Always format
- `off` - Never format
- `language_server` - Use LSP formatter

### Search

```json
{
  "search": {
    "whole_word": false,
    "case_sensitive": false,
    "include_ignored": false,
    "regex": false
  }
}
```

## UI Configuration

### Toolbar and Panels

```json
{
  "toolbar": {
    "breadcrumbs": true,
    "quick_actions": true
  },
  "project_panel": {
    "dock": "left",
    "entry_spacing": "comfortable",
    "git_status": true,
    "auto_reveal_entries": true
  },
  "outline_panel": {
    "dock": "right"
  },
  "terminal": {
    "dock": "bottom"
  }
}
```

### Tabs

```json
{
  "tabs": {
    "close_position": "right",
    "file_icons": true,
    "git_status": true
  }
}
```

### Git Integration

```json
{
  "git": {
    "inline_blame": {
      "enabled": true,
      "delay_ms": 500
    },
    "git_gutter": "tracked_files"
  }
}
```

## Language-Specific Settings

### Python

```json
{
  "languages": {
    "Python": {
      "tab_size": 4,
      "format_on_save": "on",
      "formatter": [
        { "code_action": "source.organizeImports.ruff" },
        { "code_action": "source.fixAll.ruff" },
        { "language_server": { "name": "ruff" } }
      ]
    }
  }
}
```

### Rust

```json
{
  "languages": {
    "Rust": {
      "tab_size": 4,
      "format_on_save": "on",
      "formatter": {
        "language_server": { "name": "rust-analyzer" }
      }
    }
  }
}
```

### TypeScript/JavaScript

```json
{
  "languages": {
    "TypeScript": {
      "tab_size": 2,
      "format_on_save": "on",
      "formatter": {
        "external": {
          "command": "prettier",
          "arguments": ["--stdin-filepath", "{buffer_path}"]
        }
      }
    },
    "JavaScript": {
      "tab_size": 2,
      "format_on_save": "on"
    }
  }
}
```

### Go

```json
{
  "languages": {
    "Go": {
      "tab_size": 4,
      "hard_tabs": true,
      "format_on_save": "on",
      "formatter": {
        "language_server": { "name": "gopls" }
      }
    }
  }
}
```

### JSON/YAML

```json
{
  "languages": {
    "JSON": {
      "tab_size": 2,
      "format_on_save": "on"
    },
    "YAML": {
      "tab_size": 2,
      "preferred_line_length": 120
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
      "format_on_save": "off"
    }
  }
}
```

## LSP Configuration

### General LSP Settings

```json
{
  "lsp": {
    "rust-analyzer": {
      "initialization_options": {
        "checkOnSave": {
          "command": "clippy"
        }
      }
    }
  }
}
```

### Pyright Configuration

```json
{
  "lsp": {
    "pyright": {
      "settings": {
        "python.analysis": {
          "typeCheckingMode": "basic",
          "autoImportCompletions": true,
          "diagnosticMode": "workspace",
          "useLibraryCodeForTypes": true,
          "inlayHints": {
            "functionReturnTypes": true,
            "variableTypes": true,
            "parameterTypes": true
          }
        }
      }
    }
  }
}
```

### Ruff Configuration

```json
{
  "lsp": {
    "ruff": {
      "initialization_options": {
        "settings": {
          "path": ["./pyproject.toml"],
          "lineLength": 88,
          "lint": {
            "select": ["E", "F", "I", "UP"]
          }
        }
      }
    }
  }
}
```

## Inlay Hints

```json
{
  "inlay_hints": {
    "enabled": true,
    "show_type_hints": true,
    "show_parameter_hints": true,
    "show_other_hints": true
  }
}
```

## Completions

```json
{
  "show_completions_on_input": true,
  "show_completion_documentation": true,
  "completion_documentation_secondary_query_debounce": 300
}
```

## Terminal

```json
{
  "terminal": {
    "dock": "bottom",
    "default_width": 640,
    "default_height": 320,
    "font_family": "JetBrains Mono",
    "font_size": 13,
    "line_height": { "custom": 1.4 },
    "shell": {
      "program": "/bin/zsh"
    },
    "env": {
      "TERM": "xterm-256color"
    }
  }
}
```

## Telemetry

Disable telemetry:

```json
{
  "telemetry": {
    "diagnostics": false,
    "metrics": false
  }
}
```

## File Associations

```json
{
  "file_types": {
    "Dockerfile": ["Dockerfile*", "*.dockerfile"],
    "JSON": ["*.json", ".prettierrc", ".eslintrc"],
    "YAML": ["*.yml", "*.yaml", "docker-compose*"]
  }
}
```

## Excluded Files

```json
{
  "file_scan_exclusions": [
    "**/.git",
    "**/node_modules",
    "**/__pycache__",
    "**/.venv",
    "**/target",
    "**/dist",
    "**/build"
  ]
}
```

## Project Settings

Create `.zed/settings.json` in project root for project-specific settings:

```json
{
  "tab_size": 2,
  "languages": {
    "TypeScript": {
      "tab_size": 2
    }
  },
  "lsp": {
    "typescript-language-server": {
      "initialization_options": {
        "preferences": {
          "importModuleSpecifierPreference": "relative"
        }
      }
    }
  }
}
```

## Full Configuration Example

See the [Reference](reference.md) page for a complete example configuration.
