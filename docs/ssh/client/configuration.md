# SSH Client Configuration

## Configuration Files

SSH client reads configuration from multiple sources in order:

1. Command-line options (`-o Option=value`)
2. User config (`~/.ssh/config`)
3. System config (`/etc/ssh/ssh_config`)

First match wins - put specific hosts before wildcards.

## ~/.ssh/config Structure

```bash
# Global defaults (apply to all hosts)
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Specific host
Host myserver
    HostName 192.168.1.100
    User admin
    Port 22
    IdentityFile ~/.ssh/server_key

# Pattern matching
Host *.example.com
    User deploy
    IdentityFile ~/.ssh/deploy_key

# Alias for complex connection
Host jump
    HostName bastion.example.com
    User jumpuser
    IdentityFile ~/.ssh/jump_key
```

## Basic Options

### Connection Settings

```bash
Host server
    # Required
    HostName server.example.com    # IP or hostname
    User username                   # Login user

    # Optional
    Port 22                         # SSH port (default: 22)
    AddressFamily inet              # inet (IPv4), inet6 (IPv6), any
    BindAddress 192.168.1.50        # Source IP to use
    ConnectTimeout 10               # Connection timeout in seconds
```

### Authentication

```bash
Host server
    # Key-based
    IdentityFile ~/.ssh/server_key
    IdentitiesOnly yes              # Only use specified key

    # Password (if needed)
    PreferredAuthentications publickey,keyboard-interactive,password

    # Batch mode (no prompts)
    BatchMode yes
```

### Keep-Alive

```bash
Host *
    # Client sends keep-alive every 60 seconds
    ServerAliveInterval 60
    # Disconnect after 3 missed responses
    ServerAliveCountMax 3
    # TCP keep-alive (different from ServerAlive)
    TCPKeepAlive yes
```

## Host Aliases

### Simple Alias

```bash
Host web
    HostName webserver.example.com
    User webadmin
```

Use: `ssh web`

### Multiple Aliases

```bash
Host web webserver prod
    HostName webserver.example.com
    User admin
```

Use: `ssh web` or `ssh webserver` or `ssh prod`

### Pattern Matching

```bash
# Wildcard
Host *.dev.example.com
    User developer
    IdentityFile ~/.ssh/dev_key

# Negation
Host * !*.internal
    ProxyJump bastion

# Character class
Host server[0-9]
    User admin
```

## Common Configurations

### Development Server

```bash
Host dev
    HostName dev.example.com
    User developer
    IdentityFile ~/.ssh/dev_key
    ForwardAgent yes
    LocalForward 3000 localhost:3000
    LocalForward 5432 localhost:5432
```

### Production Server (Restricted)

```bash
Host prod
    HostName prod.example.com
    User deploy
    IdentityFile ~/.ssh/prod_key
    IdentitiesOnly yes
    ForwardAgent no
    ForwardX11 no
    RequestTTY no
```

### Jump Host / Bastion

```bash
Host bastion
    HostName bastion.example.com
    User jump
    IdentityFile ~/.ssh/bastion_key
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600

Host internal-*
    ProxyJump bastion
    User admin
    IdentityFile ~/.ssh/internal_key

Host internal-web
    HostName 10.0.0.10

Host internal-db
    HostName 10.0.0.20
```

Use: `ssh internal-web` (automatically jumps through bastion)

### GitHub/GitLab

```bash
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/github_key
    IdentitiesOnly yes

Host gitlab.com
    HostName gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab_key
```

### AWS EC2

```bash
Host aws-*
    User ec2-user
    IdentityFile ~/.ssh/aws_key.pem
    StrictHostKeyChecking accept-new

Host aws-web
    HostName ec2-xx-xx-xx-xx.compute.amazonaws.com

Host aws-db
    HostName ec2-yy-yy-yy-yy.compute.amazonaws.com
```

## Advanced Options

### Agent Forwarding

```bash
Host trusted-server
    ForwardAgent yes    # Forward SSH agent
```

!!! warning "Security"
    Only enable on trusted servers. A compromised server could use your forwarded agent.

### X11 Forwarding

```bash
Host workstation
    ForwardX11 yes
    ForwardX11Trusted yes    # Less secure but more compatible
```

### Compression

