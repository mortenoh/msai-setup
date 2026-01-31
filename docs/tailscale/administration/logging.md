# Logging & Monitoring

## Tailscale Logs

### Linux (systemd)

```bash
# View daemon logs
journalctl -u tailscaled -f

# Recent logs
journalctl -u tailscaled --since "10 minutes ago"

# Filter by priority
journalctl -u tailscaled -p err

# Export logs
journalctl -u tailscaled --since today > tailscale-logs.txt
```

### macOS

```bash
# View logs
log show --predicate 'subsystem == "com.tailscale.ipn"' --last 1h

# Stream logs
log stream --predicate 'subsystem == "com.tailscale.ipn"'
```

### Windows

```powershell
# Event Viewer
Get-EventLog -LogName Application -Source Tailscale -Newest 50

# Or open Event Viewer GUI
# Application and Services Logs → Tailscale
```

### Docker

```bash
docker logs tailscale-container -f

# Or with compose
docker-compose logs -f tailscale
```

## Log Levels

### Setting Log Level

```bash
# Verbose logging
sudo tailscaled --verbose=2

# Or via environment
# /etc/default/tailscaled
FLAGS="--verbose=2"
```

### Verbosity Levels

| Level | Output |
|-------|--------|
| 0 | Errors only |
| 1 | Warnings and errors |
| 2 | Info, warnings, errors |
| 3+ | Debug (very verbose) |

## Network Diagnostics

### Connection Status

```bash
# Overall status
tailscale status

# JSON for parsing
tailscale status --json | jq

# Specific peer
tailscale status --json | jq '.Peer["nodekey:xxx"]'
```

### Network Check

```bash
# Full network diagnostic
tailscale netcheck

# Continuous check
tailscale netcheck --every 30s
```

### Ping Statistics

```bash
# Ping with stats
tailscale ping --c 100 my-server

# Until direct connection
tailscale ping --until-direct my-server
```

## Admin Console Logs

### Machine Logs

1. Go to **Machines**
2. Select a device
3. View connection history, status changes

### Audit Logs (Enterprise)

**Logs** tab shows:
- Authentication events
- Device registrations/removals
- ACL changes
- DNS configuration changes
- Admin actions

### Export Logs

Enterprise plans can export audit logs:
- SIEM integration
- Webhook notifications
- API access

## Monitoring Integrations

### Prometheus

```bash
# Enable metrics endpoint
sudo tailscaled --debug=:8080

# Metrics at
curl localhost:8080/debug/metrics
```

Example metrics:
```
tailscaled_inbound_bytes_total
tailscaled_outbound_bytes_total
tailscaled_peer_count
tailscaled_derp_home_latency_seconds
```

### Grafana Dashboard

Create dashboards for:
- Connected peers
- Traffic volume
- Connection latency
- DERP usage

### Datadog

```yaml
# datadog.yaml
logs:
  - type: journald
    source: tailscale
    service: tailscaled
    path: /run/log/journal
```

## Alerting

### Connection Alerts

Monitor for:
- Device offline
- Key expiry approaching
- Unusual traffic patterns
- DERP relay usage (direct connection failed)

### Example Alert Rules

```yaml
# Prometheus alert
- alert: TailscaleDeviceOffline
  expr: tailscaled_peer_last_seen_seconds > 300
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Tailscale device offline"
```

## Debug Commands

### Debug Information

```bash
# Full debug info
tailscale debug

# Specific debug commands
tailscale debug prefs        # Current preferences
tailscale debug netmap       # Network map
tailscale debug portmap      # Port mappings
tailscale debug derp-map     # DERP server map
tailscale debug metrics      # Metrics dump
```

### Component Logging

```bash
# Enable component-specific logging
tailscale debug component-logs magicsock

# View component logs in journal
journalctl -u tailscaled | grep magicsock
```

### Capture Network Traffic

```bash
# Capture on Tailscale interface
sudo tcpdump -i tailscale0 -w capture.pcap

# Capture WireGuard UDP (encrypted)
sudo tcpdump -i eth0 udp port 41641 -w wireguard.pcap
```

## Bug Reports

### Generate Bug Report

```bash
tailscale bugreport
```

Outputs a URL with:
- Configuration
- Logs
- Network state
- No private keys or traffic

### Manual Collection

```bash
# Collect info for support
tailscale status --json > status.json
tailscale netcheck > netcheck.txt
tailscale debug prefs > prefs.txt
journalctl -u tailscaled --since "1 hour ago" > logs.txt
```

## Security Logging

### SSH Session Recording

```json
{
  "ssh": [
    {
      "action": "accept",
      "src": ["*"],
      "dst": ["tag:server"],
      "users": ["*"],
      "recorder": ["tag:recorder"]
    }
  ]
}
```

### Network Flow Logs

Enterprise feature - log all connection attempts:
- Source/destination
- Ports
- Timestamps
- Allow/deny decisions

## Best Practices

1. **Enable verbose logging** during troubleshooting
2. **Centralize logs** for multi-device visibility
3. **Set up alerts** for critical events
4. **Regular log review** for security
5. **Export audit logs** for compliance
6. **Use bug reports** for support tickets
