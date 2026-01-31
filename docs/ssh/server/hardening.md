# SSH Server Hardening

## Security Layers

```
┌──────────────────────────────────────────────────────────────────────────┐
│                       SSH Security Layers                                 │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   Layer 1: Network                                                       │
│   ├─ Firewall (limit source IPs)                                        │
│   ├─ Non-standard port (optional)                                       │
│   └─ VPN/Jump host requirement                                          │
│                                                                           │
│   Layer 2: Authentication                                                │
│   ├─ Key-based only                                                     │
│   ├─ Strong algorithms                                                  │
│   └─ Multi-factor authentication                                        │
│                                                                           │
│   Layer 3: Authorization                                                 │
│   ├─ AllowUsers/AllowGroups                                             │
│   ├─ No root login                                                      │
│   └─ Restricted forwarding                                              │
│                                                                           │
│   Layer 4: Monitoring                                                    │
│   ├─ fail2ban / DenyHosts                                               │
│   ├─ Log analysis                                                       │
│   └─ Intrusion detection                                                │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Essential Hardening

### Disable Password Authentication

```bash
# /etc/ssh/sshd_config
PasswordAuthentication no
PermitEmptyPasswords no
KbdInteractiveAuthentication no
```

### Disable Root Login

```bash
PermitRootLogin no
# Or key-only
PermitRootLogin prohibit-password
```

### Limit Users

```bash
AllowUsers admin deploy
# or
AllowGroups ssh-users
```

### Limit Authentication Attempts

```bash
MaxAuthTries 3
LoginGraceTime 20
```

## Strong Cryptography

### Modern Algorithms Only

```bash
# /etc/ssh/sshd_config

# Key exchange
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512

# Ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr

# MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com

# Host key algorithms
HostKeyAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256
```

### Remove Weak Host Keys

```bash
# Remove DSA and ECDSA if not needed
rm /etc/ssh/ssh_host_dsa_key*
rm /etc/ssh/ssh_host_ecdsa_key*

# Regenerate RSA with larger size
rm /etc/ssh/ssh_host_rsa_key*
ssh-keygen -t rsa -b 4096 -f /etc/ssh/ssh_host_rsa_key -N ""

# Keep Ed25519
# ssh_host_ed25519_key already secure
```

Update sshd_config:

```bash
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
```

## Network Security

### Change Default Port

```bash
# /etc/ssh/sshd_config
Port 2222
```

!!! note "Security Through Obscurity"
    Changing the port reduces automated scans but isn't true security. Use with other measures.

### Firewall Rules

```bash
# UFW
ufw allow from 192.168.1.0/24 to any port 22
ufw deny 22

# iptables
iptables -A INPUT -p tcp -s 192.168.1.0/24 --dport 22 -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP
```

### TCP Wrappers

```bash
# /etc/hosts.allow
sshd: 192.168.1.0/24
sshd: trusted.example.com

# /etc/hosts.deny
sshd: ALL
```

### Listen on Specific Interface

```bash
# /etc/ssh/sshd_config
ListenAddress 192.168.1.100
# Not 0.0.0.0
```

## fail2ban

Automatically ban IPs with failed attempts.

### Install

```bash
apt install fail2ban
```

### Configure for SSH

```bash
# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
findtime = 300
bantime = 3600
ignoreip = 127.0.0.1/8 192.168.1.0/24
```

### Aggressive Settings

```bash
[sshd-aggressive]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 2
findtime = 3600
bantime = 86400
```

### Check Status

```bash
fail2ban-client status sshd
fail2ban-client status
```

### Unban IP

```bash
fail2ban-client set sshd unbanip 1.2.3.4
```

## Two-Factor Authentication

### Google Authenticator

Install:

```bash
apt install libpam-google-authenticator
```

Configure for each user:

```bash
google-authenticator
# Follow prompts, scan QR code
```

Configure PAM:

```bash
# /etc/pam.d/sshd
# Add at the end
auth required pam_google_authenticator.so
```

Configure SSHD:

```bash
# /etc/ssh/sshd_config
KbdInteractiveAuthentication yes
AuthenticationMethods publickey,keyboard-interactive
UsePAM yes
```

### YubiKey

```bash
# Install
apt install libpam-yubico

# Configure PAM
# /etc/pam.d/sshd
auth required pam_yubico.so id=XXXX
```

## Chroot SFTP Users

Restrict SFTP users to their directory.

### Setup

```bash
# Create group
groupadd sftponly

# Add user
useradd -g sftponly -s /usr/sbin/nologin sftpuser

# Create directory structure
mkdir -p /data/sftp/sftpuser/files
chown root:root /data/sftp/sftpuser
chmod 755 /data/sftp/sftpuser
chown sftpuser:sftponly /data/sftp/sftpuser/files
```

### sshd_config

```bash
Subsystem sftp internal-sftp

