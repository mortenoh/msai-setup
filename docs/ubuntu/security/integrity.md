# Integrity Monitoring

File integrity monitoring (FIM) detects unauthorized changes to system files. This is essential for detecting compromises, ensuring compliance, and maintaining system trustworthiness.

## Overview

### What Integrity Monitoring Does

```
┌─────────────────────────────────────────────────────────────┐
│                    Baseline Database                         │
│         (Hashes, permissions, ownership, timestamps)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Periodic Scan                             │
│           (Compare current state to baseline)                │
└─────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┴─────────────────┐
            ▼                                   ▼
      ┌─────────────┐                   ┌─────────────┐
      │ No Changes  │                   │  Changes    │
      │   (OK)      │                   │  Detected   │
      └─────────────┘                   └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │   Alert!    │
                                        │  Investigate│
                                        └─────────────┘
```

### Tools Covered

| Tool | Purpose |
|------|---------|
| **AIDE** | File integrity checking (like Tripwire) |
| **rkhunter** | Rootkit detection |
| **chkrootkit** | Alternative rootkit scanner |
| **debsums** | Debian package verification |

## AIDE (Advanced Intrusion Detection Environment)

### Installation

```bash
# Install AIDE
sudo apt install aide aide-common

# View configuration
cat /etc/aide/aide.conf
```

### Configuration

AIDE configuration is split across multiple files:

| File | Purpose |
|------|---------|
| `/etc/aide/aide.conf` | Main configuration |
| `/etc/aide/aide.conf.d/*.conf` | Modular configs |
| `/var/lib/aide/aide.db` | Baseline database |
| `/var/lib/aide/aide.db.new` | New database |

### Understanding Rules

```bash
# /etc/aide/aide.conf

# Rule definitions
# p: permissions
# i: inode
# n: number of links
# u: user
# g: group
# s: size
# b: block count
# m: mtime (modification time)
# a: atime (access time)
# c: ctime (change time)
# S: check for growing size
# acl: Access Control Lists
# selinux: SELinux attributes
# xattrs: Extended attributes
# md5: MD5 checksum
# sha256: SHA256 checksum
# sha512: SHA512 checksum
# rmd160: RIPEMD160 checksum

# Common rule sets
NORMAL = p+i+n+u+g+s+m+c+acl+xattrs+sha256
PERMS = p+u+g+acl
LOG = p+u+g+n+S+acl+xattrs

# What to monitor
/etc    NORMAL
/bin    NORMAL
/sbin   NORMAL
/usr    NORMAL
/boot   NORMAL
/lib    NORMAL
/lib64  NORMAL

# Exclude changing files
!/var/log/.*
!/var/spool/.*
!/var/cache/.*
```

### Custom Configuration

Create `/etc/aide/aide.conf.d/99-custom.conf`:

```bash
# Custom AIDE configuration

# Monitor critical configs
/etc/ssh NORMAL
/etc/sudoers NORMAL
/etc/passwd NORMAL
/etc/shadow NORMAL
/etc/pam.d NORMAL

# Monitor web content with checksums
/var/www NORMAL

# Exclude frequently changing files
!/var/www/app/cache
!/var/www/app/logs

# Monitor cron
/etc/cron.d NORMAL
/var/spool/cron NORMAL

# Log files - just permissions
/var/log LOG

# Exclude dynamic content
!/proc
!/sys
!/run
!/dev
!/tmp
!/var/tmp
```

### Initialize Database

```bash
# Generate initial baseline
sudo aideinit

# This creates /var/lib/aide/aide.db.new
# Move to active database
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

!!! warning "Initialize on Clean System"
    Initialize the AIDE database immediately after system setup, before putting the server into production.

### Running Checks

```bash
# Manual check
sudo aide.wrapper --check

# Or use aide directly
sudo aide --check --config=/etc/aide/aide.conf

# View report
# Report written to stdout
```

### Update Database

After legitimate changes:

```bash
# Generate new database
sudo aide.wrapper --update

# Review changes, then replace old database
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db
```

### Automated Checks

AIDE comes with a daily cron job. Configure notification:

Edit `/etc/default/aide`:

```bash
# Email report
MAILTO=admin@example.com

# Quiet mode (only email on changes)
QUIETREPORTS=yes
```

### Interpreting Reports

```
AIDE found differences between database and filesystem!!
Start timestamp: 2024-01-15 10:00:00
Summary:
  Total number of files:        125000
  Added files:                  3
  Removed files:                0
  Changed files:                5

