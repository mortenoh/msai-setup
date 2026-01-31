# SSH Hardening

This page covers Ubuntu-specific SSH hardening. For comprehensive SSH documentation including client configuration, tunneling, and file transfer, see the [SSH Guide](../../ssh/index.md).

## SSH Configuration on Ubuntu 24.04

### Configuration File Locations

| File | Purpose |
|------|---------|
| `/etc/ssh/sshd_config` | Main server configuration |
| `/etc/ssh/sshd_config.d/*.conf` | Modular configuration (preferred) |
| `/etc/ssh/ssh_config` | Client defaults |
| `~/.ssh/config` | Per-user client config |

### Ubuntu 24.04 Defaults

Ubuntu ships with reasonably secure defaults:

```bash
# View current effective configuration
sudo sshd -T
```

Key defaults:

- Root login: `prohibit-password` (keys only)
- Password auth: `yes`
- Public key auth: `yes`
- X11 forwarding: `no`

## Hardening Configuration

### Create Drop-In Configuration

Use modular configuration for easier management:

```bash
sudo nano /etc/ssh/sshd_config.d/99-hardening.conf
```

### Recommended Settings

```bash
# /etc/ssh/sshd_config.d/99-hardening.conf
# Ubuntu 24.04 SSH Hardening

###########################################
# Authentication
###########################################

# Disable root login entirely
PermitRootLogin no

# Disable password authentication (key-only)
PasswordAuthentication no
KbdInteractiveAuthentication no

# Enable public key authentication
PubkeyAuthentication yes

# Disable empty passwords
PermitEmptyPasswords no

# Limit authentication attempts
MaxAuthTries 3

# Set authentication timeout
LoginGraceTime 60

# Disable host-based authentication
HostbasedAuthentication no
IgnoreRhosts yes

###########################################
# Protocol & Algorithms
###########################################

# Use strong key exchange
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group18-sha512,diffie-hellman-group16-sha512

# Use strong ciphers
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr

# Use strong MACs
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com,umac-128-etm@openssh.com

# Use strong host key algorithms
HostKeyAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256

###########################################
# Access Control
###########################################

# Restrict users who can login (uncomment and customize)
#AllowUsers admin developer
#AllowGroups ssh-users

# Deny specific users
#DenyUsers guest
#DenyGroups noremote

###########################################
# Security Features
###########################################

# Disable X11 forwarding
X11Forwarding no

# Disable TCP forwarding (unless needed)
AllowTcpForwarding no
AllowAgentForwarding no

# Disable stream local forwarding
AllowStreamLocalForwarding no

# Disable tunneling
PermitTunnel no

# Set strict mode for file permissions
StrictModes yes

# Disable user environment
PermitUserEnvironment no

# Disable password changes via PAM
UsePAM yes

###########################################
# Connection Settings
###########################################

# Maximum concurrent sessions
MaxSessions 3

# Maximum startups before rate limiting
MaxStartups 10:30:60

# Client alive settings (detect dead connections)
ClientAliveInterval 300
ClientAliveCountMax 2

# Limit to IPv4 only (if IPv6 not used)
#AddressFamily inet

###########################################
# Logging
###########################################

# Enable verbose logging
LogLevel VERBOSE

# Log to auth facility
SyslogFacility AUTH
```

### Apply Configuration

```bash
# Test configuration syntax
sudo sshd -t

# Restart SSH service
sudo systemctl restart ssh

# Verify service status
sudo systemctl status ssh
```

!!! danger "Test Before Disconnecting"
    Always keep your current SSH session open and test connectivity in a new terminal before closing.

## Key-Only Authentication Setup

### Generate Strong Keys

On your client machine:

```bash
# ED25519 (recommended)
ssh-keygen -t ed25519 -a 100 -C "user@machine"

# RSA 4096 (for compatibility)
ssh-keygen -t rsa -b 4096 -a 100 -C "user@machine"
```

### Deploy Public Key

```bash
# From client to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub user@server

# Or manually
cat ~/.ssh/id_ed25519.pub | ssh user@server 'mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'
```

### Test Key Authentication

```bash
# Should connect without password prompt
ssh -o PasswordAuthentication=no user@server
```

Only disable password authentication after confirming key auth works.

## Two-Factor Authentication

### Install Google Authenticator

```bash
sudo apt install libpam-google-authenticator
```

### Configure Per User

Each user runs:

```bash
google-authenticator
```

Recommended answers:
- Time-based tokens: yes
- Update .google_authenticator: yes
- Disallow multiple uses: yes
- Increase time skew: no
- Rate limiting: yes

### Enable in PAM

Edit `/etc/pam.d/sshd`:

```bash
# Add after @include common-auth
auth required pam_google_authenticator.so
```

### Update SSH Config

In `/etc/ssh/sshd_config.d/99-hardening.conf`:

```bash
# Enable challenge-response
KbdInteractiveAuthentication yes

# Require key + 2FA
AuthenticationMethods publickey,keyboard-interactive
```

Restart SSH:

```bash
sudo systemctl restart ssh
```

## Port Change (Optional)

Changing the SSH port reduces automated scanning noise but is not a strong security measure.

```bash
# In /etc/ssh/sshd_config.d/99-hardening.conf
Port 2222

# Update firewall
sudo ufw allow 2222/tcp
sudo ufw delete allow ssh
sudo ufw reload

# Restart SSH
sudo systemctl restart ssh
```

