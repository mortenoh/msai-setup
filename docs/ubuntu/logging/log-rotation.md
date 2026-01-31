# Log Rotation

logrotate manages automatic rotation, compression, and deletion of log files, preventing disk space exhaustion while maintaining log history.

## logrotate Fundamentals

### How logrotate Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Daily Cron Job                            │
│            /etc/cron.daily/logrotate                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    logrotate                                 │
│           Reads /etc/logrotate.conf                          │
│           Includes /etc/logrotate.d/*                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    For each log file:                        │
│         1. Check rotation criteria (size, time)              │
│         2. Execute prerotate scripts                         │
│         3. Rotate: app.log → app.log.1                       │
│         4. Compress old files                                │
│         5. Execute postrotate scripts                        │
│         6. Remove files beyond rotate limit                  │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Files

| File | Purpose |
|------|---------|
| /etc/logrotate.conf | Main configuration |
| /etc/logrotate.d/*.conf | Per-application configs |
| /var/lib/logrotate/status | Rotation state |

## Main Configuration

### /etc/logrotate.conf

```bash
# Default settings
weekly
rotate 4
create
dateext
compress

# Uncomment to use extended pattern matching
#compresscmd /usr/bin/xz
#compressext .xz

# Include application-specific configs
include /etc/logrotate.d
```

### Key Directives

| Directive | Description |
|-----------|-------------|
| daily/weekly/monthly | Rotation frequency |
| rotate N | Keep N rotated files |
| compress | Compress rotated files |
| delaycompress | Compress on second rotation |
| create mode owner group | Create new log with permissions |
| notifempty | Don't rotate empty logs |
| missingok | Don't error if log missing |
| copytruncate | Copy then truncate (no reload) |
| dateext | Add date to rotated filename |

## Creating Rotation Rules

### Basic Example

```bash
# /etc/logrotate.d/myapp

/var/log/myapp/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
}
```

### Detailed Configuration

```bash
# /etc/logrotate.d/myapp

/var/log/myapp/*.log {
    # Rotation frequency
    daily               # Rotate daily (weekly, monthly)

    # Retention
    rotate 30           # Keep 30 rotated files
    maxage 90          # Delete files older than 90 days

    # Size-based rotation (instead of/with time)
    size 100M          # Rotate when file reaches 100M
    minsize 10M        # Don't rotate if smaller than 10M
    maxsize 500M       # Force rotate if larger than 500M

    # Compression
    compress           # Compress rotated files
    delaycompress      # Wait one rotation before compressing
    compresscmd /usr/bin/gzip
    compressoptions -9
    compressext .gz

    # File handling
    missingok          # Don't error if file is missing
    notifempty         # Don't rotate empty files
    create 0640 www-data www-data  # New file permissions
    olddir /var/log/myapp/archive  # Move old logs here

    # Naming
    dateext            # Use date in rotated filename
    dateformat -%Y%m%d # Date format (default: -%Y%m%d)

    # Scripts
    sharedscripts      # Run scripts once for all matched files
    prerotate
        echo "Starting rotation" >> /var/log/myapp/rotate.log
    endscript
    postrotate
        systemctl reload myapp > /dev/null 2>&1 || true
    endscript
    lastaction
        echo "Rotation complete" >> /var/log/myapp/rotate.log
    endscript
}
```

## Common Configurations

### Nginx

```bash
# /etc/logrotate.d/nginx

/var/log/nginx/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 www-data adm
    sharedscripts
    prerotate
        if [ -d /etc/logrotate.d/httpd-prerotate ]; then
            run-parts /etc/logrotate.d/httpd-prerotate
        fi
    endscript
    postrotate
        invoke-rc.d nginx rotate >/dev/null 2>&1 || true
    endscript
}
```

### Apache

```bash
# /etc/logrotate.d/apache2

/var/log/apache2/*.log {
    daily
    rotate 14
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    sharedscripts
    postrotate
        if invoke-rc.d apache2 status > /dev/null 2>&1; then
            invoke-rc.d apache2 reload > /dev/null 2>&1
        fi
    endscript
}
```

### Application Without Reload Support

For applications that don't support log reopening:

```bash
# /etc/logrotate.d/simpleapp

/var/log/simpleapp/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    copytruncate        # Copy then truncate original
    # No postrotate needed - app keeps writing to same file
}
```

### Large Log Files

```bash
# /etc/logrotate.d/bigapp

/var/log/bigapp/*.log {
    size 500M           # Rotate when file reaches 500M
    rotate 10
    compress
    compresscmd /usr/bin/xz    # Use xz for better compression
    compressext .xz
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
```

### Remote Archive

```bash
# /etc/logrotate.d/archive-remote

/var/log/important/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 root adm
    sharedscripts
    lastaction
        # Sync to remote storage after rotation
        rsync -avz /var/log/important/*.gz backup@storage:/logs/$(hostname)/ || true
    endscript
}
```

## Scripts in Rotation

### Script Types

| Script | When it Runs |
|--------|--------------|
| prerotate | Before rotation |
| postrotate | After rotation |
| firstaction | Once before all rotations |
| lastaction | Once after all rotations |

### Script Options

| Option | Effect |
|--------|--------|
| sharedscripts | Run scripts once for all matched files |
| nosharedscripts | Run scripts for each file (default) |

### Example: Service Reload

```bash
/var/log/myservice/*.log {
    daily
    rotate 7
    compress
    sharedscripts
    postrotate
        # Method 1: systemd
        systemctl reload myservice > /dev/null 2>&1 || true

        # Method 2: Send signal
        [ -f /var/run/myservice.pid ] && kill -USR1 $(cat /var/run/myservice.pid) || true

        # Method 3: Service command
        service myservice reload > /dev/null 2>&1 || true
    endscript
}
```

## Testing and Debugging

### Test Configuration

```bash
# Dry run (show what would happen)
sudo logrotate -d /etc/logrotate.d/myapp

# Force rotation (actually rotate)
sudo logrotate -f /etc/logrotate.d/myapp

# Verbose output
sudo logrotate -v /etc/logrotate.d/myapp
```

### Debug Output

```bash
# Verbose dry run
sudo logrotate -d -v /etc/logrotate.conf

# Output:
# reading config file /etc/logrotate.conf
# including /etc/logrotate.d
# reading config file myapp
# ...
# considering log /var/log/myapp/app.log
#   log needs rotating
# rotating log /var/log/myapp/app.log, log->rotateCount is 7
# ...
```

### Force Immediate Rotation

```bash
# Rotate specific config
sudo logrotate -f /etc/logrotate.d/myapp

# Rotate all
sudo logrotate -f /etc/logrotate.conf
```

### Check Status

```bash
# View rotation state
cat /var/lib/logrotate/status

# Output:
# logrotate state -- version 2
# "/var/log/apt/term.log" 2024-1-15-6:25:1
# "/var/log/syslog" 2024-1-15-6:25:1
```

### Reset Rotation State

```bash
# Reset specific log state
sudo sed -i '/myapp/d' /var/lib/logrotate/status

# Or reset all
sudo rm /var/lib/logrotate/status
```

## Troubleshooting

### Logs Not Rotating

```bash
# Check logrotate runs
sudo logrotate -d /etc/logrotate.d/myapp

# Common issues:
# - Missing file: Check path is correct
# - Permissions: Check user can read/write
# - Already rotated: Check status file
# - Configuration error: Test with -d
```

### Disk Space Issues

```bash
# Check rotation is working
ls -la /var/log/myapp/

# Check how much space logs use
du -sh /var/log/*

# Force cleanup of old logs
sudo logrotate -f /etc/logrotate.conf
```

### Service Not Reloading

```bash
# Test postrotate manually
sudo systemctl reload myservice

# Check if signal works
sudo kill -USR1 $(cat /var/run/myservice.pid)

# Add error logging to script
postrotate
    systemctl reload myservice 2>> /var/log/logrotate-errors.log
endscript
```

### Configuration Errors

```bash
# Syntax check
sudo logrotate -d /etc/logrotate.d/myapp 2>&1 | grep -i error

# Common syntax errors:
# - Missing closing brace
# - Invalid directive
# - Permission issue in postrotate
```

## Best Practices

### Rotation Strategy

| Log Type | Recommendation |
|----------|----------------|
| Application logs | Daily, 14-30 rotations |
| Access logs | Daily, 30-90 rotations |
| Security logs | Daily, 90+ rotations |
| Debug logs | Daily, 7 rotations |
| Error logs | Size-based (100M), 30 rotations |

### Space Management

```bash
# Calculate space needed
# Example: 100MB daily log, 30 rotations, 80% compression
# = 100MB active + (100MB × 30 × 0.2) = 700MB total

# Set conservative limits
size 100M      # Rotate at 100M
rotate 30      # Keep 30 files
maxage 90      # Delete after 90 days regardless
```

### Security Considerations

```bash
# Secure permissions
create 0640 root adm

# Secure old directory
olddir /var/log/myapp/archive
createolddir 0750 root adm

# Don't world-readable
create 0640 syslog adm
```

## Quick Reference

### Commands

```bash
# Test configuration
sudo logrotate -d /etc/logrotate.d/config

# Force rotation
sudo logrotate -f /etc/logrotate.d/config

# Verbose
sudo logrotate -v /etc/logrotate.d/config

# View state
cat /var/lib/logrotate/status
```

### Common Directives

| Directive | Example | Purpose |
|-----------|---------|---------|
| daily | daily | Rotate daily |
| weekly | weekly | Rotate weekly |
| size | size 100M | Rotate at size |
| rotate | rotate 7 | Keep N files |
| compress | compress | gzip old files |
| delaycompress | delaycompress | Compress after 1 rotation |
| create | create 0640 root adm | New file permissions |
| copytruncate | copytruncate | Copy and truncate |
| postrotate | postrotate...endscript | Run after rotation |

### Key Files

| File | Purpose |
|------|---------|
| /etc/logrotate.conf | Main config |
| /etc/logrotate.d/*.conf | App configs |
| /var/lib/logrotate/status | State file |

## Next Steps

With logging configured, proceed to [Services Management](../services/index.md) to harden and optimize running services.