---------------------------------------------------
Added files:
---------------------------------------------------
f++++++++++++++++: /etc/cron.d/newjob

---------------------------------------------------
Changed files:
---------------------------------------------------
f     ...C...: /etc/passwd
  SHA256   : OLD_HASH -> NEW_HASH

f     .....i.: /etc/nginx/nginx.conf
  Inode    : 12345 -> 12346
  SHA256   : OLD_HASH -> NEW_HASH
```

| Code | Meaning |
|------|---------|
| `+` | Added |
| `-` | Removed |
| `p` | Permissions |
| `i` | Inode |
| `n` | Links |
| `u` | User |
| `g` | Group |
| `s` | Size |
| `C` | Checksum |

## rkhunter (Rootkit Hunter)

### Installation

```bash
sudo apt install rkhunter
```

### Configuration

Edit `/etc/rkhunter.conf`:

```bash
# Update mirrors
UPDATE_MIRRORS=1
MIRRORS_MODE=0

# Web command for updates
WEB_CMD=curl

# Email alerts
MAIL-ON-WARNING=admin@example.com

# Allow script whitelisting
SCRIPTWHITELIST="/usr/bin/egrep"
SCRIPTWHITELIST="/usr/bin/fgrep"
SCRIPTWHITELIST="/usr/bin/which"

# Allow hidden directories (for legitimate purposes)
ALLOWHIDDENDIR="/dev/.udev"

# Disable specific tests if needed
# DISABLE_TESTS="suspscan hidden_procs deleted_files packet_cap_apps apps"

# Log file
LOGFILE=/var/log/rkhunter.log
```

### Update Database

```bash
# Update signatures
sudo rkhunter --update

# Update file properties database
sudo rkhunter --propupd
```

### Running Checks

```bash
# Full scan
sudo rkhunter --check

# Skip prompts
sudo rkhunter --check --skip-keypress

# Check and report only
sudo rkhunter --check --report-warnings-only

# Verbose output
sudo rkhunter --check --verbose
```

### Understanding Results

```
Checking for rootkits...
  Performing check of known rootkit files and directories
    55808 Trojan - Variant A                         [ Not found ]
    ADM Worm                                         [ Not found ]
    ...

Performing additional rootkit checks
  Suckit Rootkit additional checks                   [ OK ]
  Checking for possible rootkit files and directories [ None found ]
  Checking for possible rootkit strings              [ None found ]

Checking the local host...
  Performing system boot checks
    Checking for local host name                     [ Found ]
    Checking for system startup files                [ OK ]
  Checking for group file changes                    [ None found ]
  Checking for password file changes                 [ None found ]

System checks summary
=====================

File properties checks...
    Files checked: 142
    Suspect files: 0

Rootkit checks...
    Rootkits checked : 480
    Possible rootkits: 0
```

### Handle False Positives

Update `/etc/rkhunter.conf` for known-good items:

```bash
# Allow specific hidden files
ALLOWHIDDENFILE="/usr/share/man/man1/..teleport.1.gz"

# Allow specific scripts
SCRIPTWHITELIST="/usr/bin/ldd"

# Allow specific process paths
ALLOWIPCPID="/dev/shm/pulse-shm-*"
```

After changes:

```bash
sudo rkhunter --propupd
```

### Automated Scans

rkhunter installs a daily cron job. Configure in `/etc/default/rkhunter`:

```bash
# Run daily
CRON_DAILY_RUN="true"

# Weekly database update
CRON_DB_UPDATE="true"

# Email report
REPORT_EMAIL="admin@example.com"

# Only report warnings
APT_AUTOGEN="true"
```

## chkrootkit

### Installation

```bash
sudo apt install chkrootkit
```

### Running Checks

```bash
# Basic scan
sudo chkrootkit

# Quiet mode (errors only)
sudo chkrootkit -q

# Expert mode (show tests)
sudo chkrootkit -x
```

### Handle False Positives

Some checks may produce false positives. Check specific tests:

```bash
# Run specific test
sudo chkrootkit -x infected

# Common false positives:
# - Suckit check on ptrace restrictions
# - Hidden procs from containerized processes
```

## debsums - Package Verification

### Installation

```bash
sudo apt install debsums
```

### Usage

```bash
# Check all installed packages
sudo debsums

