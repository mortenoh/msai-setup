# MCP Clients

Connect to MCP servers from applications and AI hosts.

## Python Client

### Basic Usage

```python
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client
import asyncio

async def main():
    # Connect to server via stdio
    async with stdio_client(
        command="python",
        args=["server.py"]
    ) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print("Tools:", [t.name for t in tools.tools])

            # Call a tool
            result = await session.call_tool(
                "calculate",
                {"expression": "2 + 2"}
            )
            print("Result:", result.content[0].text)

            # List resources
            resources = await session.list_resources()
            print("Resources:", [r.name for r in resources.resources])

            # Read a resource
            content = await session.read_resource("file:///data/config.json")
            print("Content:", content.contents[0].text)

asyncio.run(main())
```

### SSE Client

```python
from mcp.client.sse import sse_client

async def main():
    async with sse_client("http://localhost:8080/sse") as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # ... use session
```

## LangChain Integration

### MCP Tools in LangChain

```python
from langchain.tools import BaseTool
from mcp.client import ClientSession
from mcp.client.stdio import stdio_client
from pydantic import BaseModel, Field
from typing import Type
import asyncio

class MCPToolWrapper(BaseTool):
    """Wrapper to use MCP tools in LangChain."""

    name: str
    description: str
    session: ClientSession
    args_schema: Type[BaseModel]

    def _run(self, **kwargs) -> str:
        return asyncio.run(self._arun(**kwargs))

    async def _arun(self, **kwargs) -> str:
        result = await self.session.call_tool(self.name, kwargs)
        return result.content[0].text

async def load_mcp_tools(server_command: str, server_args: list) -> list:
    """Load tools from an MCP server for LangChain."""

    async with stdio_client(
        command=server_command,
        args=server_args
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            tools_response = await session.list_tools()
            langchain_tools = []

            for tool in tools_response.tools:
                # Create dynamic Pydantic model from schema
                schema_class = create_schema_from_json(tool.inputSchema)

                langchain_tools.append(MCPToolWrapper(
                    name=tool.name,
                    description=tool.description,
                    session=session,
                    args_schema=schema_class
                ))

            return langchain_tools
```

### MCP Resources as Documents

```python
from langchain_core.documents import Document

async def load_mcp_resources(session: ClientSession) -> list[Document]:
    """Load MCP resources as LangChain documents."""
    resources = await session.list_resources()
    documents = []

    for resource in resources.resources:
        content = await session.read_resource(resource.uri)
        documents.append(Document(
            page_content=content.contents[0].text,
            metadata={
                "uri": resource.uri,
                "name": resource.name,
                "mime_type": resource.mimeType
            }
        ))

    return documents
```

## Custom Client

### Connection Manager

```python
from dataclasses import dataclass
from typing import Optional
import asyncio

@dataclass
class MCPConnection:
    command: str
    args: list
    session: Optional[ClientSession] = None
    _read_stream = None
    _write_stream = None

class MCPManager:
    """Manage multiple MCP server connections."""

    def __init__(self):
        self.connections: dict[str, MCPConnection] = {}

    async def connect(self, name: str, command: str, args: list):
        """Connect to an MCP server."""
        if name in self.connections:
            return

        read, write = await stdio_client(command=command, args=args).__aenter__()
        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()

        self.connections[name] = MCPConnection(
            command=command,
            args=args,
            session=session,
            _read_stream=read,
            _write_stream=write
        )

    async def disconnect(self, name: str):
        """Disconnect from an MCP server."""
        if name not in self.connections:
            return

        conn = self.connections[name]
        if conn.session:
            await conn.session.__aexit__(None, None, None)
        del self.connections[name]

    async def call_tool(self, server: str, tool: str, arguments: dict):
        """Call a tool on a specific server."""
        if server not in self.connections:
            raise ValueError(f"Not connected to {server}")

        session = self.connections[server].session
        return await session.call_tool(tool, arguments)

    async def list_all_tools(self) -> dict:
        """List tools from all connected servers."""
        all_tools = {}
        for name, conn in self.connections.items():
            tools = await conn.session.list_tools()
            all_tools[name] = tools.tools
        return all_tools
```

### Usage

```python
async def main():
    manager = MCPManager()

    # Connect to multiple servers
    await manager.connect("files", "python", ["file_server.py"])
    await manager.connect("db", "python", ["db_server.py"])

    # List all tools
    tools = await manager.list_all_tools()
    print(tools)

    # Call tools
    result = await manager.call_tool("files", "read_file", {"path": "/data/test.txt"})
    print(result.content[0].text)

    # Cleanup
    await manager.disconnect("files")
    await manager.disconnect("db")
```

## Streaming Responses

```python
async def stream_tool_call(session: ClientSession, tool: str, args: dict):
    """Stream responses from a tool call."""

    # Note: Streaming depends on server implementation
    result = await session.call_tool(tool, args)

    for content in result.content:
        if content.type == "text":
            print(content.text)
        elif content.type == "image":
            # Handle image content
            pass
```

## Error Handling

```python
from mcp.types import ErrorCode

async def safe_call_tool(session: ClientSession, tool: str, args: dict):
    """Call a tool with error handling."""
    try:
        result = await session.call_tool(tool, args)

        # Check for error content
        for content in result.content:
            if content.type == "text" and content.text.startswith("Error:"):
                return {"success": False, "error": content.text}

        return {"success": True, "result": result}

    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Client Configuration

### From JSON Config

```python
import json
from pathlib import Path

async def load_servers_from_config(config_path: str) -> MCPManager:
    """Load MCP servers from configuration file."""
    config = json.loads(Path(config_path).read_text())
    manager = MCPManager()

    for name, server_config in config.get("mcpServers", {}).items():
        command = server_config["command"]
        args = server_config.get("args", [])
        env = server_config.get("env", {})

        await manager.connect(name, command, args, env=env)

    return manager

# config.json format:
# {
#   "mcpServers": {
#     "filesystem": {
#       "command": "uvx",
#       "args": ["mcp-server-filesystem", "/data"]
#     }
#   }
# }
```

## See Also

- [MCP Overview](index.md)
- [Building Servers](servers.md)
- [Examples](examples.md)