Connect with:

```bash
ssh -p 2222 user@server
```

## Fail2ban Integration

Fail2ban protects SSH from brute force attacks. See [Fail2ban](fail2ban.md) for full configuration.

### Quick Setup

```bash
# Install
sudo apt install fail2ban

# Create SSH jail config
sudo nano /etc/fail2ban/jail.local
```

```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h
findtime = 10m
```

```bash
# Start fail2ban
sudo systemctl enable --now fail2ban

# Check status
sudo fail2ban-client status sshd
```

## SSH Key Management

### Authorized Keys Best Practices

Configure key restrictions in `~/.ssh/authorized_keys`:

```bash
# Restrict commands
command="/usr/bin/rsync" ssh-ed25519 AAAA... backup-key

# Restrict source IP
from="192.168.1.0/24" ssh-ed25519 AAAA... internal-key

# Multiple restrictions
from="10.0.0.5",command="/usr/local/bin/deploy",no-pty,no-X11-forwarding ssh-ed25519 AAAA... deploy-key
```

### Key Restriction Options

| Option | Effect |
|--------|--------|
| `command="..."` | Only run this command |
| `from="..."` | Restrict source IPs |
| `no-port-forwarding` | Disable port forwarding |
| `no-X11-forwarding` | Disable X11 forwarding |
| `no-agent-forwarding` | Disable agent forwarding |
| `no-pty` | No interactive shell |
| `environment="..."` | Set environment variable |

### Revoke Keys

```bash
# Remove a key from authorized_keys
# Edit and delete the line
nano ~/.ssh/authorized_keys

# Or use sed
sed -i '/key-comment-to-remove/d' ~/.ssh/authorized_keys
```

## Certificate-Based Authentication

For larger deployments, SSH certificates scale better than individual keys.

### Create CA

```bash
# Generate CA key (keep this VERY secure)
ssh-keygen -t ed25519 -f /etc/ssh/ca_key -C "SSH CA"
```

### Configure Server to Trust CA

```bash
# Copy CA public key to server
echo "TrustedUserCAKeys /etc/ssh/ca_key.pub" | sudo tee -a /etc/ssh/sshd_config.d/99-ca.conf

# Copy the CA public key
sudo cp ca_key.pub /etc/ssh/ca_key.pub

sudo systemctl restart ssh
```

### Sign User Keys

```bash
# Sign a user's key (valid 1 week)
ssh-keygen -s /etc/ssh/ca_key -I user@domain -n username -V +1w user_key.pub

# Result: user_key-cert.pub
```

## Logging and Auditing

### Enhanced Logging

In `/etc/ssh/sshd_config.d/99-hardening.conf`:

```bash
LogLevel VERBOSE
```

### View SSH Logs

```bash
# Real-time
sudo tail -f /var/log/auth.log | grep sshd

# With journalctl
sudo journalctl -u ssh -f

# Failed logins
sudo grep "Failed password" /var/log/auth.log

# Successful logins
sudo grep "Accepted" /var/log/auth.log

# All SSH activity today
sudo journalctl -u ssh --since today
```

### Monitor with auditd

Add audit rules for SSH:

```bash
# In /etc/audit/rules.d/ssh.rules
-w /etc/ssh/sshd_config -p wa -k sshd_config
-w /etc/ssh/sshd_config.d/ -p wa -k sshd_config
-w /root/.ssh/ -p wa -k root_ssh
```

## Verification

### Security Check Script

```bash
#!/bin/bash
echo "=== SSH Security Check ==="

echo -e "\n--- Configuration ---"
sudo sshd -T | grep -E "^(permitrootlogin|passwordauthentication|pubkeyauthentication|x11forwarding|allowtcpforwarding)"

echo -e "\n--- Host Keys ---"
ls -la /etc/ssh/ssh_host_*_key

echo -e "\n--- Listening ---"
sudo ss -tlnp | grep sshd

echo -e "\n--- Failed Logins (24h) ---"
sudo grep "Failed password" /var/log/auth.log 2>/dev/null | tail -5

echo -e "\n--- Fail2ban Status ---"
sudo fail2ban-client status sshd 2>/dev/null || echo "Not installed"
```

### Test Configuration

```bash
# Test syntax
sudo sshd -t

# Test specific settings
sudo sshd -T | grep <setting>

# Verbose connection test
ssh -v user@server
```

## Quick Reference

### Essential Commands

```bash
# Test config
sudo sshd -t

# Restart
sudo systemctl restart ssh

# Status
sudo systemctl status ssh

# View effective config
sudo sshd -T

# Generate key
ssh-keygen -t ed25519

# Copy key
ssh-copy-id user@server

# View logs
sudo journalctl -u ssh -f
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/ssh/sshd_config | Main config |
| /etc/ssh/sshd_config.d/*.conf | Drop-in configs |
| ~/.ssh/authorized_keys | Allowed public keys |
| ~/.ssh/known_hosts | Known server keys |
| /etc/ssh/ssh_host_*_key | Server host keys |

## Further Reading

For comprehensive SSH coverage, see the [SSH Guide](../../ssh/index.md):

- [SSH Keys](../../ssh/fundamentals/keys.md)
- [SSH Server Configuration](../../ssh/server/configuration.md)
- [SSH Server Hardening](../../ssh/server/hardening.md)

## Next Steps

Continue to [AppArmor](apparmor.md) to implement mandatory access control for applications.
