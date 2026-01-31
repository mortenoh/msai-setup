# SSH Agent

## Overview

The SSH agent holds your private keys in memory, so you don't need to enter passphrases repeatedly.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         SSH Agent Flow                                    │
│                                                                           │
│   ┌────────────┐         ┌────────────┐         ┌────────────┐          │
│   │    SSH     │         │    SSH     │         │   Remote   │          │
│   │   Client   │◀───────▶│   Agent    │         │   Server   │          │
│   └─────┬──────┘         └─────┬──────┘         └─────┬──────┘          │
│         │                      │                      │                  │
│         │   1. Request sign    │                      │                  │
│         │──────────────────────▶                      │                  │
│         │                      │                      │                  │
│         │   2. Return signature│                      │                  │
│         │◀──────────────────────                      │                  │
│         │                      │                      │                  │
│         │   3. Send signature  │                      │                  │
│         │─────────────────────────────────────────────▶                  │
│         │                      │                      │                  │
│                                                                           │
│   Key never leaves agent - only signatures are sent                      │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Starting the Agent

### Check if Running

```bash
echo $SSH_AUTH_SOCK
# If empty, agent not running
```

### Start Manually

```bash
eval $(ssh-agent)
```

Output:

```
Agent pid 12345
```

### Start in Shell Profile

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# Start SSH agent if not running
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval $(ssh-agent -s)
fi
```

### Systemd User Service (Recommended)

```bash
# ~/.config/systemd/user/ssh-agent.service
[Unit]
Description=SSH Authentication Agent

[Service]
Type=simple
Environment=SSH_AUTH_SOCK=%t/ssh-agent.socket
ExecStart=/usr/bin/ssh-agent -D -a $SSH_AUTH_SOCK

[Install]
WantedBy=default.target
```

Enable:

```bash
systemctl --user enable ssh-agent
systemctl --user start ssh-agent

# Add to shell profile
export SSH_AUTH_SOCK="$XDG_RUNTIME_DIR/ssh-agent.socket"
```

## Adding Keys

### Add Default Key

```bash
ssh-add
# Adds ~/.ssh/id_rsa, ~/.ssh/id_ed25519, etc.
```

### Add Specific Key

```bash
ssh-add ~/.ssh/mykey
```

### Add with Timeout

Key removed from agent after timeout:

```bash
ssh-add -t 3600 ~/.ssh/mykey    # 1 hour
ssh-add -t 1h ~/.ssh/mykey      # Same
```

### Add from Config Automatically

```bash
# ~/.ssh/config
Host *
    AddKeysToAgent yes
```

Keys added automatically on first use.

## Managing Keys

### List Keys in Agent

```bash
ssh-add -l
```

Output:

```
256 SHA256:abc123... user@host (ED25519)
4096 SHA256:def456... another@host (RSA)
```

### List Keys with Full Public Key

```bash
ssh-add -L
```

### Remove Specific Key

```bash
ssh-add -d ~/.ssh/mykey
```

### Remove All Keys

```bash
ssh-add -D
```

### Lock Agent

```bash
ssh-add -x
# Enter lock password
```

### Unlock Agent

```bash
ssh-add -X
# Enter lock password
```

## Agent Forwarding

Forward your local agent to remote servers.

### Enable Forwarding

```bash
# Command line
ssh -A user@host

# Or in config
Host server
    ForwardAgent yes
```

### How It Works

```
Local Machine              Server A                Server B
┌────────────┐           ┌────────────┐         ┌────────────┐
│            │           │            │         │            │
│ SSH Agent  │◀─────────▶│  Forwarded │◀───────▶│   Uses     │
│ (keys)     │  forward  │   Socket   │  uses   │   Keys     │
│            │           │            │         │            │
└────────────┘           └────────────┘         └────────────┘
```

From Server A, you can SSH to Server B using your local keys.

### Security Warning

!!! danger "Agent Forwarding Risk"
    Anyone with root access on the intermediate server can use your forwarded agent to authenticate as you.

    Only forward to trusted servers.

### Safer Alternative: ProxyJump

Instead of agent forwarding:

```bash
# Don't do this (agent forwarding)
ssh -A bastion
ssh internal-server

