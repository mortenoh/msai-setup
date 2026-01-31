# SSH Connection Multiplexing

## Overview

Connection multiplexing allows multiple SSH sessions to share a single TCP connection. Benefits:

- Faster subsequent connections (no new handshake)
- Reduced authentication overhead
- Single connection through firewalls
- Efficient resource usage

```
┌──────────────────────────────────────────────────────────────────────────┐
│                     Without Multiplexing                                  │
│                                                                           │
│   ssh user@host    ────────── [TCP + Auth + Crypto] ──────▶  Session 1   │
│   ssh user@host    ────────── [TCP + Auth + Crypto] ──────▶  Session 2   │
│   ssh user@host    ────────── [TCP + Auth + Crypto] ──────▶  Session 3   │
│                                                                           │
│   3 connections, 3 authentications, 3 key exchanges                      │
│                                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│                     With Multiplexing                                     │
│                                                                           │
│   ssh user@host    ────────── [TCP + Auth + Crypto] ──────┐              │
│   ssh user@host    ──────────────────────────────────────▶│  Sessions    │
│   ssh user@host    ──────────────────────────────────────▶│  1, 2, 3    │
│                                                           │              │
│   1 connection, 1 authentication, shared over socket      │              │
│                                                           └──────────────┘
└──────────────────────────────────────────────────────────────────────────┘
```

## Enable Multiplexing

### SSH Config

```bash
# ~/.ssh/config
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
```

### Create Socket Directory

```bash
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets
```

### Options Explained

| Option | Description |
|--------|-------------|
| `ControlMaster auto` | Automatically create master or use existing |
| `ControlPath` | Socket file location |
| `ControlPersist 600` | Keep connection alive 10 minutes after last session |

## ControlPath Tokens

```bash
ControlPath ~/.ssh/sockets/%r@%h-%p
```

| Token | Meaning |
|-------|---------|
| `%r` | Remote username |
| `%h` | Remote hostname |
| `%p` | Port |
| `%n` | Original hostname (before config) |
| `%l` | Local hostname |
| `%C` | Hash of %l%h%p%r (unique) |

### Recommended Paths

```bash
# Simple
ControlPath ~/.ssh/sockets/%r@%h-%p

# With hash (handles long hostnames)
ControlPath ~/.ssh/sockets/%C

# In /tmp (cleared on reboot)
ControlPath /tmp/ssh-%r@%h:%p
```

## ControlMaster Options

```bash
# Automatic (recommended)
ControlMaster auto

# Yes - always be master
ControlMaster yes

# No - never be master, use existing
ControlMaster no

# Ask - prompt before creating
ControlMaster ask

# Autoask - auto but ask for new
ControlMaster autoask
```

## ControlPersist Options

```bash
# Time in seconds
ControlPersist 600      # 10 minutes

# Or with units
ControlPersist 10m      # 10 minutes
ControlPersist 1h       # 1 hour

# Stay forever until manually closed
ControlPersist yes

# Close when last session ends
ControlPersist no
```

## Managing Multiplexed Connections

### Check Status

```bash
ssh -O check user@host
# Master running (pid=12345)
```

### List Sessions

```bash
ssh -O forward -L 8080:localhost:80 user@host  # List forwards
```

### Add Port Forward to Existing Connection

```bash
ssh -O forward -L 8080:localhost:80 user@host
ssh -O forward -R 9090:localhost:9090 user@host
```

### Cancel Port Forward

```bash
ssh -O cancel -L 8080:localhost:80 user@host
```

### Stop Master Connection

```bash
ssh -O stop user@host   # Graceful
ssh -O exit user@host   # Immediate
```

## Per-Host Configuration

```bash
# ~/.ssh/config

# Enable for most hosts
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%C
    ControlPersist 10m

# Disable for unreliable connections
Host flaky-server
    ControlMaster no

# Longer persist for frequently used
Host workstation
    ControlPersist 2h
```

## Command Line Usage

### Start Master Explicitly

```bash
ssh -M -S /tmp/mysocket user@host
```

### Use Existing Master

```bash
ssh -S /tmp/mysocket user@host
```

### Background Master

```bash
ssh -M -S /tmp/mysocket -f -N user@host
```

## Use Cases

### Faster Git Operations

```bash
# ~/.ssh/config
Host github.com
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%C
    ControlPersist 10m
```

Multiple git operations share one connection:

```bash
git fetch origin    # First: creates master
git pull            # Fast: reuses
git push            # Fast: reuses
```

### Multiple Terminals to Same Host

First terminal creates master, subsequent reuse:

```bash
# Terminal 1 (creates master)
ssh server

# Terminal 2 (instant connect)
ssh server

# Terminal 3 (instant connect)
ssh server
```

### Faster Rsync/SCP

```bash
# First transfer creates master
rsync -avz dir/ user@host:/path/

# Subsequent transfers are faster
rsync -avz file.txt user@host:/path/
scp another.txt user@host:/path/
```

### Batch Operations

```bash
#!/bin/bash
# Start master
ssh -M -S /tmp/batch-%h -N -f user@host

# Multiple operations (all fast)
for i in {1..10}; do
    ssh -S /tmp/batch-%h user@host "do_something $i"
done

# Close master
ssh -S /tmp/batch-%h -O exit user@host
```

## Troubleshooting

### Socket File Issues

```bash
# Permission denied
chmod 700 ~/.ssh/sockets

# Socket exists but stale
rm ~/.ssh/sockets/user@host-22
# Or
ssh -O exit user@host 2>/dev/null

# Path too long
# Use %C instead of %r@%h-%p
ControlPath ~/.ssh/sockets/%C
```

### Connection Sharing Failed

```bash
# Check master is running
ssh -O check user@host

# Check socket exists
ls -la ~/.ssh/sockets/

# Debug
ssh -vvv user@host 2>&1 | grep -i multiplex
```

### Master Died, Sessions Affected

When master dies, all sessions die. Solutions:

```bash
# Use longer ControlPersist
ControlPersist 1h

# Or don't use multiplexing for critical sessions
ssh -o ControlMaster=no user@host
```

### Incompatible Operations

Some operations can't share connections:

```bash
# Run without multiplexing
ssh -o ControlMaster=no -o ControlPath=none user@host
```

## Security Considerations

### Socket Permissions

```bash
# Socket directory must be 700
chmod 700 ~/.ssh/sockets

# Sockets are only usable by owner
ls -la ~/.ssh/sockets/
# srw------- 1 user user 0 Jan 1 12:00 user@host-22
```

### Shared Connection Risks

- All sessions share one connection
- If one session has higher privileges, others might access
- Consider separate connections for different security contexts

### Disabling for Sensitive Operations

```bash
Host sensitive-server
    ControlMaster no
    ControlPath none
```

## Performance Comparison

| Scenario | Without Multiplex | With Multiplex |
|----------|-------------------|----------------|
| First connection | ~500ms | ~500ms |
| Second connection | ~500ms | ~50ms |
| 10 quick commands | ~5000ms | ~500ms |
| Git fetch + pull + push | ~1500ms | ~600ms |

## Best Practices

1. **Always enable** for frequently accessed hosts
2. **Use ControlPersist** to avoid premature closure
3. **Use %C** for socket path (handles long names)
4. **Create socket directory** with proper permissions
5. **Monitor** socket files, clean stale ones
6. **Disable** for sensitive or unstable connections
7. **Test** that configuration works as expected
