# SSH Protocol

## Overview

SSH (Secure Shell) is a cryptographic network protocol for secure communication over untrusted networks. It provides:

- **Confidentiality** - Encrypted communication
- **Integrity** - Tamper detection
- **Authentication** - Identity verification

## Protocol Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SSH Protocol Stack                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Connection Protocol                           │   │
│   │              (Channels, Sessions, Forwarding)                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                   User Authentication Protocol                   │   │
│   │              (Password, Public Key, Keyboard)                    │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                    Transport Protocol                            │   │
│   │         (Key Exchange, Encryption, MAC, Compression)             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                  │                                       │
│   ┌─────────────────────────────────────────────────────────────────┐   │
│   │                         TCP/IP                                   │   │
│   │                    (Port 22 default)                             │   │
│   └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Transport Layer

Handles:
- Initial key exchange
- Server authentication
- Encryption, MAC, compression negotiation
- Key re-exchange

### Authentication Layer

Handles:
- Client authentication to server
- Multiple authentication methods
- Authentication banners

### Connection Layer

Handles:
- Multiple channels over single connection
- Interactive sessions
- Port forwarding
- X11 forwarding

## Connection Flow

```
Client                                          Server
   │                                               │
   │──────────── TCP Connect (port 22) ───────────▶│
   │                                               │
   │◀─────────── Protocol Version Exchange ────────│
   │              SSH-2.0-OpenSSH_8.9              │
   │                                               │
   │◀──────────── Key Exchange Init ───────────────│
   │              (algorithms, keys)               │
   │                                               │
   │────────────── Key Exchange ───────────────────│
   │              (Diffie-Hellman)                 │
   │                                               │
   │◀─────────── Server Host Key ──────────────────│
   │              (verify fingerprint)             │
   │                                               │
   │═══════════ Encrypted Channel Established ═════│
   │                                               │
   │────────────── User Authentication ────────────│
   │              (key, password, etc.)            │
   │                                               │
   │◀─────────── Authentication Success ───────────│
   │                                               │
   │────────────── Channel Open ───────────────────│
   │              (session, forwarding)            │
   │                                               │
   │◀══════════════ Interactive Session ══════════▶│
   │                                               │
```

## Key Exchange

Key exchange establishes a shared secret without transmitting it.

### Diffie-Hellman

```
1. Client and Server agree on parameters (p, g)
2. Client generates private a, sends A = g^a mod p
3. Server generates private b, sends B = g^b mod p
4. Both compute shared secret: K = B^a = A^b mod p
5. Neither a nor b was ever transmitted
```

### Modern Algorithms

| Algorithm | Security | Notes |
|-----------|----------|-------|
| curve25519-sha256 | Excellent | Recommended, fast |
| ecdh-sha2-nistp256 | Good | NIST curve |
| diffie-hellman-group16-sha512 | Good | Classical DH |
| diffie-hellman-group14-sha256 | Adequate | Older compatibility |

## Encryption

After key exchange, all data is encrypted.

### Symmetric Ciphers

| Cipher | Security | Speed | Notes |
|--------|----------|-------|-------|
| chacha20-poly1305 | Excellent | Fast | Recommended |
| aes256-gcm | Excellent | Fast | Hardware acceleration |
| aes128-gcm | Good | Fastest | Adequate for most |
| aes256-ctr | Good | Good | Older compatibility |

### How It Works

```
Plaintext ──▶ [Cipher + Session Key] ──▶ Ciphertext
                                              │
                                              ▼
                                         [Network]
                                              │
                                              ▼
Plaintext ◀── [Cipher + Session Key] ◀── Ciphertext
```

## Message Authentication (MAC)

MACs ensure data hasn't been tampered with.

### MAC Algorithms

| Algorithm | Security | Notes |
|-----------|----------|-------|
| hmac-sha2-512-etm | Excellent | Recommended |
| hmac-sha2-256-etm | Excellent | Good default |
| umac-128-etm | Good | Faster |

