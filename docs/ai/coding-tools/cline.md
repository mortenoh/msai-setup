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

## MCP Server Configuration

Cline supports MCP (Model Context Protocol) for extending capabilities with external tools.

### MCP Settings

In VS Code settings (`settings.json`):

```json
{
  "cline.mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user/projects"],
      "disabled": false
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "${env:GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "postgresql://user:pass@localhost/db"
      }
    }
  }
}
```

### Available MCP Servers

| Server | Purpose | Installation |
|--------|---------|--------------|
| Filesystem | File operations | `@modelcontextprotocol/server-filesystem` |
| GitHub | Repository access | `@modelcontextprotocol/server-github` |
| PostgreSQL | Database queries | `@modelcontextprotocol/server-postgres` |
| SQLite | Local databases | `@modelcontextprotocol/server-sqlite` |
| Puppeteer | Browser automation | `@modelcontextprotocol/server-puppeteer` |
| Brave Search | Web search | `@modelcontextprotocol/server-brave-search` |

### Custom MCP Server

Create custom tools for Cline:

```typescript
// my-mcp-server/src/index.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new Server(
  { name: "my-tools", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler("tools/list", async () => ({
  tools: [{
    name: "run_tests",
    description: "Run project tests",
    inputSchema: {
      type: "object",
      properties: {
        pattern: { type: "string", description: "Test file pattern" }
      }
    }
  }]
}));

server.setRequestHandler("tools/call", async (request) => {
  if (request.params.name === "run_tests") {
    const result = await runTests(request.params.arguments.pattern);
    return { content: [{ type: "text", text: result }] };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
```

Add to settings:

```json
{
  "cline.mcpServers": {
    "my-tools": {
      "command": "node",
      "args": ["/path/to/my-mcp-server/dist/index.js"]
    }
  }
}
```

## Local Model Setup

### Ollama Configuration

```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaBaseUrl": "http://localhost:11434",
  "cline.ollamaModelId": "qwen2.5-coder:32b"
}
```

### Recommended Models for Cline

| Model | VRAM | Best For |
|-------|------|----------|
| Qwen 2.5 Coder 32B | 24GB | Complex refactoring, planning |
| DeepSeek Coder V2 16B | 12GB | General coding tasks |
| Codestral 22B | 16GB | Fast code completion |
| Llama 3.3 70B | 48GB | Architecture decisions |

### LM Studio Configuration

```json
{
  "cline.apiProvider": "lmstudio",
  "cline.lmStudioBaseUrl": "http://localhost:1234",
  "cline.lmStudioModelId": "loaded-model"
}
```

### OpenAI-Compatible Servers

For llama.cpp server or other OpenAI-compatible endpoints:

```json
{
  "cline.apiProvider": "openai-compatible",
  "cline.openAiCompatibleBaseUrl": "http://localhost:8080/v1",
  "cline.openAiCompatibleApiKey": "not-needed",
  "cline.openAiCompatibleModelId": "llama3.3"
}
```

### Remote Ollama (Tailscale)

```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaBaseUrl": "http://server.tailnet.ts.net:11434",
  "cline.ollamaModelId": "qwen2.5-coder:32b"
}
```

## VS Code Integration

### Workspace Settings

Create `.vscode/settings.json` for project-specific config:

```json
{
  "cline.apiProvider": "ollama",
  "cline.ollamaModelId": "deepseek-coder-v2:16b",
  "cline.customInstructions": "This is a TypeScript React project. Use functional components and hooks."
}
```

### Task Integration

Create `.vscode/tasks.json` to work with Cline:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Run Tests",
      "type": "shell",
      "command": "npm test",
      "problemMatcher": "$tsc"
    },
    {
      "label": "Lint",
      "type": "shell",
      "command": "npm run lint",
      "problemMatcher": "$eslint-stylish"
    }
  ]
}
```

Cline can run these tasks during development.

### Keybinding Customization

Add to `keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+c",
    "command": "cline.openInNewTab"
  },
  {
    "key": "ctrl+shift+a",
    "command": "cline.acceptAllChanges"
  }
]
```

## Custom Instructions Patterns

### Project-Level Instructions (.clinerules)

Create `.clinerules` in project root:

```markdown
# Project: E-commerce API

## Stack
- Node.js 20 with TypeScript
- Express.js framework
- PostgreSQL with Prisma ORM
- Jest for testing

## Conventions
- Use async/await, never callbacks
- All functions must have TypeScript types
- Error handling with custom AppError class
- Logging with winston logger

## File Structure
- src/controllers/ - Request handlers
- src/services/ - Business logic
- src/repositories/ - Data access
- src/middleware/ - Express middleware
- src/utils/ - Helper functions

## Testing
- Unit tests in __tests__ directories
- Integration tests in tests/integration/
- Minimum 80% coverage

## Security
- Never expose internal errors to clients
- Validate all input with zod schemas
- Use parameterized queries only
```

### Task-Specific Instructions

In the Cline panel, provide context:

```plaintext
Context: This is a migration from Express to Fastify.

Rules:
1. Keep the same API structure
2. Update middleware to Fastify hooks
3. Replace Express types with Fastify types
4. Maintain all existing tests
```

### Code Style Instructions

```json
{
  "cline.customInstructions": "Follow these rules:\n1. Use 2-space indentation\n2. Prefer const over let\n3. Use arrow functions for callbacks\n4. Add JSDoc for public APIs\n5. Keep functions under 30 lines"
}
```

## Advanced Workflows

### Plan Mode Best Practices

1. Start with high-level request
2. Review Cline's plan
3. Ask clarifying questions
4. Approve or refine
5. Let Act mode execute

Example conversation:

```plaintext
You: Add user authentication to this Express API

Cline: I'll create a plan for authentication:
1. Install dependencies (jsonwebtoken, bcrypt)
2. Create User model with password hashing
3. Add auth middleware for JWT verification
4. Create /auth/register endpoint
5. Create /auth/login endpoint
6. Protect existing routes

Should I proceed with this plan?

You: Also add refresh token support

Cline: Updated plan:
1-5. [same as above]
6. Add refresh token model
7. Create /auth/refresh endpoint
8. Update login to return both tokens
9. Protect existing routes

Shall I proceed?
```

### Iterative Development

```plaintext
Step 1: "Create the data model for users"
Step 2: "Add the user service with CRUD operations"
Step 3: "Create API endpoints for user management"
Step 4: "Add input validation with zod"
Step 5: "Write unit tests for the user service"
```

### Debugging with Cline

```plaintext
"This test is failing:

[paste error]

The test file is tests/user.test.ts and it tests src/services/user.ts.
Help me understand why it's failing and fix it."
```

## Troubleshooting

### Extension Not Loading

```bash
# Check extension is installed
code --list-extensions | grep -i cline

# Reinstall if needed
code --uninstall-extension saoudrizwan.claude-dev
code --install-extension saoudrizwan.claude-dev
```

### Model Connection Issues

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Check model is available
ollama list
```

### High Memory Usage

- Use smaller models for simple tasks
- Reduce context window in model settings
- Close unused editor tabs

### Changes Not Applying

- Check file permissions
- Ensure no other process has file locked
- Try reloading VS Code window

## See Also

- [AI Coding Tools Index](index.md) - Tool comparison
- [Ollama](../inference-engines/ollama.md) - Local model serving
- [Continue.dev](continue-dev.md) - Alternative extension
- [Choosing Models](../models/choosing-models.md) - Model selection
