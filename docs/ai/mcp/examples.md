# MCP Examples

Practical MCP server implementations for common use cases.

## File System Server

```python
#!/usr/bin/env python3
"""MCP server for file system operations."""

from mcp.server import Server
from mcp.types import Tool, Resource, TextContent
from pathlib import Path
import asyncio
import os

server = Server("filesystem")

# Configuration
ALLOWED_DIR = Path("/data")

def validate_path(path: str) -> Path:
    """Ensure path is within allowed directory."""
    full_path = (ALLOWED_DIR / path).resolve()
    if not str(full_path).startswith(str(ALLOWED_DIR)):
        raise ValueError("Path outside allowed directory")
    return full_path

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="read_file",
            description="Read contents of a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Relative path to file"}
                },
                "required": ["path"]
            }
        ),
        Tool(
            name="write_file",
            description="Write content to a file",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"}
                },
                "required": ["path", "content"]
            }
        ),
        Tool(
            name="list_directory",
            description="List files in a directory",
            inputSchema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "default": "."}
                }
            }
        ),
        Tool(
            name="search_files",
            description="Search for files matching a pattern",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Glob pattern"}
                },
                "required": ["pattern"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "read_file":
            path = validate_path(arguments["path"])
            content = path.read_text()
            return [TextContent(type="text", text=content)]

        if name == "write_file":
            path = validate_path(arguments["path"])
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(arguments["content"])
            return [TextContent(type="text", text=f"Written to {path}")]

        if name == "list_directory":
            path = validate_path(arguments.get("path", "."))
            items = []
            for item in path.iterdir():
                prefix = "d " if item.is_dir() else "f "
                items.append(f"{prefix}{item.name}")
            return [TextContent(type="text", text="\n".join(items))]

        if name == "search_files":
            pattern = arguments["pattern"]
            matches = list(ALLOWED_DIR.glob(pattern))
            paths = [str(m.relative_to(ALLOWED_DIR)) for m in matches[:100]]
            return [TextContent(type="text", text="\n".join(paths))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## Database Query Server

```python
#!/usr/bin/env python3
"""MCP server for SQLite database access."""

from mcp.server import Server
from mcp.types import Tool, Resource, TextContent
import sqlite3
import json
import asyncio

server = Server("database")
DB_PATH = "/data/database.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="query",
            description="Execute a SELECT query",
            inputSchema={
                "type": "object",
                "properties": {
                    "sql": {"type": "string", "description": "SQL SELECT statement"}
                },
                "required": ["sql"]
            }
        ),
        Tool(
            name="describe_table",
            description="Get table schema",
            inputSchema={
                "type": "object",
                "properties": {
                    "table": {"type": "string", "description": "Table name"}
                },
                "required": ["table"]
            }
        )
    ]

@server.list_resources()
async def list_resources():
    conn = get_connection()
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    conn.close()

    return [
        Resource(
            uri=f"db://tables/{table[0]}",
            name=table[0],
            description=f"Table: {table[0]}",
            mimeType="application/json"
        )
        for table in tables
    ]

