# auditd - Linux Audit Framework

The Linux Audit system provides detailed tracking of security-relevant events. It's essential for compliance, forensics, and security monitoring.

## Understanding auditd

### What auditd Tracks

```
┌─────────────────────────────────────────────────────────────┐
│                    Audit Subsystem                           │
├─────────────────────────────────────────────────────────────┤
│  System Calls   │  File Access    │  User Actions           │
│  - execve       │  - read/write   │  - login/logout         │
│  - open         │  - permission   │  - sudo                 │
│  - socket       │  - attribute    │  - su                   │
│  - mount        │  - modification │  - authentication       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                /var/log/audit/audit.log                      │
│                                                              │
│  type=SYSCALL msg=audit(1234567890.123:456): arch=c000003e  │
│  syscall=59 success=yes exit=0 ... exe="/usr/bin/sudo"      │
└─────────────────────────────────────────────────────────────┘
```

### auditd vs Standard Logging

| Feature | auditd | Standard Logs |
|---------|--------|---------------|
| Detail level | Very high | Medium |
| Tamper resistance | High (kernel-level) | Lower |
| System calls | Yes | No |
| Performance impact | Higher | Lower |
| Compliance support | Yes (PCI, HIPAA, etc.) | Limited |

## Installation and Setup

### Install auditd

```bash
# Install audit daemon and tools
sudo apt install auditd audispd-plugins

# Enable and start
sudo systemctl enable --now auditd

# Verify status
sudo systemctl status auditd
```

### Configuration Files

| File | Purpose |
|------|---------|
| `/etc/audit/auditd.conf` | Daemon configuration |
| `/etc/audit/audit.rules` | Compiled rules |
| `/etc/audit/rules.d/*.rules` | Rule files |
| `/var/log/audit/audit.log` | Audit log |

## Configuring auditd

### Daemon Configuration

Edit `/etc/audit/auditd.conf`:

```ini
# Log file settings
log_file = /var/log/audit/audit.log
log_format = ENRICHED
log_group = adm

# Log file size and rotation
max_log_file = 50
num_logs = 10
max_log_file_action = ROTATE

# Space management
space_left = 100
space_left_action = SYSLOG
admin_space_left = 50
admin_space_left_action = SUSPEND
disk_full_action = SUSPEND
disk_error_action = SUSPEND

# Flush policy
flush = INCREMENTAL_ASYNC
freq = 50

# Priority boost
priority_boost = 4

# Name format in logs
name_format = HOSTNAME
```

### Log File Size Settings

| Setting | Meaning |
|---------|---------|
| max_log_file | Max size in MB |
| num_logs | Number of rotated files |
| max_log_file_action | What to do when max reached |

## Audit Rules

### Rule Syntax

```bash
# System call rule
-a action,filter -S syscall -F field=value -k key

# File watch rule
-w path -p permissions -k key

# Components:
# -a: action,list (always,exit / never,exit / etc.)
# -S: system call name or number
# -F: field condition
# -w: watch path
# -p: permissions (r=read, w=write, x=execute, a=attribute)
# -k: key for searching
```

### Create Rules File

```bash
sudo nano /etc/audit/rules.d/99-security.rules
```

### Essential Security Rules

