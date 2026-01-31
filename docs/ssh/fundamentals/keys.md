# SSH Keys

## Overview

SSH keys provide stronger authentication than passwords through public-key cryptography.

```
┌──────────────────────────────────────────────────────────────────────┐
│                        Key-Based Authentication                       │
│                                                                       │
│   Your Computer                              Remote Server            │
│   ┌─────────────────┐                       ┌─────────────────┐      │
│   │                 │                       │                 │      │
│   │  Private Key    │    Challenge/Response │  Public Key     │      │
│   │  (id_ed25519)   │◀─────────────────────▶│(authorized_keys)│      │
│   │  🔐 SECRET      │                       │  🔓 Shareable   │      │
│   │                 │                       │                 │      │
│   └─────────────────┘                       └─────────────────┘      │
│                                                                       │
└──────────────────────────────────────────────────────────────────────┘
```

## Key Types

### Ed25519 (Recommended)

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

- **Security**: Excellent (256-bit)
- **Key size**: 68 characters (public)
- **Speed**: Fastest
- **Compatibility**: OpenSSH 6.5+ (2014)

### RSA

```bash
ssh-keygen -t rsa -b 4096 -C "your@email.com"
```

- **Security**: Good (with 4096-bit)
- **Key size**: Large
- **Speed**: Slower
- **Compatibility**: Universal

### ECDSA

```bash
ssh-keygen -t ecdsa -b 521 -C "your@email.com"
```

- **Security**: Good
- **Key size**: Medium
- **Speed**: Fast
- **Compatibility**: OpenSSH 5.7+ (2011)

### Comparison

| Type | Recommended | Key Size | Use Case |
|------|-------------|----------|----------|
| Ed25519 | ✅ Yes | 256-bit fixed | Default choice |
| RSA | ⚠️ 4096-bit only | 2048-4096 bit | Legacy compatibility |
| ECDSA | ⚠️ Maybe | 256/384/521 bit | Specific requirements |
| DSA | ❌ No | 1024-bit | Deprecated |

## Generating Keys

### Basic Generation

```bash
ssh-keygen -t ed25519 -C "me@example.com"
```

Output:

```
Generating public/private ed25519 key pair.
Enter file in which to save the key (/home/user/.ssh/id_ed25519):
Enter passphrase (empty for no passphrase):
Enter same passphrase again:
Your identification has been saved in /home/user/.ssh/id_ed25519
Your public key has been saved in /home/user/.ssh/id_ed25519.pub
The key fingerprint is:
SHA256:abcd1234efgh5678ijkl9012mnop3456 me@example.com
```

### With Custom Filename

```bash
ssh-keygen -t ed25519 -f ~/.ssh/myserver_ed25519 -C "myserver"
```

### With Specific Options

```bash
ssh-keygen -t ed25519 \
  -f ~/.ssh/work_key \
  -C "work laptop $(date +%Y-%m-%d)" \
  -a 100  # KDF rounds for passphrase
```

### RSA with Strong Settings

```bash
ssh-keygen -t rsa -b 4096 -o -a 100 -C "comment"
```

- `-b 4096`: Key size
- `-o`: New OpenSSH format
- `-a 100`: KDF rounds

## Key Files

### Private Key

```bash
~/.ssh/id_ed25519
```

- **NEVER share**
- Permissions: `600` (owner read/write only)
- Optionally encrypted with passphrase

### Public Key

```bash
~/.ssh/id_ed25519.pub
```

- Safe to share
- Add to servers' `authorized_keys`
- Format: `type key comment`

Example:

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIHJrDq... me@example.com
```

## Passphrase Protection

### Why Use a Passphrase

- Protects key if file is stolen
- Defense in depth
- Required for high-security environments

### Adding Passphrase to Existing Key

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
```

### Changing Passphrase

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
# Enter old passphrase
# Enter new passphrase
```

### Removing Passphrase

```bash
ssh-keygen -p -f ~/.ssh/id_ed25519
# Enter old passphrase
# Press Enter for new (empty) passphrase
```

## Deploying Public Keys

### ssh-copy-id (Easiest)

```bash
ssh-copy-id user@hostname
```

This:
1. Connects to server (may ask for password)
2. Creates `~/.ssh` if needed
3. Appends public key to `authorized_keys`
4. Sets correct permissions

### With Specific Key

```bash
ssh-copy-id -i ~/.ssh/mykey.pub user@hostname
```

### Manual Method

```bash
# Copy public key content
cat ~/.ssh/id_ed25519.pub

