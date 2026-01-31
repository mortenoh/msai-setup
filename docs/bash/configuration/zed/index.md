# Zed Editor

Zed is a high-performance, multiplayer code editor built from scratch in Rust. It combines the speed of a native application with modern editor features.

## Why Zed?

- **Performance**: Native Rust implementation, extremely fast startup and editing
- **GPU Rendering**: Hardware-accelerated text rendering
- **Collaborative**: Built-in real-time collaboration (multiplayer)
- **AI Integration**: Native support for AI assistants and Copilot
- **Modern LSP**: Fast, asynchronous Language Server Protocol support
- **Simple Configuration**: JSON-based settings without plugin complexity

## Key Features

### Speed

Zed starts instantly and handles large files without lag. The GPU-accelerated rendering provides smooth scrolling and editing even with complex syntax highlighting.

### AI Features

- **Edit Predictions**: Copilot-powered code completions
- **Agent**: AI assistant for code generation and questions
- **Inline Assist**: AI-powered code transformations

### Collaboration

- **Channels**: Create persistent spaces for teams
- **Screen Sharing**: Share your editor with collaborators
- **Real-time Editing**: Multiple cursors in the same file
- **Voice Chat**: Built-in audio communication

### Language Support

- **LSP**: Full Language Server Protocol support
- **Tree-sitter**: Fast, accurate syntax highlighting
- **Format on Save**: Automatic code formatting
- **Diagnostics**: Inline error and warning display

## Current Configuration

This setup includes:

| Setting | Value |
|---------|-------|
| Theme | One Dark Pro |
| Font | JetBrains Mono Nerd Font |
| Base Keymap | VSCode |
| Line Numbers | Relative |
| Cursor | Block, no blink |
| AI | Copilot for predictions, Agent with Claude |

### Language Support

| Language | LSP | Formatter |
|----------|-----|-----------|
| Python | pyright + ruff | ruff |
| Rust | rust-analyzer | rustfmt |
| TypeScript | typescript-language-server | prettier |
| Go | gopls | gofmt |
| JSON | json-languageserver | prettier |
| YAML | yaml-language-server | prettier |

## Quick Start

```bash
# Open current directory
zed .

# Open specific file
zed file.py

# Open multiple files
zed file1.py file2.py

# Open at specific line
zed file.py:42
```

## Essential Shortcuts

| Key | Action |
|-----|--------|
| ++cmd+p++ | Quick open file |
| ++cmd+shift+p++ | Command palette |
| ++cmd+comma++ | Settings |
| ++cmd+b++ | Toggle sidebar |
| ++cmd+shift+e++ | File explorer |
| ++cmd+shift+f++ | Search in project |
| ++ctrl+backtick++ | Toggle terminal |

## Documentation Structure

- [Installation](installation.md) - Installing and initial setup
- [Configuration](configuration.md) - settings.json structure
- [Keybindings](keybindings.md) - Keyboard shortcuts and vim mode
- [Extensions](extensions.md) - Language support and extensions
- [AI Features](ai-features.md) - Copilot, Agent, AI integration
- [Collaboration](collaboration.md) - Multiplayer features
- [Reference](reference.md) - Quick reference card
