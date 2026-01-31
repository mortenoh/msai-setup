# Service Isolation

systemd provides powerful sandboxing features to isolate services. This page covers applying security restrictions to limit damage from compromised services.

## Understanding Service Isolation

### Defense in Depth

Even if a service is compromised, isolation limits what attackers can do:

```
┌─────────────────────────────────────────────────────────────┐
│                    Compromised Service                       │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────┐
│                   Isolation Layers                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ User        │ │ Filesystem  │ │ Network     │           │
│  │ Namespace   │ │ Restrictions│ │ Restrictions│           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐           │
│  │ Capability  │ │ System Call │ │ Resource    │           │
│  │ Limits      │ │ Filtering   │ │ Limits      │           │
│  └─────────────┘ └─────────────┘ └─────────────┘           │
└─────────────────────────────────────────────────────────────┘
          │
          ▼
     Limited damage!
```

## Assessing Current Security

### Security Score Analysis

```bash
# Check specific service
systemd-analyze security nginx.service

# Check all services
systemd-analyze security

# Output shows score 0-10 (lower = more secure)
```

### Understanding the Score

| Score | Rating | Action |
|-------|--------|--------|
| 0.0-2.0 | Safe | Maintain |
| 2.1-4.0 | OK | Review |
| 4.1-6.0 | Medium | Harden |
| 6.1-8.0 | Exposed | Prioritize |
| 8.1-10.0 | Unsafe | Urgent |

## Creating Service Overrides

### Override Directory Method

```bash
# Create override for existing service
sudo systemctl edit nginx.service
```

This creates `/etc/systemd/system/nginx.service.d/override.conf`.

### Full Unit Override

```bash
# Copy and modify entire unit
sudo cp /lib/systemd/system/nginx.service /etc/systemd/system/nginx.service
sudo nano /etc/systemd/system/nginx.service
```

### Apply Changes

```bash
sudo systemctl daemon-reload
sudo systemctl restart service-name
```

## User and Group Isolation

### Run as Non-Root

```ini
[Service]
User=nginx
Group=nginx
```

### Dynamic User

Creates ephemeral user that doesn't persist:

```ini
[Service]
DynamicUser=yes
```

### Supplementary Groups

```ini
[Service]
User=myapp
Group=myapp
SupplementaryGroups=ssl-cert
```

## Filesystem Restrictions

### ProtectSystem

| Value | Effect |
|-------|--------|
| false | No protection |
| true | /usr, /boot read-only |
| full | Above + /etc read-only |
| strict | Entire filesystem read-only (use ReadWritePaths) |

```ini
[Service]
ProtectSystem=strict
ReadWritePaths=/var/lib/myapp /var/log/myapp
```

### ProtectHome

| Value | Effect |
|-------|--------|
| false | No protection |
| true | /home, /root, /run/user inaccessible |
| read-only | Above directories read-only |
| tmpfs | Above replaced with empty tmpfs |

```ini
[Service]
ProtectHome=yes
```

### Private Directories

```ini
[Service]
# Private /tmp
PrivateTmp=yes

# Private /dev (limited devices)
PrivateDevices=yes

# Specific paths
TemporaryFileSystem=/var:ro
BindPaths=/var/lib/myapp
BindReadOnlyPaths=/etc/ssl/certs
```

### Inaccessible Paths

```ini
[Service]
InaccessiblePaths=/home /root /mnt /media
```

## Network Restrictions

### Private Network

```ini
[Service]
# Complete network isolation
PrivateNetwork=yes
```

### Restrict Address Families

```ini
[Service]
# Only IPv4 and IPv6
RestrictAddressFamilies=AF_INET AF_INET6

# Add Unix sockets
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# Network service typical
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX AF_NETLINK
```

### IP Filtering

```ini
[Service]
IPAddressDeny=any
IPAddressAllow=192.168.1.0/24
IPAddressAllow=127.0.0.0/8
```

## Capability Restrictions

### Drop All, Add Specific

```ini
[Service]
# Start with nothing
CapabilityBoundingSet=

# Add only what's needed
CapabilityBoundingSet=CAP_NET_BIND_SERVICE

# For the process to use capabilities
AmbientCapabilities=CAP_NET_BIND_SERVICE
```

### Common Capabilities

| Capability | Purpose |
|------------|---------|
| CAP_NET_BIND_SERVICE | Bind ports < 1024 |
| CAP_NET_RAW | Raw sockets |
| CAP_CHOWN | Change file ownership |
| CAP_SETUID | Set process UID |
| CAP_SETGID | Set process GID |
| CAP_SYS_ADMIN | Various admin operations |
| CAP_DAC_OVERRIDE | Bypass file permissions |

