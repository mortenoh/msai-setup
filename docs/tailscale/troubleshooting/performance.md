# Performance Troubleshooting

## Measuring Performance

### Throughput Test

```bash
# On server
iperf3 -s

# On client (through Tailscale)
iperf3 -c server.tailnet.ts.net

# Compare with direct connection if available
iperf3 -c server-direct-ip
```

### Latency Test

```bash
# Basic ping
tailscale ping my-server

# Multiple pings
tailscale ping --c 100 my-server

# Track path
tailscale ping --verbose my-server
```

## Common Performance Issues

### High Latency

**Symptoms:**
- Ping > 100ms when direct should be < 50ms
- Slow SSH sessions
- Laggy connections

**Causes & Solutions:**

```
┌──────────────────────────────────────────────────────────────────────────────┐
│   Cause                           Solution                                   │
│   ─────                           ────────                                   │
│   Using DERP relay                Open UDP/41641, check NAT                 │
│   Geographic distance             Use closer exit node if applicable        │
│   Network congestion              Check ISP, try different times            │
│   Symmetric NAT                   May require relay (unavoidable)           │
└──────────────────────────────────────────────────────────────────────────────┘
```

**Diagnostic:**

```bash
# Check connection type
tailscale status
# "relay" = problem
# "direct" = good

# Check DERP latency
tailscale netcheck
# Look at DERP latency section
```

### Using DERP When Direct Should Work

```bash
# Force new connection
sudo tailscale down && sudo tailscale up

# Check NAT type
tailscale netcheck | grep -i mapping
# "MappingVariesByDestIP: true" = symmetric NAT (problematic)

# Open firewall
sudo ufw allow 41641/udp

# Check UPnP/NAT-PMP
tailscale netcheck | grep -i portmap
```

### Low Throughput

**Expected Performance:**
- Direct: Near line speed (minus ~5% WireGuard overhead)
- DERP: Limited by relay bandwidth

**Diagnostic:**

```bash
# Test with iperf3
iperf3 -c peer.tailnet.ts.net -t 30

# Check for packet loss
tailscale ping --c 100 peer | grep -i loss

# Monitor during transfer
watch tailscale status
```

**Solutions:**

| Issue | Solution |
|-------|----------|
| DERP bottleneck | Ensure direct connection |
| MTU issues | Usually auto-handled |
| CPU bottleneck | Check both endpoints |
| Network congestion | Test at different times |

### Connection Instability

**Symptoms:**
- Frequent disconnections
- Connection flapping
- Path changes

**Diagnostic:**

```bash
# Monitor connection
watch -n 2 tailscale status

# Check for endpoint changes
tailscale ping --verbose peer

# View logs
journalctl -u tailscaled -f | grep -i "endpoint\|handshake"
```

**Solutions:**

```bash
# Increase keepalive (if NAT timeout)
# Usually handled automatically

# Check for competing network managers
sudo systemctl status NetworkManager

# Verify stable internet
ping -c 100 8.8.8.8 | tail -1
```

## Platform-Specific Performance

### Linux Optimization

```bash
# Check if kernel WireGuard is used (faster)
lsmod | grep wireguard

# If not, install kernel module
sudo apt install wireguard  # Debian/Ubuntu
sudo dnf install wireguard-tools  # Fedora

# Increase network buffers
sudo sysctl -w net.core.rmem_max=26214400
sudo sysctl -w net.core.wmem_max=26214400
```

### macOS

- Ensure using System Extension (not Network Extension)
- Check "Tailscale" in System Preferences → Security & Privacy

### Windows

- Ensure WireGuard driver is installed
- Check Windows Firewall settings

### Docker/Containers

```bash
# Ensure TUN device access
ls -la /dev/net/tun

# Check container networking mode
docker inspect container | grep NetworkMode

# Host networking is fastest
docker run --network=host ...
```

## Exit Node Performance

### Slow Through Exit Node

```bash
# Check exit node connection type
tailscale status
# Ensure "direct" not "relay"

# Test exit node bandwidth
# SSH to exit node, run:
speedtest-cli

# Test latency to exit node
tailscale ping exit-node
```

### Optimizing Exit Node

```bash
# Choose geographically close exit node
# Check available exit nodes
tailscale exit-node list

# Switch exit node
sudo tailscale up --exit-node=closer-server
```

## Subnet Router Performance

### Slow Through Subnet Router

All traffic to subnet goes through router - bandwidth limited by:
- Router's Tailscale connection
- Router's local network connection

**Solutions:**

```bash
# Ensure router has direct connection
tailscale status

# Check router's network
# On router:
iperf3 -c local-server

# Consider multiple subnet routers
# Tailscale routes to nearest
```

## Benchmarking

### Baseline Test

```bash
# Direct network baseline
iperf3 -c server-direct-ip

# Tailscale performance
iperf3 -c server.tailnet.ts.net

# Compare: Tailscale should be 90-95% of direct
```

### Latency Baseline

```bash
# Direct
ping -c 50 server-direct-ip

# Tailscale
tailscale ping --c 50 server

# Direct connection adds ~1-5ms
# DERP adds 30-100ms+ depending on region
```

## Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| High latency | Check `tailscale status` for relay |
| Low throughput | Ensure direct connection |
| Unstable connection | Open UDP/41641 on firewall |
| Exit node slow | Choose closer exit node |
| Subnet router slow | Check router's connection |

## When Performance is Unavoidably Limited

Some situations limit performance:

1. **Both peers behind symmetric NAT**: DERP required
2. **Very distant peers**: Physics limits latency
3. **Congested networks**: Not Tailscale's fault
4. **Slow endpoints**: Tailscale won't be faster than hardware
