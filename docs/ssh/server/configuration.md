# SSH Server Configuration

## Configuration File

The SSH server (sshd) is configured via `/etc/ssh/sshd_config`.

### Syntax

```bash
# Comments start with #
Keyword value
Keyword value1 value2    # Multiple values

# Conditional blocks
Match User admin
    PermitRootLogin no
```

### Include Files

```bash
# /etc/ssh/sshd_config
Include /etc/ssh/sshd_config.d/*.conf
```

### Test Configuration

```bash
sshd -t
# No output = valid

sshd -T
# Print effective configuration
```

## Essential Settings

### Listen Address and Port

```bash
# Default
Port 22

# Custom port
Port 2222

# Multiple ports
Port 22
Port 2222

# Specific interface
ListenAddress 0.0.0.0:22
ListenAddress 192.168.1.100:22
```

### Protocol Version

```bash
# SSH-2 only (SSH-1 is deprecated and insecure)
Protocol 2
```

### Address Family

```bash
AddressFamily any       # IPv4 and IPv6
AddressFamily inet      # IPv4 only
AddressFamily inet6     # IPv6 only
```

## Authentication Settings

### Password Authentication

```bash
# Enable (less secure)
PasswordAuthentication yes

# Disable (recommended)
PasswordAuthentication no

# Empty passwords (never enable)
PermitEmptyPasswords no
```

### Public Key Authentication

```bash
# Enable (recommended)
PubkeyAuthentication yes

# Authorized keys location
AuthorizedKeysFile .ssh/authorized_keys

# Multiple locations
AuthorizedKeysFile .ssh/authorized_keys .ssh/authorized_keys2
```

### Root Login

```bash
# Completely disable (recommended)
PermitRootLogin no

# Key only
PermitRootLogin prohibit-password

# Allow (not recommended)
PermitRootLogin yes
```

### Keyboard-Interactive

```bash
# For PAM, OTP, etc.
KbdInteractiveAuthentication yes
```

### Authentication Attempts

```bash
# Max attempts before disconnect
MaxAuthTries 3

# Time to complete authentication
LoginGraceTime 30
```

### Authentication Methods

```bash
# Require key AND password
AuthenticationMethods publickey,password

# Require key OR password
AuthenticationMethods publickey password

# Key then keyboard-interactive (MFA)
AuthenticationMethods publickey,keyboard-interactive
```

## Access Control

### Allow/Deny Users

```bash
# Allow only specific users
AllowUsers alice bob charlie

# Allow with patterns
AllowUsers *@192.168.1.* admin

# Deny specific users
DenyUsers guest nobody
```

### Allow/Deny Groups

```bash
# Allow only members of groups
AllowGroups ssh-users admins

# Deny groups
DenyGroups notssh
```

!!! note "Processing Order"
    Order: DenyUsers → AllowUsers → DenyGroups → AllowGroups

## Session Settings

### Max Sessions

```bash
# Sessions per connection
MaxSessions 10

# Simultaneous connections per user
MaxStartups 10:30:60
# Start:rate:full
# Start refusing after 10, randomly refuse 30% after 30, refuse all after 60
```

### Idle Timeout

```bash
# Server sends keep-alive
ClientAliveInterval 300
ClientAliveCountMax 3
# Disconnect after 15 minutes of no response (300 * 3)
```

### TCP Keep-Alive

```bash
TCPKeepAlive yes
```

## Forwarding Settings

### Port Forwarding

```bash
# Allow all forwarding (default)
AllowTcpForwarding yes

# Disable all
AllowTcpForwarding no

# Local only
AllowTcpForwarding local

# Remote only
AllowTcpForwarding remote
```

### Specific Ports

```bash
# Allow forwarding to specific addresses
PermitOpen host1:port1 host2:port2

# Allow any
PermitOpen any

# Deny all
PermitOpen none
```

### Gateway Ports

Allow remote hosts to connect to forwarded ports:

```bash
GatewayPorts no         # Only localhost (default)
GatewayPorts yes        # All interfaces
GatewayPorts clientspecified  # Client chooses
```

### Agent Forwarding

