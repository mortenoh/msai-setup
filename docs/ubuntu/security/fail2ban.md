# Fail2ban

Fail2ban scans log files and bans IPs that show malicious signs—too many password failures, seeking exploits, etc. It's essential protection against brute-force attacks.

## Understanding Fail2ban

### How Fail2ban Works

```
┌─────────────────────────────────────────────────────────────┐
│                      Log Files                               │
│     /var/log/auth.log, /var/log/nginx/error.log, etc.       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Fail2ban Filter                           │
│           (Regex patterns match failures)                    │
│      e.g., "Failed password for .* from <HOST>"              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Jail Configuration                        │
│        maxretry=5, findtime=10m, bantime=1h                 │
│        If 5 failures in 10 minutes, ban for 1 hour          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ban Action                                │
│         iptables/nftables rule blocks IP                     │
│         Optional: email notification                         │
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Term | Meaning |
|------|---------|
| **Jail** | A service being monitored (SSH, nginx, etc.) |
| **Filter** | Regex patterns to detect failures |
| **Action** | What to do when threshold reached (ban, notify) |
| **maxretry** | Failures before banning |
| **findtime** | Window for counting failures |
| **bantime** | How long to ban |

## Installation

```bash
# Install fail2ban
sudo apt install fail2ban

# Enable and start
sudo systemctl enable --now fail2ban

