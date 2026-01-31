# UFW Logging & Monitoring

## Logging Overview

UFW logging helps you:

- Detect intrusion attempts
- Debug connectivity issues
- Audit access patterns
- Monitor firewall effectiveness

## Enabling Logging

```bash
# Enable logging
sudo ufw logging on

# Set log level
sudo ufw logging low     # Log blocked packets matching default policy
sudo ufw logging medium  # Log above + rate limited + invalid
sudo ufw logging high    # Log above + all matching
sudo ufw logging full    # Log everything

# Disable logging
sudo ufw logging off
```

## Log Levels Explained

### Low (Default)

Logs packets blocked by the default policy:

```
[UFW BLOCK] IN=eth0 OUT= MAC=... SRC=10.0.0.1 DST=192.168.1.100 ...
```

### Medium

Adds:
- Rate-limited packets
- Invalid packets
- New connections not matching rules

### High

Adds:
- Packets matching allow rules
- All new connections with rate limiting

### Full

Logs every packet. **Warning:** Can fill disks quickly on busy servers.

## Log Location

```bash
# Primary location
/var/log/ufw.log

# Also appears in
/var/log/syslog
/var/log/kern.log

# View with journalctl
journalctl -k | grep UFW
```

## Log Format

```
Jan 15 10:23:45 hostname kernel: [UFW BLOCK] IN=eth0 OUT= MAC=aa:bb:cc:dd:ee:ff:11:22:33:44:55:66:08:00 SRC=10.0.0.5 DST=192.168.1.100 LEN=60 TOS=0x00 PREC=0x00 TTL=64 ID=12345 DF PROTO=TCP SPT=54321 DPT=22 WINDOW=65535 RES=0x00 SYN URGP=0
```

### Field Breakdown

| Field | Description |
|-------|-------------|
| [UFW BLOCK] | Action taken (BLOCK, ALLOW, AUDIT) |
| IN=eth0 | Incoming interface |
| OUT= | Outgoing interface (empty for incoming) |
| MAC= | MAC addresses (dst:src:protocol) |
| SRC= | Source IP address |
| DST= | Destination IP address |
| LEN= | Packet length |
| TOS= | Type of service |
| PREC= | Precedence |
| TTL= | Time to live |
| ID= | IP packet ID |
| DF | Don't fragment flag |
| PROTO= | Protocol (TCP, UDP, ICMP) |
| SPT= | Source port |
| DPT= | Destination port |
| WINDOW= | TCP window size |
| SYN | TCP flags |

## Analyzing Logs

### Real-time Monitoring

```bash
# Watch UFW logs
sudo tail -f /var/log/ufw.log

# Filter for blocks only
sudo tail -f /var/log/ufw.log | grep BLOCK

# Filter by IP
sudo tail -f /var/log/ufw.log | grep "SRC=10.0.0.5"

# With journalctl
journalctl -kf | grep UFW
```

### Log Analysis Commands

```bash
# Count blocks by source IP
grep "UFW BLOCK" /var/log/ufw.log | \
    sed -n 's/.*SRC=\([^ ]*\).*/\1/p' | \
    sort | uniq -c | sort -rn | head -20

# Count blocks by destination port
grep "UFW BLOCK" /var/log/ufw.log | \
    sed -n 's/.*DPT=\([^ ]*\).*/\1/p' | \
    sort | uniq -c | sort -rn | head -20

# Blocks in last hour
grep "UFW BLOCK" /var/log/ufw.log | \
    grep "$(date '+%b %d %H')" | wc -l

# Find SSH brute force attempts
grep "UFW BLOCK.*DPT=22" /var/log/ufw.log | \
    sed -n 's/.*SRC=\([^ ]*\).*/\1/p' | \
    sort | uniq -c | sort -rn | head -10
```

### Using awk for Analysis

```bash
# Detailed statistics
awk '/UFW BLOCK/ {
    match($0, /SRC=([^ ]+)/, src);
    match($0, /DPT=([^ ]+)/, dpt);
    match($0, /PROTO=([^ ]+)/, proto);
    print src[1], dpt[1], proto[1]
}' /var/log/ufw.log | sort | uniq -c | sort -rn
```

## Custom Logging

### Log Specific Traffic

Add to `/etc/ufw/before.rules`:

```bash
# Log all SSH attempts
-A ufw-before-input -p tcp --dport 22 -j LOG --log-prefix "[UFW SSH] "

# Log rate-limited (possible attack)
-A ufw-before-input -p tcp --dport 22 -m limit --limit 1/min \
    -j LOG --log-prefix "[UFW SSH-LIMIT] "

# Log to specific level
-A ufw-before-input -p tcp --dport 80 -j LOG --log-prefix "[UFW HTTP] " --log-level 4
```

### Log Levels

| Level | Name | Description |
|-------|------|-------------|
| 0 | emerg | System unusable |
| 1 | alert | Immediate action required |
| 2 | crit | Critical conditions |
| 3 | err | Error conditions |
| 4 | warning | Warning conditions (default) |
| 5 | notice | Normal but significant |
| 6 | info | Informational |
| 7 | debug | Debug messages |

### Conditional Logging

