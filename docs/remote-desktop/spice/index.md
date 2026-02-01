# SPICE

SPICE (Simple Protocol for Independent Computing Environments) is a remote display protocol designed for virtual machines. It offers advanced features like USB redirection and seamless guest integration.

## The macOS Reality

!!! warning "Limited macOS Support"
    SPICE on macOS is challenging. Native clients are outdated or require workarounds. Consider alternatives before committing to SPICE for macOS access.

### macOS Options (Ranked)

1. **Proxmox/virt-manager web console** - Use browser-based console
2. **virt-viewer via Homebrew** - Requires XQuartz, mediocre experience
3. **Remote-viewer in VM** - Run a Linux VM to access SPICE VMs
4. **Switch to VNC** - Often the pragmatic choice

## When SPICE Makes Sense

Despite macOS challenges, SPICE excels at:

| Feature | SPICE | VNC | RDP |
|---------|-------|-----|-----|
| USB passthrough | Full | No | Limited |
| Guest agent features | Yes | No | Yes |
| Clipboard (files) | Yes | Text | Yes |
| Multi-monitor | Dynamic | Static | Static |
| Audio | Bidirectional | No | Bidirectional |

### Use SPICE When

- USB device redirection is required
- Running Proxmox (has web console fallback)
- Accessing from Linux client
- Local-only VM access
- Dynamic display resizing needed

### Avoid SPICE When

- Primary client is macOS
- Remote/WAN access needed
- Simplicity is priority
- Using Windows VMs (use RDP instead)

## Architecture

```
┌──────────────────┐                    ┌──────────────────┐
│   SPICE Client   │                    │   QEMU/KVM       │
│                  │      SPICE         │                  │
│  virt-viewer     │◄──────────────────►│   SPICE Server   │
│  remote-viewer   │   Multiple         │   (in QEMU)      │
│  Web Console     │   Channels         │                  │
│                  │                    │  ┌────────────┐  │
└──────────────────┘                    │  │  Guest VM  │  │
                                        │  │            │  │
                                        │  │ spice-     │  │
                                        │  │ vdagent    │  │
                                        │  └────────────┘  │
                                        └──────────────────┘
```

## Topics

<div class="grid cards" markdown>

-   **Server Setup**

    ---

    Configure SPICE in KVM/QEMU VMs

    [:octicons-arrow-right-24: Server Setup](server-setup.md)

-   **macOS Clients**

    ---

    The honest truth about SPICE on macOS

    [:octicons-arrow-right-24: macOS Clients](macos-clients.md)

</div>

## Quick Comparison

### SPICE vs VNC for Linux VMs

| Scenario | Recommendation |
|----------|----------------|
| macOS client, remote access | VNC |
| macOS client, local access | VNC (or SPICE with workarounds) |
| Linux client, any access | SPICE |
| Need USB passthrough | SPICE |
| Need audio | SPICE |
| Simplicity | VNC |

## Alternative Approach

If you need SPICE features but have a macOS client:

1. **Use Proxmox** - Web-based SPICE console works everywhere
2. **VNC + USB passthrough** - Pass USB via QEMU, display via VNC
3. **Jump host** - Linux VM as jump host for SPICE access

## Related

- [Server Setup](server-setup.md) - SPICE server configuration
- [macOS Clients](macos-clients.md) - Client options and workarounds
- [VNC](../vnc/index.md) - Simpler alternative for macOS
- [GPU Passthrough](../integration/gpu-passthrough.md) - When using GPU
