# VS Code Integration

## Overview

Use VS Code's Remote Development extensions with Tailscale for secure access to remote machines.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    VS Code + Tailscale                                       │
│                                                                              │
│   Local Machine                              Remote Server                  │
│   ─────────────                              ─────────────                  │
│                                                                              │
│   ┌─────────────────┐                        ┌─────────────────┐           │
│   │    VS Code      │                        │    VS Code      │           │
│   │    (UI)         │◄─────────────────────► │    Server       │           │
│   └─────────────────┘    Tailscale SSH       └─────────────────┘           │
│                          (encrypted)                   │                    │
│                                                        │                    │
│                                               ┌────────┴────────┐          │
│                                               │   Your Code     │          │
│                                               │   (server-side) │          │
│                                               └─────────────────┘          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **VS Code** with Remote - SSH extension
2. **Tailscale** installed on both machines
3. **SSH enabled** on remote machine

## Remote - SSH Extension

### Installation

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X)
3. Search "Remote - SSH"
4. Install "Remote - SSH" by Microsoft

### Configure SSH

Create or edit `~/.ssh/config`:

```bash
# For MagicDNS names
Host my-server
    HostName my-server.tailnet.ts.net
    User developer

Host dev-vm
    HostName dev-vm.tailnet.ts.net
    User ubuntu
    ForwardAgent yes

# Wildcard for all Tailscale hosts
Host *.tailnet.ts.net
    User developer
    ForwardAgent yes
```

### Connect to Remote

1. Press `F1` or `Ctrl+Shift+P`
2. Type "Remote-SSH: Connect to Host"
3. Select your configured host
4. VS Code connects and installs server component

## Tailscale SSH Integration

If using Tailscale SSH (not traditional SSH):

```bash
# Ensure SSH is enabled on remote
sudo tailscale up --ssh

# SSH config still works
Host my-server
    HostName my-server.tailnet.ts.net
    User developer
```

## Remote Development Workflows

### Opening Folders

```bash
# Command palette
Remote-SSH: Connect to Host...
→ Select host
→ Open Folder
→ /path/to/project
```

### Opening Workspace

```bash
# Connect to host, then:
File → Open Workspace from File...
→ Select .code-workspace file
```

### Terminal

Once connected:
- Ctrl+` opens terminal on remote
- All terminal commands run on remote machine

## VS Code Settings

### Per-Host Settings

```json
// settings.json
{
  "remote.SSH.configFile": "~/.ssh/config",
  "remote.SSH.showLoginTerminal": true,
  "remote.SSH.defaultExtensions": [
    "ms-python.python",
    "golang.go"
  ]
}
```

### Remote Settings

Settings can be specific to remote machines:

```json
// Remote settings.json
{
  "python.pythonPath": "/usr/bin/python3",
  "terminal.integrated.shell.linux": "/bin/bash"
}
```

## Extensions on Remote

### Install on Remote

Some extensions run on the remote:
- Language servers
- Debuggers
- Linters

Install these on the remote side via Extensions panel → "Install in SSH: hostname"

### Local Extensions

UI extensions run locally:
- Themes
- Keymaps
- UI customization

## Port Forwarding

VS Code automatically forwards ports:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│   Remote server running app on port 3000                                     │
│                                                                              │
│   VS Code detects → Offers to forward → Access at localhost:3000            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Manual Port Forward

1. Click "Ports" tab in bottom panel
2. Click "Forward a Port"
3. Enter port number
4. Access via localhost

### Forwarding Config

```json
{
  "remote.autoForwardPorts": true,
  "remote.autoForwardPortsSource": "process"
}
```

## Debugging

### Remote Debugging

Debug configurations work on remote:

```json
// .vscode/launch.json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal"
    }
  ]
}
```

### Attach to Remote Process

```json
{
  "name": "Attach to Remote",
  "type": "node",
  "request": "attach",
  "port": 9229,
  "restart": true
}
```

## Dev Containers over Tailscale

Combine with Dev Containers extension:

```bash
# SSH config
Host dev-server
    HostName dev-server.tailnet.ts.net
    User developer
```

```json
// .devcontainer/devcontainer.json
{
  "name": "Remote Dev Container",
  "image": "mcr.microsoft.com/devcontainers/python:3",
  "features": {
    "ghcr.io/devcontainers/features/git:1": {}
  }
}
```

Connect via Remote - SSH, then "Reopen in Container".

## Troubleshooting

### Connection Failed

```bash
# Test SSH manually
ssh my-server.tailnet.ts.net

# Check Tailscale status
tailscale status

# Verify DNS
ping my-server.tailnet.ts.net
```

### VS Code Server Install Failed

```bash
# SSH to remote and check
ls ~/.vscode-server/

# Remove and let VS Code reinstall
rm -rf ~/.vscode-server/
```

### Extensions Not Working

```bash
# Reinstall extension on remote
# In VS Code: Extensions → Right-click → Install in SSH: hostname
```

### Slow Performance

```bash
# Check connection type
tailscale ping my-server

# If relayed, try improving connectivity
tailscale netcheck
```

## Tips and Best Practices

### 1. Use SSH Config File

Centralize configuration in `~/.ssh/config` instead of VS Code settings.

### 2. Enable Agent Forwarding

For Git operations requiring your local SSH keys:

```bash
Host my-server
    ForwardAgent yes
```

### 3. Set Default User

Avoid specifying user every time:

```bash
Host *.tailnet.ts.net
    User developer
```

### 4. Use Workspaces

Create `.code-workspace` files for projects:

```json
{
  "folders": [
    {"path": "/home/dev/project1"},
    {"path": "/home/dev/project2"}
  ],
  "settings": {}
}
```

### 5. Sync Settings

Enable Settings Sync to maintain consistency across machines.

## Alternative: Remote Tunnels

VS Code Remote Tunnels (code CLI) also work with Tailscale:

```bash
# On remote
code tunnel

# Creates tunnel accessible from any VS Code
# Can use Tailscale for the underlying connectivity
```
