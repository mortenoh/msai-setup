# VNC macOS Clients

Recommended VNC clients for macOS, from built-in options to feature-rich alternatives.

## Quick Comparison

| Client | Price | Performance | Features | Best For |
|--------|-------|-------------|----------|----------|
| Screen Sharing | Free | Good | Basic | Quick access |
| RealVNC Viewer | Free | Excellent | Good | Daily use |
| Jump Desktop | $35 | Excellent | Excellent | Power users |
| Screens 5 | $30 | Excellent | Excellent | Mac-first users |

## Built-in: Screen Sharing

macOS includes a VNC client called Screen Sharing.

### Quick Connect

Press ++cmd+k++ in Finder, or:

```bash
open vnc://192.168.1.100:5900
```

### Using Spotlight

1. Press ++cmd+space++
2. Type: `vnc://server-ip:5900`
3. Press ++enter++

### Via Finder

1. Open Finder
2. Press ++cmd+k++ (Connect to Server)
3. Enter: `vnc://server-ip:5900`
4. Click Connect

### Pros and Cons

| Pros | Cons |
|------|------|
| Already installed | Limited settings |
| Native integration | No compression options |
| Works immediately | Basic performance |
| Keychain support | No file transfer |

## RealVNC Viewer (Recommended Free)

The best free VNC client for macOS.

### Installation

```bash
brew install --cask vnc-viewer
```

Or download from [realvnc.com](https://www.realvnc.com/en/connect/download/viewer/).

### Features

- Optimized VNC protocol
- Connection encryption
- Auto-scaling
- Clipboard sync
- Full-screen mode
- Connection bookmarks

### Configuration Tips

1. **Picture Quality**: Set to "High" for LAN, "Medium" for WAN
2. **Enable "Adapt to network speed"** for automatic adjustment
3. **Clipboard sync**: Enabled by default

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Full screen | ++cmd+shift+f++ |
| Send Ctrl+Alt+Del | ++cmd+ctrl+delete++ |
| Connection info | ++cmd+i++ |

## Jump Desktop ($35)

Premium client with excellent features.

### Installation

Available on Mac App Store or [jumpdesktop.com](https://jumpdesktop.com/).

### Features

- Fluid remote desktop engine
- RDP and VNC in one app
- Multi-monitor support
- Touch Bar integration
- Retina display support
- Secure relay option

### Why Pay

- Best performance for high-latency connections
- Excellent retina scaling
- Unified RDP/VNC interface
- Professional support

### Configuration

1. Add new connection
2. Select VNC protocol
3. Enter hostname and port
4. Set quality to "Retina" for HiDPI

## Screens 5 ($30)

Mac-native design with cloud sync.

### Features

- Beautiful Mac-native UI
- iCloud sync of connections
- Curtain Mode (blank remote screen)
- Multi-display support
- iOS companion app

### Best For

Users who value Mac-native design and iCloud sync across devices.

## Connecting via Tailscale

Regardless of client, connecting via Tailscale is straightforward.

### Using MagicDNS

```bash
# Use Tailscale hostname
open vnc://server-name.tail-network.ts.net:5900
```

### Using Tailscale IP

```bash
# Find server's Tailscale IP
tailscale status

# Connect using 100.x.x.x IP
open vnc://100.64.0.1:5900
```

### Saving Connection in RealVNC Viewer

1. File > New Connection
2. VNC Server: `server.tail-network.ts.net:5900`
3. Name: "Server via Tailscale"
4. Click OK

## SSH Tunnel Alternative

If not using Tailscale, create an SSH tunnel.

### Create Tunnel

```bash
# Forward local port 5900 to remote VNC
ssh -L 5900:localhost:5900 user@server-ip -N
```

### Connect Through Tunnel

```bash
# In another terminal
open vnc://localhost:5900
```

### Persistent Tunnel

Add to `~/.ssh/config`:

```
Host server-vnc
    HostName server-ip
    User username
    LocalForward 5900 localhost:5900
```

Then:

```bash
ssh -N server-vnc &
open vnc://localhost:5900
```

## Performance Optimization

### Client Settings

1. **Color depth**: 16-bit for slow connections
2. **Scaling**: Native resolution when possible
3. **Compression**: Enable for WAN connections

### Network Considerations

| Network Type | Recommended Settings |
|--------------|---------------------|
| LAN (< 1ms) | Full quality, native resolution |
| Tailscale direct | High quality, may reduce if relayed |
| SSH tunnel | Medium quality, monitor latency |

### Checking Connection Quality

In RealVNC Viewer, press ++cmd+i++ to see:
- Connection type
- Latency
- Bandwidth usage

## Keyboard Mapping

### Special Keys

| macOS Key | Sent as |
|-----------|---------|
| ++cmd++ | Super/Windows |
| ++option++ | Alt |
| ++control++ | Ctrl |
| ++delete++ | Delete |
| ++fn+delete++ | Backspace |

### Linux Shortcuts via VNC

| Action | macOS Keys |
|--------|------------|
| Terminal | ++ctrl+option+t++ |
| Switch workspace | ++ctrl+option+arrow++ |
| Close window | ++option+f4++ |

## Troubleshooting

### Connection Times Out

1. Verify server is reachable: `ping server-ip`
2. Check VNC port is open: `nc -zv server-ip 5900`
3. Verify firewall allows connection

### Poor Performance

1. Reduce color depth in client
2. Lower resolution if possible
3. Check for network congestion
4. Try different encoding (if client supports)

### Clipboard Not Working

1. Ensure VNC server supports clipboard
2. Some servers require `vncconfig` running
3. Check client clipboard settings

### Garbled Display

1. Try different color depth
2. Reconnect to refresh
3. Check server-side resolution settings

## Client Comparison Summary

| Need | Recommended Client |
|------|-------------------|
| Quick, occasional access | Screen Sharing (built-in) |
| Regular use, free | RealVNC Viewer |
| Best performance | Jump Desktop |
| Mac-native experience | Screens 5 |
| RDP + VNC unified | Jump Desktop |
