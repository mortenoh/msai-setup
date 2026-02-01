# Integration

Remote desktop protocols work alongside other infrastructure. This section covers common integration scenarios.

## Topics

<div class="grid cards" markdown>

-   **Tailscale**

    ---

    Secure remote access to VMs from anywhere

    [:octicons-arrow-right-24: Tailscale Integration](tailscale.md)

-   **GPU Passthrough**

    ---

    Remote access when GPU is passed to VM

    [:octicons-arrow-right-24: GPU Passthrough](gpu-passthrough.md)

</div>

## Common Scenarios

### Home Server Access

Access your home lab VMs from anywhere:

```
[macOS Laptop] ──Tailscale──► [Home Server] ──► [VMs]
    RDP/VNC                     Tailscale      VNC/RDP/SPICE
```

Solution: [Tailscale Integration](tailscale.md)

### Windows Gaming VM

Remote desktop to a Windows VM with GPU passthrough:

```
[macOS] ──────► [Windows VM + GPU]
   ?               Direct display to nothing
```

Challenge: RDP/VNC don't work well with passed-through GPU

Solution: [GPU Passthrough scenarios](gpu-passthrough.md)

### Mixed Environment

Multiple VMs, different protocols:

| VM | OS | Best Protocol | Client |
|----|----|--------------:|--------|
| dev-linux | Ubuntu | VNC | RealVNC |
| win-work | Windows 11 | RDP | MS Remote Desktop |
| kvm-local | Fedora | SPICE | Web console |

Solution: Tailscale for all, protocol per VM type

## Security Architecture

```
┌─────────────────────────────────────────────────────────┐
│                      Internet                            │
│                          │                               │
│                          X  ← Blocked                    │
│                                                          │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   Tailscale Network                      │
│                                                          │
│  [macOS Client] ◄──────────────────► [Home Server]      │
│       100.x.x.1        WireGuard          100.x.x.2     │
│                        Encrypted                         │
│                                                          │
│                            │                             │
│                            ▼                             │
│                     [VMs on Server]                      │
│                      VNC/RDP/SPICE                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

Key points:
- VNC/RDP/SPICE never exposed to internet
- All traffic through Tailscale (WireGuard encrypted)
- Access from anywhere with Tailscale installed

## Quick Setup

### 1. Install Tailscale Everywhere

```bash
# On server
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# On macOS
brew install --cask tailscale
# Open Tailscale, sign in
```

### 2. Configure VM for Remote Access

VNC for Linux:
```xml
<graphics type='vnc' port='5900' listen='0.0.0.0'/>
```

RDP for Windows:
```powershell
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0
```

### 3. Connect via Tailscale

```bash
# VNC
open vnc://server.tail-network.ts.net:5900

# RDP
# Add PC: server.tail-network.ts.net in MS Remote Desktop
```

See detailed guides:
- [Tailscale Integration](tailscale.md)
- [GPU Passthrough](gpu-passthrough.md)
