# Quick Reference

Essential commands, shortcuts, and configuration for VS Code.

## Keyboard Shortcuts

### General

| Key | Action |
|-----|--------|
| ++cmd+shift+p++ | Command Palette |
| ++cmd+p++ | Quick Open |
| ++cmd+comma++ | Settings |
| ++cmd+b++ | Toggle Sidebar |
| ++ctrl+backtick++ | Toggle Terminal |

### Editing

| Key | Action |
|-----|--------|
| ++cmd+d++ | Select next occurrence |
| ++cmd+shift+l++ | Select all occurrences |
| ++alt+up++ / ++alt+down++ | Move line |
| ++cmd+slash++ | Toggle comment |
| ++cmd+shift+k++ | Delete line |
| ++shift+alt+f++ | Format document |

### Navigation

| Key | Action |
|-----|--------|
| ++cmd+g++ | Go to line |
| ++f12++ | Go to definition |
| ++shift+f12++ | Find references |
| ++ctrl+minus++ | Go back |
| ++cmd+shift+o++ | Go to symbol |

### Debug

| Key | Action |
|-----|--------|
| ++f5++ | Start/Continue |
| ++f9++ | Toggle breakpoint |
| ++f10++ | Step over |
| ++f11++ | Step into |
| ++shift+f11++ | Step out |

## Settings Location

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Code/User/settings.json` |
| Linux | `~/.config/Code/User/settings.json` |

## Configuration Files

```
.vscode/
├── settings.json      # Workspace settings
├── launch.json        # Debug configurations
├── tasks.json         # Build tasks
└── extensions.json    # Recommended extensions
```

## Essential Settings

```json
{
  "editor.fontFamily": "JetBrains Mono",
  "editor.fontSize": 14,
  "editor.formatOnSave": true,
  "editor.minimap.enabled": false,
  "editor.tabSize": 4,
  "workbench.colorTheme": "Dracula",
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  "telemetry.telemetryLevel": "off"
}
```

## Language Settings

### Python

```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.tabSize": 4,
    "editor.formatOnSave": true
  },
  "python.languageServer": "Pylance"
}
```

### JavaScript/TypeScript

```json
{
  "[javascript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  },
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode",
    "editor.tabSize": 2
  }
}
```

## Essential Extensions

### Python

```
ms-python.python
ms-python.vscode-pylance
ms-python.black-formatter
charliermarsh.ruff
```

### JavaScript

```
esbenp.prettier-vscode
dbaeumer.vscode-eslint
```

### Git

```
eamodio.gitlens
```

### AI

```
GitHub.copilot
GitHub.copilot-chat
```

### Productivity

```
streetsidesoftware.code-spell-checker
gruntfuggly.todo-tree
```

## CLI Commands

```bash
# Open folder
code .

# Open file at line
code -g file.py:42

# Install extension
code --install-extension ms-python.python

# List extensions
code --list-extensions

# Disable extensions
code --disable-extensions
```

## Debug Configuration

### Python

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### Node.js

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Node.js",
      "type": "node",
      "request": "launch",
      "program": "${workspaceFolder}/index.js"
    }
  ]
}
```

## Tasks

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build",
      "type": "shell",
      "command": "make build",
      "group": {
        "kind": "build",
        "isDefault": true
      }
    }
  ]
}
```

## Workspace Recommendations

`.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-python.python",
    "esbenp.prettier-vscode"
  ]
}
```

## File Exclusions

```json
{
  "files.exclude": {
    "**/__pycache__": true,
    "**/node_modules": true,
    "**/.git": true
  },
  "search.exclude": {
    "**/dist": true,
    "**/build": true
  }
}
```

## Git Settings

```json
{
  "git.enableSmartCommit": true,
  "git.autofetch": true,
  "git.confirmSync": false
}
```

## Terminal

```json
{
  "terminal.integrated.fontFamily": "JetBrains Mono",
  "terminal.integrated.fontSize": 13,
  "terminal.integrated.defaultProfile.osx": "zsh"
}
```

## Copilot Settings

```json
{
  "github.copilot.enable": {
    "*": true,
    "*.env": false,
    "*.pem": false
  }
}
```

## Common Commands

| Command | Description |
|---------|-------------|
| `Preferences: Open Settings` | Open settings |
| `Preferences: Open Keyboard Shortcuts` | Edit keybindings |
| `Developer: Reload Window` | Reload VS Code |
| `Git: Clone` | Clone repository |
| `Format Document` | Format current file |
| `Rename Symbol` | Rename across files |

## Troubleshooting

### Reset Settings

```bash
rm ~/Library/Application\ Support/Code/User/settings.json
```

### Safe Mode

```bash
code --disable-extensions
```

### View Logs

Help > Toggle Developer Tools > Console

## Themes

Popular options:

- `Dracula`
- `One Dark Pro`
- `Tokyo Night`
- `GitHub Theme`
- `Catppuccin`

Set in settings:

```json
{
  "workbench.colorTheme": "Dracula"
}
```
