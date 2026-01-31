# Logging Overview

Comprehensive logging is essential for security monitoring, troubleshooting, and compliance. This section covers Ubuntu's logging infrastructure.

## Logging Architecture

### Ubuntu 24.04 Logging Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    Applications                              │
│     (sshd, nginx, systemd services, custom apps)            │
└─────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   syslog()   │    │   sd_journal │    │  Direct file │
│   API call   │    │   API call   │    │   writing    │
└──────────────┘    └──────────────┘    └──────────────┘
          │                    │                    │
          └────────────────────┼────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │       systemd-journald         │
              │    (Binary structured logs)    │
              │   /var/log/journal/             │
              └────────────────────────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │           rsyslog              │
              │      (Text log files)          │
              │        /var/log/               │
              └────────────────────────────────┘
```

### Key Components

| Component | Purpose | Default Location |
|-----------|---------|------------------|
| systemd-journald | Binary structured logging | /var/log/journal/ |
| rsyslog | Traditional text logging | /var/log/*.log |
| logrotate | Log rotation and compression | Config in /etc/logrotate.d/ |
| auditd | Security event logging | /var/log/audit/ |

## Section Contents

| Page | Description |
|------|-------------|
| [journald](journald.md) | systemd journal configuration |
| [rsyslog](rsyslog.md) | Traditional syslog, remote logging |
| [Log Rotation](log-rotation.md) | logrotate configuration |

## Quick Start

### View Recent Logs

```bash
# All recent logs
sudo journalctl -n 100

# Follow new entries
sudo journalctl -f

# Since boot
sudo journalctl -b

# Since time
sudo journalctl --since "1 hour ago"

# Specific service
sudo journalctl -u nginx

# With priority (errors and above)
sudo journalctl -p err
```

### Common Log Files

| File | Contents |
|------|----------|
| /var/log/syslog | General system log |
| /var/log/auth.log | Authentication events |
| /var/log/kern.log | Kernel messages |
| /var/log/dmesg | Boot messages |
| /var/log/apt/history.log | Package changes |
| /var/log/ufw.log | Firewall events |

### Check Disk Usage

```bash
# Journal disk usage
journalctl --disk-usage

# Log directory size
du -sh /var/log/

# Largest log files
find /var/log -type f -exec du -h {} + | sort -rh | head -20
```

## Log Priorities

### Syslog Severity Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | emerg | System unusable |
| 1 | alert | Immediate action required |
| 2 | crit | Critical conditions |
| 3 | err | Error conditions |
| 4 | warning | Warning conditions |
| 5 | notice | Normal but significant |
| 6 | info | Informational |
| 7 | debug | Debug messages |

### Filter by Priority

```bash
# journalctl
sudo journalctl -p err         # err and above
sudo journalctl -p warning..err # warning through err

# grep in log files
grep -E "(error|critical|alert|emerg)" /var/log/syslog
```

## Log Facilities

### Syslog Facilities

| Facility | Description |
|----------|-------------|
| auth | Authentication |
| authpriv | Private auth |
| cron | Cron daemon |
| daemon | System daemons |
| kern | Kernel |
| local0-7 | Custom use |
| mail | Mail system |
| syslog | Syslog itself |
| user | User programs |

## Security Logging

### Critical Events to Monitor

| Event Type | Log Source | Search Pattern |
|------------|------------|----------------|
| Failed logins | auth.log | "Failed password" |
| Sudo usage | auth.log | "sudo:" |
| SSH connections | auth.log | "sshd" |
| Service changes | syslog | "systemd" |
| Firewall blocks | ufw.log | "BLOCK" |
| Package installs | apt/history.log | "Install:" |

### Quick Security Check

```bash
# Failed SSH logins today
sudo journalctl -u ssh --since today | grep -c "Failed password"

# Successful SSH logins
sudo journalctl -u ssh --since today | grep "Accepted"

# Sudo usage
sudo grep "sudo:" /var/log/auth.log | tail -20

# Root commands
sudo ausearch -m EXECVE -ua root --interpret | head -50
```

## Log Retention

### Default Retention

| Log Type | Default Retention |
|----------|-------------------|
| journald | 4GB or 10% disk |
| rsyslog files | 7 rotations, weekly |
| audit logs | 8MB × 5 files |

### Compliance Considerations

| Standard | Typical Requirement |
|----------|---------------------|
| PCI-DSS | 1 year online, 3 years archived |
| HIPAA | 6 years |
| SOX | 7 years |
| GDPR | Varies (minimize where possible) |

## Best Practices

### Logging Guidelines

| Practice | Reason |
|----------|--------|
| Enable persistent journald | Survive reboots |
| Configure remote logging | Protect from tampering |
| Set appropriate retention | Balance compliance/storage |
| Monitor log growth | Prevent disk exhaustion |
| Protect log permissions | Maintain integrity |

### Log Security

```bash
# Verify log permissions
ls -la /var/log/auth.log
# Should be: -rw-r----- root adm

# Verify journal permissions
ls -la /var/log/journal/
# Should be: drwxr-sr-x root systemd-journal
```

## Quick Reference

### Essential Commands

```bash
# journalctl
journalctl -f                    # Follow
journalctl -u service            # By service
journalctl -b                    # This boot
journalctl --since "1 hour ago"  # By time
journalctl -p err                # By priority
journalctl --disk-usage          # Size

# Log files
tail -f /var/log/syslog          # Follow
less /var/log/auth.log           # Read
zcat /var/log/syslog.1.gz        # Read rotated

# Management
sudo journalctl --vacuum-size=1G # Clean journal
sudo logrotate -f /etc/logrotate.conf # Force rotate
```

### Key Directories

| Path | Contents |
|------|----------|
| /var/log/ | Traditional log files |
| /var/log/journal/ | Systemd journal |
| /var/log/audit/ | Audit logs |
| /etc/rsyslog.d/ | rsyslog config |
| /etc/logrotate.d/ | Rotation config |

## Next Steps

Start with [journald Configuration](journald.md) to configure Ubuntu's primary logging system.
