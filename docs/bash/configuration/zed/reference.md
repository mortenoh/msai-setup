# Quick Reference

Essential commands, shortcuts, and configuration for Zed.

## Keyboard Shortcuts

### File Operations

| Key | Action |
|-----|--------|
| ++cmd+p++ | Quick open file |
| ++cmd+shift+p++ | Command palette |
| ++cmd+n++ | New file |
| ++cmd+s++ | Save |
| ++cmd+w++ | Close tab |

### Navigation

| Key | Action |
|-----|--------|
| ++cmd+g++ | Go to line |
| ++cmd+shift+o++ | Go to symbol |
| ++f12++ | Go to definition |
| ++shift+f12++ | Find references |
| ++ctrl+minus++ | Go back |

### Search

| Key | Action |
|-----|--------|
| ++cmd+f++ | Find in file |
| ++cmd+shift+f++ | Find in project |
| ++cmd+h++ | Find and replace |
| ++cmd+d++ | Select next occurrence |

### Editing

| Key | Action |
|-----|--------|
| ++cmd+slash++ | Toggle comment |
| ++alt+up++ / ++alt+down++ | Move line |
| ++cmd+shift+k++ | Delete line |
| ++shift+alt+f++ | Format document |
| ++cmd+period++ | Quick fix |

### View

| Key | Action |
|-----|--------|
| ++cmd+b++ | Toggle sidebar |
| ++cmd+backslash++ | Split editor |
| ++ctrl+backtick++ | Toggle terminal |
| ++cmd+comma++ | Open settings |

### AI

| Key | Action |
|-----|--------|
| ++cmd+shift+a++ | Open Agent |
| ++cmd+enter++ | Inline assist |
| ++tab++ | Accept completion |

## Configuration Files

### Settings Location

```
~/.config/zed/settings.json
~/.config/zed/keymap.json
```

### Project Settings

```
.zed/settings.json
```

## Essential Settings

### Minimal Configuration

```json
{
  "theme": "One Dark Pro",
  "buffer_font_family": "JetBrains Mono",
  "buffer_font_size": 14,
  "format_on_save": "on",
  "telemetry": {
    "diagnostics": false,
    "metrics": false
  }
}
```

### Editor Appearance

```json
{
  "cursor_blink": false,
  "cursor_shape": "block",
  "relative_line_numbers": true,
  "tab_size": 4
}
```

### AI Configuration

```json
{
  "features": {
    "edit_prediction_provider": "copilot"
  },
  "agent": {
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

## Full Configuration Example

```json
{
  "icon_theme": "VSCode Icons for Zed (Dark)",
  "theme": "One Dark Pro",
  "buffer_font_family": "JetBrains Mono",
  "buffer_font_size": 14,
  "buffer_font_weight": 400,
  "buffer_line_height": { "custom": 1.6 },
  "ui_font_family": "JetBrains Mono",
  "ui_font_size": 14,
  "base_keymap": "VSCode",
  "cursor_blink": false,
  "cursor_shape": "block",
  "relative_line_numbers": true,
  "vertical_scroll_margin": 5,
  "tab_size": 4,
  "format_on_save": "on",
  "toolbar": {
    "breadcrumbs": true,
    "quick_actions": true
  },
  "project_panel": {
    "dock": "left",
    "entry_spacing": "comfortable",
    "git_status": true
  },
  "git": {
    "inline_blame": { "enabled": false },
    "git_gutter": "tracked_files"
  },
  "inlay_hints": {
    "enabled": true,
    "show_type_hints": true,
    "show_parameter_hints": true
  },
  "telemetry": {
    "diagnostics": false,
    "metrics": false
  },
  "features": {
    "edit_prediction_provider": "copilot"
  },
  "agent": {
    "enabled": true,
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    }
  },
  "languages": {
    "Python": {
      "tab_size": 4,
      "format_on_save": "on",
      "language_servers": ["pyright", "ruff"],
      "formatter": [
        { "code_action": "source.organizeImports.ruff" },
        { "code_action": "source.fixAll.ruff" },
        { "language_server": { "name": "ruff" } }
      ]
    },
    "Rust": {
      "tab_size": 4,
      "format_on_save": "on"
    },
    "TypeScript": {
      "tab_size": 2,
      "format_on_save": "on"
    },
    "JavaScript": {
      "tab_size": 2,
      "format_on_save": "on"
    },
    "Go": {
      "tab_size": 4,
      "hard_tabs": true,
      "format_on_save": "on"
    },
    "JSON": {
      "tab_size": 2,
      "format_on_save": "on"
    },
    "YAML": {
      "tab_size": 2
    },
    "Markdown": {
      "soft_wrap": "preferred_line_length",
      "preferred_line_length": 80,
      "format_on_save": "off"
    }
  },
  "lsp": {
    "pyright": {
      "settings": {
        "python.analysis": {
          "typeCheckingMode": "basic",
          "autoImportCompletions": true,
          "diagnosticMode": "workspace"
        }
      }
    },
    "rust-analyzer": {
      "initialization_options": {
        "checkOnSave": {
          "command": "clippy"
        }
      }
    }
  },
  "terminal": {
    "dock": "bottom",
    "font_family": "JetBrains Mono",
    "font_size": 13
  },
  "file_scan_exclusions": [
    "**/.git",
    "**/node_modules",
    "**/__pycache__",
    "**/.venv",
    "**/target"
  ]
}
```

## Vim Mode Keybindings

```json
[
  {
    "context": "Editor && vim_mode == normal",
    "bindings": {
      "space space": "file_finder::Toggle",
      "space /": "workspace::NewSearch",
      "space e": "project_panel::ToggleFocus",
      "space w": "workspace::Save",
      "space q": "pane::CloseActiveItem",
      "space c a": "editor::ToggleCodeActions",
      "space c r": "editor::Rename",
      "g d": "editor::GoToDefinition",
      "g r": "editor::FindAllReferences",
      "K": "editor::Hover"
    }
  },
  {
    "context": "Pane",
    "bindings": {
      "ctrl+h": ["workspace::ActivatePaneInDirection", "Left"],
      "ctrl+l": ["workspace::ActivatePaneInDirection", "Right"],
      "ctrl+k": ["workspace::ActivatePaneInDirection", "Up"],
      "ctrl+j": ["workspace::ActivatePaneInDirection", "Down"]
    }
  }
]
```

## Common Commands

| Command | Action |
|---------|--------|
| `zed .` | Open current directory |
| `zed file.py` | Open file |
| `zed file.py:42` | Open file at line |
| `zed --new` | New window |

## LSP Commands

| Shortcut | Action |
|----------|--------|
| ++f12++ | Go to definition |
| ++alt+f12++ | Peek definition |
| ++shift+f12++ | Find references |
| ++f2++ | Rename |
| ++cmd+period++ | Code actions |
| ++shift+alt+f++ | Format |

## Diagnostics

| Shortcut | Action |
|----------|--------|
| ++f8++ | Next diagnostic |
| ++shift+f8++ | Previous diagnostic |
| ++cmd+shift+m++ | Show problems |

## Themes

Popular options:

- `One Dark Pro`
- `Tokyo Night`
- `Catppuccin Mocha`
- `Gruvbox Dark`
- `Dracula`
- `GitHub Dark`
- `Solarized Dark`

## File Patterns

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

## Troubleshooting

### View Logs

Command Palette > "zed: open log"

### Reset Settings

```bash
rm ~/.config/zed/settings.json
```

### Restart LSP

Command Palette > "lsp: restart server"

### Check Updates

Zed menu > "Check for Updates"
