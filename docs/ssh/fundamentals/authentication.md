# SSH Authentication

## Authentication Methods

SSH supports multiple authentication methods, often used in combination.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                      Authentication Flow                                  │
│                                                                           │
│   Client                                              Server              │
│     │                                                   │                 │
│     │────────── Request Authentication ────────────────▶│                 │
│     │                                                   │                 │
│     │◀───────── Available Methods ─────────────────────│                 │
│     │          (publickey, password, keyboard)          │                 │
│     │                                                   │                 │
│     │────────── Try: Public Key ───────────────────────▶│                 │
│     │◀──────── Challenge ──────────────────────────────│                 │
│     │────────── Signed Response ───────────────────────▶│                 │
│     │                                                   │                 │
│     │◀──────── Success / Partial Success ──────────────│                 │
│     │          (may require additional auth)            │                 │
│     │                                                   │                 │
└──────────────────────────────────────────────────────────────────────────┘
```

## Public Key Authentication

### How It Works

1. Client offers a public key
2. Server checks if key is in `authorized_keys`
3. Server sends a challenge (random data)
4. Client signs challenge with private key
5. Server verifies signature with public key
6. Authentication succeeds

### Enable on Server

```bash
# /etc/ssh/sshd_config
PubkeyAuthentication yes
AuthorizedKeysFile .ssh/authorized_keys
```

### Client Configuration

```bash
# ~/.ssh/config
Host server
    HostName server.example.com
    User admin
    IdentityFile ~/.ssh/server_key
    IdentitiesOnly yes
```

### Advantages

- No password transmitted
- Can't be brute-forced
- Can be automated
- Fine-grained restrictions per key

## Password Authentication

### How It Works

1. Server prompts for password
2. Client sends password (over encrypted channel)
3. Server verifies against system (PAM, /etc/shadow)

### Server Configuration

```bash
# /etc/ssh/sshd_config
PasswordAuthentication yes    # Enable
# or
PasswordAuthentication no     # Disable (recommended)
```

### When to Use

- Initial setup before deploying keys
- Backup method
- Systems where key management is impractical

### Risks

- Can be brute-forced
- Password might be weak
- Password reuse across systems

## Keyboard-Interactive

### How It Works

1. Server sends prompts to client
2. Client displays prompts to user
3. User provides responses
4. Server verifies

### Use Cases

- Multi-factor authentication (MFA)
- One-time passwords (OTP)
- Challenge-response systems
- Custom authentication flows

### Server Configuration

```bash
# /etc/ssh/sshd_config
KbdInteractiveAuthentication yes
ChallengeResponseAuthentication yes  # Legacy name
```

### PAM Integration

```bash
# /etc/pam.d/sshd
auth required pam_google_authenticator.so
```

## Certificate Authentication

### How It Works

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    Certificate-Based Auth                                │
│                                                                          │
│    Certificate Authority (CA)                                           │
│    ┌─────────────────────────┐                                          │
│    │   CA Private Key        │                                          │
│    │   Signs user/host certs │                                          │
│    └───────────┬─────────────┘                                          │
│                │                                                         │
│         Signs  │  Signs                                                  │
│                ▼                                                         │
│    ┌───────────────────┐      ┌───────────────────┐                    │
│    │  User Certificate │      │  Host Certificate │                    │
│    │  (user's key +    │      │  (host's key +    │                    │
│    │   CA signature)   │      │   CA signature)   │                    │
│    └─────────┬─────────┘      └─────────┬─────────┘                    │
│              │                          │                               │
│              ▼                          ▼                               │
│         User trusts              Server trusts                          │
│         server cert              user cert                              │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Advantages

- No authorized_keys management
- Automatic expiration
- Centralized trust
- Scalable

### Create CA

```bash
# Generate CA key
ssh-keygen -t ed25519 -f /etc/ssh/ca_key -C "SSH CA"
```

### Sign User Key

```bash
ssh-keygen -s /etc/ssh/ca_key \
  -I "user@example.com" \
  -n "username" \
  -V +52w \
  user_key.pub