@server.read_resource()
async def read_resource(uri: str):
    if uri.startswith("db://tables/"):
        table = uri.split("/")[-1]
        conn = get_connection()
        cursor = conn.execute(f"SELECT * FROM {table} LIMIT 100")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        conn.close()

        data = [dict(zip(columns, row)) for row in rows]
        return json.dumps(data, indent=2)

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "query":
            sql = arguments["sql"].strip()
            if not sql.upper().startswith("SELECT"):
                return [TextContent(type="text", text="Error: Only SELECT queries allowed")]

            conn = get_connection()
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            conn.close()

            # Format as table
            result = " | ".join(columns) + "\n"
            result += "-" * len(result) + "\n"
            for row in rows[:50]:
                result += " | ".join(str(v) for v in row) + "\n"

            return [TextContent(type="text", text=result)]

        if name == "describe_table":
            table = arguments["table"]
            conn = get_connection()
            cursor = conn.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            conn.close()

            result = "Column | Type | Nullable | Default | PK\n"
            result += "-" * 50 + "\n"
            for col in columns:
                result += f"{col[1]} | {col[2]} | {not col[3]} | {col[4]} | {col[5]}\n"

            return [TextContent(type="text", text=result)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## Git Operations Server

```python
#!/usr/bin/env python3
"""MCP server for Git operations."""

from mcp.server import Server
from mcp.types import Tool, TextContent
import subprocess
import asyncio
import os

server = Server("git")
REPO_PATH = os.environ.get("GIT_REPO_PATH", ".")

def run_git(*args) -> str:
    """Run a git command and return output."""
    result = subprocess.run(
        ["git", *args],
        cwd=REPO_PATH,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise Exception(result.stderr)
    return result.stdout

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="git_status",
            description="Show working tree status",
            inputSchema={"type": "object", "properties": {}}
        ),
        Tool(
            name="git_log",
            description="Show commit history",
            inputSchema={
                "type": "object",
                "properties": {
                    "n": {"type": "integer", "default": 10, "description": "Number of commits"}
                }
            }
        ),
        Tool(
            name="git_diff",
            description="Show changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "staged": {"type": "boolean", "default": False}
                }
            }
        ),
        Tool(
            name="git_show",
            description="Show a commit",
            inputSchema={
                "type": "object",
                "properties": {
                    "commit": {"type": "string", "default": "HEAD"}
                }
            }
        ),
        Tool(
            name="git_branch",
            description="List branches",
            inputSchema={"type": "object", "properties": {}}
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "git_status":
            output = run_git("status", "--short")
            return [TextContent(type="text", text=output or "Working tree clean")]

        if name == "git_log":
            n = arguments.get("n", 10)
            output = run_git("log", f"-{n}", "--oneline")
            return [TextContent(type="text", text=output)]

        if name == "git_diff":
            if arguments.get("staged"):
                output = run_git("diff", "--staged")
            else:
                output = run_git("diff")
            return [TextContent(type="text", text=output or "No changes")]

        if name == "git_show":
            commit = arguments.get("commit", "HEAD")
            output = run_git("show", commit, "--stat")
            return [TextContent(type="text", text=output)]

        if name == "git_branch":
            output = run_git("branch", "-a")
            return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## HTTP API Server

```python
#!/usr/bin/env python3
"""MCP server for HTTP API calls."""

from mcp.server import Server
from mcp.types import Tool, TextContent
import aiohttp
import json
import asyncio

server = Server("http-api")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="http_get",
            description="Make HTTP GET request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "headers": {"type": "object", "default": {}}
                },
                "required": ["url"]
            }
        ),
        Tool(
            name="http_post",
            description="Make HTTP POST request",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"},
                    "data": {"type": "object"},
                    "headers": {"type": "object", "default": {}}
                },
                "required": ["url", "data"]
            }
        ),
        Tool(
            name="fetch_json",
            description="Fetch and parse JSON from URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {"type": "string"}
                },
                "required": ["url"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        async with aiohttp.ClientSession() as session:
            if name == "http_get":
                async with session.get(
                    arguments["url"],
                    headers=arguments.get("headers", {})
                ) as response:
                    text = await response.text()
                    return [TextContent(type="text", text=text[:10000])]

            if name == "http_post":
                async with session.post(
                    arguments["url"],
                    json=arguments["data"],
                    headers=arguments.get("headers", {})
                ) as response:
                    text = await response.text()
                    return [TextContent(type="text", text=text[:10000])]

            if name == "fetch_json":
                async with session.get(arguments["url"]) as response:
                    data = await response.json()
                    return [TextContent(type="text", text=json.dumps(data, indent=2))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## RAG Server

```python
#!/usr/bin/env python3
"""MCP server for RAG queries."""

from mcp.server import Server
from mcp.types import Tool, TextContent
import chromadb
from langchain_community.embeddings import OllamaEmbeddings
import asyncio

server = Server("rag")

# Initialize
embeddings = OllamaEmbeddings(model="nomic-embed-text")
client = chromadb.PersistentClient(path="/data/vectordb")
collection = client.get_or_create_collection("documents")

@server.list_tools()
async def list_tools():
    return [
        Tool(
            name="search",
            description="Search documents for relevant information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "n_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="add_document",
            description="Add a document to the knowledge base",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {"type": "string"},
                    "metadata": {"type": "object", "default": {}}
                },
                "required": ["content"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    try:
        if name == "search":
            query_embedding = embeddings.embed_query(arguments["query"])
            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=arguments.get("n_results", 5)
            )

            output = []
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                output.append(f"[{i+1}] {metadata.get('source', 'Unknown')}\n{doc}\n")

            return [TextContent(type="text", text="\n---\n".join(output))]

        if name == "add_document":
            content = arguments["content"]
            metadata = arguments.get("metadata", {})
            embedding = embeddings.embed_query(content)

            collection.add(
                documents=[content],
                embeddings=[embedding],
                metadatas=[metadata],
                ids=[f"doc_{collection.count()}"]
            )

            return [TextContent(type="text", text="Document added")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]

async def main():
    from mcp.server.stdio import stdio_server
    async with stdio_server() as (read, write):
        await server.run(read, write)

if __name__ == "__main__":
    asyncio.run(main())
```

## Claude Desktop Configuration

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["/path/to/filesystem_server.py"],
      "env": {
        "ALLOWED_DIR": "/home/user/documents"
      }
    },
    "database": {
      "command": "python",
      "args": ["/path/to/database_server.py"],
      "env": {
        "DB_PATH": "/data/myapp.db"
      }
    },
    "git": {
      "command": "python",
      "args": ["/path/to/git_server.py"],
      "env": {
        "GIT_REPO_PATH": "/home/user/projects/myrepo"
      }
    },
    "rag": {
      "command": "python",
      "args": ["/path/to/rag_server.py"]
    }
  }
}
```

## See Also

- [MCP Overview](index.md)
- [Building Servers](servers.md)
- [Client Integration](clients.md)
