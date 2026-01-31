# Tailscale

Tailscale is a zero-config mesh VPN built on WireGuard that creates secure networks between your devices without complex firewall rules or port forwarding.

## Why Tailscale?

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Traditional VPN vs Tailscale                              │
│                                                                              │
│   Traditional VPN (Hub-and-Spoke)          Tailscale (Mesh)                 │
│                                                                              │
│         ┌─────────┐                    ┌─────────┐   ┌─────────┐           │
│         │   VPN   │                    │ Device  │───│ Device  │           │
│         │ Server  │                    │    A    │   │    B    │           │
│         └────┬────┘                    └────┬────┘   └────┬────┘           │
│              │                              │             │                 │
│     ┌────────┼────────┐                     └──────┬──────┘                 │
│     │        │        │                            │                        │
│  ┌──┴──┐  ┌──┴──┐  ┌──┴──┐                   ┌────┴────┐                   │
│  │  A  │  │  B  │  │  C  │                   │ Device  │                   │
│  └─────┘  └─────┘  └─────┘                   │    C    │                   │
│                                              └─────────┘                    │
│   All traffic through server             Direct peer-to-peer               │
│   Single point of failure                No central bottleneck             │
│   Complex setup                          Zero configuration                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## Key Features

| Feature | Description |
|---------|-------------|
| **Zero Config** | No firewall rules, port forwarding, or complex setup |
| **WireGuard** | Built on modern, fast, secure WireGuard protocol |
| **NAT Traversal** | Works behind any NAT, even carrier-grade NAT |
| **MagicDNS** | Automatic DNS for all devices on your network |
| **ACLs** | Fine-grained access control policies |
| **SSO** | Integrate with existing identity providers |
| **Taildrop** | Easy file sharing between devices |
| **Exit Nodes** | Route internet traffic through any device |
| **Subnet Routers** | Access entire subnets without installing Tailscale |

## Quick Start

### 1. Install Tailscale

```bash
# Ubuntu/Debian
curl -fsSL https://tailscale.com/install.sh | sh

# Or via package manager
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.noarmor.gpg | \
  sudo tee /usr/share/keyrings/tailscale-archive-keyring.gpg >/dev/null
curl -fsSL https://pkgs.tailscale.com/stable/ubuntu/jammy.tailscale-keyring.list | \
  sudo tee /etc/apt/sources.list.d/tailscale.list
sudo apt update && sudo apt install tailscale
```

### 2. Authenticate

```bash
sudo tailscale up
```

Follow the URL to authenticate with your identity provider.

### 3. Connect

```bash
# Check status
tailscale status

# Ping another device
tailscale ping my-laptop

# Access services
ssh user@my-server  # Using MagicDNS name
```

## How It Works

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Tailscale Architecture                               │
│                                                                              │
│                        ┌─────────────────────┐                              │
│                        │  Coordination       │                              │
│                        │  Server             │                              │
│                        │  (control plane)    │                              │
│                        └──────────┬──────────┘                              │
│                                   │                                          │
│              ┌────────────────────┼────────────────────┐                    │
│              │ Key exchange       │ ACL distribution   │                    │
│              │ NAT traversal      │ Device registration│                    │
│              ▼                    ▼                    ▼                    │
│        ┌──────────┐        ┌──────────┐        ┌──────────┐                │
│        │ Device A │◄──────►│ Device B │◄──────►│ Device C │                │
│        │ 100.x.x.1│        │ 100.x.x.2│        │ 100.x.x.3│                │
│        └──────────┘        └──────────┘        └──────────┘                │
│              ▲                    ▲                    ▲                    │
│              └────────────────────┴────────────────────┘                    │
│                     Direct WireGuard connections                            │
│                     (data plane - peer to peer)                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

1. **Control Plane**: Tailscale's coordination servers handle key exchange, device registration, and ACL distribution
2. **Data Plane**: Actual traffic flows directly between devices using WireGuard
3. **NAT Traversal**: DERP relays help establish connections when direct paths fail

## Documentation Sections

### :material-school: Fundamentals
- [How Tailscale Works](fundamentals/how-it-works.md) - Architecture and concepts
- [WireGuard Basics](fundamentals/wireguard.md) - Underlying protocol
- [Networking Concepts](fundamentals/networking.md) - IPs, NAT traversal, DERP

### :material-download: Installation
- [Linux](installation/linux.md) - Ubuntu, Debian, RHEL, Arch
- [Containers](installation/containers.md) - Docker, Kubernetes
- [Other Platforms](installation/other-platforms.md) - macOS, Windows, mobile

### :material-cog: Configuration
- [Basic Setup](configuration/basic-setup.md) - First-time configuration
- [CLI Reference](configuration/cli.md) - Command line interface
- [Environment Variables](configuration/environment.md) - Advanced configuration

### :material-star: Features
- [MagicDNS](features/magicdns.md) - Automatic DNS
- [Taildrop](features/taildrop.md) - File sharing
- [Exit Nodes](features/exit-nodes.md) - Route internet traffic
- [Subnet Routers](features/subnet-routers.md) - Access entire networks
- [Funnel & Serve](features/funnel-serve.md) - Expose services to internet

### :material-link: Integration
- [Docker](integration/docker.md) - Container networking
- [Kubernetes](integration/kubernetes.md) - K8s operator
- [SSH](integration/ssh.md) - Tailscale SSH
- [VS Code](integration/vscode.md) - Remote development

### :material-shield: Administration
- [Access Controls](administration/acls.md) - Policy configuration
- [User Management](administration/users.md) - Identity and teams
- [Key Management](administration/keys.md) - Auth keys and API
- [Logging & Monitoring](administration/logging.md) - Observability

### :material-wrench: Troubleshooting
- [Connection Issues](troubleshooting/connections.md) - Debugging connectivity
- [Performance](troubleshooting/performance.md) - Speed optimization
- [Common Problems](troubleshooting/common-problems.md) - FAQ

### :material-book: Reference
- [Quick Reference](reference/quick-reference.md) - Command cheat sheet
- [Network Ports](reference/ports.md) - Firewall requirements
