# GPU Passthrough and Remote Desktop

When a GPU is passed through to a VM, traditional remote desktop becomes complicated. This guide covers the challenges and solutions.

## The Problem

With GPU passthrough, the GPU is owned exclusively by the VM:

```
┌──────────────────────────────────────────────────────────────┐
│                        Host Server                            │
│                                                               │
│   ┌───────────────────────────────────────────────────────┐  │
│   │                    Windows VM                          │  │
│   │                                                        │  │
│   │   ┌────────┐     GPU drives display, but...           │  │
│   │   │  GPU   │                                          │  │
│   │   │        │     No physical monitor connected!       │  │
│   │   └────────┘     RDP sees software renderer          │  │
│   │                                                        │  │
│   └───────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

### Why RDP/VNC Don't Work Well

1. **RDP falls back to software renderer** - GPU not used
2. **VNC captures wrong display** - Or nothing at all
3. **No EDID without monitor** - Display may not initialize
4. **Performance is terrible** - No hardware acceleration

## Solution Overview

| Solution | Use Case | Complexity | Performance |
|----------|----------|------------|-------------|
| Dummy plug | Gaming, rendering | Low | Excellent |
| Sunshine + Moonlight | Gaming, general | Medium | Excellent |
| Looking Glass | Local access only | High | Excellent |
| Parsec | Gaming, commercial | Low | Excellent |
| Virtual Display | Non-gaming | Low | Good |

## Dummy Display Plug

A dummy HDMI/DP plug tricks the GPU into thinking a monitor is connected.

### What to Buy

Search for "HDMI dummy plug" or "display emulator":
- HDMI dummy plug (most common)
- DisplayPort dummy plug
- 4K@60Hz or higher for modern GPUs

### How It Works

```
GPU ──► Dummy Plug ──► GPU initializes display
                       RDP/streaming now works
```

### Configuration

1. Insert dummy plug into GPU output
2. Boot VM
3. GPU initializes normally
4. Use Sunshine/Moonlight or RDP

### Resolution Configuration

In Windows VM:
1. Right-click desktop > Display settings
2. Set resolution to match your client
3. Common: 1920x1080, 2560x1440, 3840x2160

## Sunshine + Moonlight (Recommended for Gaming)

Sunshine is a self-hosted game streaming server. Moonlight is the client.

### Architecture

```
┌───────────────┐         ┌───────────────────────┐
│ macOS Client  │         │     Windows VM        │
│               │         │                       │
│  Moonlight    │◄───────►│  Sunshine Server      │
│               │  Stream │  (uses GPU encoder)   │
│               │         │        ▲              │
└───────────────┘         │        │              │
                          │   ┌────┴────┐         │
                          │   │   GPU   │         │
                          │   └─────────┘         │
                          └───────────────────────┘
```

### Install Sunshine (Windows VM)

1. Download from [GitHub Releases](https://github.com/LizardByte/Sunshine/releases)
2. Run installer
3. Open browser: `https://localhost:47990`
4. Set username and password
5. Configure settings

### Install Moonlight (macOS)

```bash
brew install --cask moonlight
```