```bash
Host slow-connection
    Compression yes
    CompressionLevel 6    # 1-9, higher = more compression
```

### Connection Multiplexing

```bash
Host *
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
```

Create socket directory:

```bash
mkdir -p ~/.ssh/sockets
chmod 700 ~/.ssh/sockets
```

### Escape Characters

```bash
Host *
    EscapeChar ~    # Default
    # EscapeChar none  # Disable escapes
```

Escape sequences (press Enter first):
- `~.` - Disconnect
- `~^Z` - Suspend
- `~#` - List forwarded connections
- `~~` - Send literal ~

### Host Key Verification

```bash
# Strict (default, recommended)
Host *
    StrictHostKeyChecking ask

# Auto-accept new hosts (convenient but less secure)
Host trusted-network-*
    StrictHostKeyChecking accept-new

# Skip verification (dangerous!)
Host test-vm
    StrictHostKeyChecking no
    UserKnownHostsFile /dev/null
```

## Port Forwarding in Config

### Local Forward

```bash
Host dbserver
    HostName db.example.com
    # Access remote MySQL on local port
    LocalForward 3306 localhost:3306
    # Access remote web on local port
    LocalForward 8080 localhost:80
```

### Remote Forward

```bash
Host expose-local
    HostName server.example.com
    # Expose local service on remote
    RemoteForward 8080 localhost:3000
```

### Dynamic (SOCKS)

```bash
Host proxy
    HostName proxy.example.com
    DynamicForward 1080
```

## Environment

### Send Environment Variables

```bash
Host server
    SendEnv LANG LC_*
    SendEnv MY_VAR
```

Server must allow with `AcceptEnv`.

### Set Environment

```bash
Host server
    SetEnv FOO=bar
    SetEnv DEBUG=1
```

## Includes

### Include Other Config Files

```bash
# ~/.ssh/config

# Include all configs in directory
Include config.d/*

# Include specific file
Include work_config

# Conditional include
Match host *.work.com
    Include work_settings
```

### Organized Config Structure

```
~/.ssh/
├── config           # Main config with includes
├── config.d/
│   ├── personal     # Personal servers
│   ├── work         # Work servers
│   └── cloud        # Cloud providers
└── keys/
    ├── personal_ed25519
    ├── work_ed25519
    └── aws.pem
```

## Complete Example

```bash
# ~/.ssh/config

# ============================================
# Global Defaults
# ============================================
Host *
    # Security
    IdentitiesOnly yes
    HashKnownHosts yes

    # Performance
    ControlMaster auto
    ControlPath ~/.ssh/sockets/%r@%h-%p
    ControlPersist 600
    Compression yes

    # Keep-alive
    ServerAliveInterval 60
    ServerAliveCountMax 3

    # Convenience
    AddKeysToAgent yes

# ============================================
# Personal
# ============================================
Host home
    HostName home.example.com
    User me
    IdentityFile ~/.ssh/personal_ed25519
    Port 2222

Host pi
    HostName 192.168.1.50
    User pi
    IdentityFile ~/.ssh/personal_ed25519

# ============================================
# Work
# ============================================
Host work-bastion
    HostName bastion.work.com
    User admin
    IdentityFile ~/.ssh/work_ed25519

Host work-*
    ProxyJump work-bastion
    User deploy
    IdentityFile ~/.ssh/work_ed25519

Host work-web
    HostName 10.0.1.10

Host work-api
    HostName 10.0.1.20

Host work-db
    HostName 10.0.1.30
    LocalForward 5432 localhost:5432

# ============================================
# Cloud
# ============================================
Host aws-*
    User ec2-user
    IdentityFile ~/.ssh/aws.pem
    StrictHostKeyChecking accept-new

Host gcp-*
    User admin
    IdentityFile ~/.ssh/gcp_ed25519

# ============================================
# Git
# ============================================
Host github.com
    User git
    IdentityFile ~/.ssh/github_ed25519

Host gitlab.com
    User git
    IdentityFile ~/.ssh/gitlab_ed25519
```

## Debugging Configuration

### Test Config Parsing

```bash
ssh -G hostname
```

Shows resolved configuration for hostname.

### Verbose Connection

```bash
ssh -vvv hostname
```

### Check Which Config Applied

```bash
ssh -G myhost | grep -E "^(hostname|user|identityfile)"
```
