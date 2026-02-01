# VNC

VNC (Virtual Network Computing) is the standard remote desktop protocol for Linux systems. It's simple, widely supported, and works reliably across platforms.

## When to Use VNC

VNC is the best choice for:

- Linux servers and VMs
- Cross-platform access (any client to any server)
- Simple, reliable remote access
- Situations where SSH tunneling is acceptable

## VNC Architecture

```
┌──────────────────┐                    ┌──────────────────┐
│   macOS Client   │                    │   Linux Server   │
│                  │      VNC/RFB       │                  │
│  RealVNC Viewer  │◄──────────────────►│   TigerVNC       │
│  Screen Sharing  │      Port 5900     │   x11vnc         │
│  Jump Desktop    │                    │   QEMU VNC       │
└──────────────────┘                    └──────────────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Server Setup**

    ---

    Configure VNC servers on Linux systems and KVM VMs

    [:octicons-arrow-right-24: Server Setup](server-setup.md)

-   **macOS Clients**

    ---

    Client recommendations and configuration

    [:octicons-arrow-right-24: macOS Clients](macos-clients.md)

</div>

## Quick Start

### Connect to a KVM VM

1. Find your VM's VNC port:
   ```bash
   virsh vncdisplay vm-name
   # Output: :1 (means port 5901)
   ```

2. Connect from macOS:
   ```bash
   open vnc://server-ip:5901
   ```

### Connect Securely via Tailscale

```bash
# On macOS, connect via Tailscale hostname
open vnc://server.tail-network.ts.net:5900
```

See [Tailscale Integration](../integration/tailscale.md) for full setup.

## Security Warning

!!! danger "Never Expose VNC to the Internet"
    VNC was designed for trusted networks. Always use:

    - **Tailscale** (recommended) - Zero-config, works everywhere
    - **SSH tunnel** - `ssh -L 5900:localhost:5900 server`
    - **VPN** - If already configured

## Comparison with Alternatives

| Feature | VNC | RDP | SPICE |
|---------|-----|-----|-------|
| Linux support | Native | Via xrdp | Native |
| Audio | No | Yes | Yes |
| Encryption | SSH tunnel | Built-in | Optional |
| macOS client | Excellent | Excellent | Poor |

## Related

- [Server Setup](server-setup.md) - Configure VNC servers
- [macOS Clients](macos-clients.md) - Client recommendations
- [Tailscale Integration](../integration/tailscale.md) - Secure remote access
