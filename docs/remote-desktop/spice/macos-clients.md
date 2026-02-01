# SPICE macOS Clients

The honest truth about SPICE clients on macOS and practical workarounds.

## The Hard Truth

!!! warning "SPICE on macOS is Painful"
    Unlike VNC and RDP which have excellent macOS clients, SPICE support is limited. If you're primarily using macOS, consider alternatives.

### Reality Check

| Approach | Effort | Experience |
|----------|--------|------------|
| virt-viewer via Homebrew | Medium | Mediocre |
| Proxmox web console | Low | Good |
| Switch to VNC | Low | Good |
| Linux VM as jump host | High | Native SPICE |

## Option 1: virt-viewer (XQuartz Required)

The official SPICE client, but requires X11.

### Installation

```bash
# Install XQuartz (X11 for macOS)
brew install --cask xquartz

# Log out and log back in (required for XQuartz)

# Install virt-viewer
brew install virt-viewer
```

### Usage

```bash
# Connect to SPICE VM
remote-viewer spice://server-ip:5900

# Via SSH tunnel
ssh -L 5900:localhost:5900 user@server &
remote-viewer spice://localhost:5900

# Connect to libvirt VM directly
virt-viewer -c qemu+ssh://user@server/system vm-name
```

### Issues You'll Encounter

| Issue | Workaround |
|-------|------------|
| Requires XQuartz | Install it, log out/in |
| Poor keyboard mapping | May need configuration |
| Window management | XQuartz is quirky |
| Not native looking | Accept the X11 aesthetic |
| USB redirect limited | May not work at all |
| Retina scaling | Often broken |

### XQuartz Configuration

Some improvements in XQuartz preferences:

1. Open XQuartz
2. Preferences > Input
3. Check "Follow system keyboard layout"
4. Check "Enable key equivalents under X11"

## Option 2: Proxmox Web Console (Recommended)

If using Proxmox, the web console is the best option.

### Advantages

- No client install needed
- Works in any browser
- noVNC and SPICE HTML5
- Native SPICE features
- Clipboard works
- USB redirect supported

### Usage

1. Open Proxmox web UI
2. Select VM
3. Click Console tab
4. Choose noVNC or SPICE HTML5

### noVNC vs SPICE HTML5

| Feature | noVNC | SPICE HTML5 |
|---------|-------|-------------|
| Compatibility | Universal | Best for SPICE VMs |
| Performance | Good | Better |
| Clipboard | Works | Works |
| Audio | No | Limited |

## Option 3: Use VNC Instead

Often the pragmatic solution for macOS users.

### Configure VM for Both

```xml
<!-- In libvirt VM config -->
<graphics type='spice' autoport='yes'>
  <listen type='address' address='127.0.0.1'/>
</graphics>
<graphics type='vnc' port='-1' autoport='yes'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

### Connect via VNC

```bash
open vnc://server-ip:5900
```

### What You Lose

- USB redirection (use libvirt USB passthrough instead)
- Seamless display resize (set fixed resolution)
- Audio (not available in VNC anyway)

### What You Keep

- Full display access
- Keyboard and mouse
- Basic clipboard
- macOS native client experience

## Option 4: Linux Jump Host

Run a Linux VM locally for SPICE access to remote VMs.

### Architecture

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    macOS     │      │  Linux VM    │      │  SPICE VM    │
│              │─────►│  (local)     │─────►│  (remote)    │
│  VNC Client  │ VNC  │ virt-viewer  │SPICE │              │
└──────────────┘      └──────────────┘      └──────────────┘
```

### Setup

1. Create lightweight Linux VM (Ubuntu Server + XFCE)
2. Install virt-viewer: `apt install virt-viewer`
3. Access Linux VM via VNC
4. Use virt-viewer from Linux VM

### When This Makes Sense

- Multiple SPICE VMs to access
- Need full SPICE features
- USB redirect required
- Don't want XQuartz hassle

## Connecting via Tailscale

Regardless of method, secure access via Tailscale.

### Direct Connection

```bash
remote-viewer spice://server.tail-network.ts.net:5900
```

### SSH Tunnel Through Tailscale

```bash
# Tunnel SPICE port
ssh -L 5900:localhost:5900 user@server.tail-network.ts.net -N &

# Connect
remote-viewer spice://localhost:5900
```

## Feature Comparison by Method

| Feature | virt-viewer | Web Console | VNC | Jump Host |
|---------|-------------|-------------|-----|-----------|
| Setup effort | Medium | None | Low | High |
| Display quality | Good | Good | Good | Native |
| Clipboard | Works | Works | Text only | Full |
| USB redirect | Limited | Yes* | No | Full |
| Audio | Yes | Limited | No | Yes |
| Native feel | No | Browser | Yes | No |

*Proxmox web console supports USB redirect

## Keyboard Mapping

### virt-viewer with XQuartz

Common issues and fixes:

| Key | Issue | Workaround |
|-----|-------|------------|
| ++cmd++ | May not send | Use ++ctrl++ for shortcuts |
| ++option++ | Inconsistent | Check XQuartz settings |
| Function keys | May conflict | Disable macOS shortcuts |

### XQuartz Key Settings

In XQuartz Preferences > Input:
- Check "Option keys send Alt_L and Alt_R"
- Check "Follow system keyboard layout"

## Troubleshooting

### virt-viewer Won't Start

```bash
# Ensure XQuartz is running
open -a XQuartz

# Check DISPLAY variable
echo $DISPLAY
# Should show something like ":0"

# If not, set it
export DISPLAY=:0
```

### Connection Refused

1. Check SPICE port: `virsh domdisplay vm-name`
2. Verify server allows connections
3. Test with `nc -zv server-ip 5900`

### Poor Performance

1. Lower compression in VM config
2. Check network latency
3. Try web console instead
4. Consider VNC alternative

### Clipboard Not Working

1. Verify spice-vdagent running in guest
2. Restart vdagent: `systemctl restart spice-vdagent`
3. Reconnect client

## Recommendation Summary

| Situation | Recommendation |
|-----------|----------------|
| Proxmox user | Use web console |
| Occasional access | virt-viewer + XQuartz |
| Regular access, need features | Linux jump host |
| Regular access, basic needs | Switch to VNC |
| Need USB passthrough | Linux jump host or web console |
| Want native macOS experience | Use VNC |

## Bottom Line

For macOS users who need SPICE features:

1. **First choice**: Proxmox web console if applicable
2. **Pragmatic choice**: Use VNC instead
3. **Full features**: Linux VM as jump host
4. **Quick and dirty**: virt-viewer + XQuartz

SPICE was designed for Linux clients. On macOS, you're working against the grain. Make an informed decision based on which features you actually need.
