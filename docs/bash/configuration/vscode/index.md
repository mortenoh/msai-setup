# VS Code

Visual Studio Code is a free, open-source code editor from Microsoft with extensive language support, debugging, and a rich extension ecosystem.

## Why VS Code?

- **Extensive Extensions**: Thousands of extensions for any language or workflow
- **Integrated Debugging**: Built-in debugger with breakpoints and watch expressions
- **Git Integration**: Source control features built into the editor
- **Remote Development**: Edit code on remote machines, containers, or WSL
- **IntelliSense**: Smart code completion for many languages
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Key Features

### Language Support

Out-of-the-box support for:

- JavaScript/TypeScript
- Python
- HTML/CSS
- JSON/YAML/Markdown
- And many more via extensions

### Developer Experience

- **IntelliSense**: Context-aware completions
- **Code Navigation**: Go to definition, find references
- **Refactoring**: Rename, extract method, quick fixes
- **Snippets**: Code templates and shortcuts
- **Multi-cursor**: Edit multiple locations simultaneously

### Debugging

- Integrated debugger
- Breakpoints and logpoints
- Variable inspection
- Call stack navigation
- Debug console

### Source Control

- Git integration
- Diff viewer
- Branch management
- Commit history
- GitHub integration

## Current Configuration

| Setting | Value |
|---------|-------|
| Theme | Dracula |
| Font | Fira Mono Powerline |
| Language Server | Pylance (Python) |
| Formatter | Prettier |
| Format on Save | Enabled |
| Minimap | Disabled |

### Language Settings

| Language | Formatter |
|----------|-----------|
| JavaScript | Prettier |
| JSON | Prettier |
| HTML | Prettier |
| Markdown | Prettier |
| Dockerfile | Docker extension |

## Quick Start

```bash
# Open current directory
code .

# Open specific file
code file.py

# Open folder in new window
code -n ~/projects/myapp

# Open file at specific line
code -g file.py:42
```

## Essential Shortcuts

| Key | Action |
|-----|--------|
| ++cmd+p++ | Quick open file |
| ++cmd+shift+p++ | Command palette |
| ++cmd+comma++ | Settings |
| ++cmd+b++ | Toggle sidebar |
| ++ctrl+backtick++ | Toggle terminal |
| ++cmd+shift+f++ | Search in files |
| ++f12++ | Go to definition |
| ++cmd+d++ | Select next occurrence |

## Documentation Structure

- [Installation](installation.md) - Installing and setup
- [Configuration](configuration.md) - Settings structure
- [Keybindings](keybindings.md) - Keyboard shortcuts
- [Extensions](extensions.md) - Essential extensions
- [AI Features](ai-features.md) - Copilot and AI assistants
- [Debugging](debugging.md) - Debug configurations
- [Reference](reference.md) - Quick reference card