```bash
# /etc/audit/rules.d/99-security.rules

# Remove any existing rules
-D

# Set buffer size
-b 8192

# Failure mode (1=silent, 2=printk)
-f 1

###########################################
# User and Authentication
###########################################

# Monitor login/logout
-w /var/log/lastlog -p wa -k logins
-w /var/log/faillog -p wa -k logins
-w /var/log/tallylog -p wa -k logins

# Monitor user/group changes
-w /etc/passwd -p wa -k user_modification
-w /etc/shadow -p wa -k user_modification
-w /etc/group -p wa -k group_modification
-w /etc/gshadow -p wa -k group_modification
-w /etc/sudoers -p wa -k sudoers_modification
-w /etc/sudoers.d/ -p wa -k sudoers_modification

# Monitor PAM configuration
-w /etc/pam.d/ -p wa -k pam_modification

###########################################
# Privilege Escalation
###########################################

# sudo usage
-w /usr/bin/sudo -p x -k privilege_escalation
-w /usr/bin/su -p x -k privilege_escalation

# setuid/setgid changes
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k permission_changes
-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k ownership_changes

###########################################
# System Configuration
###########################################

# Kernel modules
-w /sbin/insmod -p x -k kernel_modules
-w /sbin/rmmod -p x -k kernel_modules
-w /sbin/modprobe -p x -k kernel_modules

# System time changes
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -S clock_settime -k time_change

# Network configuration
-w /etc/hosts -p wa -k network_config
-w /etc/sysconfig/network -p wa -k network_config
-w /etc/netplan/ -p wa -k network_config

# SSH configuration
-w /etc/ssh/sshd_config -p wa -k ssh_config
-w /etc/ssh/sshd_config.d/ -p wa -k ssh_config

# Firewall configuration
-w /etc/ufw/ -p wa -k firewall_config
-w /etc/default/ufw -p wa -k firewall_config

# Cron configuration
-w /etc/crontab -p wa -k cron_config
-w /etc/cron.d/ -p wa -k cron_config
-w /var/spool/cron/ -p wa -k cron_config

###########################################
# Process Execution
###########################################

# Process execution tracking
-a always,exit -F arch=b64 -S execve -F auid>=1000 -F auid!=4294967295 -k process_execution

# Shell commands by root
-a always,exit -F arch=b64 -S execve -F euid=0 -k root_command

###########################################
# Network Activity
###########################################

# Socket creation
-a always,exit -F arch=b64 -S socket -F a0=2 -k network_socket
-a always,exit -F arch=b64 -S socket -F a0=10 -k network_socket6

# Network connections
-a always,exit -F arch=b64 -S connect -k network_connect

###########################################
# File System
###########################################

# File deletion by users
-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k file_deletion

# Mount operations
-a always,exit -F arch=b64 -S mount -S umount2 -k mount_operations

###########################################
# Make rules immutable (must be last)
###########################################
-e 2
```

### Load Rules

```bash
# Load rules
sudo augenrules --load

# Or restart auditd
sudo systemctl restart auditd

# Verify rules loaded
sudo auditctl -l
```

## Viewing Audit Logs

### Basic Commands

```bash
# View raw log
sudo tail -f /var/log/audit/audit.log

# Search by key
sudo ausearch -k ssh_config

# Search by time
sudo ausearch --start today
sudo ausearch --start "1 hour ago"

# Search by user
sudo ausearch -ua root
sudo ausearch -ui 1000

# Search by event type
sudo ausearch -m USER_LOGIN
```

### aureport - Summary Reports

```bash
# Summary of all events
sudo aureport --summary

# Authentication reports
sudo aureport -au --summary
sudo aureport --failed

# Login report
sudo aureport -l

# File access report
sudo aureport -f

# Executable report
sudo aureport -x

# System call report
sudo aureport -s

# User report
sudo aureport -u

# Report for specific time
sudo aureport --start today --end now
```

### Interpreting Events

Raw log entry:

```
type=SYSCALL msg=audit(1705312345.123:456): arch=c000003e syscall=59 success=yes exit=0 a0=7ffd12345678 a1=7ffd12345680 a2=7ffd12345688 a3=0 items=2 ppid=1234 pid=1235 auid=1000 uid=0 gid=0 euid=0 suid=0 fsuid=0 egid=0 sgid=0 fsgid=0 tty=pts0 ses=1 comm="sudo" exe="/usr/bin/sudo" key="privilege_escalation"
```

| Field | Meaning |
|-------|---------|
| type | Event type |
| msg | Timestamp:serial |
| arch | Architecture |
| syscall | System call number |
| success | Whether successful |
| auid | Audit UID (original login) |
| uid | Effective UID |
| exe | Executable path |
| key | Custom key tag |

### Decode with ausearch

```bash
# Interpreted output
sudo ausearch -k privilege_escalation --interpret

# Output:
# type=SYSCALL ... auid=admin uid=root exe=/usr/bin/sudo key=privilege_escalation
```

## Common Use Cases

### Track sudo Usage

