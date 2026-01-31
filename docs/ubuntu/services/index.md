# Service Management Overview

This section covers hardening systemd services, disabling unnecessary services, and applying security isolation to running processes.

## Service Security Philosophy

### Attack Surface Reduction

Every running service is a potential attack vector:

```
┌─────────────────────────────────────────────────────────────┐
│                    Attack Surface                            │
├─────────────────────────────────────────────────────────────┤
│  Each Service = Potential Entry Point                        │
│                                                              │
│  [SSH] [HTTP] [DB] [Mail] [DNS] [FTP] [NFS] [Cups]...       │
│    ↓     ↓     ↓     ↓      ↓     ↓     ↓      ↓            │
│   Use   Use  Eval  Remove Remove Remove Remove Remove       │
└─────────────────────────────────────────────────────────────┘
```

### Service Hardening Layers

| Layer | Description |
|-------|-------------|
| Disable unnecessary | Remove what you don't need |
| User isolation | Run as non-root |
| Filesystem isolation | Restrict file access |
| Network isolation | Limit network capabilities |
| Capability restriction | Drop unneeded capabilities |
| System call filtering | Block unnecessary syscalls |

## Section Contents

| Page | Description |
|------|-------------|
| [Disable Unnecessary](disable-unnecessary.md) | Identify and remove unneeded services |
| [Service Isolation](service-isolation.md) | systemd sandboxing and hardening |
| [Network Services](network-services.md) | Hardening common network services |

## Quick Assessment

### List Running Services

```bash
# All running services
systemctl list-units --type=service --state=running

# Enabled at boot
systemctl list-unit-files --type=service --state=enabled

# Listening network services
sudo ss -tlnp
```

### Quick Security Audit

```bash
#!/bin/bash
echo "=== Service Security Audit ==="

echo -e "\n--- Running Services ---"
systemctl list-units --type=service --state=running --no-pager | head -20

echo -e "\n--- Listening Ports ---"
sudo ss -tlnp | grep LISTEN

echo -e "\n--- Services Running as Root ---"
ps aux | awk '$1=="root" && $11!~/^\[/ {print $11}' | sort -u | head -20

echo -e "\n--- Services Without Hardening ---"
for unit in $(systemctl list-units --type=service --state=running --no-legend | awk '{print $1}' | head -10); do
    score=$(systemd-analyze security "$unit" 2>/dev/null | tail -1 | grep -oP '\d+\.\d+')
    echo "$unit: $score"
done
```

## Service Security Basics

### Essential vs Optional Services

| Essential | Consider Disabling |
|-----------|-------------------|
| systemd-journald | cups (printing) |
| systemd-udevd | avahi-daemon (mDNS) |
| dbus | bluetooth |
| NetworkManager/networkd | ModemManager |
| ssh | snapd (if not using snaps) |
| cron | multipathd (if no SAN) |

### Check If Service Is Needed

Before disabling, verify:

1. **Is it in use?** Check connections/logs
2. **Do other services depend on it?** Check dependencies
3. **Will disabling break anything?** Test in staging

```bash
# Check dependencies
systemctl list-dependencies --reverse service-name

# Check if recently active
journalctl -u service-name --since "1 week ago" | head
```

## systemd Security Features

### Available Hardening Options

systemd provides extensive sandboxing:

| Category | Options |
|----------|---------|
| User/Group | User=, Group=, DynamicUser= |
| Filesystem | ProtectSystem=, ProtectHome=, PrivateTmp= |
| Network | PrivateNetwork=, RestrictAddressFamilies= |
| Capabilities | CapabilityBoundingSet=, AmbientCapabilities= |
| System calls | SystemCallFilter=, SystemCallArchitectures= |
| Resources | MemoryMax=, CPUQuota=, TasksMax= |

### Security Score

```bash
# Check service security score
systemd-analyze security nginx

# Output shows:
# - Each security setting
# - Current status (enabled/disabled)
# - Exposure score (0=secure, 10=exposed)

# Batch check all services
systemd-analyze security
```

## Common Patterns

### Minimal Service

```ini
[Unit]
Description=Minimal Secure Service

[Service]
Type=simple
User=appuser
Group=appgroup
ExecStart=/usr/local/bin/myapp

# Security
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
```

### Network Service

```ini
[Unit]
Description=Network Service

[Service]
Type=simple
User=nobody
ExecStart=/usr/local/bin/netservice

# Security
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes

# Network specific
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
RestrictAddressFamilies=AF_INET AF_INET6

[Install]
WantedBy=multi-user.target
```

## Best Practices

### Service Hardening Checklist

- [ ] Service runs as non-root user
- [ ] Filesystem access is restricted
- [ ] Private tmp directory is used
- [ ] Network access is limited
- [ ] Capabilities are minimized
- [ ] System calls are filtered
- [ ] Resource limits are set

### Monitoring

```bash
# Watch service resource usage
systemd-cgtop

# Check service status
systemctl status service-name

# View service security settings
systemctl show service-name | grep -E "(User|Protect|Private|Capability)"
```

## Quick Reference

### Commands

```bash
# List services
systemctl list-units --type=service
systemctl list-unit-files --type=service

# Manage service
systemctl start|stop|restart|reload service
systemctl enable|disable service
systemctl mask|unmask service

# Security analysis
systemd-analyze security service
systemd-analyze security  # All services

# View settings
systemctl show service
systemctl cat service
```

### Key Paths

| Path | Purpose |
|------|---------|
| /lib/systemd/system/ | Package units |
| /etc/systemd/system/ | Admin units (override) |
| /run/systemd/system/ | Runtime units |

## Next Steps

Begin with [Disable Unnecessary Services](disable-unnecessary.md) to reduce attack surface.
