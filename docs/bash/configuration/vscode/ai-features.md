# AI Features

GitHub Copilot and AI assistants in VS Code.

## GitHub Copilot

### Overview

GitHub Copilot provides AI-powered code completions:

- Inline suggestions
- Multi-line completions
- Comment-to-code generation
- Code explanations

### Installation

1. Install extension: `GitHub.copilot`
2. Sign in with GitHub
3. Copilot subscription required

### Configuration

```json
{
  "github.copilot.enable": {
    "*": true,
    "yaml": true,
    "markdown": true,
    "plaintext": false
  },
  "github.copilot.editor.enableAutoCompletions": true
}
```

### Using Copilot

**Inline Suggestions**

- Start typing, suggestions appear as gray text
- ++tab++ to accept
- ++esc++ to dismiss
- ++alt+bracket-right++ for next suggestion
- ++alt+bracket-left++ for previous suggestion

**Multi-line Suggestions**

Copilot suggests complete functions, classes, and code blocks.

**Comment-Driven**

Write a comment describing what you want:

```python
# Function to calculate fibonacci sequence up to n
```

Copilot generates the implementation.

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| ++tab++ | Accept suggestion |
| ++esc++ | Dismiss suggestion |
| ++alt+bracket-right++ | Next suggestion |
| ++alt+bracket-left++ | Previous suggestion |
| ++alt+backslash++ | Trigger suggestion |
| ++ctrl+enter++ | Open Copilot panel |

### Disable for Specific Files

```json
{
  "github.copilot.enable": {
    "*.env": false,
    "*.pem": false,
    "*.key": false
  }
}
```

## GitHub Copilot Chat

### Installation

Install extension: `GitHub.copilot-chat`

### Features

- Ask coding questions
- Explain code
- Generate tests
- Fix errors
- Refactor code

### Opening Chat

- ++cmd+shift+i++ or
- Click Copilot icon in Activity Bar

### Chat Commands

| Command | Action |
|---------|--------|
| `/explain` | Explain selected code |
| `/fix` | Fix problems in code |
| `/tests` | Generate tests |
| `/doc` | Generate documentation |
| `/clear` | Clear chat history |
| `@workspace` | Ask about workspace |
| `@vscode` | Ask about VS Code |
| `@terminal` | Ask about terminal |

### Inline Chat

1. Select code
2. ++cmd+i++ to open inline chat
3. Type instruction
4. Review and accept changes

### Examples

```
Explain this function

@workspace How do I run tests?

/fix this code has a bug

/tests write tests for this class
```

### Configuration

```json
{
  "github.copilot.chat.localeOverride": "en"
}
```

## Alternative AI Extensions

### Continue

**Continue** (`continue.continue`)

Open-source AI assistant:

- Works with any LLM (Claude, GPT, Ollama)
- Customizable prompts
- Context-aware completions

Configuration (`~/.continue/config.json`):

```json
{
  "models": [
    {
      "title": "Claude",
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "apiKey": "YOUR_API_KEY"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Ollama",
    "provider": "ollama",
    "model": "codellama"
  }
}
```

### Codeium

**Codeium** (`codeium.codeium`)

Free AI code completion:

- No subscription required
- Multi-language support
- Chat interface

### Tabnine

**Tabnine** (`tabnine.tabnine-vscode`)

AI assistant with local model option:

- Privacy-focused
- Team training available

## Claude Integration (via Continue)

### Setup

1. Install Continue extension
2. Configure with Anthropic API:

```json
{
  "models": [
    {
      "title": "Claude Sonnet",
      "provider": "anthropic",
      "model": "claude-sonnet-4-20250514",
      "apiKey": "${ANTHROPIC_API_KEY}"
    }
  ]
}
```

### Environment Variable

```bash
export ANTHROPIC_API_KEY="your-api-key"
```

### Using Claude

- ++cmd+l++ to open Continue chat
- Select code and ask questions
- Use `/edit` to modify code

## Local AI with Ollama

### Setup

1. Install Ollama: `brew install ollama`
2. Pull model: `ollama pull codellama`
3. Configure Continue:

```json
{
  "models": [
    {
      "title": "CodeLlama",
      "provider": "ollama",
      "model": "codellama:13b"
    }
  ],
  "tabAutocompleteModel": {
    "title": "Local Complete",
    "provider": "ollama",
    "model": "codellama:7b"
  }
}
```

## Best Practices

### Security

```json
{
  "github.copilot.enable": {
    "*.env*": false,
    "*.pem": false,
    "*.key": false,
    "**/.ssh/*": false
  }
}
```

### Quality Suggestions

1. Write clear comments
2. Use descriptive variable names
3. Follow consistent patterns
4. Review all suggestions

### When to Use AI

- Boilerplate code
- Standard implementations
- Code explanations
- Test generation
- Documentation

### When Not to Use AI

- Security-critical code (review carefully)
- Business logic (validate thoroughly)
- Sensitive data handling

## Troubleshooting

### Copilot Not Working

1. Check subscription status
2. Sign out and sign in again
3. Check extension is enabled
4. Restart VS Code

### Slow Suggestions

1. Check network connection
2. Reduce context size
3. Disable for large files

### No Suggestions Appearing

1. Check file type is enabled
2. Try ++alt+backslash++ to trigger manually
3. Check Copilot status in status bar

## Keyboard Reference

| Key | Action |
|-----|--------|
| ++tab++ | Accept inline suggestion |
| ++esc++ | Dismiss suggestion |
| ++alt+bracket-right++ | Next suggestion |
| ++alt+bracket-left++ | Previous suggestion |
| ++ctrl+enter++ | Open suggestions panel |
| ++cmd+shift+i++ | Open Copilot Chat |
| ++cmd+i++ | Inline chat (with selection) |
