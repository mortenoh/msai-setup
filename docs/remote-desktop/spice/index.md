# SPICE

SPICE (Simple Protocol for Independent Computing Environments) is a remote display protocol designed for virtual machines. It offers advanced features like USB redirection and seamless guest integration.

## The macOS Reality

!!! warning "Limited macOS Support"
    SPICE on macOS is challenging. Native clients are outdated or require workarounds. Consider alternatives before committing to SPICE for macOS access.

!!! note "This build runs bare KVM/libvirt, not Proxmox"
    This host runs KVM/QEMU directly on Ubuntu Server via libvirt (see
    `START.md`) — there is no Proxmox and therefore no Proxmox
    web console. Where other SPICE guides suggest "use the Proxmox console", the
    equivalents here are `virt-manager` connecting over SSH
    (`qemu+ssh://user@host/system`), or `remote-viewer`/`virt-viewer` against a
    manually forwarded SPICE port. Those are the options described below.

### macOS Options (Ranked)

1. **virt-manager over SSH** - Manage VMs and open their SPICE console from a
   macOS-side virt-manager pointed at `qemu+ssh://user@host/system`
2. **virt-viewer / remote-viewer via Homebrew** - Requires XQuartz, mediocre
   experience; connect over an SSH-forwarded SPICE port
3. **Remote-viewer in a Linux VM** - Run a Linux VM to access SPICE VMs
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
- Managing VMs with virt-manager/virt-viewer (the libvirt-native console)
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
│  virt-viewer     │<──────────────────>│   SPICE Server   │
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

1. **virt-manager over SSH** - Drive the libvirt console from macOS via
   `qemu+ssh://user@host/system`, or `remote-viewer` over an SSH-forwarded
   SPICE port
2. **VNC + USB passthrough** - Pass USB via QEMU, display via VNC
3. **Jump host** - Linux VM as jump host for SPICE access

## Related

- [Server Setup](server-setup.md) - SPICE server configuration
- [macOS Clients](macos-clients.md) - Client options and workarounds
- [VNC](../vnc/index.md) - Simpler alternative for macOS
- [GPU Passthrough](../integration/gpu-passthrough.md) - When using GPU
