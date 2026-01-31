# Building MCP Servers

Create custom MCP servers to extend AI capabilities.

## Server Structure

```python
from mcp.server import Server
from mcp.types import Tool, Resource, Prompt, TextContent
import asyncio

# Create server instance
server = Server("my-server")

# Define tools
@server.list_tools()
async def list_tools():
    return [...]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    ...

# Define resources
@server.list_resources()
async def list_resources():
    return [...]

@server.read_resource()
async def read_resource(uri: str):
    ...

# Run server
async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## Tools

### Basic Tool

```python
from mcp.types import Tool, TextContent

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="calculate",
            description="Perform mathematical calculations",
            inputSchema={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "calculate":
        try:
            result = eval(arguments["expression"])
            return [TextContent(type="text", text=str(result))]
        except Exception as e:
            return [TextContent(type="text", text=f"Error: {e}")]

    raise ValueError(f"Unknown tool: {name}")
```

### Tool with Complex Schema

```python
@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search_files",
            description="Search for files matching criteria",
            inputSchema={
                "type": "object",
                "properties": {
                    "directory": {
                        "type": "string",
                        "description": "Directory to search"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g., *.py)"
                    },
                    "recursive": {
                        "type": "boolean",
                        "description": "Search subdirectories",
                        "default": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum results to return",
                        "default": 100
                    }
                },
                "required": ["directory", "pattern"]
            }
        )
    ]
```

### Async Tool Operations

```python
import aiohttp
import asyncio

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "fetch_url":
        async with aiohttp.ClientSession() as session:
            async with session.get(arguments["url"]) as response:
                content = await response.text()
                return [TextContent(type="text", text=content[:10000])]

    if name == "parallel_fetch":
        urls = arguments["urls"]
        async with aiohttp.ClientSession() as session:
            tasks = [fetch_one(session, url) for url in urls]
            results = await asyncio.gather(*tasks)
            return [TextContent(type="text", text="\n\n".join(results))]
```

## Resources

### Static Resources

```python
from mcp.types import Resource

@server.list_resources()
async def list_resources():
    return [
        Resource(
            uri="config://app/settings",
            name="Application Settings",
            description="Current application configuration",
            mimeType="application/json"
        ),
        Resource(
            uri="file:///data/readme.md",
            name="README",
            description="Project documentation",
            mimeType="text/markdown"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri == "config://app/settings":
        return json.dumps({"debug": True, "version": "1.0"})

    if uri.startswith("file://"):
        path = uri.replace("file://", "")
        with open(path) as f:
            return f.read()

    raise ValueError(f"Unknown resource: {uri}")
```

### Dynamic Resources

```python
from pathlib import Path

@server.list_resources()
async def list_resources():
    """List all markdown files in docs directory."""
    resources = []
    docs_dir = Path("/data/docs")

    for md_file in docs_dir.glob("**/*.md"):
        resources.append(Resource(
            uri=f"file://{md_file}",
            name=md_file.stem,
            description=f"Documentation: {md_file.name}",
            mimeType="text/markdown"
        ))

    return resources
```

### Resource Templates

```python
from mcp.types import ResourceTemplate

@server.list_resource_templates()
async def list_resource_templates():
    return [
        ResourceTemplate(
            uriTemplate="db://users/{user_id}",
            name="User Profile",
            description="Get user data by ID",
            mimeType="application/json"
        )
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri.startswith("db://users/"):
        user_id = uri.split("/")[-1]
        user = await get_user(user_id)
        return json.dumps(user)
```

## Prompts

### Basic Prompt

```python
from mcp.types import Prompt, PromptArgument, PromptMessage, GetPromptResult

@server.list_prompts()
async def list_prompts():
    return [
        Prompt(
            name="summarize",
            description="Summarize a document",
            arguments=[
                PromptArgument(
                    name="content",
                    description="Content to summarize",
                    required=True
                ),
                PromptArgument(
                    name="style",
                    description="Summary style (brief, detailed)",
                    required=False
                )
            ]
        )
    ]

@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "summarize":
        style = arguments.get("style", "brief")
        content = arguments["content"]

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"Please provide a {style} summary of:\n\n{content}"
                    )
                )
            ]
        )
