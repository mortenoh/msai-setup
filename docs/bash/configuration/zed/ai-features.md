# AI Features

Configuring AI assistants and code completion in Zed.

## Overview

Zed provides three types of AI integration:

1. **Edit Predictions**: Inline code completions (Copilot, Supermaven)
2. **Agent**: AI chat assistant for code questions and generation
3. **Inline Assist**: AI-powered code transformations

## Edit Predictions (Copilot)

### Enable Copilot

```json
{
  "features": {
    "edit_prediction_provider": "copilot"
  }
}
```

### Providers

| Provider | Description |
|----------|-------------|
| `copilot` | GitHub Copilot |
| `supermaven` | Supermaven (fast completions) |
| `zed` | Zed's built-in completions |
| `none` | Disable predictions |

### Sign In to Copilot

1. Command Palette (++cmd+shift+p++)
2. Search "copilot: sign in"
3. Follow authentication flow

### Copilot Settings

```json
{
  "features": {
    "edit_prediction_provider": "copilot"
  },
  "copilot": {
    "disabled_globs": [
      ".env",
      "*.pem",
      "*.key"
    ]
  }
}
```

### Using Completions

- Completions appear as gray text
- Press ++tab++ to accept
- Press ++esc++ to dismiss
- Continue typing to ignore

## Agent (AI Assistant)

### Enable Agent

```json
{
  "agent": {
    "enabled": true,
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

### Available Providers

| Provider | Models |
|----------|--------|
| `anthropic` | claude-sonnet-4-20250514, claude-opus-4-20250514 |
| `openai` | gpt-4o, gpt-4-turbo, gpt-3.5-turbo |
| `copilot_chat` | gpt-4o (via Copilot subscription) |
| `ollama` | Local models |
| `google` | gemini-pro, gemini-ultra |

### Anthropic (Claude) Setup

1. Get API key from [Anthropic Console](https://console.anthropic.com/)
2. Configure in Zed settings or environment:

```json
{
  "agent": {
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    }
  }
}
```

Set API key:

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

Or via Zed: Command Palette > "assistant: configure api key"

### OpenAI Setup

```json
{
  "agent": {
    "default_model": {
      "provider": "openai",
      "model": "gpt-4o"
    }
  }
}
```

Set API key:

```bash
export OPENAI_API_KEY="your-api-key"
```

### Copilot Chat (No Extra Cost)

Use Copilot subscription for chat:

```json
{
  "agent": {
    "default_model": {
      "provider": "copilot_chat",
      "model": "gpt-4o"
    }
  }
}
```

Requires Copilot sign-in.

### Ollama (Local Models)

Run models locally with Ollama:

1. Install Ollama: `brew install ollama`
2. Start server: `ollama serve`
3. Pull model: `ollama pull llama3.2`
4. Configure:

```json
{
  "agent": {
    "default_model": {
      "provider": "ollama",
      "model": "llama3.2"
    }
  }
}
```

### Using the Agent

Open Agent panel:

- ++cmd+shift+a++ or
- Command Palette > "assistant: new conversation"

In the Agent:

- Type questions naturally
- Reference code with `@file.py`
- Use `/` commands for actions
- Click "Apply" to insert code suggestions

### Agent Slash Commands

| Command | Action |
|---------|--------|
| `/file` | Include file content |
| `/tab` | Include open tab content |
| `/selection` | Include selected text |
| `/diagnostics` | Include current diagnostics |
| `/terminal` | Include terminal output |
| `/fetch` | Fetch URL content |

## Inline Assist

Transform code with AI directly in the editor.

### Trigger Inline Assist

1. Select code
2. Press ++cmd+enter++ or ++ctrl+enter++
3. Type instruction
4. Press ++enter++ to apply

### Examples

- Select function > "Add error handling"
- Select code > "Convert to async/await"
- Select block > "Add TypeScript types"
- Cursor in function > "Write tests for this function"

### Inline Assist Settings

```json
{
  "inline_assist": {
    "enabled": true
  }
}
```

## Recommended Configuration

### For Claude Users

```json
{
  "features": {
    "edit_prediction_provider": "copilot"
  },
  "agent": {
    "enabled": true,
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    },
    "version": "2"
  }
}
```

### For Copilot-Only Users

```json
{
  "features": {
    "edit_prediction_provider": "copilot"
  },
  "agent": {
    "enabled": true,
    "default_model": {
      "provider": "copilot_chat",
      "model": "gpt-4o"
    }
  }
}
```

### For Local-Only (Ollama)

```json
{
  "features": {
    "edit_prediction_provider": "none"
  },
  "agent": {
    "enabled": true,
    "default_model": {
      "provider": "ollama",
      "model": "codellama:34b"
    }
  }
}
```

### Disable All AI

```json
{
  "features": {
    "edit_prediction_provider": "none"
  },
  "agent": {
    "enabled": false
  }
}
```

## Multiple Model Configuration

Configure multiple models for different tasks:

```json
{
  "agent": {
    "default_model": {
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514"
    },
    "models": {
      "anthropic": {
        "available_models": [
          {
            "name": "claude-sonnet-4-20250514",
            "max_tokens": 8192
          },
          {
            "name": "claude-opus-4-20250514",
            "max_tokens": 4096
          }
        ]
      }
    }
  }
}
```

Switch models in Agent panel using the model selector.

## Privacy Considerations

### Disable Telemetry

```json
{
  "telemetry": {
    "diagnostics": false,
    "metrics": false
  }
}
```

### Exclude Sensitive Files from Copilot

```json
{
  "copilot": {
    "disabled_globs": [
      ".env*",
      "*.pem",
      "*.key",
      "**/secrets/**",
      "**/credentials/**"
    ]
  }
}
```

## Troubleshooting

### Copilot Not Working

1. Check sign-in status: Command Palette > "copilot: status"
2. Re-authenticate: Command Palette > "copilot: sign out" then sign in
3. Check subscription is active

### Agent Not Responding

1. Verify API key is set
2. Check network connectivity
3. View logs: Command Palette > "zed: open log"

### Ollama Connection Failed

1. Ensure Ollama is running: `ollama serve`
2. Verify model is pulled: `ollama list`
3. Check default port (11434) is available

## Keybindings

| Key | Action |
|-----|--------|
| ++cmd+shift+a++ | Open Agent panel |
| ++cmd+enter++ | Inline assist (with selection) |
| ++tab++ | Accept completion |
| ++esc++ | Dismiss completion |