```bash
AllowAgentForwarding yes    # Default
AllowAgentForwarding no     # Disable
```

### X11 Forwarding

```bash
X11Forwarding yes
X11DisplayOffset 10
X11UseLocalhost yes
```

### Stream Local Forwarding

```bash
AllowStreamLocalForwarding yes
```

## SFTP Configuration

### Enable SFTP

```bash
Subsystem sftp /usr/lib/openssh/sftp-server
```

### Internal SFTP (For Chroot)

```bash
Subsystem sftp internal-sftp
```

### SFTP-Only User

```bash
Match User sftpuser
    ForceCommand internal-sftp
    ChrootDirectory /home/%u
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
```

## Logging

### Log Level

```bash
LogLevel INFO           # Default
LogLevel VERBOSE        # More detail
LogLevel DEBUG          # Maximum (for troubleshooting)
```

### Log Facility

```bash
SyslogFacility AUTH     # Default
SyslogFacility AUTHPRIV # Private auth messages
```

### View Logs

```bash
journalctl -u sshd
# or
tail -f /var/log/auth.log
```

## Host Keys

### Key Files

```bash
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
HostKey /etc/ssh/ssh_host_ecdsa_key
```

### Generate New Keys

```bash
ssh-keygen -t ed25519 -f /etc/ssh/ssh_host_ed25519_key -N ""
ssh-keygen -t rsa -b 4096 -f /etc/ssh/ssh_host_rsa_key -N ""
```

### Key Algorithms

```bash
# Prefer Ed25519, then RSA
HostKeyAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256
```

## Cryptographic Settings

### Key Exchange

```bash
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
```

### Ciphers

```bash
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
```

### MACs

```bash
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

## Match Blocks

Conditional configuration based on criteria.

### Match User

```bash
Match User admin
    PasswordAuthentication no
    AuthenticationMethods publickey,keyboard-interactive

Match User sftp*
    ForceCommand internal-sftp
    ChrootDirectory /data/sftp/%u
```

### Match Group

```bash
Match Group developers
    AllowTcpForwarding yes

Match Group contractors
    AllowTcpForwarding no
    PermitTTY yes
```

### Match Address

```bash
# Internal network
Match Address 192.168.0.0/16
    PasswordAuthentication yes

# External
Match Address *,!192.168.0.0/16
    PasswordAuthentication no
    MaxAuthTries 2
```

### Match Host

```bash
Match Host *.internal.example.com
    PermitRootLogin yes
```

### Combined Match

```bash
Match User admin Address 10.0.0.0/8
    PermitRootLogin yes
```

## Applying Changes

### Restart Service

```bash
systemctl restart sshd
```

### Reload Configuration

```bash
systemctl reload sshd
# or
kill -HUP $(pgrep -f "sshd -D")
```

!!! warning "Keep a Session Open"
    When changing sshd config remotely, keep an existing session open. If the new config has errors, you won't be locked out.

## Verification

### Test Config Syntax

```bash
sshd -t
```

### Show Effective Config

```bash
sshd -T
```

### Show Config for User

```bash
sshd -T -C user=admin,host=192.168.1.100
```

## Complete Secure Example

```bash
# /etc/ssh/sshd_config

# Network
Port 22
AddressFamily any
ListenAddress 0.0.0.0

# Host keys
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key

# Cryptography
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
PasswordAuthentication no
PermitEmptyPasswords no
KbdInteractiveAuthentication no
MaxAuthTries 3
LoginGraceTime 30

# Authorization
AllowGroups ssh-users admins

# Session
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 5

# Forwarding
AllowTcpForwarding no
AllowAgentForwarding no
X11Forwarding no
PermitTunnel no

# Logging
LogLevel VERBOSE
SyslogFacility AUTH

# SFTP
Subsystem sftp internal-sftp

# Admin access (more permissive)
Match Group admins
    AllowTcpForwarding yes
    AllowAgentForwarding yes

# SFTP-only users
Match Group sftponly
    ForceCommand internal-sftp
    ChrootDirectory /data/sftp/%u
    AllowTcpForwarding no
```