### No New Privileges

Prevent gaining new privileges:

```ini
[Service]
NoNewPrivileges=yes
```

## System Call Filtering

### Predefined Filters

```ini
[Service]
# Common service calls only
SystemCallFilter=@system-service

# Exclude privileged calls
SystemCallFilter=~@privileged @resources
```

### System Call Groups

| Group | Contents |
|-------|----------|
| @system-service | Common service operations |
| @privileged | Requires capabilities |
| @network-io | Network operations |
| @file-system | Filesystem operations |
| @process | Process operations |
| @raw-io | Raw I/O |
| @reboot | System reboot |
| @swap | Swap operations |
| @clock | Time modification |
| @mount | Mount operations |
| @module | Kernel modules |

```ini
[Service]
SystemCallFilter=@system-service @network-io
SystemCallFilter=~@privileged @mount @reboot
SystemCallArchitectures=native
SystemCallErrorNumber=EPERM
```

## Kernel Protection

```ini
[Service]
# Can't load kernel modules
ProtectKernelModules=yes

# Can't modify kernel tunables (/proc, /sys)
ProtectKernelTunables=yes

# Can't read kernel logs
ProtectKernelLogs=yes

# Can't modify control groups
ProtectControlGroups=yes

# Can't change system clock
ProtectClock=yes

# Can't change hostname
ProtectHostname=yes
```

## Additional Restrictions

```ini
[Service]
# Can't create SUID/SGID files
RestrictSUIDSGID=yes

# Can't use realtime scheduling
RestrictRealtime=yes

# Lock execution domain
LockPersonality=yes

# W^X enforcement (no writable+executable memory)
MemoryDenyWriteExecute=yes

# Restrict namespace creation
RestrictNamespaces=yes
```

## Complete Hardened Template

### Web Application Service

```ini
# /etc/systemd/system/webapp.service

[Unit]
Description=Web Application
After=network.target

[Service]
Type=simple
User=webapp
Group=webapp
WorkingDirectory=/opt/webapp

# Process
ExecStart=/opt/webapp/bin/server
Restart=on-failure
RestartSec=5

# Filesystem
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes
ReadWritePaths=/opt/webapp/data /var/log/webapp

# Network
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# Privileges
NoNewPrivileges=yes
RestrictSUIDSGID=yes

# System calls
SystemCallFilter=@system-service @network-io
SystemCallFilter=~@privileged @resources
SystemCallArchitectures=native
SystemCallErrorNumber=EPERM

# Kernel
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes
ProtectClock=yes
ProtectHostname=yes

# Memory
MemoryDenyWriteExecute=yes
LockPersonality=yes

# Misc
RestrictRealtime=yes
RestrictNamespaces=yes

[Install]
WantedBy=multi-user.target
```

### Database Service

```ini
# /etc/systemd/system/mydb.service.d/override.conf

[Service]
# Filesystem
ProtectSystem=full
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/var/lib/mydb /var/log/mydb /run/mydb

# Network
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX

# Privileges
NoNewPrivileges=yes
CapabilityBoundingSet=
PrivateDevices=yes

# Kernel
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes

# Limited syscalls (databases need more)
SystemCallFilter=@system-service @io-event @ipc
SystemCallArchitectures=native
```

## Testing Hardening

### Verify Settings

```bash
# Show effective settings
systemctl show webapp.service | grep -E "(ProtectSystem|ProtectHome|User|NoNew)"

# Check security score improvement
systemd-analyze security webapp.service
```

### Test Service Works

```bash
# Restart and verify
sudo systemctl restart webapp.service
sudo systemctl status webapp.service

# Check for permission errors
sudo journalctl -u webapp.service | grep -i denied
```

### Debug Issues

```bash
# If service fails after hardening:

# Check logs
sudo journalctl -u webapp.service -n 50

# Temporarily relax restrictions
# Add back permissions one at a time

# Common fixes:
# - Add paths to ReadWritePaths
# - Add capabilities to CapabilityBoundingSet
# - Add syscall groups to SystemCallFilter
```

## Quick Reference

### Essential Hardening

```ini
[Service]
# Always apply these
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
PrivateDevices=yes

# Usually apply these
ProtectKernelModules=yes
ProtectKernelTunables=yes
ProtectControlGroups=yes
```

### Network Service

```ini
[Service]
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX
```

### Commands

```bash
# Check security
systemd-analyze security service-name

# Create override
sudo systemctl edit service-name

# Apply changes
sudo systemctl daemon-reload
sudo systemctl restart service-name

# View effective config
systemctl show service-name
systemctl cat service-name
```

## Next Steps

Continue to [Network Services](network-services.md) for guidance on hardening specific network-facing services.