```

### Sign Host Key

```bash
ssh-keygen -s /etc/ssh/ca_key \
  -I "server.example.com" \
  -h \
  -n "server.example.com,server,192.168.1.100" \
  -V +52w \
  /etc/ssh/ssh_host_ed25519_key.pub
```

### Server Configuration

```bash
# /etc/ssh/sshd_config
TrustedUserCAKeys /etc/ssh/ca_key.pub
HostCertificate /etc/ssh/ssh_host_ed25519_key-cert.pub
```

### Client Configuration

```bash
# ~/.ssh/known_hosts
@cert-authority *.example.com ssh-ed25519 AAAAC3...CA_PUBLIC_KEY
```

## Multi-Factor Authentication

### Two-Factor with TOTP

Combine key + TOTP:

```bash
# Install Google Authenticator PAM
apt install libpam-google-authenticator

# Configure for user
google-authenticator

# /etc/pam.d/sshd
auth required pam_google_authenticator.so

# /etc/ssh/sshd_config
AuthenticationMethods publickey,keyboard-interactive
KbdInteractiveAuthentication yes
UsePAM yes
```

### Two-Factor with YubiKey

```bash
# /etc/ssh/sshd_config
AuthenticationMethods publickey,keyboard-interactive

# Use YubiKey for second factor via PAM
```

## Authentication Order

### Server Preference

```bash
# /etc/ssh/sshd_config
# Require both key AND password
AuthenticationMethods publickey,password

# Require key OR password
AuthenticationMethods publickey password

# Key, then if enabled, keyboard-interactive
AuthenticationMethods publickey,keyboard-interactive publickey
```

### Client Preference

```bash
# ~/.ssh/config
Host server
    PreferredAuthentications publickey,keyboard-interactive,password
```

## Per-User/Group Settings

### Match Blocks

```bash
# /etc/ssh/sshd_config

# Default settings
PasswordAuthentication no
PubkeyAuthentication yes

# Allow password for specific user
Match User tempuser
    PasswordAuthentication yes

# Restrict sftp-only users
Match Group sftponly
    ForceCommand internal-sftp
    PasswordAuthentication yes
    PubkeyAuthentication no
    AllowTcpForwarding no

# Stricter for admins
Match Group admins
    AuthenticationMethods publickey,keyboard-interactive
```

## Debugging Authentication

### Verbose Client

```bash
ssh -vvv user@host 2>&1 | grep -i auth
```

### Server Logs

```bash
# Real-time
journalctl -u sshd -f

# With debug
# /etc/ssh/sshd_config
LogLevel DEBUG3
```

### Common Issues

| Problem | Check |
|---------|-------|
| Key rejected | Permissions on ~/.ssh (700) and authorized_keys (600) |
| Password rejected | PAM configuration, account locked |
| MFA not prompting | PAM order, sshd_config settings |
| Certificate rejected | Validity period, principals, CA trust |

## Authentication Hardening

### Recommended Settings

```bash
# /etc/ssh/sshd_config

# Disable password authentication
PasswordAuthentication no
PermitEmptyPasswords no

# Enable key authentication
PubkeyAuthentication yes

# Disable root login
PermitRootLogin no
# Or only with key
PermitRootLogin prohibit-password

# Limit authentication attempts
MaxAuthTries 3

# Set authentication timeout
LoginGraceTime 30

# Require MFA for sensitive access
Match Group admins
    AuthenticationMethods publickey,keyboard-interactive
```

### Audit Checklist

- [ ] Password authentication disabled
- [ ] Root login disabled or key-only
- [ ] Strong keys deployed (Ed25519/RSA-4096)
- [ ] Unused keys removed from authorized_keys
- [ ] MFA enabled for privileged accounts
- [ ] fail2ban or similar configured
- [ ] Authentication logs monitored
