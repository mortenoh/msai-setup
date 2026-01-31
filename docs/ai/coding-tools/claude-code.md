# Claude Code

Anthropic's official command-line interface for Claude.

## Overview

Claude Code provides:

- **Terminal-based** - Work directly in your shell
- **Multi-file editing** - Modify multiple files in one session
- **Code execution** - Run commands and scripts
- **File operations** - Read, write, create files
- **Git integration** - Commit, branch, PR operations

## Installation

### Prerequisites

- Node.js 18+
- Anthropic API key

### Install

```bash
# Using npm
npm install -g @anthropic-ai/claude-code

# Using Homebrew (macOS)
brew install anthropic/tap/claude-code
```

### Verify Installation

```bash
claude --version
```

## API Key Setup

Claude Code uses the Anthropic API by default:

```bash
# Set API key
export ANTHROPIC_API_KEY=sk-ant-xxxxx

# Add to shell profile
echo 'export ANTHROPIC_API_KEY=sk-ant-xxxxx' >> ~/.bashrc
```

### Get API Key

1. Visit [console.anthropic.com](https://console.anthropic.com)
2. Create API key
3. Set environment variable

## Basic Usage

### Start Session

```bash
# Start in current directory
claude

# Start with a prompt
claude "Explain this codebase"

# Start in specific directory
claude --cwd /path/to/project
```

### Interactive Commands

Within a Claude Code session:

| Command | Action |
|---------|--------|
| `/help` | Show available commands |
| `/clear` | Clear conversation |
| `/compact` | Compact conversation history |
| `/exit` | Exit session |

### Common Tasks

```bash
# Code review
claude "Review the code in src/main.py for security issues"

# Refactoring
claude "Refactor this function to be more readable"

# Debugging
claude "Help me debug why this test is failing"

# Documentation
claude "Add docstrings to all functions in this file"
```

## Configuration

### Config File

Create `~/.config/claude-code/config.json`:

```json
{
  "model": "claude-sonnet-4-20250514",
  "maxTokens": 4096,
  "temperature": 0,
  "defaultPermissions": {
    "allowedCommands": ["npm", "git", "python"],
    "allowFileWrite": true,
    "allowFileRead": true
  }
}
```

### Model Selection

```bash
# Use specific model
claude --model claude-sonnet-4-20250514

# Available models
claude --list-models
```

### Available Models

| Model | Context | Best For |
|-------|---------|----------|
| claude-opus-4-20250514 | 200K | Complex reasoning |
| claude-sonnet-4-20250514 | 200K | Balanced (default) |
| claude-haiku-3-5-20241022 | 200K | Fast, simple tasks |

## Working with Code

### File Operations

```bash
# Read a file
"Show me the contents of src/main.py"

# Edit a file
"Add error handling to the parse_data function in utils.py"

# Create new files
"Create a new test file for the user module"
```

### Multi-file Editing

```bash
# Work across files
"Refactor the authentication logic:
 - Move auth functions to auth.py
 - Update imports in main.py
 - Add tests in test_auth.py"
```

### Running Commands

Claude Code can execute shell commands:

```bash
# Run tests
"Run the test suite and fix any failures"

# Install dependencies
"Add pytest to requirements.txt and install it"
```

## Git Integration

### Commits

```bash
# Create commit
"Commit these changes with an appropriate message"

# Review and commit
"Review the staged changes and create a commit"
```

### Branches

```bash
# Create feature branch
"Create a new branch for the login feature"

# Merge
"Merge the feature branch into main"
```

### Pull Requests

```bash
# Create PR
"Create a pull request with a description of changes"
```

## Using with Local Models

Claude Code is designed for the Anthropic API, but can be configured to use OpenAI-compatible endpoints:

### Via Environment Variables

```bash
# Point to local Ollama (experimental)
export ANTHROPIC_API_BASE=http://localhost:11434/v1

# This may require API translation layer
```

### Recommended Alternative

For local models, consider [Aider](aider.md) which has native Ollama support.

## Advanced Usage

### Session Persistence

```bash
# Resume previous session
claude --resume

# Name sessions
claude --session my-project
```

### Batch Operations

```bash
# Non-interactive mode
claude --no-interactive "Fix all linting errors in src/"
```

### Context Management

```bash
# Include specific files
claude --include "src/*.py" --include "tests/*.py"

# Exclude patterns
claude --exclude "node_modules" --exclude "*.log"
```

## Permissions

### Approval Prompts

Claude Code asks before:
- Writing files
- Running commands
- Deleting files

### Auto-approve

```bash
# Skip approval for safe operations
claude --yes-file-writes

# Skip all approvals (use carefully)
claude --yes-all
```

## Best Practices

### Effective Prompts

```bash
# Be specific
claude "Add input validation to the user registration endpoint in api/users.py"

# Provide context
claude "This is a Django app. Update the User model to include email verification"

# Break down complex tasks
claude "Let's implement OAuth. First, show me the current auth setup"
```

### Code Review

```bash
# Review before committing
claude "Review my staged changes for potential issues"

# Security review
claude "Check this code for security vulnerabilities"
```

## Troubleshooting

### API Key Issues

```bash
# Verify key is set
echo $ANTHROPIC_API_KEY

# Test API
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
  https://api.anthropic.com/v1/messages
```

### Rate Limits

- Monitor usage in Anthropic console
- Use smaller models for simple tasks
- Batch similar operations

### Context Overflow

```bash
# Compact conversation
/compact

# Start fresh
/clear
```

## Comparison with Alternatives

| Feature | Claude Code | Aider | Cline |
|---------|-------------|-------|-------|
| Interface | CLI | CLI | VS Code |
| Local models | Via proxy | Native | Native |
| Git integration | Yes | Yes | Limited |
| Multi-file | Yes | Yes | Yes |
| Code execution | Yes | Limited | Yes |

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Aider](aider.md) - Alternative with local model support
- [API Serving](../api-serving/index.md) - Local API setup
