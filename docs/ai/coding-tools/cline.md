# Cline

VS Code extension for AI-powered coding with Plan/Act workflow and local model support.

## Overview

Cline provides:

- **VS Code integration** - Native editor experience
- **Plan/Act modes** - Structured development workflow
- **Local models** - Ollama, LM Studio, and OpenAI-compatible
- **MCP support** - Model Context Protocol for extensions
- **File operations** - Read, write, create files

## Installation

### VS Code Marketplace

1. Open VS Code
2. Go to Extensions (`Ctrl+Shift+X`)
3. Search "Cline"
4. Click Install

### Via CLI

```bash
code --install-extension saoudrizwan.claude-dev
```

## Configuration

### Open Settings

1. Click Cline icon in sidebar
2. Click gear icon (Settings)

### Configure Local Provider

#### Ollama

1. API Provider: **Ollama**
2. Base URL: `http://localhost:11434`
3. Select model from dropdown

#### LM Studio

1. API Provider: **LM Studio**
2. Base URL: `http://localhost:1234`
3. Model: Auto-detected

#### OpenAI-Compatible

1. API Provider: **OpenAI Compatible**
2. Base URL: `http://localhost:8080/v1`
3. API Key: `not-needed`
4. Model: Enter model name

### Settings JSON

In VS Code settings (`settings.json`):

```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaBaseUrl": "http://localhost:11434",
  "cline.ollamaModelId": "deepseek-coder-v2:16b",
  "cline.customInstructions": "Focus on clean, maintainable code. Use TypeScript when possible."
}
```

## Basic Usage

### Start Session

1. Open Cline panel (sidebar icon)
2. Type your request
3. Review and approve changes

### Example Requests

```
Add input validation to the login form in src/components/Login.tsx

Create a unit test for the UserService class

Refactor this function to use async/await instead of callbacks
```

## Plan/Act Workflow

### Plan Mode

Cline first creates a plan:

```
User: Add authentication to the API

Cline: I'll create a plan for adding authentication:
1. Create auth middleware
2. Add JWT token generation
3. Protect API routes
4. Add login/register endpoints

Shall I proceed with this plan?
```

### Act Mode

After approval, Cline executes:

```
Cline: Creating auth middleware...
[Shows diff for src/middleware/auth.ts]

Approve this change? [Yes/No]
```

### Control Flow

| Action | Behavior |
|--------|----------|
| Approve | Apply change, continue |
| Reject | Skip change, continue |
| Edit | Modify before applying |
| Stop | End session |

## File Operations

### Reading Files

Cline reads files automatically when needed:

```
User: Explain what UserController does

Cline: Let me read src/controllers/UserController.ts...
```

### Writing Files

```
User: Add error handling to the database connection

Cline: I'll modify src/db/connection.ts:
[Shows diff with changes]
```

### Creating Files

```
User: Create a new test file for the auth service

Cline: Creating tests/auth.test.ts:
[Shows new file content]
```

## Model Recommendations

### For Cline

| Model | Context | Best For |
|-------|---------|----------|
| DeepSeek Coder V2 16B | 128K | General coding |
| Qwen 2.5 Coder 32B | 128K | Complex refactoring |
| Llama 3.3 70B | 128K | Planning, reasoning |
| Mistral 7B | 32K | Quick edits |

### Configuration

```json
{
  "cline.ollamaModelId": "deepseek-coder-v2:16b"
}
```

## Custom Instructions

### System Prompt

Add custom instructions in settings:

```json
{
  "cline.customInstructions": "You are a senior TypeScript developer. Follow these principles:\n- Use functional programming patterns\n- Write comprehensive error handling\n- Include JSDoc comments\n- Follow project's ESLint rules"
}
```

### Per-Project Instructions

Create `.clinerules` in project root:

```
This is a React 18 project using TypeScript.
Use Tailwind CSS for styling.
Follow the existing component structure in src/components.
Write tests using React Testing Library.
```

## MCP (Model Context Protocol)

### What is MCP?

MCP extends Cline's capabilities with external tools and resources.

### Available Integrations

- File system access
- Git operations
- Database connections
- API integrations

### Configure MCP

In Cline settings, enable MCP servers:

```json
{
  "cline.mcpServers": {
    "filesystem": {
      "enabled": true
    },
    "git": {
      "enabled": true
    }
  }
}
```

## Advanced Features

### Terminal Commands

Cline can run terminal commands:

```
User: Run the tests and fix any failures

Cline: Running npm test...
[Shows test output]
3 tests failed. Let me fix them...
```

### Multi-file Operations

```
User: Rename the User class to Account across all files

Cline: I'll update the following files:
- src/models/User.ts → Account.ts
- src/controllers/UserController.ts
- src/services/UserService.ts
- tests/User.test.ts
```

### Code Review

```
User: Review this PR for potential issues

Cline: I'll analyze the changes...
[Provides detailed review]
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+P` → "Cline" | Open Cline commands |
| `Ctrl+L` | Focus Cline input |
| `Escape` | Cancel current operation |

## Troubleshooting

### Ollama Not Connecting

```bash
# Verify Ollama is running
curl http://localhost:11434/

# Check firewall
# Ollama should listen on all interfaces if needed
OLLAMA_HOST=0.0.0.0 ollama serve
```

### Model Not Loading

- Ensure model is pulled: `ollama pull deepseek-coder-v2:16b`
- Check model name matches exactly
- Verify sufficient memory

### Slow Responses

- Use smaller model for quick tasks
- Reduce file context
- Check GPU utilization

### Changes Not Applying

- Check file permissions
- Verify VS Code has write access
- Look for conflicting extensions

## Comparison with Alternatives

| Feature | Cline | Continue | Aider |
|---------|-------|----------|-------|
| Interface | VS Code | VS Code/JetBrains | CLI |
| Local models | Yes | Yes | Yes |
| Plan/Act | Yes | No | No |
| MCP support | Yes | No | No |
| File operations | Yes | Limited | Yes |
| Git integration | Basic | Basic | Advanced |

## Best Practices

### Effective Prompts

```
# Be specific
"Add null checking to the getUserById function in UserService.ts"

# Provide context
"This is a TypeScript Express app. Add rate limiting middleware"

# Reference existing code
"Use the same error handling pattern as in AuthController"
```

### Review Changes

- Always review diffs before approving
- Test changes before committing
- Use Plan mode for complex tasks

### Context Management

- Keep focused file context
- Use .clinerules for project conventions
- Reference documentation when needed

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Ollama](../inference-engines/ollama.md) - Local model serving
- [Continue.dev](continue-dev.md) - Alternative extension
- [Choosing Models](../models/choosing-models.md) - Model selection
