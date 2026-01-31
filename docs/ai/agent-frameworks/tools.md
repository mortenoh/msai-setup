# Building Agent Tools

Tools enable agents to interact with the world beyond text generation.

## Tool Anatomy

A tool has:

1. **Name** - Identifier the agent uses
2. **Description** - Explains when/how to use it
3. **Input schema** - Expected parameters
4. **Implementation** - The actual function

## LangChain Tools

### Function Decorator

```python
from langchain.tools import tool

@tool
def search_web(query: str) -> str:
    """Search the web for information on a topic.

    Args:
        query: The search query string
    """
    # Implementation
    import requests
    response = requests.get(f"https://api.search.com?q={query}")
    return response.json()["results"]
```

### With Pydantic Schema

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(description="The search query")
    max_results: int = Field(default=5, description="Maximum results to return")

@tool(args_schema=SearchInput)
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web for information."""
    # Implementation
    pass
```

### Class-Based Tool

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type

class FileReadInput(BaseModel):
    path: str = Field(description="Path to the file")
    encoding: str = Field(default="utf-8", description="File encoding")

class FileReadTool(BaseTool):
    name: str = "read_file"
    description: str = "Read contents of a file from disk"
    args_schema: Type[BaseModel] = FileReadInput

    def _run(self, path: str, encoding: str = "utf-8") -> str:
        try:
            with open(path, encoding=encoding) as f:
                return f.read()
        except Exception as e:
            return f"Error reading file: {e}"

    async def _arun(self, path: str, encoding: str = "utf-8") -> str:
        # Async implementation
        return self._run(path, encoding)
```

## Common Tool Patterns

### File System Tools

```python
import os
from langchain.tools import tool

@tool
def list_directory(path: str = ".") -> str:
    """List files and directories in a path."""
    try:
        items = os.listdir(path)
        return "\n".join(items)
    except Exception as e:
        return f"Error: {e}"

@tool
def read_file(path: str) -> str:
    """Read contents of a text file."""
    try:
        with open(path) as f:
            return f.read()
    except Exception as e:
        return f"Error: {e}"

@tool
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error: {e}"
```

### Shell Execution

```python
import subprocess

@tool
def run_command(command: str) -> str:
    """Execute a shell command and return output.

    Use with caution - only for trusted inputs.
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30
        )
        output = result.stdout or result.stderr
        return output[:2000]  # Limit output size
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Error: {e}"
```

### HTTP Requests

```python
import requests

@tool
def http_get(url: str) -> str:
    """Make an HTTP GET request."""
    try:
        response = requests.get(url, timeout=10)
        return response.text[:5000]  # Limit response size
    except Exception as e:
        return f"Error: {e}"

@tool
def http_post(url: str, data: str) -> str:
    """Make an HTTP POST request with JSON data."""
    import json
    try:
        response = requests.post(
            url,
            json=json.loads(data),
            timeout=10
        )
        return response.text[:5000]
    except Exception as e:
        return f"Error: {e}"
```

### Database Tools

```python
import sqlite3

@tool
def query_database(sql: str) -> str:
    """Execute a SELECT query on the database.

    Only SELECT queries are allowed for safety.
    """
    if not sql.strip().upper().startswith("SELECT"):
        return "Error: Only SELECT queries allowed"

    try:
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()
        conn.close()

        if not results:
            return "No results found"

        return "\n".join([str(row) for row in results[:100]])
    except Exception as e:
        return f"Error: {e}"
```

### Code Execution

```python
import sys
from io import StringIO

@tool
def run_python(code: str) -> str:
    """Execute Python code and return output.

    Warning: Only use with trusted input.
    """
    old_stdout = sys.stdout
    sys.stdout = StringIO()

    try:
        exec(code)
        output = sys.stdout.getvalue()
        return output or "Code executed successfully (no output)"
    except Exception as e:
        return f"Error: {e}"
    finally:
        sys.stdout = old_stdout
```

## Tool Best Practices

### Clear Descriptions

```python
# Bad - vague
@tool
def process(data: str) -> str:
    """Process the data."""
    pass

# Good - specific
@tool
def extract_emails(text: str) -> str:
    """Extract all email addresses from the given text.

    Args:
        text: The text to search for email addresses

    Returns:
        A newline-separated list of found email addresses,
        or "No emails found" if none exist.
    """
    pass
```

### Error Handling

```python
@tool
def safe_divide(a: float, b: float) -> str:
    """Divide two numbers safely."""
    try:
        if b == 0:
            return "Error: Cannot divide by zero"
        result = a / b
        return str(result)
    except Exception as e:
        return f"Error: {e}"
```

### Input Validation

```python
from pydantic import BaseModel, Field, validator

class FilePathInput(BaseModel):
    path: str = Field(description="File path")

    @validator("path")
    def validate_path(cls, v):
        # Prevent path traversal
        if ".." in v or v.startswith("/"):
            raise ValueError("Invalid path")
        return v
```

### Output Limits

```python
@tool
def read_large_file(path: str) -> str:
    """Read a file, limiting output size."""
    MAX_CHARS = 10000

    with open(path) as f:
        content = f.read(MAX_CHARS)

    if len(content) == MAX_CHARS:
        content += "\n... (truncated)"

    return content
```

## Toolkit Pattern

Group related tools:

```python
from langchain.tools import BaseTool
from typing import List

class FileSystemToolkit:
    """Collection of file system tools."""

    def __init__(self, root_dir: str = "."):
        self.root_dir = root_dir

    def get_tools(self) -> List[BaseTool]:
        return [
            self._create_read_tool(),
            self._create_write_tool(),
            self._create_list_tool(),
        ]

    def _create_read_tool(self) -> BaseTool:
        @tool
        def read_file(path: str) -> str:
            """Read a file."""
            full_path = os.path.join(self.root_dir, path)
            with open(full_path) as f:
                return f.read()
        return read_file

    # ... other tools
```

## MCP Tools

See [MCP Guide](../mcp/index.md) for using MCP servers as tools.

```python
# MCP tools can be loaded and used like regular tools
from langchain_mcp import MCPToolkit

toolkit = MCPToolkit(server_url="http://localhost:3000")
tools = toolkit.get_tools()
```

## Testing Tools

```python
import pytest

def test_search_tool():
    result = search_web.invoke({"query": "test"})
    assert isinstance(result, str)
    assert "Error" not in result

def test_file_read_error():
    result = read_file.invoke({"path": "/nonexistent"})
    assert "Error" in result
```

## See Also

- [Agent Frameworks Overview](index.md)
- [LangChain Guide](langchain.md)
- [MCP Guide](../mcp/index.md)
