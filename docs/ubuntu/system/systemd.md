# systemd Service Management

systemd is the init system and service manager for Ubuntu. Understanding systemd is essential for managing services, configuring system behavior, and implementing security controls.

## systemd Fundamentals

### What systemd Manages

```
┌─────────────────────────────────────────────────────────────┐
│                        systemd                               │
├─────────────────────────────────────────────────────────────┤
│  Services    │  Timers     │  Mounts     │  Targets        │
│  (.service)  │  (.timer)   │  (.mount)   │  (.target)      │
├─────────────────────────────────────────────────────────────┤
│  Sockets     │  Devices    │  Paths      │  Slices         │
│  (.socket)   │  (.device)  │  (.path)    │  (.slice)       │
└─────────────────────────────────────────────────────────────┘
```

### Unit Types

| Type | Purpose | Example |
|------|---------|---------|
| .service | Daemon or process | nginx.service |
| .socket | Socket activation | sshd.socket |
| .timer | Scheduled tasks (cron replacement) | apt-daily.timer |
| .mount | Filesystem mounts | home.mount |
| .target | Grouping of units | multi-user.target |
| .path | File/directory watching | myapp.path |
| .slice | Resource control groups | user.slice |

## Service Management

### Basic Commands

```bash
# Start/stop/restart
sudo systemctl start nginx
sudo systemctl stop nginx
sudo systemctl restart nginx
sudo systemctl reload nginx    # Reload config without restart

# Enable/disable (auto-start at boot)
sudo systemctl enable nginx
sudo systemctl disable nginx

# Combined enable and start
sudo systemctl enable --now nginx

# Status and info
systemctl status nginx
systemctl is-active nginx
systemctl is-enabled nginx
systemctl is-failed nginx

# List services
systemctl list-units --type=service
systemctl list-units --type=service --state=running
systemctl list-units --type=service --state=failed
systemctl list-unit-files --type=service
```

### Service Status Interpretation

```bash
$ systemctl status nginx
● nginx.service - A high performance web server
     Loaded: loaded (/lib/systemd/system/nginx.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2024-01-15 10:30:00 UTC; 2h ago
       Docs: man:nginx(8)
    Process: 1234 ExecStart=/usr/sbin/nginx -g daemon on; (code=exited, status=0/SUCCESS)
   Main PID: 1235 (nginx)
      Tasks: 3 (limit: 4915)
     Memory: 8.5M
        CPU: 150ms
     CGroup: /system.slice/nginx.service
             ├─1235 "nginx: master process /usr/sbin/nginx"
             └─1236 "nginx: worker process"
```

| Field | Meaning |
|-------|---------|
| Loaded | Unit file location and enable status |
| Active | Current state and uptime |
| Process | Start command and exit status |
| Main PID | Primary process ID |
| Tasks | Number of tasks in cgroup |
| Memory | Memory usage |
| CGroup | Control group hierarchy |

## Unit Files

### File Locations

| Location | Purpose |
|----------|---------|
| `/lib/systemd/system/` | Package-provided units |
| `/etc/systemd/system/` | Administrator units (override) |
| `/run/systemd/system/` | Runtime units |
| `~/.config/systemd/user/` | User units |

### Unit File Structure

```ini
[Unit]
Description=My Application
Documentation=https://example.com/docs
After=network.target
Wants=network-online.target
Requires=postgresql.service

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/bin/myapp
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Service Types

| Type | Behavior |
|------|----------|
| simple | Process started is main service (default) |
| forking | Parent exits, child continues |
| oneshot | Completes then exits (for scripts) |
| notify | Sends notification when ready |
| idle | Waits for other jobs to finish |

### Common Directives

**[Unit] Section:**

| Directive | Purpose |
|-----------|---------|
| Description | Human-readable description |
| After | Start after these units |
| Before | Start before these units |
| Requires | Hard dependency (fails if dep fails) |
| Wants | Soft dependency (doesn't fail if dep fails) |
| Conflicts | Cannot run with these units |

**[Service] Section:**

| Directive | Purpose |
|-----------|---------|
| ExecStart | Main command |
| ExecStartPre | Pre-start commands |
| ExecStartPost | Post-start commands |
| ExecStop | Stop command |
| ExecReload | Reload command |
| Restart | When to restart (no, on-failure, always) |
| RestartSec | Delay before restart |
| User/Group | Run as user/group |
| WorkingDirectory | Working directory |
| Environment | Environment variables |
| EnvironmentFile | File with environment variables |

**[Install] Section:**

| Directive | Purpose |
|-----------|---------|
| WantedBy | Target that wants this unit |
| RequiredBy | Target that requires this unit |
| Alias | Alternative names |

## Creating Custom Services

### Example: Node.js Application

```bash
sudo nano /etc/systemd/system/myapp.service
```

```ini
[Unit]
Description=My Node.js Application
Documentation=https://github.com/example/myapp
After=network.target