# Do this instead (ProxyJump)
ssh -J bastion internal-server
```

ProxyJump tunnels the connection without exposing your agent.

## Keychain (Persistent Agent)

Keychain manages ssh-agent across sessions.

### Install

```bash
# Debian/Ubuntu
apt install keychain

# macOS
brew install keychain
```

### Configure

Add to `~/.bashrc`:

```bash
eval $(keychain --eval --agents ssh id_ed25519)
```

### With Multiple Keys

```bash
eval $(keychain --eval --agents ssh id_ed25519 work_key github_key)
```

### Options

```bash
keychain --eval \
    --agents ssh \
    --timeout 480 \      # Minutes before key timeout
    --quiet \            # Suppress output
    id_ed25519
```

## macOS Keychain Integration

macOS can store passphrases in system Keychain.

### Add Key to Keychain

```bash
ssh-add --apple-use-keychain ~/.ssh/id_ed25519
```

### Load from Keychain on Login

```bash
# ~/.ssh/config
Host *
    UseKeychain yes
    AddKeysToAgent yes
    IdentityFile ~/.ssh/id_ed25519
```

## GNOME Keyring (Linux Desktop)

GNOME Keyring often runs as SSH agent automatically.

### Check

```bash
echo $SSH_AUTH_SOCK
# /run/user/1000/keyring/ssh
```

### Disable (if using ssh-agent instead)

```bash
# Disable GNOME Keyring SSH component
mkdir -p ~/.config/autostart
cp /etc/xdg/autostart/gnome-keyring-ssh.desktop ~/.config/autostart/
echo "Hidden=true" >> ~/.config/autostart/gnome-keyring-ssh.desktop
```

## Hardware Keys (YubiKey, etc.)

### FIDO2/U2F Keys

```bash
# Generate key on hardware
ssh-keygen -t ed25519-sk -C "yubikey"

# The -sk suffix means "security key"
# Key requires physical touch to use
```

### Add to Agent

```bash
ssh-add ~/.ssh/id_ed25519_sk
# May require touch
```

### Resident Keys

Store key ON the hardware device:

```bash
ssh-keygen -t ed25519-sk -O resident -C "yubikey"
```

Load from device:

```bash
ssh-add -K    # Load resident keys from FIDO device
```

## Agent Sockets

### Default Socket

```bash
echo $SSH_AUTH_SOCK
# /tmp/ssh-XXXXXX/agent.12345
```

### Custom Socket Location

```bash
ssh-agent -a /path/to/socket
export SSH_AUTH_SOCK=/path/to/socket
```

### Sharing Agent Across Sessions

```bash
# In ~/.bashrc
SOCK="/tmp/ssh-agent-$USER"
if [ -S "$SSH_AUTH_SOCK" ] && [ "$SSH_AUTH_SOCK" != "$SOCK" ]; then
    ln -sf "$SSH_AUTH_SOCK" "$SOCK"
fi
export SSH_AUTH_SOCK="$SOCK"
```

## Debugging Agent Issues

### Check Agent is Running

```bash
ssh-add -l
# If "Could not open connection", agent not running
```

### Check Socket Exists

```bash
ls -la $SSH_AUTH_SOCK
```

### Test Key

```bash
ssh -T git@github.com
# Should show "Hi username!"
```

### Verbose

```bash
ssh -vvv user@host 2>&1 | grep -i agent
```

### Common Issues

| Problem | Solution |
|---------|----------|
| Agent not running | `eval $(ssh-agent)` |
| Key not added | `ssh-add ~/.ssh/mykey` |
| Wrong key offered | Use `IdentitiesOnly yes` in config |
| Passphrase asked every time | Add to agent, use keychain |
| Agent forwarding not working | Check `ForwardAgent yes`, server allows it |

## Best Practices

1. **Use agent** - Don't type passphrases repeatedly
2. **Set key timeouts** - `-t` flag for sensitive keys
3. **Limit forwarding** - Only to trusted servers
4. **Prefer ProxyJump** - Over agent forwarding
5. **Use keychain** - Persist across sessions
6. **Hardware keys** - For high-security needs
7. **Lock agent** - When stepping away
