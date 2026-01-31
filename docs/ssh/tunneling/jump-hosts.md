# Jump Hosts (Bastion Servers)

## Overview

Jump hosts (bastion hosts) provide controlled access to internal networks. Instead of exposing internal servers directly, all access goes through the hardened jump host.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Jump Host Architecture                            │
│                                                                           │
│   Internet          DMZ              Internal Network                     │
│                                                                           │
│   ┌─────┐      ┌─────────┐      ┌─────────┐  ┌─────────┐                │
│   │ You │─────▶│ Bastion │─────▶│  Web    │  │   DB    │                │
│   └─────┘      │  (jump) │      │ Server  │  │ Server  │                │
│                └─────────┘      └─────────┘  └─────────┘                │
│                     │           ┌─────────┐  ┌─────────┐                │
│                     └──────────▶│  App    │  │  Redis  │                │
│                                 │ Server  │  │ Server  │                │
│                                 └─────────┘  └─────────┘                │
│                                                                           │
│   Direct access to internal servers: ❌                                  │
│   Access through bastion: ✅                                             │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## ProxyJump (Recommended)

The modern, simple way to use jump hosts.

### Basic Usage

```bash
ssh -J jump_host destination
ssh -J bastion.example.com internal-server
```

### With User and Port

```bash
ssh -J jumpuser@bastion.example.com:2222 admin@internal-server
```

### Multiple Jumps

```bash
ssh -J jump1,jump2,jump3 destination
ssh -J bastion.example.com,internal-jump.local admin@deep-server
```

### SSH Config

```bash
# ~/.ssh/config
Host bastion
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/bastion_key

Host internal-*
    ProxyJump bastion
    User admin
    IdentityFile ~/.ssh/internal_key

Host internal-web
    HostName 10.0.0.10

Host internal-db
    HostName 10.0.0.20

Host internal-app
    HostName 10.0.0.30
```

Usage becomes simple:

```bash
ssh internal-web    # Automatically jumps through bastion
ssh internal-db     # Same
scp file.txt internal-app:/home/admin/   # Also works
```

## ProxyCommand (Legacy)

Before ProxyJump, ProxyCommand was used:

```bash
ssh -o ProxyCommand="ssh -W %h:%p jumphost" destination
```

### SSH Config with ProxyCommand

```bash
Host internal-*
    ProxyCommand ssh -W %h:%p bastion.example.com
```

### Difference

| Method | Introduced | Syntax | Features |
|--------|------------|--------|----------|
| ProxyJump | OpenSSH 7.3 | `-J host` | Simple, chainable |
| ProxyCommand | Older | `-o ProxyCommand=...` | Flexible, scriptable |

Use ProxyJump unless you need custom logic.

## Agent Forwarding vs ProxyJump

### Agent Forwarding (Risky)

```bash
ssh -A bastion.example.com
# Then from bastion:
ssh internal-server
```

**Problem**: Anyone with root on bastion can use your agent.

### ProxyJump (Safer)

```bash
ssh -J bastion.example.com internal-server
```

**Better**: Your keys never touch the bastion server.

## File Transfer Through Jump

### SCP

```bash
scp -J bastion.example.com file.txt admin@internal:/home/admin/
scp -J bastion.example.com admin@internal:/var/log/app.log ./
```

### Rsync

```bash
rsync -avz -e "ssh -J bastion.example.com" /local/dir/ admin@internal:/remote/dir/
```

### SFTP

```bash
sftp -J bastion.example.com admin@internal
```

## Port Forwarding Through Jump

### Local Forward

Access internal service through bastion:

```bash
ssh -J bastion.example.com -L 5432:localhost:5432 admin@internal-db
# localhost:5432 → bastion → internal-db:5432
```

### With Config

```bash
Host internal-db
    HostName 10.0.0.20
    User admin
    ProxyJump bastion
    LocalForward 5432 localhost:5432
```

### Remote Forward

```bash
ssh -J bastion.example.com -R 8080:localhost:3000 admin@internal-web
```

## Multiple Jump Hosts

### Chained Jumps