Or download from [moonlight-stream.org](https://moonlight-stream.org/).

### Connect

1. Open Moonlight on macOS
2. Add host: VM's Tailscale IP or hostname
3. Pair with PIN displayed in Sunshine
4. Connect

### Sunshine Settings

Recommended for quality:

| Setting | Value |
|---------|-------|
| Bitrate | 50+ Mbps (LAN) |
| Encoder | NVENC (NVIDIA) or AMF (AMD) |
| Resolution | Match display |
| FPS | 60+ |

### Port Requirements

| Port | Protocol | Purpose |
|------|----------|---------|
| 47984 | TCP | HTTPS web UI |
| 47989 | TCP | HTTP web UI |
| 48010 | TCP | RTSP |
| 47998-48000 | UDP | Video/Audio/Control |

On Tailscale, these work automatically.

## Looking Glass (Advanced)

Looking Glass captures the GPU framebuffer and shares it via shared memory. Requires host access to the framebuffer.

### Requirements

- IVSHMEM device configured
- Looking Glass host app in VM
- Looking Glass client on host
- Only works for local access (same machine)

### When to Use

- Need absolute lowest latency
- VM and client on same physical machine
- Comfortable with complex setup

### Not Covered Here

Looking Glass setup is complex. See [Looking Glass documentation](https://looking-glass.io/docs/).

## Parsec (Commercial Alternative)

Cloud gaming technology that works well for remote VM access.

### Advantages

- Easy setup
- Good macOS client
- Works through NAT/firewalls
- Hardware encoding support

### Setup

1. Create account at [parsec.app](https://parsec.app)
2. Install Parsec in Windows VM
3. Install Parsec on macOS
4. Connect

### Considerations

- Free tier has limitations
- Commercial product (may change)
- Data goes through their servers

## Virtual Display Driver

Software-based virtual display without hardware.

### IddSampleDriver

Open-source virtual display driver for Windows:

1. Download from [GitHub](https://github.com/roshkins/IddSampleDriver)
2. Install in Windows VM
3. Configure resolution in driver settings
4. Use RDP normally

### When Useful

- Non-gaming workloads
- RDP access to GPU VM
- CUDA/compute workloads where display doesn't matter

## Configuration Examples

### Gaming VM Setup

```
Components:
- GPU passed through to VM
- Dummy HDMI plug in GPU
- Sunshine installed in VM
- Moonlight on macOS

Connection:
macOS ──Tailscale──► Sunshine ──► VM Display
```

### Workstation VM Setup

```
Components:
- GPU passed through to VM
- Virtual display driver
- RDP enabled

Connection:
macOS ──Tailscale──► RDP ──► VM
(GPU available for CUDA/rendering, RDP for display)
```

### Hybrid Setup

```
Components:
- GPU passed through
- Dummy plug
- Both Sunshine AND RDP

Use Cases:
- Gaming: Moonlight for low latency
- Work: RDP when gaming not needed
```

## Network Considerations

### Sunshine over Tailscale

```bash
# Check connection type
tailscale ping windows-vm

# Direct connection preferred for streaming
# Relay adds latency
```

### Bandwidth Requirements

| Quality | Bandwidth Needed |
|---------|------------------|
| 1080p60 | 20-50 Mbps |
| 1440p60 | 35-75 Mbps |
| 4K60 | 80-150 Mbps |

### Tailscale Direct vs Relay

| Connection | Streaming Quality |
|------------|-------------------|
| Direct (LAN) | Excellent |
| Direct (WAN) | Good |
| Relay (DERP) | May have issues |

## Troubleshooting

### No Display in VM

1. Check dummy plug is inserted
2. Verify GPU passthrough working
3. Check display drivers installed
4. Try different dummy plug resolution

### Sunshine Won't Start

1. Run as administrator
2. Check firewall rules
3. Verify GPU drivers installed
4. Check Sunshine logs

### Moonlight Can't Connect

1. Verify Sunshine running
2. Check firewall (host and VM)
3. Test Tailscale connectivity
4. Try local network first

### High Latency

1. Check for direct Tailscale connection
2. Reduce resolution/bitrate
3. Enable/verify hardware encoding
4. Check network congestion

### No Audio

1. Enable audio in Sunshine settings
2. Check Windows audio device
3. Verify Moonlight audio settings

## Comparison Summary

| Need | Best Solution |
|------|---------------|
| Gaming remotely | Sunshine + Moonlight |
| Simple setup | Parsec |
| Local VM access | Looking Glass |
| Non-gaming work | Virtual display + RDP |
| Just need it to work | Dummy plug + Sunshine |

## Related

- [GPU Passthrough](../../virtualization/gpu-passthrough.md)
- [Windows VM](../../virtualization/windows-vm.md)
- [Tailscale Integration](tailscale.md)
