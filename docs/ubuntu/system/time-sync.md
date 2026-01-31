# Time Synchronization

Accurate time is critical for security—log correlation, certificate validation, Kerberos authentication, and time-based tokens all depend on synchronized clocks.

## Why Time Matters for Security

| Security Function | Time Dependency |
|-------------------|-----------------|
| Log correlation | Matching events across systems |
| TLS certificates | Valid from/to timestamps |
| Kerberos auth | Tickets have time windows |
| TOTP/2FA | 30-second code windows |
| File timestamps | Forensic analysis |
| Scheduled tasks | Execute at correct time |
| Legal compliance | Accurate audit timestamps |

## Time Sync Options in Ubuntu

### systemd-timesyncd

Ubuntu's default lightweight NTP client:

- Built into systemd
- Simple SNTP implementation
- Good for most workloads
- Low resource usage

### chrony

More sophisticated NTP implementation:

- Better accuracy
- Faster synchronization
- Works better with variable network conditions
- Required for environments needing sub-second accuracy
- Supports NTP server mode

### Comparison

| Feature | systemd-timesyncd | chrony |
|---------|-------------------|--------|
| Resource usage | Very low | Low |
| Initial sync speed | Standard | Fast |
| Accuracy | Milliseconds | Microseconds |
| Intermittent networks | Basic | Excellent |
| Server mode | No | Yes |
| Hardware clock support | Basic | Advanced |
| Leap second handling | Basic | Advanced |

## Checking Current Time Configuration

### View Time Status

```bash
# Overall time configuration
timedatectl

# Output example:
#                Local time: Mon 2024-01-15 14:30:00 UTC
#            Universal time: Mon 2024-01-15 14:30:00 UTC
#                  RTC time: Mon 2024-01-15 14:30:00
#                 Time zone: UTC (UTC, +0000)
# System clock synchronized: yes
#               NTP service: active
#           RTC in local TZ: no
```

### Key Fields

| Field | Meaning |
|-------|---------|
| Local time | System time in configured timezone |
| Universal time | UTC time |
| RTC time | Hardware clock time |
| System clock synchronized | Whether synced via NTP |
| NTP service | Status of time sync daemon |
| RTC in local TZ | Whether hardware clock uses local time |

## systemd-timesyncd Configuration

### Enable timesyncd

```bash
# Check status
systemctl status systemd-timesyncd

# Enable if not running
sudo systemctl enable --now systemd-timesyncd

# Verify sync
timedatectl show-timesync
```

### Configure Time Servers

Edit `/etc/systemd/timesyncd.conf`:

```ini
[Time]
# Primary NTP servers
NTP=0.ubuntu.pool.ntp.org 1.ubuntu.pool.ntp.org 2.ubuntu.pool.ntp.org 3.ubuntu.pool.ntp.org

# Fallback servers
FallbackNTP=ntp.ubuntu.com time.cloudflare.com
```

Or override with drop-in:

```bash
sudo mkdir -p /etc/systemd/timesyncd.conf.d/
sudo nano /etc/systemd/timesyncd.conf.d/custom.conf
```

```ini
[Time]
NTP=time.google.com time.cloudflare.com
```

Restart to apply:

```bash
sudo systemctl restart systemd-timesyncd
```

### Verify Synchronization

```bash
# Sync status
timedatectl timesync-status

# Output:
#        Server: 216.239.35.0 (time.google.com)
# Poll interval: 34min 8s (min: 32s; max 34min 8s)
#          Leap: normal
#       Version: 4
#       Stratum: 1
#     Reference: GPS
#     Precision: 1us (-20)
# Root distance: 335us (max: 5s)
#        Offset: +1.085ms
#         Delay: 12.231ms
#        Jitter: 788us
#  Packet count: 5
```

## chrony Configuration

### Install chrony

```bash
# Install (replaces timesyncd)
sudo apt install chrony

# chrony disables timesyncd automatically
systemctl status systemd-timesyncd
# Should show: inactive (dead)
```

### Configure chrony

Edit `/etc/chrony/chrony.conf`:

```ini
# Time sources
pool ntp.ubuntu.com        iburst maxsources 4
pool 0.ubuntu.pool.ntp.org iburst maxsources 2
pool 1.ubuntu.pool.ntp.org iburst maxsources 2

# Or specific servers
server time.cloudflare.com iburst
server time.google.com iburst prefer

# Record rate at which system clock gains/loses time
driftfile /var/lib/chrony/chrony.drift

# Allow system clock to be stepped in first 3 updates
# if offset is larger than 1 second
makestep 1.0 3

# Enable kernel synchronization of RTC
rtcsync

# Save NTS key/cookies to disk
ntsdumpdir /var/lib/chrony

# Log files location
logdir /var/log/chrony

# Select sources based on number of votes
minsources 2

# Specify directory for log files
logdir /var/log/chrony

# Log measurements, statistics, and tracking
log measurements statistics tracking
```

### chrony Server Options

| Option | Purpose |
|--------|---------|
| iburst | Send burst of requests on startup |
| prefer | Prefer this source |
| minpoll/maxpoll | Polling interval exponents (2^n seconds) |
| maxsources | Maximum sources from pool |

### Manage chrony

```bash
# Check status
chronyc tracking

# View sources
chronyc sources -v

# View source statistics
chronyc sourcestats

# Force sync
sudo chronyc makestep

# Check activity
chronyc activity
```

### Sample chronyc Output

