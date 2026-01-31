# Continue.dev

Multi-editor AI assistant with local-first configuration and autocomplete.

## Overview

Continue.dev provides:

- **Multi-editor** - VS Code and JetBrains support
- **Autocomplete** - Tab completion with local models
- **Chat** - Inline and panel chat
- **Local-first** - Native Ollama and local API support
- **Configurable** - JSON-based configuration

## Installation

### VS Code

1. Open Extensions (`Ctrl+Shift+X`)
2. Search "Continue"
3. Click Install

### JetBrains

1. Open Settings → Plugins
2. Search "Continue"
3. Click Install

### Via CLI

```bash
# VS Code
code --install-extension Continue.continue
```

## Configuration

### Config File Location

| Platform | Path |
|----------|------|
| macOS | `~/.continue/config.json` |
| Linux | `~/.continue/config.json` |
| Windows | `%USERPROFILE%\.continue\config.json` |

### Basic Configuration

```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Autocomplete",
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b"
  }
}
```

### Full Configuration

```json
{
  "models": [
    {
      "title": "DeepSeek Coder (Local)",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Llama 3.3 70B (Local)",
      "provider": "ollama",
      "model": "llama3.3:70b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Fast Model",
      "provider": "ollama",
      "model": "mistral:7b"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Autocomplete",
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b"
  },
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "customCommands": [
    {
      "name": "test",
      "description": "Write unit tests",
      "prompt": "Write unit tests for the selected code. Use the project's testing framework."
    }
  ],
  "contextProviders": [
    {
      "name": "code",
      "params": {}
    },
    {
      "name": "docs",
      "params": {}
    }
  ]
}
```

## Providers

### Ollama

```json
{
  "models": [
    {
      "title": "Local Ollama",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "apiBase": "http://localhost:11434"
    }
  ]
}
```

### OpenAI-Compatible

```json
{
  "models": [
    {
      "title": "Local llama.cpp",
      "provider": "openai",
      "model": "llama3.3",
      "apiBase": "http://localhost:8080/v1",
      "apiKey": "not-needed"
    }
  ]
}
```

### LM Studio

```json
{
  "models": [
    {
      "title": "LM Studio",
      "provider": "lmstudio",
      "model": "loaded-model"
    }
  ]
}
```

### Remote Ollama

```json
{
  "models": [
    {
      "title": "Remote Server",
      "provider": "ollama",
      "model": "llama3.3:70b",
      "apiBase": "https://server.tailnet.ts.net"
    }
  ]
}
```

## Features

### Tab Autocomplete

Enable intelligent code completion:

```json
{
  "tabAutocompleteModel": {
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b"
  },
  "tabAutocompleteOptions": {
    "debounceDelay": 500,
    "maxPromptTokens": 1024
  }
}
```

Usage:
- Type code
- Wait for suggestion
- Press `Tab` to accept

### Chat

Open chat panel:
- `Ctrl+L` (VS Code)
- Click Continue icon in sidebar

### Inline Editing

Select code and:
- `Ctrl+I` for inline edit
- Type instruction
- Review and apply

### Slash Commands

In chat:

| Command | Action |
|---------|--------|
| `/edit` | Edit selected code |
| `/comment` | Add comments |
| `/test` | Generate tests |
| `/docs` | Generate documentation |
| `/share` | Share conversation |

### @ Mentions

Reference context:

| Mention | Description |
|---------|-------------|
| `@file` | Include file content |
| `@folder` | Include folder context |
| `@codebase` | Search codebase |
| `@docs` | Include documentation |
| `@terminal` | Include terminal output |

## Custom Commands

### Define Commands

```json
{
  "customCommands": [
    {
      "name": "review",
      "description": "Code review",
      "prompt": "Review this code for:\n- Bugs and errors\n- Performance issues\n- Security vulnerabilities\n- Code style"
    },
    {
      "name": "explain",
      "description": "Explain code",
      "prompt": "Explain what this code does in simple terms."
    },
    {
      "name": "optimize",
      "description": "Optimize code",
      "prompt": "Suggest optimizations for this code. Focus on performance and readability."
    }
  ]
}
```

### Use Commands

In chat:
```
/review

/explain

/optimize
```

## Context Providers

### Built-in Providers

```json
{
  "contextProviders": [
    {
      "name": "code",
      "params": {}
    },
    {
      "name": "docs",
      "params": {}
    },
    {
      "name": "terminal",
      "params": {}
    },
    {
      "name": "open",
      "params": {}
    }
  ]
}
```

### Documentation Provider

Index project docs:

```json
{
  "contextProviders": [
    {
      "name": "docs",
      "params": {
        "sites": [
          {
            "title": "Project Docs",
            "startUrl": "https://docs.example.com",
            "rootUrl": "https://docs.example.com"
          }
        ]
      }
    }
  ]
}
```

## Embeddings

### Local Embeddings

```json
{
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  }
}
```

### Codebase Indexing

Enable codebase search:

```json
{
  "contextProviders": [
    {
      "name": "codebase",
      "params": {
        "nRetrieve": 10,
        "nFinal": 5
      }
    }
  ]
}
```

Usage in chat:
```
@codebase How is authentication implemented?
```

## Model Settings

### Per-Model Configuration

```json
{
  "models": [
    {
      "title": "Coding Model",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "contextLength": 16384,
      "completionOptions": {
        "temperature": 0.3,
        "topP": 0.95,
        "maxTokens": 2048
      },
      "systemMessage": "You are a senior software engineer..."
    }
  ]
}
```

### Template Override

```json
{
  "models": [
    {
      "title": "Custom Template",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "template": "deepseek"
    }
  ]
}
```

## Keyboard Shortcuts

### VS Code

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Open chat |
| `Ctrl+I` | Inline edit |
| `Tab` | Accept autocomplete |
| `Ctrl+Shift+L` | Add to chat |
| `Ctrl+Shift+R` | Reject all |

### JetBrains

| Shortcut | Action |
|----------|--------|
| `Ctrl+J` | Open chat |
| `Ctrl+Shift+J` | Inline edit |
| `Tab` | Accept autocomplete |

## Troubleshooting

### No Autocomplete

```bash
# Verify Ollama is running
curl http://localhost:11434/

# Check model is pulled
ollama list

# Verify config
cat ~/.continue/config.json
```

### Chat Not Working

- Check model configuration
- Verify API base URL
- Test with curl:
  ```bash
  curl http://localhost:11434/v1/chat/completions \
    -d '{"model":"deepseek-coder-v2:16b","messages":[{"role":"user","content":"Hi"}]}'
  ```

### Slow Performance

- Use faster model for autocomplete
- Reduce context length
- Check GPU utilization

### Context Issues

- Use `@file` to explicitly include files
- Check `.continueignore` for excluded patterns
- Reduce codebase index size

## .continueignore

Create `.continueignore` in project:

```
node_modules/
dist/
build/
.git/
*.log
*.min.js
```

## Comparison with Alternatives

| Feature | Continue | Cline | Aider |
|---------|----------|-------|-------|
| Editor | VS Code, JetBrains | VS Code | CLI |
| Autocomplete | Yes | No | No |
| Local models | Yes | Yes | Yes |
| Codebase search | Yes | Limited | Yes |
| Custom commands | Yes | No | No |

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Ollama](../inference-engines/ollama.md) - Local model serving
- [Cline](cline.md) - Alternative extension
- [Choosing Models](../models/choosing-models.md) - Model selection