# Check specific package
sudo debsums openssh-server

# Silent mode (show only errors)
sudo debsums -s

# Check only configuration files
sudo debsums -e

# Generate missing md5sums
sudo debsums --generate=all
```

### Interpret Results

```
/usr/bin/sshd                                        OK
/etc/ssh/sshd_config                                 CHANGED
```

- `OK`: File matches package
- `CHANGED`: File modified
- `MISSING`: File missing

## Comprehensive Integrity Script

Create `/usr/local/bin/integrity-check.sh`:

```bash
#!/bin/bash
# Comprehensive integrity check

MAILTO="admin@example.com"
LOGDIR="/var/log/integrity"
DATE=$(date +%Y%m%d)

mkdir -p $LOGDIR

echo "=== Integrity Check $(date) ===" | tee $LOGDIR/check-$DATE.log

# AIDE check
echo -e "\n--- AIDE Check ---" | tee -a $LOGDIR/check-$DATE.log
sudo aide.wrapper --check >> $LOGDIR/aide-$DATE.log 2>&1
AIDE_STATUS=$?

# rkhunter check
echo -e "\n--- rkhunter Check ---" | tee -a $LOGDIR/check-$DATE.log
sudo rkhunter --check --skip-keypress --report-warnings-only >> $LOGDIR/rkhunter-$DATE.log 2>&1
RKHUNTER_STATUS=$?

# debsums check
echo -e "\n--- debsums Check ---" | tee -a $LOGDIR/check-$DATE.log
sudo debsums -s >> $LOGDIR/debsums-$DATE.log 2>&1
DEBSUMS_STATUS=$?

# Summary
echo -e "\n=== Summary ===" | tee -a $LOGDIR/check-$DATE.log
echo "AIDE: $([ $AIDE_STATUS -eq 0 ] && echo 'OK' || echo 'CHANGES DETECTED')" | tee -a $LOGDIR/check-$DATE.log
echo "rkhunter: $([ $RKHUNTER_STATUS -eq 0 ] && echo 'OK' || echo 'WARNINGS')" | tee -a $LOGDIR/check-$DATE.log
echo "debsums: $([ $DEBSUMS_STATUS -eq 0 ] && echo 'OK' || echo 'CHANGES')" | tee -a $LOGDIR/check-$DATE.log

# Alert if issues found
if [ $AIDE_STATUS -ne 0 ] || [ $RKHUNTER_STATUS -ne 0 ]; then
    cat $LOGDIR/check-$DATE.log | mail -s "[ALERT] Integrity check issues on $(hostname)" $MAILTO
fi
```

```bash
sudo chmod +x /usr/local/bin/integrity-check.sh

# Add to cron
echo "0 2 * * * root /usr/local/bin/integrity-check.sh" | sudo tee /etc/cron.d/integrity-check
```

## Best Practices

### Initial Setup

1. Install and configure tools on clean system
2. Initialize baselines immediately
3. Document legitimate baseline changes
4. Store baseline backups offline

### Regular Maintenance

| Task | Frequency |
|------|-----------|
| AIDE check | Daily |
| rkhunter check | Daily |
| debsums check | Weekly |
| Update AIDE baseline | After legitimate changes |
| Update rkhunter signatures | Weekly |

### Incident Response

When integrity check finds changes:

1. **Don't panic** - May be legitimate
2. **Document** - Save all check outputs
3. **Investigate** - Determine if change is expected
4. **Verify** - Check change logs, update tickets
5. **Update or alert** - Update baseline if legitimate, investigate if not

## Quick Reference

### AIDE Commands

```bash
sudo aideinit                    # Initialize database
sudo aide.wrapper --check        # Run check
sudo aide.wrapper --update       # Update database
sudo cp /var/lib/aide/aide.db.new /var/lib/aide/aide.db  # Apply update
```

### rkhunter Commands

```bash
sudo rkhunter --update           # Update signatures
sudo rkhunter --propupd          # Update properties database
sudo rkhunter --check            # Run scan
```

### Key Files

| Tool | Config | Database |
|------|--------|----------|
| AIDE | /etc/aide/aide.conf | /var/lib/aide/aide.db |
| rkhunter | /etc/rkhunter.conf | /var/lib/rkhunter/db/ |

## Next Steps

Continue to [CIS Benchmarks](cis-benchmarks.md) to implement compliance-focused hardening based on industry standards.
