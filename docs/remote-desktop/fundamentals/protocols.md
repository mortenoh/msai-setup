# Protocol Deep-Dive

Technical details on how VNC, RDP, and SPICE work under the hood.

## VNC / RFB Protocol

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   VNC Client    │◄───────►│   VNC Server    │
│                 │   RFB   │                 │
│  - Displays     │ Protocol│  - Captures     │
│    framebuffer  │         │    screen       │
│  - Sends input  │         │  - Injects      │
│                 │         │    input        │
└─────────────────┘         └─────────────────┘
```

### Protocol Flow

1. **Handshake** - Version negotiation
2. **Security** - Authentication (if configured)
3. **Initialization** - Screen dimensions, pixel format
4. **Pixel data** - Rectangles of changed pixels

### Encoding Types

| Encoding | Description | Use Case |
|----------|-------------|----------|
| Raw | Uncompressed pixels | Debugging |
| CopyRect | Copy existing region | Fast for window moves |
| RRE | Run-length encoding | Simple compression |
| Hextile | 16x16 tile-based | Balanced performance |
| ZRLE | Zlib + RLE | Best compression |
| Tight | Adaptive JPEG/PNG | Modern default |

### VNC Flavors

Different VNC implementations add features:

- **TightVNC** - Better compression, file transfer
- **TigerVNC** - TightVNC fork, more active
- **RealVNC** - Commercial, encryption
- **x11vnc** - Shares existing X display
- **wayvnc** - Wayland native

## RDP Protocol

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│   RDP Client    │◄───────►│   RDP Server    │
│                 │   RDP   │                 │
│  - Renders GDI  │ Protocol│  - Intercepts   │
│    commands     │         │    GDI calls    │
│  - Local audio  │         │  - Encodes      │
│  - USB redirect │         │    multimedia   │
└─────────────────┘         └─────────────────┘
```

### Virtual Channels

RDP uses virtual channels for different data types:

| Channel | Purpose |
|---------|---------|
| rdpdr | Device redirection |
| cliprdr | Clipboard |
| rdpsnd | Audio |
| drdynvc | Dynamic virtual channels |
| rail | RemoteApp |

### Network Level Authentication (NLA)

Modern RDP uses NLA:

1. TLS connection established
2. CredSSP authentication before session
3. Prevents pre-auth attacks
4. Required on Windows 10/11

### RemoteFX

Microsoft's GPU virtualization extension:

- Hardware-accelerated encoding
- H.264/AVC compression
- 60 FPS possible
- Requires compatible GPU

## SPICE Protocol

### Architecture

```
┌─────────────────┐         ┌─────────────────┐
│  SPICE Client   │◄───────►│  SPICE Server   │
│                 │  SPICE  │  (in QEMU)      │
│  - Display      │ Protocol│                 │
│  - USB          │         │  ┌───────────┐  │
│  - Audio        │         │  │ Guest VM  │  │
│                 │         │  │           │  │
└─────────────────┘         │  │ SPICE     │  │
                            │  │ Agent     │  │
                            │  └───────────┘  │
                            └─────────────────┘
```

### Channels

SPICE uses multiple channels (separate connections):

| Channel | Purpose |
|---------|---------|
| main | Control and configuration |
| display | Screen data |
| inputs | Keyboard/mouse |
| cursor | Mouse cursor images |
| playback | Audio to client |
| record | Audio from client |
| usbredir | USB device forwarding |
| webdav | File sharing |

### SPICE Agent

The guest agent (`spice-vdagent`) provides:

- Seamless mouse integration
- Clipboard sharing
- Display resizing
- File drag-and-drop

### QXL Driver

Virtual GPU driver for guests:

- Hardware-accelerated 2D
- Multiple monitors
- Dynamic resolution
- Required for best performance

## Protocol Comparison Matrix

### Bandwidth Efficiency

| Scenario | VNC | RDP | SPICE |
|----------|-----|-----|-------|
| Static desktop | Medium | High | High |
| Text editing | Low | High | High |
| Video playback | Poor | Good | Good |
| Gaming | Poor | Fair | Fair |

### Latency Sensitivity

| Protocol | Local (< 1ms) | LAN (< 10ms) | WAN (> 50ms) |
|----------|---------------|--------------|--------------|
| VNC | Good | Good | Usable |
| RDP | Excellent | Excellent | Good |
| SPICE | Excellent | Good | Poor |

### Security Features

| Feature | VNC | RDP | SPICE |
|---------|-----|-----|-------|
| Encryption | External* | TLS | Optional TLS |
| Auth methods | Password | NLA/Kerberos | SASL/Tickets |
| Enterprise SSO | No | Yes (AD) | Partial |

*VNC typically tunneled through SSH for encryption

## Choosing the Right Protocol

### Use VNC When

- Accessing Linux systems
- Cross-platform compatibility needed
- Simple setup required
- Encryption via SSH tunnel acceptable

### Use RDP When

- Connecting to Windows
- Need audio support
- WAN/internet access
- Enterprise environment

### Use SPICE When

- Running local KVM VMs
- USB passthrough needed
- Guest agent benefits desired
- macOS client limitations acceptable
