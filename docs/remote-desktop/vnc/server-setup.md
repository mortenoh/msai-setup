# VNC Server Setup

Configure VNC servers on Linux systems and KVM virtual machines.

## KVM/QEMU VNC (Recommended for VMs)

KVM VMs have built-in VNC support through QEMU. This is the simplest option for VM console access.

### Check VM VNC Configuration

```bash
# List all VMs and their VNC ports
virsh list --all
virsh vncdisplay your-vm-name
# Output: :1 means port 5901
```

### Configure VNC in VM XML

Edit VM configuration:

```bash
virsh edit your-vm-name
```

Add or modify the graphics section:

```xml
<graphics type='vnc' port='-1' autoport='yes' listen='127.0.0.1'>
  <listen type='address' address='127.0.0.1'/>
</graphics>
```

Options explained:

| Attribute | Value | Description |
|-----------|-------|-------------|
| `port` | `-1` | Auto-assign port |
| `autoport` | `yes` | Automatically select available port |
| `listen` | `127.0.0.1` | Bind to localhost only (secure) |
| `listen` | `0.0.0.0` | Bind to all interfaces (use with firewall) |
| `passwd` | `secret` | Optional VNC password |

### Listen on All Interfaces

For Tailscale or LAN access:

```xml
<graphics type='vnc' port='5901' autoport='no' listen='0.0.0.0' passwd='your-password'>
  <listen type='address' address='0.0.0.0'/>
</graphics>
```

!!! warning "Firewall Required"
    When binding to `0.0.0.0`, ensure your firewall blocks VNC from untrusted networks.

### Using virt-manager

In virt-manager GUI:

1. Open VM settings
2. Go to "Display VNC"
3. Set address to "All interfaces" or specific IP
4. Optionally set password
5. Click Apply

## TigerVNC Server (Desktop Linux)

For accessing a full Linux desktop session.

### Installation

=== "Ubuntu/Debian"
    ```bash
    sudo apt install tigervnc-standalone-server tigervnc-common
    ```

=== "Fedora/RHEL"
    ```bash
    sudo dnf install tigervnc-server
    ```

=== "Arch"
    ```bash
    sudo pacman -S tigervnc
    ```

### Initial Setup

Set VNC password:

```bash
vncpasswd
# Enter password twice
# Answer "n" for view-only password
```

### Start VNC Server

```bash
# Start on display :1 (port 5901)
vncserver :1 -geometry 1920x1080 -depth 24

# Start with specific desktop
vncserver :1 -geometry 1920x1080 -xstartup /usr/bin/startxfce4
```

### Configure Desktop Environment

Create `~/.vnc/xstartup`:

```bash
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS

# Choose your desktop environment:

# GNOME
# exec gnome-session

# XFCE (lighter)
exec startxfce4

# KDE Plasma
# exec startplasma-x11

# i3
# exec i3
```

Make executable:

```bash
chmod +x ~/.vnc/xstartup
```

### Systemd Service

Create `/etc/systemd/system/vncserver@.service`:

```ini
[Unit]
Description=TigerVNC server for %i
After=syslog.target network.target

[Service]
Type=forking
User=%i
WorkingDirectory=/home/%i
ExecStart=/usr/bin/vncserver -geometry 1920x1080 -depth 24 -localhost no :1
ExecStop=/usr/bin/vncserver -kill :1
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable vncserver@username
sudo systemctl start vncserver@username
```

## x11vnc (Share Existing Display)

Share the actual running X session (what's shown on the physical monitor).

### Installation

```bash
sudo apt install x11vnc
```

### One-time Use

```bash
# Share display :0 (main display)
x11vnc -display :0 -auth guess -forever -loop -noxdamage -repeat -rfbauth ~/.vnc/passwd -rfbport 5900 -shared
```

### Systemd Service

Create `/etc/systemd/system/x11vnc.service`:

```ini
[Unit]
Description=x11vnc VNC Server
After=display-manager.service

[Service]
Type=simple
ExecStart=/usr/bin/x11vnc -display :0 -auth guess -forever -loop -noxdamage -repeat -rfbport 5900 -shared -nopw
ExecStop=/usr/bin/killall x11vnc
Restart=on-failure

[Install]
WantedBy=graphical.target
```

## wayvnc (Wayland)

For Wayland-based desktops (modern GNOME, KDE).

### Installation

```bash
sudo apt install wayvnc
```

### Usage

```bash
wayvnc 0.0.0.0 5900
```

Configuration in `~/.config/wayvnc/config`:

```ini
address=0.0.0.0
port=5900
```

## Performance Tuning

### Server-side Optimizations

1. **Reduce color depth** for slow connections:
   ```bash
   vncserver :1 -depth 16
   ```

2. **Lower resolution**:
   ```bash
   vncserver :1 -geometry 1280x720
   ```

3. **Disable desktop effects** in guest DE

### QEMU VNC Options

In VM XML:

```xml
<graphics type='vnc' port='5901' autoport='no'>
  <listen type='address' address='0.0.0.0'/>
  <image compression='auto_glz'/>
  <streaming mode='filter'/>
  <zlib compression='auto'/>
</graphics>
```

## Firewall Configuration

### UFW Rules

```bash
# Allow VNC from Tailscale only
sudo ufw allow in on tailscale0 to any port 5900:5910 proto tcp

# Allow VNC from LAN
sudo ufw allow from 192.168.1.0/24 to any port 5900:5910 proto tcp
```

### Verify Listening

```bash
ss -tlnp | grep 590
```

## Troubleshooting

### Connection Refused

```bash
# Check VNC is running
ps aux | grep vnc

# Check port is listening
ss -tlnp | grep 5901

# Check firewall
sudo ufw status | grep 590
```

### Black Screen

1. Check `~/.vnc/xstartup` is executable
2. Verify desktop environment is installed
3. Check `~/.vnc/*.log` for errors

### Performance Issues

1. Enable compression in client
2. Reduce color depth
3. Disable desktop effects
4. Check network latency: `ping server`

## Security Checklist

- [ ] VNC password set (`vncpasswd`)
- [ ] Firewall configured
- [ ] Not exposed to internet
- [ ] Using Tailscale or SSH tunnel for remote access
- [ ] Localhost-only for KVM (access via Tailscale)
