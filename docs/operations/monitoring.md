# Monitoring

Hardware health monitoring and alerting for proactive maintenance.

## Hardware Monitoring

### lm-sensors

Install and configure hardware sensors:

```bash
sudo apt install -y lm-sensors
sudo sensors-detect --auto
```

View current readings:

```bash
sensors
```

Example output:

```
k10temp-pci-00c3
Adapter: PCI adapter
Tctl:         +45.0°C

nvme-pci-0100
Adapter: PCI adapter
Composite:    +38.9°C

amdgpu-pci-0600
Adapter: PCI adapter
edge:         +42.0°C
```

### Temperature Thresholds

| Component | Normal | Warning | Critical |
|-----------|--------|---------|----------|
| CPU (Tctl) | < 70C | 70-85C | > 85C |
| GPU (edge) | < 75C | 75-90C | > 90C |
| NVMe | < 50C | 50-70C | > 70C |

### Continuous Monitoring

Watch temperatures in real-time:

```bash
watch -n 2 sensors
```

## Disk Health

### smartmontools

Install SMART monitoring tools:

```bash
sudo apt install -y smartmontools
```

### NVMe Health

```bash
# Overall health
sudo smartctl -H /dev/nvme0n1

# Detailed info
sudo smartctl -a /dev/nvme0n1
```

Key metrics to watch:

- **Percentage Used**: Wear indicator (0-100%)
- **Available Spare**: Remaining spare blocks
- **Temperature**: Operating temperature
- **Media Errors**: Should be 0

### SATA Drive Health

```bash
# Health summary
sudo smartctl -H /dev/sda

# Full report with error log
sudo smartctl -a /dev/sda
```

Key attributes:

| Attribute | Good | Warning |
|-----------|------|---------|
| Reallocated_Sector_Ct | 0 | Any increase |
| Current_Pending_Sector | 0 | > 0 |
| Offline_Uncorrectable | 0 | > 0 |
| UDMA_CRC_Error_Count | 0 | Increasing (cable issue) |

### Enable SMART Daemon

```bash
sudo systemctl enable --now smartd
```

Configure `/etc/smartd.conf` for email alerts:

```
DEVICESCAN -a -o on -S on -n standby,q -s (S/../.././02|L/../../6/03) -W 4,45,55 -m root
```

### ZFS Scrub Scheduling

Scrubs detect and repair silent data corruption:

```bash
# Check last scrub status
zpool status tank

# Manual scrub
sudo zpool scrub tank

# Check scrub progress
zpool status | grep scan
```

Schedule monthly scrubs via systemd timer:

```bash
# /etc/systemd/system/zfs-scrub.timer
[Unit]
Description=Monthly ZFS scrub

[Timer]
OnCalendar=monthly
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# /etc/systemd/system/zfs-scrub.service
[Unit]
Description=ZFS scrub

[Service]
Type=oneshot
ExecStart=/sbin/zpool scrub tank
```

Enable the timer:

```bash
sudo systemctl enable --now zfs-scrub.timer
```

## Resource Monitoring

### Memory and Swap

```bash
# Current usage
free -h

# Detailed breakdown
cat /proc/meminfo | head -20
```

Monitor for memory pressure:

```bash
# Memory available (not just free)
awk '/MemAvailable/ {print $2/1024 " MB"}' /proc/meminfo

# Swap usage (should be minimal)
swapon --show
```

### CPU Utilization

```bash
# Quick overview
top -bn1 | head -5

# Per-core usage
mpstat -P ALL 1 1

# Average load
uptime
```

Load average guidelines for 8-core system:

| Load | Status |
|------|--------|
| < 8 | Normal |
| 8-16 | High |
| > 16 | Overloaded |

### Disk Capacity

```bash
# Filesystem usage
df -h

# ZFS pool capacity
zpool list

# Dataset breakdown
zfs list -o name,used,avail,refer
```

Capacity thresholds:

| Usage | Action |
|-------|--------|
| < 70% | Normal |
| 70-80% | Plan cleanup |
| 80-90% | Cleanup required |
| > 90% | Critical |

!!! warning "ZFS Performance"
    ZFS performance degrades significantly above 80% capacity. Keep pools below 80% full.

### cgroup Resource View

```bash
# Interactive cgroup resource monitor
systemd-cgtop

# Docker container resources
docker stats --no-stream
```

## Alerting

### Health Check Script

Create a monitoring script:

```bash
#!/bin/bash
# /usr/local/bin/health-check.sh

set -euo pipefail

ALERT_FILE="/tmp/health-alerts"
> "$ALERT_FILE"

# Check CPU temperature
CPU_TEMP=$(sensors | awk '/Tctl/ {print int($2)}')
if [ "$CPU_TEMP" -gt 85 ]; then
    echo "CRITICAL: CPU temperature ${CPU_TEMP}C" >> "$ALERT_FILE"
elif [ "$CPU_TEMP" -gt 70 ]; then
    echo "WARNING: CPU temperature ${CPU_TEMP}C" >> "$ALERT_FILE"
fi

# Check ZFS pool health
POOL_HEALTH=$(zpool status -x)
if [ "$POOL_HEALTH" != "all pools are healthy" ]; then
    echo "CRITICAL: ZFS pool issue detected" >> "$ALERT_FILE"
    zpool status >> "$ALERT_FILE"
fi

# Check disk space
ZFS_CAP=$(zpool list -H -o capacity tank | tr -d '%')
if [ "$ZFS_CAP" -gt 90 ]; then
    echo "CRITICAL: ZFS pool at ${ZFS_CAP}%" >> "$ALERT_FILE"
elif [ "$ZFS_CAP" -gt 80 ]; then
    echo "WARNING: ZFS pool at ${ZFS_CAP}%" >> "$ALERT_FILE"
fi

# Check SMART health
for disk in /dev/nvme?n1 /dev/sd?; do
    [ -b "$disk" ] || continue
    if ! sudo smartctl -H "$disk" | grep -q "PASSED\|OK"; then
        echo "CRITICAL: SMART failure on $disk" >> "$ALERT_FILE"
    fi
done

# Check memory
MEM_AVAIL=$(awk '/MemAvailable/ {print int($2/1024)}' /proc/meminfo)
if [ "$MEM_AVAIL" -lt 1024 ]; then
    echo "WARNING: Low memory (${MEM_AVAIL}MB available)" >> "$ALERT_FILE"
fi

# Output results
if [ -s "$ALERT_FILE" ]; then
    cat "$ALERT_FILE"
    exit 1
fi

echo "All systems healthy"
exit 0
```

Make executable:

```bash
sudo chmod +x /usr/local/bin/health-check.sh
```

### Systemd Timer for Health Checks

```bash
# /etc/systemd/system/health-check.timer
[Unit]
Description=Hourly health check

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

```bash
# /etc/systemd/system/health-check.service
[Unit]
Description=System health check

[Service]
Type=oneshot
ExecStart=/usr/local/bin/health-check.sh
StandardOutput=journal
StandardError=journal
```

Enable:

```bash
sudo systemctl enable --now health-check.timer
```

### Notification Options

#### Email Alerts

Configure msmtp for sending alerts:

```bash
sudo apt install -y msmtp msmtp-mta
```

Configure `/etc/msmtprc`:

```
defaults
auth           on
tls            on
tls_trust_file /etc/ssl/certs/ca-certificates.crt

account        default
host           smtp.example.com
port           587
from           server@example.com
user           smtp-user
password       smtp-password
```

Modify health check to send email on failure:

```bash
if [ -s "$ALERT_FILE" ]; then
    cat "$ALERT_FILE" | mail -s "Server Alert: $(hostname)" admin@example.com
fi
```

#### Webhook Alerts

For services like ntfy, Discord, or Slack:

```bash
# ntfy.sh example
if [ -s "$ALERT_FILE" ]; then
    curl -d "$(cat $ALERT_FILE)" ntfy.sh/your-topic
fi

# Discord webhook
if [ -s "$ALERT_FILE" ]; then
    curl -H "Content-Type: application/json" \
         -d "{\"content\": \"$(cat $ALERT_FILE | tr '\n' ' ')\"}" \
         https://discord.com/api/webhooks/xxx/yyy
fi
```

### View Health Check Logs

```bash
# Recent checks
journalctl -u health-check.service --since "1 hour ago"

# Failed checks only
journalctl -u health-check.service -p err
```

## Quick Reference

| Task | Command |
|------|---------|
| View temperatures | `sensors` |
| Check disk health | `sudo smartctl -H /dev/nvme0n1` |
| ZFS pool status | `zpool status` |
| Memory usage | `free -h` |
| Disk capacity | `zpool list` |
| Run health check | `/usr/local/bin/health-check.sh` |
| Check timer status | `systemctl list-timers` |