```

### Multi-Message Prompt

```python
@server.get_prompt()
async def get_prompt(name: str, arguments: dict):
    if name == "code_review":
        code = arguments["code"]
        language = arguments.get("language", "unknown")

        return GetPromptResult(
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"I have some {language} code to review:"
                    )
                ),
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text=f"```{language}\n{code}\n```"
                    )
                ),
                PromptMessage(
                    role="user",
                    content=TextContent(
                        type="text",
                        text="Please review this code for bugs, security issues, and improvements."
                    )
                )
            ]
        )
```

## Error Handling

```python
from mcp.types import TextContent, ErrorData

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "risky_operation":
            # Validate inputs
            if "path" not in arguments:
                return [TextContent(type="text", text="Error: 'path' argument required")]

            path = arguments["path"]
            if ".." in path:
                return [TextContent(type="text", text="Error: Path traversal not allowed")]

            # Perform operation
            result = await perform_operation(path)
            return [TextContent(type="text", text=result)]

    except PermissionError:
        return [TextContent(type="text", text="Error: Permission denied")]
    except FileNotFoundError:
        return [TextContent(type="text", text="Error: File not found")]
    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

## Server with State

```python
class StatefulServer:
    def __init__(self):
        self.server = Server("stateful-server")
        self.data = {}

        # Register handlers
        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    async def list_tools(self):
        return [
            Tool(name="set", description="Set a value", inputSchema={...}),
            Tool(name="get", description="Get a value", inputSchema={...}),
        ]

    async def call_tool(self, name: str, arguments: dict):
        if name == "set":
            self.data[arguments["key"]] = arguments["value"]
            return [TextContent(type="text", text="OK")]

        if name == "get":
            value = self.data.get(arguments["key"], "Not found")
            return [TextContent(type="text", text=str(value))]

    async def run(self):
        from mcp.server.stdio import stdio_server
        async with stdio_server() as (read, write):
            await self.server.run(read, write)

if __name__ == "__main__":
    server = StatefulServer()
    asyncio.run(server.run())
```

## Database Server Example

```python
import sqlite3
from contextlib import contextmanager

class DatabaseServer:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.server = Server("database-server")

        self.server.list_tools()(self.list_tools)
        self.server.call_tool()(self.call_tool)

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    async def list_tools(self):
        return [
            Tool(
                name="query",
                description="Execute a SELECT query",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "sql": {"type": "string", "description": "SELECT query"}
                    },
                    "required": ["sql"]
                }
            ),
            Tool(
                name="list_tables",
                description="List all tables",
                inputSchema={"type": "object", "properties": {}}
            )
        ]

    async def call_tool(self, name: str, arguments: dict):
        if name == "query":
            sql = arguments["sql"].strip().upper()
            if not sql.startswith("SELECT"):
                return [TextContent(type="text", text="Error: Only SELECT allowed")]

            with self.get_connection() as conn:
                cursor = conn.execute(arguments["sql"])
                rows = cursor.fetchall()
                return [TextContent(type="text", text=str(rows))]

        if name == "list_tables":
            with self.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [row[0] for row in cursor.fetchall()]
                return [TextContent(type="text", text="\n".join(tables))]
```

## Testing

```python
import pytest
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_server():
    async with stdio_client(
        command="python",
        args=["server.py"]
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()

            # Test tools
            tools = await session.list_tools()
            assert len(tools.tools) > 0

            # Call tool
            result = await session.call_tool("calculate", {"expression": "2+2"})
            assert "4" in result.content[0].text
```

## See Also

- [MCP Overview](index.md)
- [Client Integration](clients.md)
- [Examples](examples.md)