[Service]
Type=simple
User=myapp
Group=myapp
WorkingDirectory=/opt/myapp

# Environment
Environment=NODE_ENV=production
Environment=PORT=3000
EnvironmentFile=-/opt/myapp/.env

# Process management
ExecStart=/usr/bin/node /opt/myapp/server.js
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=10
StartLimitIntervalSec=60
StartLimitBurst=3

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=myapp

# Security hardening
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
ReadWritePaths=/opt/myapp/data

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myapp
```

### Override Package Units

Don't modify files in `/lib/systemd/system/`. Use overrides:

```bash
# Create override directory and file
sudo systemctl edit nginx
```

This creates `/etc/systemd/system/nginx.service.d/override.conf`:

```ini
[Service]
# Add security hardening
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes
```

Apply changes:

```bash
sudo systemctl daemon-reload
sudo systemctl restart nginx
```

## Service Hardening

### Security Directives

systemd provides extensive sandboxing:

```ini
[Service]
# User/Group isolation
User=myapp
Group=myapp
DynamicUser=yes                    # Create ephemeral user

# Filesystem protection
ProtectSystem=strict               # /usr, /boot, /efi read-only
ProtectHome=yes                    # /home, /root, /run/user inaccessible
PrivateTmp=yes                     # Private /tmp and /var/tmp
ReadWritePaths=/var/lib/myapp      # Exceptions
ReadOnlyPaths=/etc/myapp           # Read-only access
InaccessiblePaths=/mnt             # Completely hidden

# Privilege restrictions
NoNewPrivileges=yes                # Can't gain privileges
CapabilityBoundingSet=CAP_NET_BIND_SERVICE  # Limit capabilities
AmbientCapabilities=CAP_NET_BIND_SERVICE

# System call filtering
SystemCallFilter=@system-service   # Only allowed syscalls
SystemCallFilter=~@privileged      # Block privileged syscalls
SystemCallErrorNumber=EPERM        # Return error instead of kill

# Network isolation
PrivateNetwork=yes                 # Own network namespace
RestrictAddressFamilies=AF_INET AF_INET6

# Kernel hardening
ProtectKernelModules=yes           # Can't load modules
ProtectKernelTunables=yes          # Can't modify /proc, /sys
ProtectKernelLogs=yes              # No access to kernel logs
ProtectControlGroups=yes           # Can't modify cgroups

# Misc restrictions
ProtectClock=yes                   # Can't set system clock
ProtectHostname=yes                # Can't change hostname
RestrictRealtime=yes               # Can't use realtime scheduling
RestrictSUIDSGID=yes               # Can't create SUID/SGID files
LockPersonality=yes                # Lock execution domain
MemoryDenyWriteExecute=yes         # W^X enforcement
```

### Analyze Security

```bash
# Check security score of a unit
systemd-analyze security nginx

# Security overview
systemd-analyze security
```

Output shows security score and recommendations:

```
  NAME                         DESCRIPTION                              EXPOSURE
✗ PrivateNetwork=              Service has access to the host's network      0.5
✓ PrivateTmp=                  Service has access to private tmp
✗ ProtectSystem=               Service has full access to the file system   0.5
...
→ Overall exposure level for nginx.service: 7.2 MEDIUM
```

### Example: Hardened Web Service

```ini
[Unit]
Description=Hardened Web Application
After=network.target

[Service]
Type=simple
User=webapp
Group=webapp

ExecStart=/opt/webapp/bin/server

# Strong isolation
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
NoNewPrivileges=yes

# Only needed filesystem access
ReadWritePaths=/var/lib/webapp
ReadOnlyPaths=/etc/webapp

