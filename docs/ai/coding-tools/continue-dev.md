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

## Multi-Provider Configuration

Configure multiple providers with fallback support.

### Local + Cloud Hybrid

```json
{
  "models": [
    {
      "title": "Local Qwen (Primary)",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "apiBase": "http://localhost:11434"
    },
    {
      "title": "Claude (Fallback)",
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "apiKey": "${env:ANTHROPIC_API_KEY}"
    },
    {
      "title": "Local Fast (Quick Tasks)",
      "provider": "ollama",
      "model": "codestral:22b"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Local Autocomplete",
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b"
  }
}
```

### Remote Ollama Server

```json
{
  "models": [
    {
      "title": "Remote GPU Server",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "apiBase": "http://gpu-server.tailnet.ts.net:11434"
    }
  ]
}
```

### Multiple Local Providers

```json
{
  "models": [
    {
      "title": "Ollama - DeepSeek",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b"
    },
    {
      "title": "LM Studio - Llama",
      "provider": "lmstudio",
      "model": "llama-3.3-70b"
    },
    {
      "title": "llama.cpp Server",
      "provider": "openai",
      "model": "codestral",
      "apiBase": "http://localhost:8080/v1",
      "apiKey": "not-needed"
    }
  ]
}
```

## Ollama Integration Examples

### Basic Ollama Setup

```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b",
      "contextLength": 16384,
      "completionOptions": {
        "temperature": 0.2,
        "topP": 0.9,
        "maxTokens": 4096
      }
    }
  ]
}
```

### Model-Specific Settings

```json
{
  "models": [
    {
      "title": "Qwen Coder (Precise)",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "completionOptions": {
        "temperature": 0.1,
        "topP": 0.95,
        "frequencyPenalty": 0.1
      },
      "systemMessage": "You are an expert software engineer. Write clean, efficient code."
    },
    {
      "title": "Llama (Creative)",
      "provider": "ollama",
      "model": "llama3.3:70b",
      "completionOptions": {
        "temperature": 0.7,
        "topP": 0.9
      }
    }
  ]
}
```

### Autocomplete with Local Models

```json
{
  "tabAutocompleteModel": {
    "title": "Fast Autocomplete",
    "provider": "ollama",
    "model": "deepseek-coder-v2:16b",
    "completionOptions": {
      "temperature": 0.0,
      "maxTokens": 256
    }
  },
  "tabAutocompleteOptions": {
    "debounceDelay": 300,
    "maxPromptTokens": 1024,
    "multilineCompletions": "always"
  }
}
```

## Custom Slash Commands

### Define Custom Commands

```json
{
  "customCommands": [
    {
      "name": "test",
      "description": "Generate unit tests",
      "prompt": "Write comprehensive unit tests for the selected code. Use the project's testing framework. Include edge cases and error scenarios."
    },
    {
      "name": "review",
      "description": "Code review",
      "prompt": "Review this code for:\n- Bugs and potential errors\n- Performance issues\n- Security vulnerabilities\n- Code style and readability\n- Suggestions for improvement"
    },
    {
      "name": "refactor",
      "description": "Suggest refactoring",
      "prompt": "Analyze this code and suggest refactoring opportunities:\n- Extract methods/functions\n- Reduce complexity\n- Improve naming\n- Apply design patterns where appropriate"
    },
    {
      "name": "docs",
      "description": "Generate documentation",
      "prompt": "Generate comprehensive documentation for this code including:\n- Function/class description\n- Parameters and return values\n- Usage examples\n- Any important notes or caveats"
    },
    {
      "name": "security",
      "description": "Security audit",
      "prompt": "Perform a security audit of this code. Check for:\n- Input validation issues\n- Injection vulnerabilities\n- Authentication/authorization problems\n- Data exposure risks\n- OWASP Top 10 vulnerabilities"
    },
    {
      "name": "perf",
      "description": "Performance analysis",
      "prompt": "Analyze this code for performance issues:\n- Time complexity\n- Space complexity\n- Database query optimization\n- Caching opportunities\n- Async/parallel processing potential"
    }
  ]
}
```

### Language-Specific Commands

