# Remote Desktop

Remote desktop protocols enable graphical access to servers and virtual machines. This guide covers VNC, RDP, and SPICE with a focus on macOS clients connecting to Linux/KVM servers and Windows VMs.

## Protocol Comparison

| Feature | VNC | RDP | SPICE |
|---------|-----|-----|-------|
| **macOS Client Quality** | Good | Good | Poor |
| **Built-in Encryption** | No | TLS | Optional |
| **Audio Support** | No | Yes | Yes |
| **USB Redirect** | No | Limited | Full |
| **Clipboard Sync** | Basic | Full | Full |
| **WAN Performance** | OK | Good | Poor |
| **Best For** | Linux VMs | Windows VMs | Local KVM only |

## Quick Recommendations

### Linux VMs/Servers

Use **VNC** for Linux systems:

- Works universally across all Linux distributions
- Native support in KVM/QEMU
- Built into macOS Screen Sharing for quick access
- Use RealVNC Viewer or Jump Desktop for better experience

### Windows VMs

Use **RDP** for Windows systems:

- Native Windows feature (no server install needed)
- Best compression and performance over networks
- Full audio, clipboard, and multi-monitor support
- Microsoft Remote Desktop on macOS is excellent

### Local KVM with USB Passthrough

Consider **SPICE** only when:

- USB device redirection is required
- Running VMs locally (same network)
- Willing to deal with limited macOS client options

## Security First

!!! danger "Never Expose to Internet"
    VNC and RDP should **never** be directly exposed to the internet. Both protocols have been targets of widespread attacks.

**Secure Access Methods:**

1. **Tailscale (Recommended)** - Zero-config VPN, works from anywhere
2. **SSH Tunneling** - Classic approach, requires SSH access
3. **VPN** - Traditional VPN if already configured

See [Integration with Tailscale](integration/tailscale.md) for the recommended approach.

## Default Ports

| Protocol | Port | Notes |
|----------|------|-------|
| VNC | 5900+ | Display :0 = 5900, :1 = 5901, etc. |
| RDP | 3389 | TCP and UDP |
| SPICE | 5900 | Configurable per VM |

## Documentation Structure

<div class="grid cards" markdown>

-   **Fundamentals**

    ---

    Protocol deep-dive and technical details

    [:octicons-arrow-right-24: Protocols](fundamentals/protocols.md)

-   **VNC**

    ---

    Server setup and macOS clients for Linux VMs

    [:octicons-arrow-right-24: VNC Guide](vnc/index.md)

-   **RDP**

    ---

    Windows VM access and macOS clients

    [:octicons-arrow-right-24: RDP Guide](rdp/index.md)

-   **SPICE**

    ---

    Advanced KVM features and macOS limitations

    [:octicons-arrow-right-24: SPICE Guide](spice/index.md)

-   **Integration**

    ---

    Tailscale and GPU passthrough scenarios

    [:octicons-arrow-right-24: Integration](integration/index.md)

-   **Reference**

    ---

    Quick reference and cheat sheet

    [:octicons-arrow-right-24: Quick Reference](reference/quick-reference.md)

</div>

## Related Documentation

- [KVM Setup](../virtualization/kvm-setup.md) - Virtual machine basics
- [Windows 11 VM](../virtualization/windows-vm.md) - Windows VM configuration
- [GPU Passthrough](../virtualization/gpu-passthrough.md) - Graphics card passthrough
- [Tailscale](../tailscale/index.md) - Secure remote access
