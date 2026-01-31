# systemd-journald Configuration

systemd-journald is Ubuntu's primary logging service, providing structured binary logging with powerful query capabilities.

## journald Fundamentals

### Journal Features

| Feature | Description |
|---------|-------------|
| Structured | Key-value metadata per entry |
| Indexed | Fast queries by any field |
| Authenticated | Cryptographic sealing |
| Compressed | Automatic compression |
| Rate-limited | Prevents log floods |

### Journal Location

| Path | Contents |
|------|----------|
| /run/log/journal/ | Volatile (non-persistent) |
| /var/log/journal/ | Persistent (if enabled) |

## Enable Persistent Storage

By default, journal may be volatile (lost on reboot). Enable persistent storage:

```bash
# Create journal directory
sudo mkdir -p /var/log/journal

# Set correct ownership
sudo systemd-tmpfiles --create --prefix /var/log/journal

# Restart journald
sudo systemctl restart systemd-journald

# Verify persistence
ls -la /var/log/journal/
```

Or configure explicitly in `/etc/systemd/journald.conf`:

```ini
[Journal]
Storage=persistent
```

## Configuration

### Main Configuration File

Edit `/etc/systemd/journald.conf`:

```ini
[Journal]
# Storage: volatile, persistent, auto, none
Storage=persistent

# Compress large entries
Compress=yes

# Cryptographic sealing (requires setup)
#Seal=yes

# Split by user (more granular)
SplitMode=uid

# Rate limiting per service
RateLimitIntervalSec=30s
RateLimitBurst=10000

# Maximum disk usage
SystemMaxUse=4G
SystemKeepFree=1G
SystemMaxFileSize=100M
SystemMaxFiles=100

# Runtime (volatile) limits
RuntimeMaxUse=100M
RuntimeKeepFree=100M

# Maximum log entry size
MaxFileSec=1month
MaxRetentionSec=1year

# Forward to syslog
ForwardToSyslog=yes

# Forward to console
#ForwardToConsole=no

# Forward to wall
#ForwardToWall=yes

# TTY path for console
#TTYPath=/dev/console

# Maximum log level to store
#MaxLevelStore=debug

# Maximum log level to forward to syslog
#MaxLevelSyslog=debug
```

### Apply Configuration

```bash
# Restart journald
sudo systemctl restart systemd-journald

# Verify settings
systemd-analyze cat-config systemd/journald.conf
```

## Size Management

### View Disk Usage

```bash
# Total journal size
journalctl --disk-usage

# Output: Archived and active journals take up 256.0M in the file system.
```

### Limit Journal Size

```ini
# /etc/systemd/journald.conf
[Journal]
# Maximum disk space (absolute)
SystemMaxUse=2G

# Keep this much free space
SystemKeepFree=1G

# Maximum size per file
SystemMaxFileSize=100M

# Maximum number of files
SystemMaxFiles=100

# Maximum retention time
MaxRetentionSec=1month
```

### Manual Cleanup

```bash
# Reduce to specific size
sudo journalctl --vacuum-size=1G

# Remove entries older than time
sudo journalctl --vacuum-time=1month

# Remove all but N most recent files
sudo journalctl --vacuum-files=10

# Verify new size
journalctl --disk-usage
```

## Querying the Journal

### Basic Queries

```bash
# All entries
sudo journalctl

# Most recent N entries
sudo journalctl -n 50

# Follow new entries (like tail -f)
sudo journalctl -f

# Reverse order (newest first)
sudo journalctl -r

# No pager (for scripts)
sudo journalctl --no-pager
```

### Filter by Time

```bash
# This boot
sudo journalctl -b

# Previous boot
sudo journalctl -b -1

# List boots
sudo journalctl --list-boots

# Since/until
sudo journalctl --since "2024-01-15 10:00:00"
sudo journalctl --since "1 hour ago"
sudo journalctl --since "yesterday"
sudo journalctl --until "2024-01-15 12:00:00"

# Time range
sudo journalctl --since "09:00" --until "10:00"
```

### Filter by Unit

```bash
# Specific service
sudo journalctl -u nginx
sudo journalctl -u nginx.service

# Multiple services
sudo journalctl -u nginx -u php-fpm

# All units matching pattern
sudo journalctl -u "nginx*"
```

### Filter by Priority

```bash
# Error and above
sudo journalctl -p err

# Specific priority
sudo journalctl -p warning

# Priority range
sudo journalctl -p warning..err
```

Priority levels: emerg(0), alert(1), crit(2), err(3), warning(4), notice(5), info(6), debug(7)

### Filter by Fields

```bash
# By PID
sudo journalctl _PID=1234

# By UID
sudo journalctl _UID=1000

# By executable
sudo journalctl _COMM=sshd

# By hostname
sudo journalctl _HOSTNAME=server01

# By binary path
sudo journalctl _EXE=/usr/sbin/sshd

# Kernel messages
sudo journalctl -k
sudo journalctl _TRANSPORT=kernel

# Combine filters (AND)
sudo journalctl _UID=0 _COMM=sudo
```

### Output Formats

```bash
# Short (default)
sudo journalctl -o short

# With microseconds
sudo journalctl -o short-precise

# Verbose (all fields)
sudo journalctl -o verbose

# JSON (for parsing)
sudo journalctl -o json
sudo journalctl -o json-pretty

# Export format (for backup)
sudo journalctl -o export > journal-backup.export

# Cat (just messages)
sudo journalctl -o cat
```

