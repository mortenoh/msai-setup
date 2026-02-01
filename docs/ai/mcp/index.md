# Model Context Protocol (MCP)

MCP is an open standard for connecting AI assistants to external data sources and tools.

## What is MCP?

MCP provides a standardized way for LLMs to:

- **Access data** from files, databases, APIs
- **Use tools** to perform actions
- **Maintain context** across interactions

```
┌─────────────────────────────────────────────────────────────┐
│                       MCP Architecture                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌──────────────┐                    ┌──────────────┐     │
│   │   AI Host    │                    │  MCP Server  │     │
│   │ (Claude, etc)│◄──── Protocol ────►│  (Your App)  │     │
│   └──────────────┘                    └──────────────┘     │
│          │                                   │              │
│          v                                   v              │
│   ┌──────────────┐                    ┌──────────────┐     │
│   │    Tools     │                    │  Resources   │     │
│   │  - search    │                    │  - files     │     │
│   │  - execute   │                    │  - database  │     │
│   │  - query     │                    │  - API data  │     │
│   └──────────────┘                    └──────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## In This Section

| Document | Description |
|----------|-------------|
| [Servers](servers.md) | Building MCP servers |
| [Clients](clients.md) | Connecting to MCP servers |
| [Examples](examples.md) | Practical MCP implementations |

## Quick Start

### Install MCP SDK

```bash
# Python
pip install mcp

# Node.js
npm install @modelcontextprotocol/sdk
```

### Simple MCP Server (Python)

```python
#!/usr/bin/env python3
from mcp.server import Server
from mcp.types import Tool, TextContent
import asyncio

server = Server("example-server")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="greet",
            description="Generate a greeting",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Name to greet"}
                },
                "required": ["name"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "greet":
        return [TextContent(
            type="text",
            text=f"Hello, {arguments['name']}!"
        )]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

### Use with Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "example": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## MCP Features

### Tools

Functions the AI can call:

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search",
            description="Search for information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search":
        results = perform_search(arguments["query"])
        return [TextContent(type="text", text=results)]
```

### Resources

Data the AI can read:

```python
@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="file:///data/config.json",
            name="Configuration",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "file:///data/config.json":
        with open("/data/config.json") as f:
            return f.read()
```

### Prompts

Reusable prompt templates:

```python
@server.list_prompts()
async def list_prompts():
    return [
        Prompt(
            name="analyze",
            description="Analyze data",
            arguments=[
                PromptArgument(name="data", description="Data to analyze")
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "analyze":
        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Analyze this data: {arguments['data']}"
                    )
                )
            ]
        )
```

## Available MCP Servers

### Official Servers

| Server | Description |
|--------|-------------|
| filesystem | Read/write local files |
| git | Git repository operations |
| github | GitHub API access |
| postgres | PostgreSQL database |
| sqlite | SQLite database |
| slack | Slack workspace |
| google-drive | Google Drive access |

### Community Servers

| Server | Description |
|--------|-------------|
| browserbase | Web browser automation |
| puppeteer | Headless browser control |
| docker | Container management |
| kubernetes | K8s cluster operations |

### Install Official Servers

```bash
# Using uvx (recommended)
uvx mcp-server-filesystem

# Using npx
npx -y @modelcontextprotocol/server-github
```

## Configuration

### Claude Desktop

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "uvx",
      "args": ["mcp-server-filesystem", "/path/to/allowed/directory"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "ghp_xxxx"
      }
    }
  }
}
```

### Claude Code

```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "myserver": {
      "command": "python",
      "args": ["/path/to/server.py"]
    }
  }
}
```

## Transport Options

### Stdio (Default)

Server communicates via stdin/stdout:

```python
async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)
```

### HTTP/SSE

Server over HTTP with Server-Sent Events:

```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.routing import Route

sse = SseServerTransport("/messages")

async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await server.run(streams[0], streams[1])

app = Starlette(routes=[
    Route("/sse", endpoint=handle_sse),
    sse.handle_post_message,
])
```

## Best Practices

### Tool Design

1. **Clear descriptions** - Help the AI understand when to use tools
2. **Validate inputs** - Check arguments before processing
3. **Handle errors gracefully** - Return informative error messages
4. **Limit scope** - Each tool should do one thing well

### Security

1. **Validate all inputs** - Never trust AI-provided arguments
2. **Limit file access** - Restrict to specific directories
3. **Use environment variables** - Don't hardcode credentials
4. **Log operations** - Track what the AI does

### Performance

1. **Async operations** - Use async/await for I/O
2. **Cache when possible** - Avoid repeated expensive operations
3. **Timeout long operations** - Don't let calls hang indefinitely

## See Also

- [Building Servers](servers.md)
- [Client Integration](clients.md)
- [Examples](examples.md)
- [Agent Frameworks](../agent-frameworks/index.md)