### Encrypt-then-MAC (ETM)

```
1. Encrypt the plaintext
2. Calculate MAC over ciphertext
3. Send ciphertext + MAC

Receiver:
1. Verify MAC (reject if invalid)
2. Decrypt ciphertext
```

## Host Keys

Server host keys prove the server's identity.

### Key Types

| Type | Key Size | Notes |
|------|----------|-------|
| Ed25519 | 256-bit | Recommended, fast |
| ECDSA | 256/384/521-bit | Good |
| RSA | 2048-4096 bit | Compatible, larger |
| DSA | 1024-bit | Deprecated |

### First Connection (TOFU)

Trust On First Use:

```
$ ssh server.example.com
The authenticity of host 'server.example.com (192.168.1.100)' can't be established.
ED25519 key fingerprint is SHA256:abcd1234...
Are you sure you want to continue connecting (yes/no/[fingerprint])?
```

- First time: verify fingerprint out-of-band
- Subsequent: SSH verifies automatically
- Change detected: **WARNING** (possible MITM attack)

### Known Hosts

Stored in `~/.ssh/known_hosts`:

```
server.example.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...
192.168.1.100 ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAI...
```

## Authentication Methods

### Public Key (Recommended)

```
1. Client has private key (secret)
2. Server has public key (in authorized_keys)
3. Client proves it has private key (without revealing it)
4. Server grants access
```

### Password

```
1. Client sends username
2. Server requests password
3. Client sends password (encrypted)
4. Server verifies against system
```

### Keyboard-Interactive

For multi-factor authentication:

```
1. Server sends prompts
2. Client responds
3. Can include OTP, challenges, etc.
```

### Certificate-Based

```
1. CA signs user/host keys
2. Server/client trusts CA
3. No need for authorized_keys/known_hosts
```

## Channels

SSH multiplexes multiple channels over one connection.

### Channel Types

| Type | Purpose |
|------|---------|
| session | Shell, command execution |
| direct-tcpip | Local port forwarding |
| forwarded-tcpip | Remote port forwarding |
| x11 | X11 forwarding |

### Multiplexing

```
┌──────────────────────────────────────────────────────────┐
│                   SSH Connection                          │
│                                                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │  Channel 0  │ │  Channel 1  │ │  Channel 2  │        │
│  │   (shell)   │ │ (forwarded) │ │   (sftp)    │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

## SSH Versions

### SSH-1 (Deprecated)

- Released 1995
- Security vulnerabilities
- **Do not use**

### SSH-2 (Current)

- Released 2006 (RFC 4251-4256)
- Completely redesigned
- All modern implementations

### Protocol Negotiation

```
SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.1
│     │   │
│     │   └── Implementation details
│     └────── Implementation name
└──────────── Protocol version
```

## Security Considerations

### Perfect Forward Secrecy (PFS)

Even if long-term keys are compromised, past sessions remain secure because:
- Session keys are ephemeral
- Derived from Diffie-Hellman exchange
- Destroyed after session ends

### Defense in Depth

```
┌─────────────────────────────────────────────────────────┐
│                    Security Layers                       │
├─────────────────────────────────────────────────────────┤
│  Network        │ Firewall, fail2ban, port knocking     │
│  Transport      │ Encryption, MAC, key exchange         │
│  Authentication │ Keys, MFA, certificates               │
│  Authorization  │ AllowUsers, sudo, SELinux             │
│  Audit          │ Logging, monitoring, alerts           │
└─────────────────────────────────────────────────────────┘
```

## Checking Connection Security

### View Negotiated Algorithms

```bash
ssh -vv user@host 2>&1 | grep "kex:"
```

Output shows:
- Key exchange algorithm
- Host key type
- Cipher
- MAC

### Check Server Key

```bash
ssh-keyscan -t ed25519 hostname
```

### Verify Fingerprint

```bash
ssh-keygen -lf /etc/ssh/ssh_host_ed25519_key.pub
```