Match Group sftponly
    ChrootDirectory /data/sftp/%u
    ForceCommand internal-sftp
    AllowTcpForwarding no
    X11Forwarding no
    PermitTunnel no
```

## Restrict Forwarding

### Disable All Forwarding

```bash
AllowTcpForwarding no
AllowAgentForwarding no
AllowStreamLocalForwarding no
X11Forwarding no
PermitTunnel no
GatewayPorts no
```

### Allow for Specific Users

```bash
AllowTcpForwarding no

Match User developer
    AllowTcpForwarding yes
```

## Session Security

### Idle Timeout

```bash
ClientAliveInterval 300
ClientAliveCountMax 2
# Disconnects after 10 minutes idle
```

### Limit Concurrent Sessions

```bash
MaxSessions 2
```

### Limit Simultaneous Connections

```bash
MaxStartups 10:30:60
```

## Logging and Auditing

### Verbose Logging

```bash
LogLevel VERBOSE
SyslogFacility AUTH
```

### Log All Commands (auditd)

```bash
# Install auditd
apt install auditd

# Add rule for SSH sessions
auditctl -a always,exit -F arch=b64 -S execve -k ssh_commands
```

### Monitor Logs

```bash
# Real-time
tail -f /var/log/auth.log | grep sshd

# Failed logins
grep "Failed password" /var/log/auth.log

# Successful logins
grep "Accepted" /var/log/auth.log
```

## Banner and Warning

### Login Banner

```bash
# /etc/ssh/sshd_config
Banner /etc/ssh/banner.txt
```

```bash
# /etc/ssh/banner.txt
******************************************************************
*                    AUTHORIZED ACCESS ONLY                       *
*  This system is for authorized users only. All activity may be *
*  monitored and recorded. Unauthorized access is prohibited.     *
******************************************************************
```

### MOTD

```bash
# /etc/motd
Welcome to server.example.com
Last security update: 2024-01-15
```

## Port Knocking

Hide SSH until specific ports are "knocked."

### Install

```bash
apt install knockd
```

### Configure

```bash
# /etc/knockd.conf
[options]
    UseSyslog

[openSSH]
    sequence = 7000,8000,9000
    seq_timeout = 5
    command = /sbin/iptables -A INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags = syn

[closeSSH]
    sequence = 9000,8000,7000
    seq_timeout = 5
    command = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 22 -j ACCEPT
    tcpflags = syn
```

### Use

```bash
# From client
knock server.example.com 7000 8000 9000
ssh user@server.example.com
knock server.example.com 9000 8000 7000
```

## Security Checklist

### Authentication
- [ ] Password authentication disabled
- [ ] Root login disabled
- [ ] Key-based authentication only
- [ ] Strong key algorithms (Ed25519)
- [ ] MFA for privileged accounts
- [ ] AllowUsers/AllowGroups configured

### Network
- [ ] Firewall limits source IPs
- [ ] Non-standard port (optional)
- [ ] fail2ban installed
- [ ] TCP wrappers (optional)

### Cryptography
- [ ] Weak ciphers removed
- [ ] Weak MACs removed
- [ ] Weak key exchanges removed
- [ ] DSA host keys removed

### Forwarding
- [ ] Port forwarding restricted
- [ ] Agent forwarding restricted
- [ ] X11 forwarding disabled

### Logging
- [ ] Verbose logging enabled
- [ ] Logs monitored
- [ ] Audit rules in place

### Session
- [ ] Idle timeout configured
- [ ] Max sessions limited
- [ ] Login grace time reduced

## Hardened Configuration Example

```bash
# /etc/ssh/sshd_config - Hardened

# Network
Port 22
AddressFamily inet
ListenAddress 0.0.0.0

# Ciphers and algorithms
HostKey /etc/ssh/ssh_host_ed25519_key
HostKey /etc/ssh/ssh_host_rsa_key
KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,rsa-sha2-512,rsa-sha2-256

# Authentication
PermitRootLogin no
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
PasswordAuthentication no
PermitEmptyPasswords no
KbdInteractiveAuthentication no
UsePAM yes
MaxAuthTries 3
LoginGraceTime 20

# Authorization
AllowGroups ssh-users

# Sessions
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 3
MaxStartups 10:30:60

# Forwarding
AllowTcpForwarding no
AllowAgentForwarding no
X11Forwarding no
PermitTunnel no

# Misc
PrintMotd yes
PrintLastLog yes
TCPKeepAlive yes
PermitUserEnvironment no
Compression delayed

# Logging
LogLevel VERBOSE
SyslogFacility AUTH

# Banner
Banner /etc/ssh/banner.txt

# Subsystems
Subsystem sftp internal-sftp

# Admin overrides
Match Group admins
    AllowTcpForwarding yes
    AllowAgentForwarding yes
```
