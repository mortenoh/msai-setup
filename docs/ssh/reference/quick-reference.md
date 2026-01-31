# SSH Quick Reference

## Connection Commands

```bash
# Basic connection
ssh user@host
ssh -p 2222 user@host

# With key
ssh -i ~/.ssh/key user@host

# Run command
ssh user@host "command"

# Verbose (debugging)
ssh -v user@host
ssh -vvv user@host
```

## Key Management

```bash
# Generate key
ssh-keygen -t ed25519 -C "comment"
ssh-keygen -t rsa -b 4096 -C "comment"

# Copy key to server
ssh-copy-id user@host
ssh-copy-id -i ~/.ssh/key.pub user@host

# View fingerprint
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# Change passphrase
ssh-keygen -p -f ~/.ssh/id_ed25519
```

## SSH Agent

```bash
# Start agent
eval $(ssh-agent)

# Add key
ssh-add
ssh-add ~/.ssh/specific_key
ssh-add -t 3600 ~/.ssh/key  # Timeout

# List keys
ssh-add -l

# Remove keys
ssh-add -d ~/.ssh/key
ssh-add -D  # All
```

## Port Forwarding

```bash
# Local: access remote service locally
ssh -L 8080:localhost:80 user@host
ssh -L 5432:db.internal:5432 user@host

# Remote: expose local service remotely
ssh -R 8080:localhost:3000 user@host

# Dynamic (SOCKS proxy)
ssh -D 1080 user@host

# Tunnel only (no shell)
ssh -N -L 8080:localhost:80 user@host

# Background tunnel
ssh -f -N -L 8080:localhost:80 user@host
```

## Jump Hosts

```bash
# ProxyJump
ssh -J jump user@destination
ssh -J jump1,jump2 user@destination

# File transfer through jump
scp -J jump file.txt user@dest:/path/
rsync -avz -e "ssh -J jump" src/ user@dest:/path/
```

## File Transfer

```bash
# SCP
scp file.txt user@host:/path/
scp user@host:/path/file.txt ./
scp -r dir/ user@host:/path/

# SFTP
sftp user@host

# Rsync
rsync -avzP /src/ user@host:/dest/
rsync -avz --delete /src/ user@host:/dest/
```

## SSH Config (~/.ssh/config)

```bash
Host myserver
    HostName server.example.com
    User admin
    Port 2222
    IdentityFile ~/.ssh/server_key
    IdentitiesOnly yes

Host *
    ServerAliveInterval 60
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%C
    ControlPersist 10m
```

## Server Config (/etc/ssh/sshd_config)

```bash
# Security
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# Access control
AllowUsers admin deploy
AllowGroups ssh-users

# Forwarding
AllowTcpForwarding yes
AllowAgentForwarding no
X11Forwarding no

# Timeouts
ClientAliveInterval 300
ClientAliveCountMax 2
LoginGraceTime 30
MaxAuthTries 3
```

## Common Options

| Option | Description |
|--------|-------------|
| `-p port` | Connect to port |
| `-i key` | Use identity file |
| `-l user` | Login as user |
| `-v` | Verbose mode |
| `-N` | No command (tunnel only) |
| `-f` | Background after auth |
| `-L` | Local forward |
| `-R` | Remote forward |
| `-D` | Dynamic (SOCKS) |
| `-J` | Jump host |
| `-A` | Agent forwarding |
| `-X` | X11 forwarding |
| `-C` | Compression |
| `-q` | Quiet mode |
| `-T` | No TTY |
| `-t` | Force TTY |

## Escape Sequences

Press `Enter` then:

| Sequence | Action |
|----------|--------|
| `~.` | Disconnect |
| `~^Z` | Suspend |
| `~#` | List forwarded connections |
| `~&` | Background (at logout) |
| `~?` | Help |
| `~~` | Send literal ~ |

## Debugging

```bash
# Client verbose
ssh -vvv user@host

# Test config
ssh -G hostname

# Server test
sshd -t
sshd -T

# Server logs
journalctl -u sshd -f
tail -f /var/log/auth.log
```

## Key Permissions

```bash
~/.ssh/               700  drwx------
~/.ssh/id_ed25519     600  -rw-------
~/.ssh/id_ed25519.pub 644  -rw-r--r--
~/.ssh/authorized_keys 600  -rw-------
~/.ssh/known_hosts    644  -rw-r--r--
~/.ssh/config         600  -rw-------
```

## Authorized Keys Options

```bash
# Restrict key
command="cmd" ssh-ed25519 AAAA...
from="192.168.1.*" ssh-ed25519 AAAA...
no-port-forwarding ssh-ed25519 AAAA...
no-agent-forwarding ssh-ed25519 AAAA...
no-pty ssh-ed25519 AAAA...

# Combined
restrict,command="/usr/local/bin/backup" ssh-ed25519 AAAA...
```

## sshd_config Match Blocks

```bash
Match User sftpuser
    ForceCommand internal-sftp
    ChrootDirectory /data/sftp/%u

Match Address 192.168.1.0/24
    PasswordAuthentication yes

Match Group admins
    AllowTcpForwarding yes
```

## Useful Aliases

```bash
# ~/.bashrc
alias sshr='ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null'
alias sshv='ssh -vvv'
alias scp-resume='rsync -avzP --partial'
```

## Quick Fixes

| Problem | Fix |
|---------|-----|
| Permission denied (key) | `chmod 600 ~/.ssh/id_ed25519` |
| Too many auth failures | `ssh -o IdentitiesOnly=yes -i key` |
| Host key changed | `ssh-keygen -R hostname` |
| Slow connection | `UseDNS no` in sshd_config |
| Connection drops | `ServerAliveInterval 60` |
| Can't forward | `AllowTcpForwarding yes` in sshd_config |
