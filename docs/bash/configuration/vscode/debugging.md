# Debugging

Debug configurations and techniques in VS Code.

## Overview

VS Code provides built-in debugging for:

- JavaScript/TypeScript (Node.js, browser)
- Python
- Go
- C/C++
- Many more via extensions

## Debug View

Open Debug view:

- ++cmd+shift+d++ or
- Click Debug icon in Activity Bar

## Launch Configuration

### Creating launch.json

1. Open Debug view
2. Click "create a launch.json file"
3. Select debugger type
4. Configuration created in `.vscode/launch.json`

### Basic Structure

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Debug Program",
      "type": "python",
      "request": "launch",
      "program": "${file}"
    }
  ]
}
```

### Configuration Properties

| Property | Description |
|----------|-------------|
| `name` | Display name in dropdown |
| `type` | Debugger type |
| `request` | `launch` or `attach` |
| `program` | File to debug |
| `args` | Command line arguments |
| `cwd` | Working directory |
| `env` | Environment variables |
| `preLaunchTask` | Task to run before debug |

## Python Debugging

### Basic Configuration

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "debugpy",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### With Arguments

```json
{
  "name": "Python: With Args",
  "type": "debugpy",
  "request": "launch",
  "program": "${file}",
  "args": ["--verbose", "--config", "dev.yaml"],
  "console": "integratedTerminal"
}
```

### Module

```json
{
  "name": "Python: Module",
  "type": "debugpy",
  "request": "launch",
  "module": "mypackage.main",
  "console": "integratedTerminal"
}
```

### Django

```json
{
  "name": "Django",
  "type": "debugpy",
  "request": "launch",
  "program": "${workspaceFolder}/manage.py",
  "args": ["runserver", "--noreload"],
  "django": true
}
```

### FastAPI

```json
{
  "name": "FastAPI",
  "type": "debugpy",
  "request": "launch",
  "module": "uvicorn",
  "args": ["main:app", "--reload"],
  "console": "integratedTerminal"
}
```

### pytest

```json
{
  "name": "pytest",
  "type": "debugpy",
  "request": "launch",
  "module": "pytest",
  "args": ["-v", "tests/"],
  "console": "integratedTerminal"
}
```

## JavaScript/Node.js Debugging

### Node.js

```json
{
  "name": "Node.js",
  "type": "node",
  "request": "launch",
  "program": "${workspaceFolder}/index.js"
}
```

### TypeScript

```json
{
  "name": "TypeScript",
  "type": "node",
  "request": "launch",
  "program": "${workspaceFolder}/src/index.ts",
  "preLaunchTask": "tsc: build",
  "outFiles": ["${workspaceFolder}/dist/**/*.js"]
}
```

### npm Script

```json
{
  "name": "npm start",
  "type": "node",
  "request": "launch",
  "runtimeExecutable": "npm",
  "runtimeArgs": ["start"]
}
```

### Chrome/Edge

```json
{
  "name": "Chrome",
  "type": "chrome",
  "request": "launch",
  "url": "http://localhost:3000",
  "webRoot": "${workspaceFolder}/src"
}
```

## Go Debugging

```json
{
  "name": "Go: Launch",
  "type": "go",
  "request": "launch",
  "mode": "auto",
  "program": "${fileDirname}"
}
```

### With Arguments

```json
{
  "name": "Go: With Args",
  "type": "go",
  "request": "launch",
  "mode": "auto",
  "program": "${workspaceFolder}",
  "args": ["--config", "dev.yaml"]
}
```

### Test

```json
{
  "name": "Go: Test",
  "type": "go",
  "request": "launch",
  "mode": "test",
  "program": "${workspaceFolder}"
}
```

## Rust Debugging

Requires CodeLLDB extension:

```json
{
  "name": "Rust: Debug",
  "type": "lldb",
  "request": "launch",
  "program": "${workspaceFolder}/target/debug/${workspaceFolderBasename}",
  "args": [],
  "cwd": "${workspaceFolder}",
  "preLaunchTask": "cargo build"
}
```

## Breakpoints

### Setting Breakpoints

- Click left of line number
- ++f9++ to toggle
- Right-click for conditional breakpoints

### Breakpoint Types

| Type | Description |
|------|-------------|
| Standard | Pause at line |
| Conditional | Pause when condition is true |
| Logpoint | Log message without pausing |
| Hit count | Pause after N hits |

### Conditional Breakpoint

Right-click > "Add Conditional Breakpoint":

```python
# Expression that evaluates to boolean
x > 10
user.name == "admin"
len(items) > 100
```

### Logpoint

Right-click > "Add Logpoint":

```
User logged in: {user.name}
Processing item {i} of {total}
```

## Debug Actions

| Key | Action |
|-----|--------|
| ++f5++ | Start/Continue |
| ++shift+f5++ | Stop |
| ++cmd+shift+f5++ | Restart |
| ++f10++ | Step Over |
| ++f11++ | Step Into |
| ++shift+f11++ | Step Out |
| ++f9++ | Toggle Breakpoint |

## Debug Panels

### Variables

View local and global variables. Expand objects to inspect properties.

### Watch

Add expressions to watch:

- Right-click variable > "Add to Watch"
- Click + in Watch panel

### Call Stack

View execution path. Click to jump to frame.

### Debug Console

Execute code in current context:

```python
# Evaluate expressions
print(my_variable)
my_function()
len(my_list)
```

## Environment Variables

### In launch.json

```json
{
  "name": "With Env",
  "type": "python",
  "request": "launch",
  "program": "${file}",
  "env": {
    "DEBUG": "true",
    "DATABASE_URL": "postgres://localhost/dev"
  }
}
```

### From .env File

```json
{
  "name": "With .env",
  "type": "python",
  "request": "launch",
  "program": "${file}",
  "envFile": "${workspaceFolder}/.env"
}
```

## Compound Configurations

Debug multiple targets together:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Server",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/server.py"
    },
    {
      "name": "Client",
      "type": "chrome",
      "request": "launch",
      "url": "http://localhost:3000"
    }
  ],
  "compounds": [
    {
      "name": "Full Stack",
      "configurations": ["Server", "Client"]
    }
  ]
}
```

## Attach to Running Process

### Python

```json
{
  "name": "Python: Attach",
  "type": "debugpy",
  "request": "attach",
  "connect": {
    "host": "localhost",
    "port": 5678
  }
}
```

In your code:

```python
import debugpy
debugpy.listen(5678)
debugpy.wait_for_client()
```

### Node.js

Start with `--inspect`:

```bash
node --inspect server.js
```

```json
{
  "name": "Node: Attach",
  "type": "node",
  "request": "attach",
  "port": 9229
}
```

## Tasks Integration

Run task before debugging:

```json
{
  "name": "Debug with Build",
  "type": "python",
  "request": "launch",
  "program": "${file}",
  "preLaunchTask": "build"
}
```

Define task in `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "build",
      "type": "shell",
      "command": "make build"
    }
  ]
}
```

## Debug Settings

```json
{
  "debug.console.fontSize": 13,
  "debug.internalConsoleOptions": "openOnSessionStart",
  "debug.showBreakpointsInOverviewRuler": true,
  "debug.toolBarLocation": "docked"
}
```

## Troubleshooting

### Debugger Not Starting

1. Check debugger extension installed
2. Verify launch.json syntax
3. Check program path exists

### Breakpoints Not Hit

1. Verify source maps (JS/TS)
2. Check code is being executed
3. Try unconditional breakpoint first

### Can't Attach

1. Check port is correct
2. Verify process is running
3. Check firewall settings
