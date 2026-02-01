# RDP

Remote Desktop Protocol (RDP) is Microsoft's native remote access protocol, built into Windows. It's the best choice for accessing Windows VMs and servers from macOS.

## When to Use RDP

RDP is the best choice for:

- Windows servers and VMs
- Remote work scenarios
- Need for audio support
- Printer and drive redirection
- Enterprise environments with Active Directory

## RDP Architecture

```
┌──────────────────┐                    ┌──────────────────┐
│   macOS Client   │                    │   Windows VM     │
│                  │       RDP/TLS      │                  │
│  MS Remote       │◄──────────────────►│   RDP Server     │
│  Desktop         │      Port 3389     │   (built-in)     │
│  Jump Desktop    │                    │                  │
└──────────────────┘                    └──────────────────┘
```

## Advantages Over VNC

| Feature | RDP | VNC |
|---------|-----|-----|
| Compression | Superior | Good |
| Audio | Yes | No |
| Clipboard | Full (files too) | Text only |
| Drive mapping | Yes | No |
| Multi-monitor | Excellent | Basic |
| Encryption | Built-in TLS | External |

## Topics

<div class="grid cards" markdown>

-   **Windows Setup**

    ---

    Configure RDP on Windows servers and VMs

    [:octicons-arrow-right-24: Windows Setup](windows-setup.md)

-   **macOS Clients**

    ---

    Client recommendations and configuration

    [:octicons-arrow-right-24: macOS Clients](macos-clients.md)

</div>

## Quick Start

### Enable RDP on Windows

1. Settings > System > Remote Desktop
2. Enable "Remote Desktop"
3. Note the PC name

### Connect from macOS

1. Install Microsoft Remote Desktop from App Store
2. Add PC: `windows-vm.tail-network.ts.net`
3. Enter credentials
4. Connect

See [Windows Setup](windows-setup.md) for detailed configuration.

## Security

!!! danger "Never Expose to Internet"
    RDP has been a major attack vector. The BlueKeep vulnerability (CVE-2019-0708) and others have led to widespread attacks.

**Secure Access Methods:**

1. **Tailscale** (recommended) - Zero-config, encrypted
2. **VPN** - Traditional approach
3. **RD Gateway** - Enterprise solution

## Default Port

| Protocol | Port | Notes |
|----------|------|-------|
| RDP | 3389 | TCP and UDP |

## Related

- [Windows Setup](windows-setup.md) - Enable and configure RDP
- [macOS Clients](macos-clients.md) - Client recommendations
- [Tailscale Integration](../integration/tailscale.md) - Secure remote access
- [Windows 11 VM](../../virtualization/windows-vm.md) - VM setup