# Network: only needed ports
RestrictAddressFamilies=AF_INET AF_INET6

# Capabilities: only bind to low ports
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE

# System calls: service calls only
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources

# Kernel protection
ProtectKernelTunables=yes
ProtectKernelModules=yes
ProtectKernelLogs=yes
ProtectControlGroups=yes

# Additional hardening
ProtectClock=yes
ProtectHostname=yes
LockPersonality=yes
RestrictRealtime=yes
RestrictSUIDSGID=yes
MemoryDenyWriteExecute=yes

[Install]
WantedBy=multi-user.target
```

## Resource Management

### Set Resource Limits

```ini
[Service]
# CPU
CPUQuota=50%                       # Max 50% of one CPU
CPUWeight=100                      # Relative weight

# Memory
MemoryMax=512M                     # Hard limit
MemoryHigh=256M                    # Soft limit (triggers reclaim)

# I/O
IOWeight=100                       # Relative I/O weight
IOReadBandwidthMax=/dev/sda 10M    # Read bandwidth limit

# Process limits
TasksMax=100                       # Max processes/threads
```

### View Resource Usage

```bash
# Resource usage by unit
systemd-cgtop

# Detailed unit resources
systemctl show nginx --property=MemoryCurrent,TasksCurrent,CPUUsageNSec

# CGroup details
systemctl status nginx | grep CGroup
cat /sys/fs/cgroup/system.slice/nginx.service/memory.current
```

## Timers (Cron Replacement)

### Create a Timer

Service unit (`/etc/systemd/system/backup.service`):

```ini
[Unit]
Description=Backup Service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
```

Timer unit (`/etc/systemd/system/backup.timer`):

```ini
[Unit]
Description=Daily Backup Timer

[Timer]
OnCalendar=*-*-* 02:00:00
RandomizedDelaySec=1800
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:

```bash
sudo systemctl enable --now backup.timer
```

### Timer Syntax

| Syntax | Meaning |
|--------|---------|
| OnCalendar=daily | Every day at 00:00 |
| OnCalendar=weekly | Every Monday at 00:00 |
| OnCalendar=*-*-* 02:00:00 | Every day at 02:00 |
| OnCalendar=Mon *-*-* 09:00:00 | Every Monday at 09:00 |
| OnBootSec=5min | 5 minutes after boot |
| OnUnitActiveSec=1h | 1 hour after unit last activated |

### List Timers

```bash
systemctl list-timers --all
```

## Troubleshooting

### View Logs

```bash
# Service logs
sudo journalctl -u nginx

# Recent logs
sudo journalctl -u nginx --since "1 hour ago"

# Follow logs
sudo journalctl -u nginx -f

# Boot messages
sudo journalctl -b

# Failed units
systemctl --failed
```

### Debug Startup Issues

```bash
# Analyze boot time
systemd-analyze blame

# Critical chain
systemd-analyze critical-chain

# Plot boot graph
systemd-analyze plot > boot.svg

# Verify unit file
systemd-analyze verify myapp.service

# Check dependencies
systemctl list-dependencies nginx
```

### Common Issues

**Service fails to start:**

```bash
# Check status and logs
systemctl status myapp -l
journalctl -u myapp --no-pager

# Check unit file syntax
systemd-analyze verify myapp.service
```

**Service keeps restarting:**

```bash
# Check restart limits
systemctl show myapp -p StartLimitBurst,StartLimitIntervalSec

# Reset failure counter
systemctl reset-failed myapp
```

**Dependency issues:**

```bash
# See what unit is waiting for
systemctl list-jobs

# Check dependency tree
systemctl list-dependencies --all myapp
```

## Quick Reference

### Essential Commands

```bash
# Lifecycle
systemctl start|stop|restart|reload service
systemctl enable|disable service
systemctl enable --now service
systemctl mask|unmask service

# Information
systemctl status service
systemctl show service
systemctl cat service
systemctl list-dependencies service

# System
systemctl daemon-reload
systemctl list-units
systemctl list-unit-files
systemctl --failed
systemctl isolate multi-user.target
systemctl get-default

# Logs
journalctl -u service
journalctl -f
journalctl -b
journalctl --since "1 hour ago"
```

## Next Steps

Continue to [Time Synchronization](time-sync.md) to configure accurate time keeping, which is essential for security (logs, certificates, authentication).