### Show All Fields

```bash
# List all fields
sudo journalctl --fields

# Show specific entry fields
sudo journalctl -o verbose -n 1
```

## Useful Query Examples

### Security Analysis

```bash
# Failed SSH logins
sudo journalctl -u ssh | grep "Failed password"

# Successful sudo
sudo journalctl _COMM=sudo | grep "COMMAND"

# All auth-related
sudo journalctl SYSLOG_FACILITY=10

# Root actions
sudo journalctl _UID=0 -o verbose

# Service failures
sudo journalctl -p err -b
```

### System Troubleshooting

```bash
# Service startup issues
sudo journalctl -u nginx --since "boot"

# Kernel errors
sudo journalctl -k -p err

# OOM events
sudo journalctl -k | grep -i "out of memory"

# Disk errors
sudo journalctl -k | grep -i "error"

# Network issues
sudo journalctl | grep -i "network"
```

### Monitoring Specific Events

```bash
# Follow SSH attempts
sudo journalctl -u ssh -f

# Follow with specific pattern
sudo journalctl -f | grep --line-buffered "Failed"

# Watch for errors
sudo journalctl -p err -f
```

## Remote Logging

### Send to Remote Server

journald can forward to a remote systemd-journal-remote server:

```bash
# Install remote component
sudo apt install systemd-journal-remote

# Configure upload
sudo nano /etc/systemd/journal-upload.conf
```

```ini
[Upload]
URL=https://logserver.example.com:19532
ServerKeyFile=/etc/ssl/private/journal-upload.pem
ServerCertificateFile=/etc/ssl/certs/journal-upload.pem
TrustedCertificateFile=/etc/ssl/certs/ca-certificates.crt
```

### Forward to Syslog

For compatibility with existing log infrastructure:

```ini
# /etc/systemd/journald.conf
[Journal]
ForwardToSyslog=yes
```

This forwards entries to rsyslog for further processing.

## Journal Integrity

### Enable Sealing

Cryptographic sealing protects log integrity:

```bash
# Generate seal key
sudo journalctl --setup-keys

# Enable sealing
sudo nano /etc/systemd/journald.conf
# Set: Seal=yes

# Restart journald
sudo systemctl restart systemd-journald

# Verify seal
sudo journalctl --verify
```

### Verify Journal

```bash
# Check journal integrity
sudo journalctl --verify

# Output:
# PASS: /var/log/journal/.../system.journal
```

## User Journals

### Per-User Logs

```bash
# View current user's journal
journalctl --user

# Follow user journal
journalctl --user -f

# Specific user (as root)
sudo journalctl _UID=1000
```

### Configure User Journals

```ini
# /etc/systemd/journald.conf
[Journal]
SplitMode=uid
```

## Performance Tuning

### Rate Limiting

Prevent log floods:

```ini
[Journal]
# Interval to count messages
RateLimitIntervalSec=30s

# Maximum burst in interval
RateLimitBurst=10000
```

To disable for specific service:

```ini
# In service unit file
[Service]
LogRateLimitIntervalSec=0
```

### Compression

```ini
[Journal]
# Enable compression (default)
Compress=yes

# Compression threshold (bytes)
#Compress=512
```

## Troubleshooting

### Journal Not Starting

```bash
# Check status
systemctl status systemd-journald

# View journal errors (use dmesg as fallback)
dmesg | grep journal

# Check disk space
df -h /var/log/journal/
```

### Journal Corruption

```bash
# Verify journal
sudo journalctl --verify

# If corrupt, rotate and start fresh
sudo journalctl --rotate
sudo journalctl --vacuum-time=1d

# Nuclear option: remove and recreate
sudo rm -rf /var/log/journal/*
sudo systemctl restart systemd-journald
```

### Missing Logs

```bash
# Check if forwarding to syslog
grep ForwardToSyslog /etc/systemd/journald.conf

# Check storage setting
grep Storage /etc/systemd/journald.conf

# Verify directory exists
ls -la /var/log/journal/
```

## Quick Reference

### Commands

```bash
# View logs
journalctl                       # All entries
journalctl -b                    # This boot
journalctl -f                    # Follow
journalctl -u service            # By service
journalctl -p err                # By priority
journalctl --since "1 hour ago"  # By time

# Output
journalctl -o verbose            # All fields
journalctl -o json               # JSON format
journalctl -o short-precise      # With microseconds

# Management
journalctl --disk-usage          # Check size
journalctl --vacuum-size=1G      # Reduce size
journalctl --vacuum-time=1week   # Remove old
journalctl --rotate              # Rotate logs
journalctl --verify              # Check integrity

# System
systemctl restart systemd-journald  # Restart
```

### Configuration File

`/etc/systemd/journald.conf`

Key settings:

| Setting | Purpose |
|---------|---------|
| Storage | persistent/volatile/auto |
| SystemMaxUse | Max disk usage |
| SystemKeepFree | Keep free space |
| MaxRetentionSec | Max age |
| ForwardToSyslog | Send to rsyslog |
| Compress | Enable compression |

## Next Steps

Continue to [rsyslog](rsyslog.md) for traditional syslog configuration and remote logging.
