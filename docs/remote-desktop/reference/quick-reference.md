# Quick Reference

Ports, commands, and quick setup guides for remote desktop protocols.

## Default Ports

| Protocol | Port | Notes |
|----------|------|-------|
| VNC | 5900 | Display :0 |
| VNC | 5901 | Display :1 |
| VNC | 5900+N | Display :N |
| RDP | 3389 | TCP and UDP |
| SPICE | 5900 | Default, configurable |
| Sunshine | 47984-48010 | Multiple ports |

## Quick Connect Commands

### VNC

```bash
# macOS built-in
open vnc://192.168.1.100:5900
open vnc://server.tail-network.ts.net:5900

# Via SSH tunnel
ssh -L 5900:localhost:5900 user@server -N &
open vnc://localhost:5900
```

### RDP

```bash
# Open Microsoft Remote Desktop and add PC
# Or use open with RDP file
open ~/connection.rdp
```

### SPICE

```bash
# With virt-viewer installed
remote-viewer spice://server:5900
virt-viewer -c qemu+ssh://user@server/system vm-name
```

## Server Setup Commands

### VNC (Linux)

```bash
# Install TigerVNC
sudo apt install tigervnc-standalone-server

# Set password
vncpasswd

# Start server
vncserver :1 -geometry 1920x1080 -depth 24

# Stop server
vncserver -kill :1
```

### RDP (Windows)

```powershell
# Enable RDP
Set-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server' -Name "fDenyTSConnections" -Value 0

# Enable firewall rule
Enable-NetFirewallRule -DisplayGroup "Remote Desktop"

# Add user to Remote Desktop Users
Add-LocalGroupMember -Group "Remote Desktop Users" -Member "username"
```

### SPICE (libvirt)

```bash
# Check SPICE port
virsh domdisplay vm-name

# Edit VM for SPICE
virsh edit vm-name
```

SPICE graphics config:
```xml
<graphics type='spice' autoport='yes'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

## macOS Client Installation

```bash
# VNC - RealVNC Viewer
brew install --cask vnc-viewer

# RDP - Microsoft Remote Desktop
# Install from Mac App Store

# SPICE - virt-viewer (requires XQuartz)
brew install --cask xquartz
brew install virt-viewer

# Game streaming - Moonlight
brew install --cask moonlight
```

## Firewall Rules

### UFW (Ubuntu)

```bash
# VNC from Tailscale only
sudo ufw allow in on tailscale0 to any port 5900:5910 proto tcp

# RDP from Tailscale only
sudo ufw allow in on tailscale0 to any port 3389 proto tcp

# Block from other interfaces
sudo ufw deny 5900:5910/tcp
sudo ufw deny 3389/tcp
```

### Windows Firewall

```powershell
# Restrict RDP to Tailscale network
Set-NetFirewallRule -DisplayName "Remote Desktop - User Mode (TCP-In)" -RemoteAddress 100.64.0.0/10
```

## Protocol Selection Guide

| Scenario | Protocol | Why |
|----------|----------|-----|
| Linux VM | VNC | Native, simple |
| Windows VM | RDP | Built-in, best features |
| USB passthrough | SPICE | Only option |
| macOS client | VNC or RDP | Best client support |
| GPU passthrough | Sunshine | Hardware encoding |
| Remote over internet | RDP | Best compression |

## Troubleshooting Commands

### Check Ports

```bash
# Server side - what's listening
ss -tlnp | grep -E "5900|3389|590"

# Client side - can I reach it
nc -zv server-ip 5900
nc -zv server-ip 3389
```

### Check Services

```bash
# VNC
ps aux | grep vnc
systemctl status vncserver@1

# Tailscale
tailscale status
tailscale ping server
```

### Windows RDP

```powershell
# Check RDP enabled
(Get-ItemProperty -Path 'HKLM:\System\CurrentControlSet\Control\Terminal Server').fDenyTSConnections

# Check service
Get-Service TermService

# Check port
netstat -an | findstr 3389
```

### VM Display

```bash
# KVM VNC port
virsh vncdisplay vm-name

# KVM SPICE port
virsh domdisplay vm-name
```

## Common Issues

| Problem | Solution |
|---------|----------|
| Connection refused | Check service running, firewall, port |
| Black screen (VNC) | Check xstartup, DE installed |
| Black screen (RDP) | Wait for GPU init, check drivers |
| Slow performance | Reduce color depth, check network |
| No clipboard | Install guest agent |
| No audio (RDP) | Check audio redirection settings |

## Performance Settings

### Low Bandwidth

| Setting | Value |
|---------|-------|
| Color depth | 16-bit |
| Resolution | 1280x720 |
| Compression | High |
| Visual effects | Disabled |

### High Bandwidth (LAN)

| Setting | Value |
|---------|-------|
| Color depth | 32-bit |
| Resolution | Native |
| Compression | Low/Off |
| Visual effects | Enabled |

## Security Checklist

- [ ] Never expose to internet directly
- [ ] Use Tailscale or SSH tunnel
- [ ] Set strong passwords
- [ ] Enable NLA for RDP
- [ ] Configure firewall
- [ ] Keep software updated

## Tailscale Integration

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Get Tailscale IP/hostname
tailscale status

# Connect via Tailscale
open vnc://server.tail-network.ts.net:5900
```

## libvirt VM Configs

### VNC

```xml
<graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

### SPICE

```xml
<graphics type='spice' autoport='yes'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
<video>
  <model type='qxl' ram='65536' vram='65536' heads='1'/>
</video>
<channel type='spicevmc'>
  <target type='virtio' name='com.redhat.spice.0'/>
</channel>
```

### Both (Fallback)

```xml
<graphics type='spice' autoport='yes'/>
<graphics type='vnc' autoport='yes'/>
```

## Keyboard Shortcuts

### VNC (RealVNC)

| Action | macOS Keys |
|--------|------------|
| Full screen | ++cmd+shift+f++ |
| Send Ctrl+Alt+Del | ++cmd+ctrl+delete++ |

### RDP (Microsoft)

| Action | macOS Keys |
|--------|------------|
| Full screen | ++cmd+ctrl+f++ |
| Send Ctrl+Alt+Del | ++ctrl+option+delete++ |
| Disconnect | ++cmd+w++ |

## File Locations

### Linux

```
~/.vnc/passwd           # VNC password
~/.vnc/xstartup         # VNC startup script
~/.vnc/*.log            # VNC logs
/etc/libvirt/qemu/      # VM definitions
```

### Windows

```
HKLM:\System\CurrentControlSet\Control\Terminal Server  # RDP registry
%USERPROFILE%\Documents\*.rdp  # Saved RDP connections
```

### macOS

```
~/Library/Containers/com.microsoft.rdc.macos/  # MS Remote Desktop
~/Library/Application Support/VNC Viewer/      # RealVNC
```
