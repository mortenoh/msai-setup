# Taildrop

## Overview

Taildrop is Tailscale's secure file sharing feature. Transfer files directly between devices on your tailnet without cloud storage or external services.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Taildrop File Transfer                                    │
│                                                                              │
│   ┌─────────────┐                              ┌─────────────┐              │
│   │   Laptop    │     document.pdf             │   Desktop   │              │
│   │             │ ─────────────────────────────►│             │              │
│   │             │     Direct, encrypted        │             │              │
│   └─────────────┘     over Tailscale           └─────────────┘              │
│                                                                              │
│   Features:                                                                  │
│   • End-to-end encrypted                                                    │
│   • No size limits                                                          │
│   • No cloud storage involved                                               │
│   • Works across all platforms                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## How It Works

1. Files transfer directly between devices via WireGuard tunnel
2. No intermediate servers store your files
3. Transfer speed depends on connection between devices
4. Files queue if recipient is offline (temporarily)

## Sending Files

### CLI

```bash
# Send single file
tailscale file cp document.pdf my-laptop:

# Send multiple files
tailscale file cp file1.txt file2.txt my-laptop:

# Send with glob pattern
tailscale file cp *.jpg my-laptop:

# Send to multiple recipients
tailscale file cp report.pdf laptop: desktop: phone:
```

### macOS/iOS

1. **Finder/Files**: Right-click file → Share → Tailscale
2. **Share Sheet**: Any app → Share → Tailscale → Select device
3. **Drag and Drop**: Drag file onto Tailscale menu bar icon

### Windows

1. **File Explorer**: Right-click → Send to → Tailscale
2. **System Tray**: Right-click Tailscale → Send file

### Android

1. **Share**: Any app → Share → Tailscale
2. **App**: Open Tailscale → Send files

## Receiving Files

### CLI

```bash
# Receive files to current directory
tailscale file get .

# Receive to specific directory
tailscale file get ~/Downloads/

# List pending files (without receiving)
tailscale file get --verbose .
```

### GUI Applications

- **macOS**: Files appear in Downloads or configured location
- **Windows**: Files appear in Downloads
- **iOS/Android**: Notification appears, tap to save
- **Linux**: Use `tailscale file get` or configure GUI

### Auto-Receive

Configure automatic receiving:

**macOS**: Tailscale Preferences → Taildrop → Set receive location

**Linux systemd service**:

```bash
# /etc/systemd/system/taildrop-receive.service
[Unit]
Description=Taildrop file receiver
After=tailscaled.service

[Service]
Type=simple
ExecStart=/usr/bin/tailscale file get --loop /home/user/Taildrop/
Restart=always
User=user

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now taildrop-receive
```

## File Transfer Status

### Check Pending Files

```bash
# List files waiting to be received
tailscale file get --verbose --wait=false .
```

### Monitor Transfer

```bash
# Watch for incoming files
tailscale file get --loop ~/Taildrop/
```

## Performance

### Transfer Speed

Speed depends on:
- **Direct connection**: Full speed of slowest link
- **Relayed (DERP)**: Limited by relay server bandwidth

Check connection type:

```bash
tailscale ping recipient-device
```

### Large Files

No size limit, but consider:
- Connection stability for very large files
- Available disk space on recipient
- Network speed

## ACL Configuration

Control who can send files to whom:

```json
{
  "acls": [
    {
      "action": "accept",
      "src": ["group:employees"],
      "dst": ["group:employees"],
      "proto": ["tcp"],
      "dstPorts": ["*:*"]
    }
  ]
}
```

Taildrop uses the same ACLs as other Tailscale traffic.

## Security

### Encryption

- Files encrypted in transit via WireGuard
- No intermediate storage on Tailscale servers
- Files transfer directly between devices

### Access Control

- Only tailnet members can send you files
- ACLs can restrict who sends to whom
- No anonymous or public sharing

### Verification

- Files come from authenticated Tailscale identities
- You can verify sender via `tailscale status`

## Troubleshooting

### Files Not Sending

```bash
# Check connectivity
tailscale ping recipient-device

# Verify Tailscale is running
tailscale status

# Check ACLs allow traffic
```

### Files Not Receiving

```bash
# Check for pending files
tailscale file get --verbose --wait=false .

# Ensure receive directory exists and is writable
ls -la ~/Taildrop/

# Check Tailscale is connected
tailscale status
```

### Slow Transfer

```bash
# Check if using DERP relay
tailscale ping recipient
# "via DERP" = relayed (slower)
# "via <IP>" = direct (faster)

# Improve direct connectivity
# - Open UDP/41641
# - Check NAT type with `tailscale netcheck`
```

### Permission Errors

```bash
# Linux: ensure proper ownership
sudo chown -R $USER:$USER ~/Taildrop/

# Check SELinux/AppArmor if applicable
```

## Platform Notes

### Linux Headless

For servers without GUI:

```bash
# Create receive directory
mkdir -p ~/Taildrop

# Run receiver in background
nohup tailscale file get --loop ~/Taildrop/ &

# Or use systemd service (see above)
```

### Docker

Taildrop works in containers:

```yaml
services:
  tailscale:
    image: tailscale/tailscale:latest
    volumes:
      - ./taildrop:/taildrop
    environment:
      - TS_AUTHKEY=${TS_AUTHKEY}
```

```bash
# In container
tailscale file get --loop /taildrop/
```

### iOS Limitations

- Files save to Files app
- Large files may timeout on mobile connection
- Background receiving limited by iOS

## Comparison with Alternatives

| Feature | Taildrop | AirDrop | Cloud Storage |
|---------|----------|---------|---------------|
| Cross-platform | ✓ | Apple only | ✓ |
| No account needed | Via Tailscale | Yes | No |
| End-to-end encrypted | ✓ | ✓ | Varies |
| Works over internet | ✓ | Local only | ✓ |
| File size limit | None | 5GB practical | Varies |
| Speed | Direct WireGuard | Local WiFi | Upload/Download |

## Best Practices

1. **Set up receive directory** on each device
2. **Use auto-receive** for convenience
3. **Monitor disk space** on receiving devices
4. **Check connection type** for large transfers
5. **Use direct connections** when possible for speed
