# Common Problems

## Quick Fixes Reference

| Problem | Quick Fix |
|---------|-----------|
| Not connected | `sudo tailscale up` |
| Key expired | `sudo tailscale up --force-reauth` |
| DNS not working | `sudo tailscale up --accept-dns` |
| Can't reach peer | Check peer online, check ACLs |
| Using relay | Open UDP/41641 on firewall |
| Service won't start | `sudo systemctl restart tailscaled` |
| Slow connection | Ensure direct (not relay) connection |

## Installation Problems

### "tailscale: command not found"

```bash
# Check installation
which tailscale
which tailscaled

# Reinstall
curl -fsSL https://tailscale.com/install.sh | sh

# Add to PATH if needed
export PATH=$PATH:/usr/sbin:/usr/bin
```

### Service Won't Start

```bash
# Check status
sudo systemctl status tailscaled

# View errors
journalctl -u tailscaled --no-pager -n 50

# Common fixes:
# 1. Check TUN device
ls -la /dev/net/tun

# 2. Create TUN if missing
sudo mkdir -p /dev/net
sudo mknod /dev/net/tun c 10 200
sudo chmod 666 /dev/net/tun

# 3. Restart service
sudo systemctl restart tailscaled
```

### Permission Denied

```bash
# Run with sudo
sudo tailscale up

# Or set operator
sudo tailscale set --operator=$USER
# Then run without sudo (for most commands)
```

## Authentication Problems

### Can't Authenticate

```bash
# Clear state and retry
sudo tailscale logout
sudo tailscale up

# If browser doesn't open
sudo tailscale up --qr  # Show QR code
# Or manually visit the URL shown
```

### Auth Key Not Working

```bash
# Check key hasn't expired
# Generate new key in admin console

# Verify key format
# Should be: tskey-auth-xxxx...

# Try with key
sudo tailscale up --auth-key=tskey-auth-NEW-KEY
```

### "This device is not authorized"

- Check if device is approved in admin console
- Verify you're in the correct tailnet
- Check ACLs don't block your access

## Connection Problems

### Can't Reach Peer

```bash
# 1. Verify peer is online
tailscale status
# Peer should be listed

# 2. Check ACLs
# Admin console → Access controls
# Verify rules allow your connection

# 3. Test connectivity
tailscale ping peer-name

# 4. Check firewall on target
# SSH to peer and check:
sudo iptables -L -n | grep 22  # or relevant port
```

### Intermittent Disconnections

```bash
# Check for NAT timeouts
tailscale netcheck

# Monitor connection
watch -n 5 tailscale status

# Check logs for clues
journalctl -u tailscaled -f
```

### "No route to host"

```bash
# Check if using subnet router
tailscale status

# Verify accept-routes is enabled
sudo tailscale up --accept-routes

# Check subnet router is online and approved
```

## DNS Problems

### MagicDNS Not Working

```bash
# Check accept-dns is set
sudo tailscale up --accept-dns

# Verify MagicDNS enabled in admin console
# DNS → MagicDNS → Enabled

# Check resolv.conf
cat /etc/resolv.conf
# Should include 100.100.100.100 or similar

# Restart DNS resolver
sudo systemctl restart systemd-resolved
```

### "Name resolution failed"

```bash
# Try full name
ping my-server.tailnet.ts.net

# If full name works but short doesn't:
# Check search domain in resolv.conf

# Test DNS directly
dig @100.100.100.100 my-server.tailnet.ts.net
```

## Subnet Router Problems

### Routes Not Working

```bash
# On router: verify routes advertised
tailscale status --json | jq '.Self.AllowedIPs'

# Check IP forwarding
sysctl net.ipv4.ip_forward
# Should be 1

# On client: verify routes accepted
sudo tailscale up --accept-routes

# Check route in admin console is approved
```

### Can't Reach Devices on Subnet

```bash
# Test from subnet router itself
ping 192.168.1.100  # Should work

# Check firewall allows forwarding
sudo iptables -L FORWARD -n

# Verify SNAT is working (or disable if needed)
tailscale debug prefs | grep SNAT
```

## Exit Node Problems

### Exit Node Not Working

```bash
# Check exit node is advertising
tailscale exit-node list

# Ensure exit node is approved in admin console

# Verify IP forwarding on exit node
sysctl net.ipv4.ip_forward
# Should be 1

# Check you're using exit node
tailscale status
# Should show exit node active
```

### "Unable to use exit node"

```bash
# Verify exit node is online
tailscale ping exit-node-name

# Check ACLs allow exit node usage
# Need autogroup:internet access

# Try different exit node
sudo tailscale up --exit-node=other-exit
```

## SSH Problems

### Tailscale SSH Not Working

```bash
# Verify SSH enabled on target
tailscale status
# Should show "ssh" capability

# Enable if not
sudo tailscale up --ssh

# Check SSH ACLs in admin console
```

### "Permission denied"

```bash
# Check ACL allows your user
# Admin console → Access controls → ssh section

# Verify Unix user exists on target
id username

# Check ACL explicitly allows username or autogroup:nonroot
```

## Container Problems

### TUN Device Not Available

```bash
# Check TUN exists
ls -la /dev/net/tun

# Create in container
mkdir -p /dev/net
mknod /dev/net/tun c 10 200

# Or run with --device
docker run --device=/dev/net/tun ...
```

### Container Can't Connect

```bash
# Check capabilities
docker run --cap-add=NET_ADMIN --cap-add=NET_RAW ...

# Check state volume
docker volume inspect tailscale-state

# Verify auth key
docker logs tailscale-container
```

## Platform-Specific Problems

### Linux: Interface Missing

```bash
# Restart daemon
sudo systemctl restart tailscaled

# Check for errors
journalctl -u tailscaled | grep -i error

# Recreate TUN
sudo modprobe tun
```

### macOS: "System Extension Blocked"

1. System Preferences → Security & Privacy
2. Click "Allow" for Tailscale
3. Restart Tailscale

### Windows: Not Connecting

```powershell
# Restart service
Restart-Service Tailscale

# Check Windows Firewall
Get-NetFirewallRule | Where-Object {$_.DisplayName -like "*Tailscale*"}

# Reinstall if needed
winget install Tailscale.Tailscale --force
```

## Getting Help

### Generate Bug Report

```bash
tailscale bugreport
```

Provides URL with diagnostic info for support.

### Collect Information

```bash
# Status
tailscale status --json > status.json

# Network check
tailscale netcheck > netcheck.txt

# Logs
journalctl -u tailscaled --since "1 hour ago" > logs.txt

# Preferences
tailscale debug prefs > prefs.txt
```

### Support Resources

- [Tailscale Knowledge Base](https://tailscale.com/kb/)
- [GitHub Issues](https://github.com/tailscale/tailscale/issues)
- [Community Forum](https://forum.tailscale.com/)