```bash
# Rules for sudo
-w /usr/bin/sudo -p x -k sudo_usage
-a always,exit -F arch=b64 -S execve -F path=/usr/bin/sudo -k sudo_execution

# Search sudo events
sudo ausearch -k sudo_usage --interpret | less
```

### Track File Changes

```bash
# Watch specific file
-w /etc/nginx/nginx.conf -p wa -k nginx_config

# Search changes
sudo ausearch -k nginx_config --interpret
```

### Track User Commands

```bash
# All commands by user ID 1001
sudo ausearch -ui 1001 -x --interpret

# All commands by username
sudo ausearch -ua admin -x --interpret
```

### Detect Unauthorized Access

```bash
# Failed access attempts
sudo aureport --failed

# Failed authentication
sudo ausearch -m USER_AUTH -sv no

# Failed file access
sudo ausearch -m SYSCALL -sv no -k file_access
```

## Log Management

### Log Rotation

Edit `/etc/audit/auditd.conf`:

```ini
# Rotate when file reaches 50MB
max_log_file = 50

# Keep 10 rotated files
num_logs = 10

# Action when max reached
max_log_file_action = ROTATE
```

### Export Logs

```bash
# Export to file
sudo ausearch --start today --format csv > audit_today.csv

# Export specific key
sudo ausearch -k ssh_config --format text > ssh_changes.txt
```

### Remote Logging

Configure auditd to send to remote syslog:

Edit `/etc/audit/plugins.d/syslog.conf`:

```ini
active = yes
direction = out
path = builtin_syslog
type = builtin
args = LOG_INFO
format = string
```

## Integration with SIEM

### Send to Syslog

```bash
# Enable syslog plugin
sudo nano /etc/audit/plugins.d/syslog.conf
# Set: active = yes

sudo systemctl restart auditd
```

### JSON Output

```bash
# Convert to JSON for SIEM
sudo ausearch -k privilege_escalation --format json
```

## Performance Considerations

### Reduce Overhead

```bash
# Exclude high-volume, low-value events
-a never,exit -F arch=b64 -S read -S write -F dir=/var/log/

# Exclude specific binaries
-a never,exit -F path=/usr/bin/ls
```

### Monitor auditd Performance

```bash
# Check backlog
sudo auditctl -s

# Output:
# enabled 1
# failure 1
# pid 1234
# rate_limit 0
# backlog_limit 8192
# lost 0
# backlog 0
```

If "lost" is high, increase buffer:

```bash
-b 16384
```

## Troubleshooting

### Common Issues

**Rules not loading:**

```bash
# Check rule syntax
sudo auditctl -R /etc/audit/rules.d/99-security.rules

# View errors
sudo augenrules --check

# Check auditd log
sudo journalctl -u auditd
```

**High CPU usage:**

```bash
# Check for overly broad rules
sudo auditctl -l

# Look for rules without filters
# Add exclusions for high-volume events
```

**Disk filling up:**

```bash
# Check log size
du -h /var/log/audit/

# Verify rotation settings
grep -E "max_log|num_logs" /etc/audit/auditd.conf
```

### Verify Audit is Working

```bash
# Generate test event
sudo ls /etc/shadow

# Search for it
sudo ausearch -f /etc/shadow --interpret
```

## Quick Reference

### Commands

```bash
# Rule management
sudo auditctl -l           # List rules
sudo auditctl -D           # Delete rules
sudo augenrules --load     # Load rules

# Search
sudo ausearch -k KEY       # By key
sudo ausearch -ua USER     # By user
sudo ausearch -f FILE      # By file
sudo ausearch --start TIME # By time

# Reports
sudo aureport --summary    # Summary
sudo aureport -au          # Auth attempts
sudo aureport -l           # Logins
sudo aureport --failed     # Failures

# Status
sudo auditctl -s           # Audit status
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/audit/auditd.conf | Daemon config |
| /etc/audit/rules.d/*.rules | Rule files |
| /var/log/audit/audit.log | Log file |

## Next Steps

Continue to [Integrity Monitoring](integrity.md) to set up file integrity checking with AIDE and rkhunter.