# Check status
sudo systemctl status fail2ban
```

## Configuration Files

### File Hierarchy

| File | Purpose |
|------|---------|
| `/etc/fail2ban/fail2ban.conf` | Main configuration |
| `/etc/fail2ban/jail.conf` | Default jail settings (don't edit) |
| `/etc/fail2ban/jail.local` | Local overrides (create this) |
| `/etc/fail2ban/jail.d/*.conf` | Modular jail configs |
| `/etc/fail2ban/filter.d/*.conf` | Filter definitions |
| `/etc/fail2ban/action.d/*.conf` | Action definitions |

### Create Local Configuration

Never edit `.conf` files directly—they're overwritten on updates:

```bash
sudo nano /etc/fail2ban/jail.local
```

## Basic Configuration

### /etc/fail2ban/jail.local

```ini
[DEFAULT]
# Ban duration (1 hour)
bantime = 1h

# Time window for counting failures
findtime = 10m

# Max failures before ban
maxretry = 5

# Ignore these IPs (whitelist)
ignoreip = 127.0.0.1/8 ::1 192.168.1.0/24

# Action to take
banaction = iptables-multiport
banaction_allports = iptables-allports

# Email notifications (optional)
#destemail = admin@example.com
#sender = fail2ban@example.com
#mta = sendmail
#action = %(action_mwl)s

# Backend for log monitoring
backend = systemd

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h
findtime = 10m
```

### Apply Configuration

```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Check configuration
sudo fail2ban-client -d

# View loaded jails
sudo fail2ban-client status
```

## SSH Protection

### Default SSH Jail

```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 1h
findtime = 10m
```

### Aggressive SSH Jail

For systems facing heavy attacks:

```ini
[sshd-aggressive]
enabled = true
port = ssh
filter = sshd[mode=aggressive]
logpath = /var/log/auth.log
maxretry = 2
bantime = 24h
findtime = 1h
```

### SSH DDoS Protection

```ini
[sshd-ddos]
enabled = true
port = ssh
filter = sshd-ddos
logpath = /var/log/auth.log
maxretry = 6
bantime = 1h
findtime = 1m
```

## Common Jail Configurations

### Nginx

```ini
[nginx-http-auth]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 1h

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 1d

[nginx-badbots]
enabled = true
port = http,https
filter = apache-badbots
logpath = /var/log/nginx/access.log
maxretry = 2
bantime = 1d

[nginx-noscript]
enabled = true
port = http,https
filter = nginx-noscript
logpath = /var/log/nginx/access.log
maxretry = 6
bantime = 1d
```

### Apache

```ini
[apache-auth]
enabled = true
port = http,https
filter = apache-auth
logpath = /var/log/apache2/error.log
maxretry = 3
bantime = 1h

[apache-overflows]
enabled = true
port = http,https
filter = apache-overflows
logpath = /var/log/apache2/error.log
maxretry = 2
bantime = 1d
```

### Postfix (Mail)

```ini
[postfix]
enabled = true
port = smtp,ssmtp,submission
filter = postfix
logpath = /var/log/mail.log
maxretry = 3
bantime = 1h

[postfix-sasl]
enabled = true
port = smtp,ssmtp,submission,imap,imaps
filter = postfix[mode=auth]
logpath = /var/log/mail.log
maxretry = 3
bantime = 1d
```

### Nextcloud

```ini
[nextcloud]
enabled = true
port = 80,443
protocol = tcp
filter = nextcloud
logpath = /var/log/nextcloud/nextcloud.log
maxretry = 3
bantime = 1h
```

Create filter at `/etc/fail2ban/filter.d/nextcloud.conf`:

```ini
[Definition]
failregex = ^.*Login failed: '?.*'? \(Remote IP: '?<HOST>'?\).*$
            ^.*\"remoteAddr\":\"<HOST>\".*\"message\":\"Login failed.*$
ignoreregex =
```

## Creating Custom Filters

### Filter Structure

```ini
# /etc/fail2ban/filter.d/myapp.conf

[Definition]
# Regex for failure (use <HOST> for IP)
failregex = ^.* authentication failure from <HOST>$
            ^.* invalid login attempt from <HOST>$

# Regex for lines to ignore
ignoreregex = ^.* allowed login from .*$

# Optional: Date pattern
#datepattern = %%Y-%%m-%%d %%H:%%M:%%S
```

### Test Filters

```bash
# Test filter against log file
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

# Verbose output
sudo fail2ban-regex --print-all-matched /var/log/myapp.log /etc/fail2ban/filter.d/myapp.conf
```

## Managing Bans

### View Status

```bash
# All jails
sudo fail2ban-client status

# Specific jail
sudo fail2ban-client status sshd

# Output:
# Status for the jail: sshd
# |- Filter
# |  |- Currently failed: 3
# |  |- Total failed:     150
# |  `- Journal matches:  _SYSTEMD_UNIT=sshd.service
# `- Actions
#    |- Currently banned: 5
#    |- Total banned:     42
#    `- Banned IP list:   192.168.1.50 10.0.0.100 ...
```

### Manual Ban/Unban

```bash
# Ban an IP
sudo fail2ban-client set sshd banip 192.168.1.100

# Unban an IP
sudo fail2ban-client set sshd unbanip 192.168.1.100

# Unban all
sudo fail2ban-client unban --all
```

### Check If IP is Banned

```bash
# Check specific jail
sudo fail2ban-client get sshd banned

# Check iptables directly
sudo iptables -L f2b-sshd -n
```

## Advanced Configuration

### Incremental Bans

Increase ban time for repeat offenders:

```ini
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3

# Incremental banning
bantime = 1h
bantime.increment = true
bantime.multipliers = 1 2 4 8 16 32 64
bantime.maxtime = 4w
```

With multipliers: 1h, 2h, 4h, 8h, 16h, 32h, 64h (max 4 weeks).

### Database for Persistence

```ini
[DEFAULT]
# Use database to remember bans across restarts
dbfile = /var/lib/fail2ban/fail2ban.sqlite3
dbpurgeage = 1d
```

### Action on Ban

```ini
[DEFAULT]
# Just ban
action = %(action_)s

# Ban and send email
action = %(action_mw)s

# Ban, email with whois and logs
action = %(action_mwl)s

# Custom action
action = iptables-multiport[name=%(__name__)s, port="%(port)s", protocol="%(protocol)s"]
         myaction[name=%(__name__)s]
```

### Custom Action Example

Create `/etc/fail2ban/action.d/notify-webhook.conf`:

```ini
[Definition]
actionban = curl -X POST https://webhook.example.com/banned \
            -d "ip=<ip>&jail=<name>&time=<time>"

actionunban = curl -X POST https://webhook.example.com/unbanned \
              -d "ip=<ip>&jail=<name>"
```

## Email Notifications

### Configure Email

```ini
[DEFAULT]
destemail = security@example.com
sender = fail2ban@example.com

# Use sendmail
mta = sendmail

# Or use mail command
#mta = mail

# Action with email
action = %(action_mwl)s
```

### Install Mail Tools

```bash
# For sendmail action
sudo apt install msmtp msmtp-mta

# Configure /etc/msmtprc for SMTP relay
```

## Monitoring Fail2ban

### View Logs

```bash
# Fail2ban log
sudo tail -f /var/log/fail2ban.log

# Recent bans
sudo grep "Ban" /var/log/fail2ban.log | tail -20

# Failed attempts
sudo grep "Found" /var/log/fail2ban.log | tail -20
```

### Statistics

```bash
# Ban statistics
sudo fail2ban-client status sshd

# All statistics
for jail in $(sudo fail2ban-client status | grep "Jail list" | sed 's/.*://'); do
    echo "=== $jail ==="
    sudo fail2ban-client status $jail
done
```

## nftables vs iptables

Ubuntu 24.04 may use nftables backend:

```ini
[DEFAULT]
# Use nftables
banaction = nftables-multiport
banaction_allports = nftables-allports

# Or stay with iptables
#banaction = iptables-multiport
```

Check current backend:

```bash
# View action configuration
sudo fail2ban-client get sshd actions
```

## Troubleshooting

### Common Issues

**Jail not starting:**

```bash
# Check configuration
sudo fail2ban-client -d

# Test filter
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

# Check log path exists
ls -la /var/log/auth.log
```

**IPs not being banned:**

```bash
# Check if filter matches
sudo fail2ban-regex /var/log/auth.log /etc/fail2ban/filter.d/sshd.conf

# Check fail2ban log
sudo tail -f /var/log/fail2ban.log

# Verify iptables rules
sudo iptables -L -n | grep f2b
```

**Bans not persisting:**

```bash
# Enable database
# In jail.local [DEFAULT]:
dbfile = /var/lib/fail2ban/fail2ban.sqlite3

# Restart
sudo systemctl restart fail2ban
```

### Debug Mode

```bash
# Increase logging
sudo fail2ban-client set loglevel DEBUG

# View detailed logs
sudo tail -f /var/log/fail2ban.log

# Reset to normal
sudo fail2ban-client set loglevel INFO
```

## Best Practices

### Security Recommendations

| Practice | Reason |
|----------|--------|
| Whitelist your IP | Don't lock yourself out |
| Use incremental bans | Deter repeat offenders |
| Monitor ban rates | Detect attack patterns |
| Review filters | Ensure accurate matching |
| Set reasonable thresholds | Balance security/usability |

### Performance

```ini
[DEFAULT]
# Use systemd backend (more efficient)
backend = systemd

# Reduce poll time for busy servers
#backend = polling
#polltime = 1
```

## Quick Reference

### Commands

```bash
# Service
sudo systemctl status fail2ban
sudo systemctl restart fail2ban

# Status
sudo fail2ban-client status
sudo fail2ban-client status sshd

# Ban management
sudo fail2ban-client set sshd banip IP
sudo fail2ban-client set sshd unbanip IP
sudo fail2ban-client unban --all

# Configuration
sudo fail2ban-client -d
sudo fail2ban-regex LOGFILE FILTER

# Logging
sudo fail2ban-client set loglevel INFO
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/fail2ban/jail.local | Main configuration |
| /etc/fail2ban/jail.d/*.conf | Modular jails |
| /etc/fail2ban/filter.d/*.conf | Filters |
| /var/log/fail2ban.log | Fail2ban log |
| /var/lib/fail2ban/fail2ban.sqlite3 | Ban database |

## Next Steps

Continue to [auditd](auditd.md) to set up comprehensive system auditing.
