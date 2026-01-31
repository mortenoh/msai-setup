# SSH Guide

## Overview

SSH (Secure Shell) is the foundation of secure remote administration. This guide covers everything from basic connections to advanced tunneling and automation.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                           SSH Capabilities                                │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│   Remote Shell          File Transfer         Port Forwarding            │
│   ┌─────────┐           ┌─────────┐          ┌─────────┐                │
│   │   ssh   │           │scp/sftp │          │ Tunnels │                │
│   │ user@   │           │ rsync   │          │ Local   │                │
│   │ host    │           │         │          │ Remote  │                │
│   └─────────┘           └─────────┘          │ Dynamic │                │
│                                              └─────────┘                │
│                                                                           │
│   Key Auth              Jump Hosts            Automation                 │
│   ┌─────────┐           ┌─────────┐          ┌─────────┐                │
│   │ Ed25519 │           │ Proxy   │          │ Scripts │                │
│   │ RSA     │           │ Jump    │          │ Ansible │                │
│   │ Agent   │           │ Bastion │          │ CI/CD   │                │
│   └─────────┘           └─────────┘          └─────────┘                │
│                                                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## What You'll Learn

### :material-school: Fundamentals
- How SSH works (protocol, encryption, authentication)
- Key concepts and terminology
- Security model and trust

### :material-laptop: Client Configuration
- SSH client setup and `~/.ssh/config`
- Key generation and management
- SSH agent for key handling
- Connection options and shortcuts

### :material-server: Server Configuration
- OpenSSH server (`sshd`) setup
- Authentication methods
- Security hardening
- Access control

### :material-file-sync: File Transfer
- SCP for simple copies
- SFTP for interactive transfers
- Rsync over SSH for efficient sync
- Large file handling

### :material-tunnel: Tunneling & Port Forwarding
- Local port forwarding
- Remote port forwarding
- Dynamic (SOCKS) proxy
- Jump hosts and bastion servers
- VPN-like configurations

### :material-cog: Advanced Topics
- Connection multiplexing
- SSH certificates
- Two-factor authentication
- Automation and scripting

## Quick Start

### Connect to a Server

```bash
ssh user@hostname
ssh -p 2222 user@hostname    # Custom port
```

### Generate SSH Key

```bash
ssh-keygen -t ed25519 -C "your@email.com"
```

### Copy Key to Server

```bash
ssh-copy-id user@hostname
```

### Copy Files

```bash
# To remote
scp file.txt user@host:/path/

# From remote
scp user@host:/path/file.txt ./

# Directory
scp -r folder/ user@host:/path/
```

### Port Forwarding

```bash
# Access remote service locally
ssh -L 8080:localhost:80 user@host

# Expose local service remotely
ssh -R 8080:localhost:80 user@host

# SOCKS proxy
ssh -D 1080 user@host
```

## Security First

SSH is secure by design, but proper configuration is essential:

| Practice | Why |
|----------|-----|
| Use key authentication | Stronger than passwords |
| Disable root login | Limit attack surface |
| Use Ed25519 keys | Modern, secure, fast |
| Keep software updated | Security patches |
| Use fail2ban | Prevent brute force |
| Audit access logs | Detect intrusions |

## Guide Sections

<div class="grid cards" markdown>

-   :material-book-open-variant:{ .lg .middle } **Fundamentals**

    ---

    Protocol details, encryption, authentication flow

    [:octicons-arrow-right-24: Learn the basics](fundamentals/protocol.md)

-   :material-laptop:{ .lg .middle } **Client Setup**

    ---

    Configuration, keys, agent, connection options

    [:octicons-arrow-right-24: Configure client](client/configuration.md)

-   :material-server:{ .lg .middle } **Server Setup**

    ---

    sshd configuration, hardening, access control

    [:octicons-arrow-right-24: Configure server](server/configuration.md)

-   :material-file-sync:{ .lg .middle } **File Transfer**

    ---

    SCP, SFTP, rsync for moving files securely

    [:octicons-arrow-right-24: Transfer files](file-transfer/scp.md)

-   :material-tunnel:{ .lg .middle } **Tunneling**

    ---

    Port forwarding, jump hosts, SOCKS proxy

    [:octicons-arrow-right-24: Create tunnels](tunneling/local-forwarding.md)

-   :material-cog:{ .lg .middle } **Advanced**

    ---

    Multiplexing, certificates, automation

    [:octicons-arrow-right-24: Advanced topics](advanced/multiplexing.md)

</div>