```json
{
  "customCommands": [
    {
      "name": "pytest",
      "description": "Generate pytest tests",
      "prompt": "Generate pytest test cases for this Python code. Use fixtures where appropriate, parametrize test cases, and include both happy path and error scenarios."
    },
    {
      "name": "types",
      "description": "Add TypeScript types",
      "prompt": "Add comprehensive TypeScript types to this code. Use interfaces for objects, enums where appropriate, and generic types when needed."
    },
    {
      "name": "hook",
      "description": "Convert to React hook",
      "prompt": "Convert this logic into a reusable React hook. Follow React hooks best practices, handle cleanup properly, and include TypeScript types."
    }
  ]
}
```

## Context Providers Setup

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
      "name": "diff",
      "params": {}
    },
    {
      "name": "terminal",
      "params": {}
    },
    {
      "name": "problems",
      "params": {}
    },
    {
      "name": "folder",
      "params": {}
    },
    {
      "name": "codebase",
      "params": {
        "nRetrieve": 25,
        "nFinal": 10,
        "useReranking": true
      }
    }
  ]
}
```

### Documentation Provider

Index external documentation:

```json
{
  "contextProviders": [
    {
      "name": "docs",
      "params": {
        "sites": [
          {
            "title": "React Docs",
            "startUrl": "https://react.dev/reference",
            "rootUrl": "https://react.dev"
          },
          {
            "title": "FastAPI",
            "startUrl": "https://fastapi.tiangolo.com/",
            "rootUrl": "https://fastapi.tiangolo.com"
          },
          {
            "title": "Project Wiki",
            "startUrl": "https://wiki.internal.company.com/project",
            "rootUrl": "https://wiki.internal.company.com"
          }
        ]
      }
    }
  ]
}
```

### Codebase Indexing

```json
{
  "embeddingsProvider": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "contextProviders": [
    {
      "name": "codebase",
      "params": {
        "nRetrieve": 50,
        "nFinal": 10,
        "useReranking": true
      }
    }
  ]
}
```

Usage in chat:

```plaintext
@codebase How is authentication implemented in this project?
```

### Database Context Provider

```json
{
  "contextProviders": [
    {
      "name": "database",
      "params": {
        "connections": [
          {
            "name": "dev-db",
            "connectionString": "postgresql://user:pass@localhost/dev"
          }
        ]
      }
    }
  ]
}
```

### URL Context Provider

```json
{
  "contextProviders": [
    {
      "name": "url",
      "params": {}
    }
  ]
}
```

Usage:

```plaintext
@url https://api.example.com/openapi.json
Generate a TypeScript client from this OpenAPI spec
```

## Advanced Configuration

### Per-Workspace Config

Create `.continue/config.json` in workspace root:

```json
{
  "models": [
    {
      "title": "Project Model",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b"
    }
  ],
  "customCommands": [
    {
      "name": "django",
      "description": "Django patterns",
      "prompt": "Follow Django best practices. Use class-based views, proper model design, and Django REST framework patterns."
    }
  ]
}
```

### System Messages

```json
{
  "models": [
    {
      "title": "Senior Engineer",
      "provider": "ollama",
      "model": "qwen2.5-coder:32b",
      "systemMessage": "You are a senior software engineer with expertise in Python, TypeScript, and cloud architecture. You write clean, maintainable code with comprehensive error handling. You always consider security implications and performance optimization."
    }
  ]
}
```

### Proxy Configuration

```json
{
  "requestOptions": {
    "proxy": "http://proxy.company.com:8080",
    "timeout": 30000,
    "verifySsl": true
  }
}
```

## Troubleshooting

### Autocomplete Not Working

```bash
# Verify Ollama is serving
curl http://localhost:11434/api/tags

# Check model is loaded
ollama ps

# Test generation
curl http://localhost:11434/api/generate -d '{
  "model": "deepseek-coder-v2:16b",
  "prompt": "def hello():"
}'
```

### High Latency

- Use quantized models (q4_K_M)
- Reduce `contextLength`
- Lower `maxTokens` in completionOptions
- Use faster model for autocomplete

### Embeddings Not Working

```bash
# Pull embedding model
ollama pull nomic-embed-text

# Test embeddings
curl http://localhost:11434/api/embeddings -d '{
  "model": "nomic-embed-text",
  "prompt": "test text"
}'
```

### Config Not Loading

```bash
# Check config location
ls -la ~/.continue/

# Validate JSON
cat ~/.continue/config.json | python -m json.tool
```

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Ollama](../inference-engines/ollama.md) - Local model serving
- [Cline](cline.md) - Alternative extension
- [Choosing Models](../models/choosing-models.md) - Model selection
