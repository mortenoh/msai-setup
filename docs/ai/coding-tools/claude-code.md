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

## MCP (Model Context Protocol) Servers

Claude Code supports MCP servers for extending functionality with external tools and data sources.

### Configure MCP Servers

Create or edit `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_xxxxx"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://user:pass@localhost/db"]
    }
  }
}
```

### Available MCP Servers

| Server | Purpose | Package |
|--------|---------|---------|
| Filesystem | File access | `@modelcontextprotocol/server-filesystem` |
| GitHub | Repository access | `@modelcontextprotocol/server-github` |
| PostgreSQL | Database queries | `@modelcontextprotocol/server-postgres` |
| SQLite | Local databases | `@modelcontextprotocol/server-sqlite` |
| Fetch | HTTP requests | `@modelcontextprotocol/server-fetch` |

### Custom MCP Server

Build your own MCP server:

```typescript
// mcp-server/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-mcp-server", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler("tools/list", async () => ({
  tools: [{
    name: "my_tool",
    description: "Does something useful",
    inputSchema: {
      type: "object",
      properties: { query: { type: "string" } }
    }
  }]
}));

const transport = new StdioServerTransport();
await server.connect(transport);
```

## Custom Hooks

Hooks run shell commands at specific points during Claude Code execution.

### Hook Configuration

Create `~/.claude/hooks.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["echo 'Running command...' >> /tmp/claude-log.txt"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": ["prettier --write \"$CLAUDE_FILE_PATH\""]
      }
    ],
    "Notification": [
      {
        "matcher": "*",
        "hooks": ["terminal-notifier -message \"$CLAUDE_NOTIFICATION\""]
      }
    ]
  }
}
```

### Available Hook Points

| Hook | Trigger | Environment Variables |
|------|---------|----------------------|
| `PreToolUse` | Before tool execution | `CLAUDE_TOOL_NAME`, `CLAUDE_TOOL_INPUT` |
| `PostToolUse` | After tool execution | `CLAUDE_TOOL_NAME`, `CLAUDE_TOOL_OUTPUT` |
| `Notification` | On notifications | `CLAUDE_NOTIFICATION` |
| `Stop` | Session ends | `CLAUDE_SESSION_ID` |

### Auto-Format Hook Example

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write",
        "hooks": [
          "case \"$CLAUDE_FILE_PATH\" in *.py) black \"$CLAUDE_FILE_PATH\" ;; *.js|*.ts) prettier --write \"$CLAUDE_FILE_PATH\" ;; esac"
        ]
      }
    ]
  }
}
```

## Project-Specific Configuration (CLAUDE.md)

Create `CLAUDE.md` in your project root to provide context and instructions.

### Basic CLAUDE.md

```markdown
# Claude Code Instructions

## Project Overview
This is a Python FastAPI application with PostgreSQL backend.

## Code Style
- Use Black for formatting
- Follow PEP 8 conventions
- Type hints required for all functions

## Testing
- Run tests with: pytest tests/
- Coverage required: 80%+

## File Structure
- src/api/ - API endpoints
- src/models/ - SQLAlchemy models
- src/services/ - Business logic
```

### Advanced CLAUDE.md

```markdown
# Claude Code Instructions

## Git Commits
- Use conventional commits format (feat:, fix:, docs:, chore:)
- No co-authored-by lines
- Keep messages concise

## Security
- Never commit secrets or API keys
- Use environment variables for configuration
- Sanitize user input

## Database
- Migrations in alembic/versions/
- Run: alembic upgrade head
- Never modify production data directly

## Dependencies
- Package manager: uv
- Add deps: uv add <package>
- Lock file must be committed

## Patterns
- Repository pattern for data access
- Dependency injection via FastAPI
- Pydantic for validation
```

### Per-Directory Instructions

Create `.claude/instructions.md` for directory-specific context:

```markdown
# API Endpoints

All endpoints in this directory follow REST conventions:
- GET /items - List all
- GET /items/{id} - Get one
- POST /items - Create
- PUT /items/{id} - Update
- DELETE /items/{id} - Delete

Error responses use RFC 7807 Problem Details format.
```

## Local Workflow Patterns

### Development Workflow

```bash
# Start new feature
claude "Create a new branch for user authentication feature"

# Implement with tests
claude "Implement JWT authentication with tests. Follow the patterns in src/auth/"

# Review before commit
claude "Review my changes and suggest improvements"

# Commit with conventional format
claude "Commit these changes"
```

### Code Review Workflow

```bash
# Review PR
claude "Review PR #42 for security issues and code quality"

# Get specific feedback
claude "Check the database queries in this PR for N+1 problems"
```

### Debugging Workflow

```bash
# Analyze error
claude "This test is failing with 'KeyError: user_id'. Help me debug"

# Trace issue
claude "Follow the data flow from the API endpoint to the database for the create_user function"
```

## Integration with Ollama (Fallback)

While Claude Code is designed for the Anthropic API, you can set up Ollama as a fallback for when the API is unavailable.

### Ollama Proxy Setup

Use an API translation proxy like LiteLLM:

```bash
# Install LiteLLM
pip install litellm

# Start proxy
litellm --model ollama/llama3.3 --port 4000
```

```bash
# Set environment
export ANTHROPIC_API_BASE=http://localhost:4000/v1
```

### When to Use Local Fallback

| Scenario | Recommendation |
|----------|----------------|
| API unavailable | Use local fallback |
| Rate limited | Use local for simple tasks |
| Offline work | Use local models |
| Complex refactoring | Use Anthropic API |
| Security-sensitive | Use local models |

### Alternative: Aider for Local

For native local model support, use [Aider](aider.md) alongside Claude Code:

```bash
# Claude Code for complex tasks
claude "Architect the new microservice structure"

# Aider for local model tasks
aider --model ollama/deepseek-coder-v2:16b "Implement the data models"
```

## Environment Variables Reference

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | API key for authentication | Required |
| `ANTHROPIC_API_BASE` | API base URL | `https://api.anthropic.com` |
| `CLAUDE_CONFIG_DIR` | Config directory | `~/.claude` |
| `CLAUDE_MODEL` | Default model | `claude-sonnet-4-20250514` |
| `CLAUDE_MAX_TOKENS` | Max response tokens | `4096` |

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Aider](aider.md) - Alternative with local model support
- [API Serving](../api-serving/index.md) - Local API setup
