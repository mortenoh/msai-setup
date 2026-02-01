# RDP macOS Clients

Recommended RDP clients for macOS to connect to Windows VMs and servers.

## Quick Comparison

| Client | Price | Quality | Features | Best For |
|--------|-------|---------|----------|----------|
| Microsoft Remote Desktop | Free | Excellent | Full | Everyone |
| Jump Desktop | $35 | Excellent | Premium | Power users |
| Parallels Client | Free | Good | Enterprise | Parallels RAS users |
| Royal TSX | Free/Pro | Good | Multi-protocol | IT professionals |

## Microsoft Remote Desktop (Recommended)

The official Microsoft client is excellent and free.

### Installation

From Mac App Store:
- Search "Microsoft Remote Desktop"
- Or direct link: [Mac App Store](https://apps.apple.com/app/microsoft-remote-desktop/id1295203466)

### Add a Connection

1. Click **+** > **Add PC**
2. **PC name**: Enter IP or hostname
   - Tailscale: `windows.tail-network.ts.net`
   - Direct: `192.168.1.100`
3. **User account**: Add or select credentials
4. **Friendly name**: Optional display name
5. Click **Add**

### Connection Settings

#### Display

| Setting | Recommendation |
|---------|----------------|
| Resolution | Match local display |
| Scale content | Retina displays |
| Use all monitors | Multi-monitor setups |
| Start in full screen | Personal preference |

#### Devices & Audio

| Setting | Description |
|---------|-------------|
| Sound | Play on this computer |
| Microphone | Redirect if needed |
| Clipboard | Always enable |
| Folders | Map local folders to share files |

### Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Full screen | ++cmd+ctrl+f++ |
| Minimize | ++cmd+m++ |
| Disconnect | ++cmd+w++ |
| Send Ctrl+Alt+Del | ++ctrl+option+delete++ |
| Toggle menu bar | ++cmd+option+m++ |

### Redirect Local Folders

1. Edit connection > Folders tab
2. Click **+** to add folder
3. Select local folder to share
4. Appears as network drive in Windows

## Jump Desktop ($35)

Premium client supporting both RDP and VNC.

### Installation

- Mac App Store or [jumpdesktop.com](https://jumpdesktop.com/)

### Why Pay for Jump Desktop

| Feature | MS Remote Desktop | Jump Desktop |
|---------|-------------------|--------------|
| Fluid engine | No | Yes |
| RDP + VNC | RDP only | Both |
| Touch Bar | Basic | Full |
| Multi-monitor | Good | Excellent |
| Retina scaling | Good | Excellent |

### Fluid Remote Desktop

Jump Desktop's "Fluid" engine:
- Lower latency than standard RDP
- Better for high-latency connections
- Smoother scrolling and animations
- Requires client on Windows (free download)

### Configuration

1. Add new computer
2. Select RDP
3. Enter hostname: `windows.tail-network.ts.net`
4. Enter credentials
5. Enable "Fluid" for best performance

## Royal TSX (Free/Pro)

Multi-protocol connection manager for IT professionals.

### Installation

```bash
brew install --cask royal-tsx
```

### Features

- RDP, VNC, SSH, SFTP in one app
- Credential management
- Connection folders
- Tabbed interface
- Team sharing (Pro)

### When to Use

- Managing multiple servers
- Need SSH + RDP in one app
- Team environments
- Complex connection hierarchies

## Connecting via Tailscale

### Using MagicDNS

```
windows.tail-network.ts.net
```

In Microsoft Remote Desktop:
1. Add PC
2. PC name: `windows.tail-network.ts.net`
3. Connect

### Using Tailscale IP

```bash
# Find Windows VM's Tailscale IP
tailscale status | grep windows
# 100.64.0.5    windows-vm
```

Use `100.64.0.5` as PC name.

## Connection Quality Settings

### High Bandwidth (LAN/Tailscale Direct)

In Microsoft Remote Desktop:
- Display: Full resolution
- Color: 32-bit
- Check "Enable all Mac shortcuts"

### Lower Bandwidth (Relayed/WAN)

- Display: Scaled down
- Color: 16-bit
- Uncheck visual enhancements

### Checking Connection Type

Tailscale shows connection type:
```bash
tailscale status
# Look for "direct" vs "relay"
```

## Multi-Monitor Setup

### Microsoft Remote Desktop

1. Edit connection
2. Display tab
3. Check "Use all monitors"
4. Choose scaling option

### Selective Monitors

```bash
# Create .rdp file with specific monitors
selectedmonitors:s:0,1
use multimon:i:1
```

## Keyboard Mapping

### Windows Keys on Mac

| Windows Key | Mac Key |
|-------------|---------|
| ++ctrl++ | ++control++ |
| ++alt++ | ++option++ |
| ++win++ | ++cmd++ (configurable) |
| ++delete++ | ++fn+delete++ |
| ++print-screen++ | ++cmd+shift+3++ (local) |

### Configure Windows Key

In Microsoft Remote Desktop:
1. Preferences > Keyboard
2. Select how ++cmd++ maps

Options:
- Windows key
- Ctrl (for Ctrl+C, etc.)

## File Transfer

### Folder Redirection

1. Edit connection > Folders
2. Add local folder
3. Access in Windows at: `\\tsclient\FolderName`

### Clipboard

Files can be copied via clipboard:
1. Copy file on Mac
2. Paste in Windows Explorer

Size limits apply (~2GB typically).

## Audio Configuration

### Remote Audio Playback

Default: Plays on local Mac

Settings:
- Play on this computer (recommended)
- Play on remote computer
- Do not play

### Microphone Redirect

1. Edit connection
2. Devices & Audio tab
3. Enable microphone

## Troubleshooting

### Connection Refused

1. Verify RDP is enabled on Windows
2. Check Windows Firewall
3. Test port: `nc -zv windows-ip 3389`
4. Verify Tailscale connection: `tailscale ping windows`

### NLA/CredSSP Errors

"An authentication error has occurred":
1. Ensure clocks are synchronized
2. Update client app
3. Check Windows updates
4. Temporarily disable NLA to test

### Slow/Laggy

1. Check connection type (direct vs relay)
2. Reduce color depth
3. Disable visual effects
4. Check for network congestion

### Black Screen

1. Wait 30+ seconds (GPU init)
2. Press ++ctrl+option+delete++
3. Try reconnecting
4. Disable UDP:
   - Add custom RDP file
   - Add line: `networkautodetect:i:0`

### Keyboard Issues

1. Check keyboard preferences in client
2. Try different Windows key mapping
3. Use on-screen keyboard for special keys

## Recommended Configurations

### Home Lab Windows VM

```
PC name: windows.tail-network.ts.net
Resolution: Same as local display
Color: 32-bit
Folders: ~/Documents, ~/Downloads
Audio: Play on this computer
```

### Work Windows Server

```
PC name: server.company.com
Gateway: rd.company.com (if required)
Resolution: 1920x1080
Folders: None (security)
Clipboard: Enabled
```

### Low-Bandwidth Remote

```
PC name: 100.64.0.x
Resolution: 1280x720
Color: 16-bit
Desktop background: Disabled
Smooth fonts: Disabled
```

## Client Comparison Summary

| Need | Recommended |
|------|-------------|
| Standard use | Microsoft Remote Desktop |
| Also need VNC | Jump Desktop |
| Managing many servers | Royal TSX |
| Enterprise with Parallels | Parallels Client |
| Best performance | Jump Desktop (Fluid) |
| Free and works | Microsoft Remote Desktop |