```bash
$ chronyc tracking
Reference ID    : D8EF230A (time.google.com)
Stratum         : 2
Ref time (UTC)  : Mon Jan 15 14:30:00 2024
System time     : 0.000001234 seconds fast of NTP time
Last offset     : +0.000000543 seconds
RMS offset      : 0.000002345 seconds
Frequency       : 1.234 ppm slow
Residual freq   : +0.000 ppm
Skew            : 0.012 ppm
Root delay      : 0.012345678 seconds
Root dispersion : 0.000123456 seconds
Update interval : 1024.5 seconds
Leap status     : Normal
```

## NTS (Network Time Security)

NTS provides authenticated NTP, preventing man-in-the-middle attacks.

### Enable NTS in chrony

```ini
# /etc/chrony/chrony.conf

# NTS-enabled time sources
server time.cloudflare.com iburst nts
server nts.sth1.ntp.se iburst nts

# Store NTS keys
ntsdumpdir /var/lib/chrony
```

Restart chrony:

```bash
sudo systemctl restart chrony

# Verify NTS
chronyc -N authdata
```

## Timezone Configuration

### Set Timezone

```bash
# List timezones
timedatectl list-timezones

# Set timezone
sudo timedatectl set-timezone America/New_York

# Or for UTC (recommended for servers)
sudo timedatectl set-timezone UTC
```

!!! tip "Use UTC for Servers"
    UTC avoids daylight saving time issues and makes log correlation easier across geographically distributed systems.

### Alternative Method

```bash
# Using dpkg-reconfigure
sudo dpkg-reconfigure tzdata
```

## Hardware Clock

### RTC (Real-Time Clock) Settings

```bash
# View RTC time
timedatectl

# Set RTC from system time
sudo hwclock --systohc

# Set system time from RTC
sudo hwclock --hctosys

# Read RTC directly
sudo hwclock --show
```

### UTC vs Local Time

```bash
# Check if RTC is in local time
timedatectl | grep "RTC in local TZ"

# Set RTC to use UTC (recommended)
sudo timedatectl set-local-rtc 0

# Set RTC to use local time (not recommended, Windows dual-boot)
sudo timedatectl set-local-rtc 1
```

## Troubleshooting

### Time Not Synchronizing

```bash
# Check NTP service
timedatectl status

# Check firewall (NTP uses UDP 123)
sudo ufw status | grep 123

# Allow NTP through firewall
sudo ufw allow out 123/udp

# Test NTP server reachability
ntpdate -q pool.ntp.org

# Check chrony sources
chronyc sources
```

### Large Time Offset

If system time is very wrong (minutes or hours):

```bash
# With chrony, force step
sudo chronyc makestep

# With timesyncd, restart may help
sudo systemctl restart systemd-timesyncd

# Or manually set close to correct time first
sudo date -s "2024-01-15 14:30:00"
```

### Check NTP Traffic

```bash
# Monitor NTP traffic
sudo tcpdump -i any port 123

# Check if packets reach server
sudo tcpdump -i eth0 udp port 123
```

## Security Recommendations

### NTP Security Best Practices

| Practice | Reason |
|----------|--------|
| Use NTS when possible | Authenticated time |
| Multiple time sources | Detect rogue sources |
| Use pool addresses | Automatic server selection |
| Firewall egress 123/udp | Allow only needed NTP traffic |
| Monitor for large offsets | Detect time manipulation |

### Restrict chrony Network Access

If not acting as time server:

```ini
# /etc/chrony/chrony.conf

# Don't act as server
port 0

# Don't reply to cmdmon requests from network
cmdport 0

# Or allow only localhost
bindcmdaddress 127.0.0.1
bindcmdaddress ::1
```

### Time Source Selection

| Source Type | Security Consideration |
|-------------|------------------------|
| Public pools | Convenient but untrusted |
| Cloud providers | Trusted for their VMs |
| Internal NTP | Best for enterprise |
| GPS receivers | Highest stratum, tamper-resistant |

## Monitoring Time Sync

### Basic Monitoring

```bash
# Create monitoring script
cat << 'EOF' | sudo tee /usr/local/bin/check-time-sync.sh
#!/bin/bash
# Check if time is synchronized
if timedatectl status | grep -q "synchronized: yes"; then
    echo "OK: Time synchronized"
    exit 0
else
    echo "CRITICAL: Time not synchronized"
    exit 2
fi
EOF
sudo chmod +x /usr/local/bin/check-time-sync.sh
```

### Alert on Drift

```bash
# Check offset with chrony
chronyc tracking | grep "System time" | awk '{
    offset = $4
    if (offset > 0.1 || offset < -0.1) {
        print "WARNING: Time offset is " offset " seconds"
        exit 1
    }
}'
```

## Quick Reference

### Commands

```bash
# Status
timedatectl
timedatectl timesync-status
chronyc tracking
chronyc sources -v

# Configuration
sudo timedatectl set-timezone UTC
sudo timedatectl set-ntp true

# Services
sudo systemctl status systemd-timesyncd
sudo systemctl status chrony

# Manual sync
sudo chronyc makestep

# Hardware clock
sudo hwclock --systohc
sudo hwclock --show
```

### Configuration Files

| File | Purpose |
|------|---------|
| `/etc/systemd/timesyncd.conf` | timesyncd configuration |
| `/etc/chrony/chrony.conf` | chrony configuration |
| `/etc/timezone` | Timezone setting |
| `/etc/localtime` | Symlink to timezone file |

## Next Steps

With system configuration complete, proceed to the [Security section](../security/index.md) for comprehensive hardening measures.
