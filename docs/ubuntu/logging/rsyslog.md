# rsyslog Configuration

rsyslog is Ubuntu's traditional syslog daemon, providing text-based logging, remote logging, and compatibility with log management systems.

## rsyslog Fundamentals

### How rsyslog Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Input Modules                             │
│    (imuxsock, imjournal, imtcp, imudp, imfile)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Processing Rules                          │
│         (filters, property-based filters, templates)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Modules                            │
│     (omfile, omfwd, omelasticsearch, omkafka)               │
└─────────────────────────────────────────────────────────────┘
```

### Configuration Files

| File | Purpose |
|------|---------|
| /etc/rsyslog.conf | Main configuration |
| /etc/rsyslog.d/*.conf | Drop-in configs |
| /var/log/ | Log file output |

## Basic Configuration

### Default Configuration

View default config:

```bash
cat /etc/rsyslog.conf
```

Key sections:

```bash
# Modules
module(load="imuxsock")   # Local system logging
module(load="imjournal")  # Access to systemd journal

# Global directives
$FileOwner syslog
$FileGroup adm
$FileCreateMode 0640
$DirCreateMode 0755

# Include drop-in configs
$IncludeConfig /etc/rsyslog.d/*.conf
```

### Default Rules (50-default.conf)

```bash
# /etc/rsyslog.d/50-default.conf

# Log auth messages to auth.log
auth,authpriv.*                 /var/log/auth.log

# Log everything except auth to syslog
*.*;auth,authpriv.none          /var/log/syslog

# Log cron messages
cron.*                          /var/log/cron.log

# Log daemon messages
daemon.*                        /var/log/daemon.log

# Log kernel messages
kern.*                          /var/log/kern.log

# Log mail messages
mail.*                          /var/log/mail.log

# Emergency messages to everyone
*.emerg                         :omusrmsg:*
```

## Rule Syntax

### Traditional Format

```
facility.priority    action
```

Examples:

```bash
# All auth messages
auth.*                      /var/log/auth.log

# Warning and above for all facilities
*.warning                   /var/log/warnings.log

# Specific priority only
mail.=info                  /var/log/mail-info.log

# Range of priorities
mail.warning;mail.!err      /var/log/mail-warnings.log

# Multiple facilities
auth,authpriv.*             /var/log/auth.log

# Exclude facility
*.*;auth,authpriv.none      /var/log/syslog
```

### RainerScript (Modern)

More powerful filter syntax:

```bash
# Filter by property
if $programname == 'sshd' then /var/log/sshd.log

# Multiple conditions
if $programname == 'nginx' and $syslogseverity <= 4 then /var/log/nginx-errors.log

# Regular expression
if $msg contains 'error' then /var/log/errors.log

# Stop further processing
if $programname == 'audit' then {
    /var/log/audit.log
    stop
}
```

### Property-Based Filters

Available properties:

| Property | Description |
|----------|-------------|
| $msg | Message content |
| $hostname | Source hostname |
| $programname | Program name |
| $syslogseverity | Numeric severity (0-7) |
| $syslogfacility | Numeric facility |
| $timestamp | Message timestamp |
| $fromhost-ip | Source IP address |

## Custom Logging Rules

### Create Custom Config

```bash
sudo nano /etc/rsyslog.d/60-custom.conf
```

### Example: Application Logging

```bash
# /etc/rsyslog.d/60-custom.conf

# Custom application log
if $programname == 'myapp' then {
    /var/log/myapp/myapp.log
    stop
}

# Log errors separately
if $programname == 'myapp' and $syslogseverity <= 3 then {
    /var/log/myapp/errors.log
}
```

### Example: Security Logging

```bash
# /etc/rsyslog.d/60-security.conf

# Collect all security-relevant logs
template(name="SecurityFormat" type="string"
    string="%timestamp% %hostname% %programname%: %msg%\n")

if $syslogfacility-text == 'auth' or
   $syslogfacility-text == 'authpriv' or
   $programname == 'sudo' or
   $programname == 'sshd' then {
    /var/log/security.log;SecurityFormat
}
```

## Remote Logging

### Send Logs to Remote Server

#### UDP (Simple, less reliable)

```bash
# /etc/rsyslog.d/60-remote.conf

# Send all logs via UDP
*.* @logserver.example.com:514

# Send specific logs
auth.* @logserver.example.com:514
```

#### TCP (Reliable)

```bash
# Send all logs via TCP
*.* @@logserver.example.com:514

# With queue for reliability
*.* action(type="omfwd"
    target="logserver.example.com"
    port="514"
    protocol="tcp"
    action.resumeRetryCount="-1"
    queue.type="linkedList"
    queue.filename="remote-queue"
    queue.saveonshutdown="on"
)
```

#### TLS Encrypted

```bash
# Load TLS module
module(load="omrelp")

# Or for standard TLS
$DefaultNetstreamDriverCAFile /etc/ssl/certs/ca-certificates.crt
$DefaultNetstreamDriverCertFile /etc/ssl/certs/client-cert.pem
$DefaultNetstreamDriverKeyFile /etc/ssl/private/client-key.pem

$ActionSendStreamDriver gtls
$ActionSendStreamDriverMode 1
$ActionSendStreamDriverAuthMode x509/name
$ActionSendStreamDriverPermittedPeer logserver.example.com

*.* @@logserver.example.com:6514
```

### Receive Logs (Log Server)

```bash
# /etc/rsyslog.conf - on log server

# Enable TCP reception
module(load="imtcp")
input(type="imtcp" port="514")

# Enable UDP reception
module(load="imudp")
input(type="imudp" port="514")

# Template for remote logs
template(name="RemoteLogs" type="string"
    string="/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log")

# Store remote logs by hostname
if $fromhost-ip != '127.0.0.1' then {
    ?RemoteLogs
    stop
}
```

## Templates

### Custom Output Format

```bash
# JSON format
template(name="JsonFormat" type="list") {
    constant(value="{")
    constant(value="\"timestamp\":\"")     property(name="timestamp" dateFormat="rfc3339")
    constant(value="\",\"host\":\"")        property(name="hostname")
    constant(value="\",\"program\":\"")     property(name="programname")
    constant(value="\",\"severity\":\"")    property(name="syslogseverity-text")
    constant(value="\",\"message\":\"")     property(name="msg" format="json")
    constant(value="\"}\n")
}

# Use template
*.* /var/log/json.log;JsonFormat
```

### Dynamic Filenames

```bash
# Log by program name
template(name="PerProgram" type="string"
    string="/var/log/apps/%programname%.log")

if $syslogfacility-text == 'local0' then {
    ?PerProgram
}

# Log by date
template(name="DailyLog" type="string"
    string="/var/log/daily/%$year%-%$month%-%$day%.log")
```

## Rate Limiting

### Limit Message Rate

```bash
# /etc/rsyslog.d/60-ratelimit.conf

# Global rate limit
$IMUXSockRateLimitInterval 1
$IMUXSockRateLimitBurst 1000

# Per-program rate limit
if $programname == 'noisy-app' then {
    action(type="omfile"
        file="/var/log/noisy-app.log"
        action.execOnlyWhenPreviousIsSuspended="on"
        action.resumeInterval="60"
    )
    stop
}
```

## High-Volume Optimization

### Queue Configuration

```bash
# Main queue settings
main_queue(
    queue.size="100000"
    queue.type="LinkedList"
    queue.filename="main-queue"
    queue.saveonshutdown="on"
    queue.highwatermark="80000"
    queue.lowwatermark="20000"
)

# Action queue for remote
action(type="omfwd"
    target="logserver"
    port="514"
    protocol="tcp"
    queue.type="LinkedList"
    queue.size="50000"
    queue.filename="fwd-queue"
    queue.saveonshutdown="on"
    queue.highwatermark="40000"
    queue.discardmark="48000"
    queue.discardseverity="6"
)
```

### Async Writing

```bash
# Enable async writing
$MainMsgQueueType LinkedList
$MainMsgQueueFileName mainmsgqueue
$MainMsgQueueSize 100000
$MainMsgQueueSaveOnShutdown on
```

## Troubleshooting

### Debug Mode

```bash
# Test configuration
sudo rsyslogd -N1

# Run in foreground with debug
sudo rsyslogd -n -d

# Check status
systemctl status rsyslog
```

### View rsyslog Stats

```bash
# Enable statistics
module(load="impstats"
    interval="60"
    facility="5"
    log.syslog="on")

# View stats
grep rsyslogd /var/log/syslog | tail
```

### Common Issues

**Logs not appearing:**

```bash
# Check rsyslog is running
systemctl status rsyslog

# Check configuration
sudo rsyslogd -N1

# Check permissions
ls -la /var/log/
```

**Remote logging not working:**

```bash
# Check firewall
sudo ufw allow 514/tcp
sudo ufw allow 514/udp

# Test connection
nc -vz logserver.example.com 514

# Check listener on server
sudo ss -tlnp | grep 514
```

### View Processing

```bash
# Enable debug
$DebugLevel 2
$DebugFile /var/log/rsyslog-debug.log

# Restart and check
sudo systemctl restart rsyslog
tail -f /var/log/rsyslog-debug.log
```

## Integration Examples

### Elasticsearch

```bash
# Load module
module(load="omelasticsearch")

# Send to Elasticsearch
action(type="omelasticsearch"
    server="elasticsearch.example.com"
    serverport="9200"
    searchIndex="logs"
    dynSearchIndex="on"
    template="JsonFormat"
    bulkmode="on"
    queue.type="LinkedList"
    queue.size="5000"
    queue.saveonshutdown="on"
)
```

### Kafka

```bash
# Load module
module(load="omkafka")

# Send to Kafka
action(type="omkafka"
    topic="syslog"
    broker="kafka1:9092,kafka2:9092"
    template="JsonFormat"
    queue.type="LinkedList"
    queue.size="10000"
)
```

## Quick Reference

### Commands

```bash
# Service management
sudo systemctl restart rsyslog
sudo systemctl status rsyslog

# Test configuration
sudo rsyslogd -N1

# Manual log entry
logger "Test message"
logger -p auth.info "Auth test"

# View logs
tail -f /var/log/syslog
```

### Severity Shortcuts

| Keyword | Level | Meaning |
|---------|-------|---------|
| emerg | 0 | System unusable |
| alert | 1 | Immediate action |
| crit | 2 | Critical |
| err | 3 | Error |
| warning | 4 | Warning |
| notice | 5 | Notable |
| info | 6 | Informational |
| debug | 7 | Debug |

### Key Files

| File | Purpose |
|------|---------|
| /etc/rsyslog.conf | Main config |
| /etc/rsyslog.d/*.conf | Drop-in configs |
| /var/log/syslog | General log |
| /var/log/auth.log | Auth log |

## Next Steps

Continue to [Log Rotation](log-rotation.md) to configure automatic log management and archival.