# On server, add to authorized_keys
echo "ssh-ed25519 AAAAC3..." >> ~/.ssh/authorized_keys

# Set permissions
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
```

### One-Liner

```bash
cat ~/.ssh/id_ed25519.pub | ssh user@host "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

## Multiple Keys

### Different Keys for Different Servers

```bash
# Generate keys
ssh-keygen -t ed25519 -f ~/.ssh/work_key
ssh-keygen -t ed25519 -f ~/.ssh/personal_key
ssh-keygen -t ed25519 -f ~/.ssh/github_key
```

### Configure in ~/.ssh/config

```
Host work
    HostName work.example.com
    IdentityFile ~/.ssh/work_key

Host personal
    HostName personal.example.com
    IdentityFile ~/.ssh/personal_key

Host github.com
    IdentityFile ~/.ssh/github_key
```

## Key Fingerprints

### View Fingerprint

```bash
ssh-keygen -lf ~/.ssh/id_ed25519.pub
```

Output:

```
256 SHA256:abcd1234efgh5678ijkl9012mnop3456 me@example.com (ED25519)
```

### Different Formats

```bash
# SHA256 (default)
ssh-keygen -lf ~/.ssh/id_ed25519.pub

# MD5 (legacy)
ssh-keygen -lf ~/.ssh/id_ed25519.pub -E md5
```

### Verify Server Fingerprint

```bash
# Get server's fingerprint
ssh-keyscan -t ed25519 hostname | ssh-keygen -lf -
```

## Authorized Keys Options

The `authorized_keys` file supports options per key:

```bash
# ~/.ssh/authorized_keys

# Basic entry
ssh-ed25519 AAAAC3... user@host

# With options
command="/usr/bin/backup" ssh-ed25519 AAAAC3... backup-key
from="192.168.1.*" ssh-ed25519 AAAAC3... internal-key
no-port-forwarding,no-agent-forwarding ssh-ed25519 AAAAC3... restricted-key
```

### Common Options

| Option | Effect |
|--------|--------|
| `command="cmd"` | Only run this command |
| `from="pattern"` | Restrict source IPs |
| `no-port-forwarding` | Disable tunneling |
| `no-agent-forwarding` | Disable agent forwarding |
| `no-X11-forwarding` | Disable X11 forwarding |
| `no-pty` | No terminal allocation |
| `environment="VAR=value"` | Set environment variable |
| `expiry-time="YYYYMMDD"` | Key expiration |

### Restricted Key Example

```bash
from="10.0.0.0/8",command="/usr/local/bin/backup-script",no-port-forwarding,no-X11-forwarding,no-agent-forwarding ssh-ed25519 AAAAC3... backup-server
```

## Key Management Best Practices

### Do

- ✅ Use Ed25519 for new keys
- ✅ Use passphrases on private keys
- ✅ Use ssh-agent to avoid retyping
- ✅ Use different keys for different purposes
- ✅ Regularly audit authorized_keys
- ✅ Rotate keys periodically

### Don't

- ❌ Share private keys
- ❌ Use DSA keys
- ❌ Use RSA keys under 2048 bits
- ❌ Store private keys in repos
- ❌ Use the same key everywhere
- ❌ Leave orphaned keys on servers

## Troubleshooting Keys

### Check Permissions

```bash
ls -la ~/.ssh/
# drwx------  .ssh/
# -rw-------  id_ed25519
# -rw-r--r--  id_ed25519.pub
# -rw-------  authorized_keys
```

### Fix Permissions

```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub
chmod 600 ~/.ssh/authorized_keys
```

### Debug Connection

```bash
ssh -vvv user@host 2>&1 | grep -i key
```

### Test Key

```bash
ssh -i ~/.ssh/mykey -o BatchMode=yes user@host echo "Key works"
```

### List Keys in Agent

```bash
ssh-add -l
```
