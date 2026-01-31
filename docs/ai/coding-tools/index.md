# AI Coding Tools

Configure AI-powered coding assistants to use local LLM backends.

## Overview

AI coding tools can connect to:

- **Local Ollama** - Self-hosted, private
- **Local llama.cpp** - Custom configurations
- **OpenAI-compatible APIs** - Any compatible endpoint
- **Cloud APIs** - Anthropic, OpenAI (fallback)

## Tool Comparison

| Tool | Interface | Local Model Support | Best For |
|------|-----------|---------------------|----------|
| [Claude Code](claude-code.md) | CLI | Via API proxy | Anthropic CLI users |
| [Aider](aider.md) | CLI | Native Ollama | Git-integrated coding |
| [Cline](cline.md) | VS Code | Native | VS Code users |
| [Continue.dev](continue-dev.md) | Multi-editor | Native | IDE integration |

## Feature Matrix

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Coding Tools                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  CLI Tools:                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │    Claude Code      │    │       Aider         │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ ✓ Official Claude   │    │ ✓ Git-aware         │             │
│  │ ✓ Multi-file edits  │    │ ✓ Local models      │             │
│  │ ✓ Code execution    │    │ ✓ Auto-commits      │             │
│  │ ✓ File operations   │    │ ✓ Multiple LLMs     │             │
│  └─────────────────────┘    └─────────────────────┘             │
│                                                                  │
│  IDE Extensions:                                                 │
│  ┌─────────────────────┐    ┌─────────────────────┐             │
│  │       Cline         │    │    Continue.dev     │             │
│  ├─────────────────────┤    ├─────────────────────┤             │
│  │ ✓ VS Code           │    │ ✓ VS Code + JetBrains│            │
│  │ ✓ Plan/Act modes    │    │ ✓ Autocomplete      │             │
│  │ ✓ Local providers   │    │ ✓ Chat + Edit       │             │
│  │ ✓ MCP support       │    │ ✓ Local-first       │             │
│  └─────────────────────┘    └─────────────────────┘             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Recommended Setup

### Development Workflow

```
                    ┌─────────────────┐
                    │  Code Question  │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
     ┌──────────┐     ┌──────────┐     ┌──────────┐
     │ Continue │     │   Aider  │     │   Cline  │
     │ (IDE)    │     │  (CLI)   │     │ (VS Code)│
     └────┬─────┘     └────┬─────┘     └────┬─────┘
          │                │                │
          └────────────────┴────────────────┘
                           │
                    ┌──────┴──────┐
                    │   Ollama    │
                    │ (Local LLM) │
                    └─────────────┘
```

### Model Recommendations

| Task | Model | Notes |
|------|-------|-------|
| Code completion | DeepSeek Coder V2 16B | Fast, accurate |
| Code chat | Llama 3.3 70B | Good reasoning |
| Refactoring | Qwen 2.5 Coder 32B | Balanced |
| Quick answers | Mistral 7B | Very fast |

## Quick Configuration

### Environment Variables

```bash
# For OpenAI-compatible tools
export OPENAI_API_BASE=http://localhost:11434/v1
export OPENAI_API_KEY=not-needed

# For Ollama-native tools
export OLLAMA_HOST=http://localhost:11434
```

### Ollama Setup

Ensure Ollama is running with your preferred model:

```bash
# Start Ollama
ollama serve

# Pull coding model
ollama pull deepseek-coder-v2:16b

# Verify
curl http://localhost:11434/v1/models
```

## Topics

<div class="grid cards" markdown>

-   :material-console: **Claude Code**

    ---

    Anthropic's official CLI for Claude

    [:octicons-arrow-right-24: Claude Code guide](claude-code.md)

-   :material-git: **Aider**

    ---

    Git-smart AI pair programming in terminal

    [:octicons-arrow-right-24: Aider guide](aider.md)

-   :material-microsoft-visual-studio-code: **Cline**

    ---

    VS Code extension with Plan/Act modes

    [:octicons-arrow-right-24: Cline guide](cline.md)

-   :material-code-tags: **Continue.dev**

    ---

    Multi-editor extension with local-first config

    [:octicons-arrow-right-24: Continue guide](continue-dev.md)

</div>

## Model Configuration Examples

### For Aider

```bash
# Using Ollama
aider --model ollama/deepseek-coder-v2:16b

# Using OpenAI-compatible
aider --openai-api-base http://localhost:8080/v1 --model llama3.3
```

### For Continue.dev

```json
{
  "models": [
    {
      "title": "DeepSeek Coder",
      "provider": "ollama",
      "model": "deepseek-coder-v2:16b"
    }
  ]
}
```

### For Cline

Settings → Cline → API Provider → Ollama

## See Also

- [Inference Engines](../inference-engines/index.md) - Backend setup
- [Ollama](../inference-engines/ollama.md) - Local model serving
- [API Serving](../api-serving/index.md) - OpenAI-compatible APIs
- [Choosing Models](../models/choosing-models.md) - Model selection