```bash
# Log only new connections
-A ufw-before-input -p tcp --dport 443 -m conntrack --ctstate NEW \
    -j LOG --log-prefix "[UFW HTTPS-NEW] "

# Log with packet limit (prevent log flooding)
-A ufw-before-input -m limit --limit 5/min --limit-burst 10 \
    -j LOG --log-prefix "[UFW RATE] "
```

## Log Rotation

### Default Configuration

```bash
# /etc/logrotate.d/ufw
/var/log/ufw.log
{
    rotate 4
    weekly
    missingok
    notifempty
    compress
    delaycompress
    sharedscripts
    postrotate
        invoke-rc.d rsyslog rotate >/dev/null 2>&1 || true
    endscript
}
```

### Custom Rotation

```bash
# More aggressive rotation for busy servers
/var/log/ufw.log
{
    rotate 7
    daily
    compress
    delaycompress
    missingok
    notifempty
    size 100M
    sharedscripts
    postrotate
        invoke-rc.d rsyslog rotate >/dev/null 2>&1 || true
    endscript
}
```

## Separate Log File

### Configure rsyslog

```bash
# /etc/rsyslog.d/20-ufw.conf
:msg,contains,"[UFW " /var/log/ufw.log
& stop
```

This:
- Captures all messages containing "[UFW "
- Writes to /var/log/ufw.log
- Stops processing (won't duplicate in syslog)

### Restart rsyslog

```bash
sudo systemctl restart rsyslog
```

## Log Monitoring Tools

### Using watch

```bash
# Live block counter
watch -n 1 'grep -c "UFW BLOCK" /var/log/ufw.log'

# Top blocked IPs (updates every 5 seconds)
watch -n 5 'grep "UFW BLOCK" /var/log/ufw.log | \
    sed -n "s/.*SRC=\([^ ]*\).*/\1/p" | \
    sort | uniq -c | sort -rn | head -10'
```

### Using multitail

```bash
# Install
sudo apt install multitail

# Monitor multiple log streams
multitail -i /var/log/ufw.log -i /var/log/auth.log
```

### Using GoAccess (for formatted reports)

While GoAccess is for web logs, you can preprocess UFW logs:

```bash
# Convert UFW logs to CSV
grep "UFW BLOCK" /var/log/ufw.log | \
    awk '{
        match($0, /SRC=([^ ]+)/, src);
        match($0, /DPT=([^ ]+)/, dpt);
        print src[1] "," dpt[1]
    }' > /tmp/ufw-blocks.csv
```

## Alerting

### Using logwatch

```bash
sudo apt install logwatch

# Configure UFW section
# /etc/logwatch/conf/services/ufw.conf
LogFile = ufw.log
*OnlyService = ufw

# Run manually
logwatch --service ufw --detail high
```

### Simple Alert Script

```bash
#!/bin/bash
# /usr/local/bin/ufw-alert.sh

THRESHOLD=100
COUNT=$(grep -c "UFW BLOCK" /var/log/ufw.log)

if [ $COUNT -gt $THRESHOLD ]; then
    echo "High firewall activity: $COUNT blocks" | \
        mail -s "UFW Alert" admin@example.com
fi
```

Add to cron:

```bash
# Every hour
0 * * * * /usr/local/bin/ufw-alert.sh
```

### Using fail2ban for Alerts

```ini
# /etc/fail2ban/jail.local
[ufw-portscan]
enabled = true
filter = ufw-portscan
logpath = /var/log/ufw.log
maxretry = 20
findtime = 60
bantime = 3600
action = ufw[name=portscan]
         mail-whois[name=portscan, dest=admin@example.com]
```

```ini
# /etc/fail2ban/filter.d/ufw-portscan.conf
[Definition]
failregex = .*\[UFW BLOCK\].*SRC=<HOST>.*
ignoreregex =
```

## Performance Considerations

### High Log Volume

On busy servers, logging can:
- Fill disk space
- Impact performance
- Overwhelm analysis

### Mitigations

```bash
# 1. Use rate limiting in log rules
-A ufw-before-input -m limit --limit 10/sec -j LOG

# 2. Log to ramdisk
mount -t tmpfs -o size=100M tmpfs /var/log/ufw-ram
# (Configure rsyslog to use this path)

# 3. Use lower log level
sudo ufw logging low

# 4. Aggressive log rotation
# See custom rotation above
```

### Sampling

```bash
# Log every 100th packet
-A ufw-before-input -m statistic --mode nth --every 100 \
    -j LOG --log-prefix "[UFW SAMPLE] "
```

## Centralized Logging

### Send to Remote Syslog

```bash
# /etc/rsyslog.d/50-ufw-remote.conf
:msg,contains,"[UFW " @logserver.example.com:514
```

### Using Vector/Filebeat

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    paths:
      - /var/log/ufw.log
    fields:
      log_type: ufw

output.elasticsearch:
  hosts: ["elasticsearch:9200"]
```

## Debugging with Logs

### Traffic Not Reaching Service

```bash
# Enable full logging temporarily
sudo ufw logging full

# Generate test traffic
curl http://server:8080

# Check logs
grep "DPT=8080" /var/log/ufw.log

# Restore normal logging
sudo ufw logging low
```

### Verify Rule is Working

```bash
# Add logging to specific rule (before.rules)
-A ufw-before-input -p tcp --dport 22 -j LOG --log-prefix "[UFW SSH-HIT] "

# Watch for hits
tail -f /var/log/ufw.log | grep "SSH-HIT"
```
