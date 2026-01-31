# Connection Troubleshooting

## Quick Diagnostics

```bash
# Check Tailscale status
tailscale status

# Network check
tailscale netcheck

# Test specific peer
tailscale ping peer-name

# View logs
journalctl -u tailscaled -f
```

## Common Connection Issues

### Device Not Appearing in Status

**Symptoms:**
- Device not listed in `tailscale status`
- Can't ping device

**Causes:**
- Device not authenticated
- Device offline
- Different tailnet

**Solutions:**

```bash
# Check if authenticated
tailscale status

# If not, authenticate
sudo tailscale up

# Verify tailnet
tailscale status --json | jq '.Self.DNSName'
```

### Can't Connect to Peer

**Symptoms:**
- Ping timeout
- Connection refused

**Diagnostic Steps:**

```bash
# 1. Verify peer is online
tailscale status
# Look for peer in list

# 2. Check connectivity
tailscale ping peer-name

# 3. Check for relay
tailscale status | grep peer-name
# "relay" means indirect connection
# "direct" means peer-to-peer

# 4. Debug connection
tailscale ping --verbose peer-name
```

### Using DERP Relay (Not Direct)

**Symptoms:**
- `tailscale status` shows "relay" not "direct"
- Higher latency

**Causes:**
- Symmetric NAT
- Firewall blocking UDP
- Both peers behind strict NAT

**Solutions:**

```bash
# Check NAT type
tailscale netcheck
# Look for "MappingVariesByDestIP" - true means symmetric NAT

# Open firewall port
# On router/firewall, allow UDP 41641 inbound

# Try restarting to trigger new connection
sudo tailscale down && sudo tailscale up
```

### Connection Drops

**Symptoms:**
- Intermittent disconnections
- Peer appears online then offline

**Causes:**
- NAT timeout
- Network instability
- Key expiry

**Solutions:**

```bash
# Check key status
tailscale status --json | jq '.Self.KeyExpiry'

# Check for NAT issues
tailscale netcheck

# Monitor connection
watch -n 5 tailscale status
```

## Authentication Issues

### Key Expired

**Symptoms:**
- "key expired" message
- Device shows as offline

**Solutions:**

```bash
# Re-authenticate
sudo tailscale up --force-reauth

# Or for permanent servers, disable key expiry in admin console
```

### Auth Key Invalid

**Symptoms:**
- "auth key invalid" error

**Causes:**
- Key expired
- Key revoked
- Key already used (one-time key)

**Solutions:**

```bash
# Generate new auth key in admin console
# Then:
sudo tailscale up --auth-key=tskey-auth-NEW-KEY
```

### Can't Login

**Symptoms:**
- Browser auth fails
- "unable to authenticate" error

**Solutions:**

```bash
# Try explicit logout first
sudo tailscale logout

# Clear state and retry
sudo systemctl stop tailscaled
sudo rm -rf /var/lib/tailscale
sudo systemctl start tailscaled
sudo tailscale up
```

## DNS Issues

### Can't Resolve MagicDNS Names

**Symptoms:**
- `ping my-server` fails
- `ping 100.x.x.x` works

**Solutions:**

```bash
# Check MagicDNS is enabled
tailscale dns status

# Verify DNS setting
sudo tailscale up --accept-dns

# Check system DNS
cat /etc/resolv.conf

# Restart DNS resolver
sudo systemctl restart systemd-resolved
```

### Split DNS Not Working

**Solutions:**

```bash
# Test specific DNS query
dig @100.100.100.100 my-server.tailnet.ts.net

# Check DNS nameserver is reachable
tailscale ping dns-server

# Verify configuration in admin console
```

## Firewall Issues

### Firewall Blocking Tailscale

**Symptoms:**
- Connection timeout
- "netcheck" shows issues

**Diagnostic:**

```bash
tailscale netcheck
# Check for:
# - UDP: false (blocked)
# - IPv4/IPv6: no
```

**Solutions:**

```bash
# UFW
sudo ufw allow 41641/udp

# iptables
sudo iptables -A INPUT -p udp --dport 41641 -j ACCEPT
sudo iptables -A OUTPUT -p udp --dport 41641 -j ACCEPT

# firewalld
sudo firewall-cmd --add-port=41641/udp --permanent
sudo firewall-cmd --reload
```

### Corporate Firewall

If behind strict corporate firewall:

```bash
# Tailscale uses these ports:
# UDP 41641 - WireGuard (primary)
# UDP 3478 - STUN
# TCP 443 - HTTPS (fallback)

# If all else fails, Tailscale can tunnel over HTTPS
# via DERP relay
```

## Service Issues

### tailscaled Not Running

```bash
# Check status
sudo systemctl status tailscaled

# Start if stopped
sudo systemctl start tailscaled

# Enable on boot
sudo systemctl enable tailscaled

# Check for errors
journalctl -u tailscaled --no-pager -n 100
```

### Interface Missing

```bash
# Check for tailscale0
ip addr show tailscale0

# If missing, restart daemon
sudo systemctl restart tailscaled

# Check logs for errors
journalctl -u tailscaled | grep -i error
```

## Debug Tools

### Comprehensive Debug

```bash
# Network state
tailscale netcheck --verbose

# Connection details
tailscale debug netmap

# Preferences
tailscale debug prefs

# Generate bug report
tailscale bugreport
```

### Packet Capture

```bash
# Capture Tailscale traffic
sudo tcpdump -i tailscale0 -n

# Capture WireGuard UDP
sudo tcpdump -i eth0 udp port 41641
```

## Escalation

If issues persist:

1. **Generate bug report:** `tailscale bugreport`
2. **Collect logs:** `journalctl -u tailscaled > logs.txt`
3. **Collect netcheck:** `tailscale netcheck > netcheck.txt`
4. **Contact support** with collected info

## Quick Reference

| Issue | Quick Fix |
|-------|-----------|
| Not authenticated | `sudo tailscale up` |
| Key expired | `sudo tailscale up --force-reauth` |
| DNS not working | `sudo tailscale up --accept-dns` |
| Using relay | Open UDP/41641 inbound |
| Service stopped | `sudo systemctl start tailscaled` |
| Can't reach peer | Check peer is online, check ACLs |
