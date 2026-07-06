# SPICE macOS Clients

The honest truth about SPICE clients on macOS and practical workarounds.

## The Hard Truth

!!! warning "SPICE on macOS is Painful"
    Unlike VNC and RDP which have excellent macOS clients, SPICE support is limited. If you're primarily using macOS, consider alternatives.

### Reality Check

!!! note "No Proxmox on this build"
    This host runs bare KVM/libvirt on Ubuntu Server, not Proxmox, so there is
    no Proxmox web console to fall back to. The libvirt-native equivalents are
    `virt-manager` connected over SSH, or `remote-viewer`/`virt-viewer` against
    an SSH-forwarded SPICE port — used below in place of the "web console"
    option.

| Approach | Effort | Experience |
|----------|--------|------------|
| virt-viewer via Homebrew | Medium | Mediocre |
| virt-manager over SSH | Low | Good |
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

## Option 2: virt-manager over SSH (Recommended)

Since this build uses libvirt directly, the closest thing to a "just works"
console is `virt-manager` on the Mac talking to the host's libvirt daemon over
SSH. It lists every VM and opens each one's SPICE (or VNC) console for you, with
no ports published on the network — the traffic rides the SSH connection.

### Advantages

- Uses libvirt's own console; no manual port math
- Nothing exposed on the network — tunneled over SSH
- Lists and manages all VMs from one window
- SPICE features (clipboard, dynamic resize) work through virt-viewer

### Usage

```bash
# Install on macOS (still pulls in XQuartz for the X11 GUI)
brew install --cask xquartz
brew install virt-manager virt-viewer

# Point virt-manager at the host's libvirt over SSH
virt-manager -c qemu+ssh://user@host.tail-network.ts.net/system
```

Then double-click a VM to open its SPICE console. For a single VM without the
full manager UI, `virt-viewer -c qemu+ssh://user@host/system vm-name` opens just
that console.

!!! note "virt-manager on macOS still needs XQuartz"
    virt-manager is a GTK/X11 app, so the same XQuartz caveats as Option 1
    apply. If you want to avoid XQuartz entirely, forward the SPICE port over
    SSH and use a native client, or fall back to VNC (Option 3).

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
│              │─────>│  (local)     │─────>│  (remote)    │
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

| Feature | virt-viewer | virt-manager (SSH) | VNC | Jump Host |
|---------|-------------|--------------------|-----|-----------|
| Setup effort | Medium | Low | Low | High |
| Display quality | Good | Good | Good | Native |
| Clipboard | Works | Works | Text only | Full |
| USB redirect | Limited | Limited | No | Full |
| Audio | Yes | Yes | No | Yes |
| Native feel | No | No (X11) | Yes | No |

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
3. Try virt-manager over SSH instead
4. Consider VNC alternative

### Clipboard Not Working

1. Verify spice-vdagent running in guest
2. Restart vdagent: `systemctl restart spice-vdagent`
3. Reconnect client

## Recommendation Summary

| Situation | Recommendation |
|-----------|----------------|
| Managing several VMs | virt-manager over SSH |
| Occasional access | virt-viewer + XQuartz |
| Regular access, need features | Linux jump host |
| Regular access, basic needs | Switch to VNC |
| Need USB passthrough | Linux jump host |
| Want native macOS experience | Use VNC |

## Bottom Line

For macOS users who need SPICE features:

1. **First choice**: virt-manager over SSH (libvirt-native, nothing exposed)
2. **Pragmatic choice**: Use VNC instead
3. **Full features**: Linux VM as jump host
4. **Quick and dirty**: virt-viewer + XQuartz

SPICE was designed for Linux clients. On macOS, you're working against the grain. Make an informed decision based on which features you actually need.