```bash
ssh -J jump1,jump2 destination
```

```
You → jump1 → jump2 → destination
```

### Config for Deep Networks

```bash
# ~/.ssh/config
Host bastion
    HostName bastion.example.com
    User admin

Host internal-jump
    HostName 10.0.0.1
    ProxyJump bastion
    User admin

Host deep-server
    HostName 192.168.10.50
    ProxyJump internal-jump
    User app
```

```bash
ssh deep-server
# You → bastion → internal-jump → deep-server
```

## Bastion Server Setup

### Hardened Configuration

```bash
# /etc/ssh/sshd_config on bastion

# Listen on standard port
Port 22

# Key-only authentication
PasswordAuthentication no
PubkeyAuthentication yes

# No root login
PermitRootLogin no

# Limit users
AllowUsers jumpuser admin

# Allow forwarding (needed for jump)
AllowTcpForwarding yes
AllowAgentForwarding no    # Don't allow agent forwarding

# Minimal features
X11Forwarding no
PermitTunnel no

# Logging
LogLevel VERBOSE

# Idle timeout
ClientAliveInterval 300
ClientAliveCountMax 2

# Restrict tunneling to internal network
Match User jumpuser
    PermitOpen 10.0.0.0/8:22 192.168.0.0/16:22
    AllowTcpForwarding yes
    PermitTTY no
    ForceCommand /bin/false
```

### Jump-Only User

User that can only be used for jumping:

```bash
# Create user
useradd -m -s /usr/sbin/nologin jumpuser

# SSH key
mkdir /home/jumpuser/.ssh
cat > /home/jumpuser/.ssh/authorized_keys << 'EOF'
restrict,port-forwarding,permitopen="10.0.0.*:22" ssh-ed25519 AAAAC3... user@client
EOF

chown -R jumpuser:jumpuser /home/jumpuser/.ssh
chmod 700 /home/jumpuser/.ssh
chmod 600 /home/jumpuser/.ssh/authorized_keys
```

## Session Recording

For audit compliance:

### Using script

```bash
# On bastion, record sessions
Match User *
    ForceCommand /usr/bin/script -f -q /var/log/ssh-sessions/%u-%Y%m%d%H%M%S.log
```

### Using asciinema

```bash
# Wrapper script
#!/bin/bash
asciinema rec --quiet --command "$SHELL" /var/log/sessions/$(whoami)-$(date +%Y%m%d%H%M%S).cast
```

## Monitoring and Alerts

### Failed Login Alerts

```bash
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
maxretry = 3
bantime = 3600
```

### Session Logging

```bash
# Check who's connected
who
w

# Recent logins
last -a

# Failed logins
lastb

# Auth logs
journalctl -u sshd | tail -100
```

## Alternatives

### Commercial Solutions

- **AWS SSM Session Manager**: Agentless, no SSH needed
- **Teleport**: SSH certificates, audit logging, MFA
- **Boundary (HashiCorp)**: Zero-trust access

### VPN

VPN provides network-level access vs SSH's application-level:

| Aspect | Jump Host | VPN |
|--------|-----------|-----|
| Access control | Per-user, per-server | Network-wide |
| Audit | Excellent | Varies |
| Performance | Good | Better for bulk |
| Setup | Simple | More complex |
| Attack surface | SSH only | VPN + services |

## Troubleshooting

### Can't Connect Through Jump

```bash
# Test direct connection to bastion
ssh bastion

# Test connectivity from bastion to internal
ssh bastion "nc -zv internal-server 22"

# Verbose output
ssh -v -J bastion internal-server
```

### Permission Denied

```bash
# Check keys are accessible
ssh-add -l

# Check config
ssh -G internal-server | grep -i proxy

# Ensure both hop keys work
ssh -i ~/.ssh/bastion_key bastion
ssh -i ~/.ssh/internal_key internal-server  # directly if possible
```

### Slow Connection

```bash
# Enable multiplexing on bastion connection
Host bastion
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
```

### Timeout

```bash
# Add keep-alive
Host bastion
    ServerAliveInterval 60
    ServerAliveCountMax 3
```
