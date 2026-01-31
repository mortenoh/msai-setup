# Security Incident Response

This page covers initial response to suspected security incidents on Ubuntu Server.

## Incident Response Basics

### Response Priorities

```
┌─────────────────────────────────────────────────────────────┐
│                    1. Don't Panic                            │
│             Hasty actions destroy evidence                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    2. Assess Severity                        │
│         What's affected? Is it ongoing?                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    3. Contain                                │
│             Limit damage without destroying evidence         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    4. Preserve Evidence                      │
│                 Logs, memory, disk images                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    5. Investigate                            │
│                 Determine scope and method                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    6. Remediate                              │
│               Remove access, patch, restore                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    7. Review                                 │
│               Improve defenses, document                     │
└─────────────────────────────────────────────────────────────┘
```

## Initial Assessment

### Signs of Compromise

| Indicator | What to Check |
|-----------|---------------|
| Unexpected processes | `ps aux`, `top` |
| Unknown network connections | `ss -anp`, `netstat` |
| Modified system files | `debsums`, AIDE |
| Unauthorized users | `last`, `w`, `/etc/passwd` |
| Unusual log entries | `auth.log`, `syslog` |
| High resource usage | CPU, memory, network |
| Unexpected cron jobs | `/var/spool/cron`, `/etc/cron.*` |
| Modified startup | systemd units, rc scripts |

### Quick Assessment Script

```bash
#!/bin/bash
echo "=== Security Assessment ==="
DATE=$(date +%Y%m%d_%H%M%S)
OUTFILE="/tmp/security-assessment-$DATE.txt"

echo "Output: $OUTFILE"
exec > >(tee -a "$OUTFILE") 2>&1

echo "=== Current Users ==="
w
echo ""
who

echo -e "\n=== Recent Logins ==="
last -n 20

echo -e "\n=== Failed Logins ==="
sudo grep "Failed password" /var/log/auth.log | tail -20

echo -e "\n=== Running Processes ==="
ps auxf | head -50

echo -e "\n=== Network Connections ==="
sudo ss -anp | grep -E "ESTABLISHED|LISTEN"

echo -e "\n=== Listening Ports ==="
sudo ss -tlnp

echo -e "\n=== Cron Jobs ==="
for user in $(cut -f1 -d: /etc/passwd); do
    crontab -l -u $user 2>/dev/null
done

echo -e "\n=== Recent File Changes in /etc ==="
sudo find /etc -mtime -1 -type f 2>/dev/null

echo -e "\n=== SUID/SGID Files ==="
sudo find / -type f \( -perm -4000 -o -perm -2000 \) 2>/dev/null | head -30

echo -e "\n=== Recent Auth Log ==="
sudo tail -50 /var/log/auth.log

echo -e "\n=== Assessment Complete ==="
echo "Results saved to: $OUTFILE"
```

## Containment

### Network Isolation

**Immediate isolation (high severity):**

```bash
# Block all traffic except existing SSH
sudo iptables -I INPUT 1 -m conntrack --ctstate ESTABLISHED -j ACCEPT
sudo iptables -I INPUT 2 -p tcp --dport 22 -j ACCEPT
sudo iptables -I INPUT 3 -j DROP
```

**Partial isolation:**

```bash
# Block outbound (stop data exfiltration)
sudo iptables -I OUTPUT 1 -m conntrack --ctstate ESTABLISHED -j ACCEPT
sudo iptables -I OUTPUT 2 -j DROP
```

**Record active connections first:**

```bash
sudo ss -anp > /tmp/connections-$(date +%Y%m%d_%H%M%S).txt
```

### Account Containment

```bash
# Disable compromised account
sudo usermod -L compromised_user

# Kill user's sessions
sudo pkill -u compromised_user

# Expire password
sudo passwd -e compromised_user

# Check for persistence
crontab -l -u compromised_user
sudo ls -la /home/compromised_user/.ssh/
```

### Service Containment

```bash
# Stop compromised service
sudo systemctl stop suspicious_service

# Prevent restart
sudo systemctl mask suspicious_service

# Check service logs
sudo journalctl -u suspicious_service --since "1 week ago"
```

## Evidence Preservation

### Log Collection

```bash
# Create evidence directory
EVIDENCE_DIR="/root/incident-$(date +%Y%m%d)"
sudo mkdir -p "$EVIDENCE_DIR"

# Copy logs
sudo cp -a /var/log "$EVIDENCE_DIR/"

# Copy audit logs
sudo cp -a /var/log/audit "$EVIDENCE_DIR/" 2>/dev/null

# Copy journal
sudo journalctl --since "1 month ago" > "$EVIDENCE_DIR/journal.txt"

# Compress
sudo tar -czvf "$EVIDENCE_DIR.tar.gz" "$EVIDENCE_DIR"
```

### System State

```bash
# Process list
ps auxf > "$EVIDENCE_DIR/processes.txt"

# Network connections
ss -anp > "$EVIDENCE_DIR/connections.txt"
netstat -anp > "$EVIDENCE_DIR/netstat.txt"

# User info
cat /etc/passwd > "$EVIDENCE_DIR/passwd.txt"
cat /etc/shadow > "$EVIDENCE_DIR/shadow.txt"
last > "$EVIDENCE_DIR/last.txt"
lastlog > "$EVIDENCE_DIR/lastlog.txt"

# Cron
cp -r /var/spool/cron "$EVIDENCE_DIR/"
cp -r /etc/cron.* "$EVIDENCE_DIR/"

# Startup
systemctl list-unit-files --state=enabled > "$EVIDENCE_DIR/enabled-services.txt"
```

### Memory Capture (Advanced)

```bash
# Install LiME (if prepared in advance)
sudo apt install lime-forensics-dkms

# Capture memory
sudo insmod /lib/modules/$(uname -r)/updates/dkms/lime.ko "path=/tmp/memory.lime format=lime"
```

### Disk Image (If Needed)

```bash
# Create disk image (requires unmounted or live USB)
sudo dd if=/dev/sda of=/path/to/external/disk.img bs=4M status=progress
```

## Investigation

### User Activity

```bash
# Who is/was logged in
w
last
lastlog

# Failed logins
grep "Failed password" /var/log/auth.log

# Successful logins
grep "Accepted" /var/log/auth.log

# sudo usage
grep "sudo:" /var/log/auth.log

# su usage
grep "su:" /var/log/auth.log
```

### Process Analysis

```bash
# Running processes with details
ps auxf

# Processes with network connections
sudo ss -anp | grep ESTABLISHED

# Check /proc for suspicious processes
ls -la /proc/[0-9]*/exe 2>/dev/null | grep deleted

# Open files by process
lsof -p PID
```

### File System Analysis

```bash
# Recently modified files
find / -mtime -7 -type f 2>/dev/null

# Recently accessed
find / -atime -1 -type f 2>/dev/null

# New SUID files
find / -type f -perm -4000 -mtime -30 2>/dev/null

# Check for hidden files in unusual places
find / -name ".*" -type f 2>/dev/null | grep -v -E "^/home|^/root"

# Package verification
sudo debsums -c
```

### Network Analysis

```bash
# Current connections
ss -anp

# Listening services
ss -tlnp

# DNS queries (if logged)
grep -r "query" /var/log/*

# Firewall logs
grep "UFW" /var/log/ufw.log
```

### Persistence Mechanisms

Check common persistence locations:

```bash
# Cron
cat /etc/crontab
ls -la /etc/cron.*
for user in $(cut -f1 -d: /etc/passwd); do
    echo "=== $user ===" && crontab -l -u $user 2>/dev/null
done

# systemd
systemctl list-unit-files --state=enabled
ls -la /etc/systemd/system/

# rc.local
cat /etc/rc.local

# Profile scripts
ls -la /etc/profile.d/
cat /etc/profile
cat /etc/bash.bashrc

# User profiles
for home in /home/*; do
    cat "$home/.bashrc" "$home/.profile" 2>/dev/null
done

# SSH authorized keys
find /home -name "authorized_keys" -exec cat {} \;
cat /root/.ssh/authorized_keys

# Init scripts
ls -la /etc/init.d/
```

## Common Attack Patterns

### SSH Brute Force

```bash
# Check for attacks
grep "Failed password" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn | head

# Check successful logins from attackers
grep "Accepted" /var/log/auth.log | awk '{print $(NF-3)}' | sort | uniq -c | sort -rn
```

### Web Shell

```bash
# Find PHP shells
find /var/www -name "*.php" -exec grep -l "eval\|base64_decode\|exec\|system\|passthru" {} \;

# Recently modified web files
find /var/www -mtime -7 -type f

# Unusual permissions
find /var/www -perm -o+w -type f
```

### Cryptominer

```bash
# High CPU usage
ps aux --sort=-%cpu | head

# Suspicious processes
ps aux | grep -E "xmrig|minerd|cgminer"

# Unusual network connections
ss -anp | grep -E ":3333|:4444|:8333"
```

### Rootkit

```bash
# Run rkhunter
sudo rkhunter --check

# Run chkrootkit
sudo chkrootkit

# Check for hidden processes
ps aux | wc -l
ls -d /proc/[0-9]* | wc -l
# Numbers should match approximately
```

## Remediation

### Remove Unauthorized Access

```bash
# Change all passwords
sudo passwd root
sudo passwd admin

# Regenerate SSH keys
sudo rm /etc/ssh/ssh_host_*
sudo dpkg-reconfigure openssh-server

# Review authorized_keys
find / -name "authorized_keys" -exec cat {} \; -exec echo "---" \;

# Remove unauthorized keys
```

### Clean Persistence

```bash
# Remove malicious cron jobs
crontab -r -u compromised_user

# Remove malicious services
sudo systemctl stop malicious.service
sudo systemctl disable malicious.service
sudo rm /etc/systemd/system/malicious.service
sudo systemctl daemon-reload

# Remove malicious files
# (After investigation and backup)
```

### System Restore

For severe compromise, consider:

1. **Restore from backup** - Cleanest option
2. **Reinstall** - Fresh system, restore data only
3. **Clean in place** - Riskier, may miss persistence

## Prevention After Incident

### Immediate Actions

- [ ] Patch the vulnerability that was exploited
- [ ] Change all credentials
- [ ] Review and harden SSH
- [ ] Enable/review fail2ban
- [ ] Review firewall rules
- [ ] Enable comprehensive logging

### Long-term Improvements

- [ ] Implement intrusion detection (AIDE, OSSEC)
- [ ] Enable audit logging
- [ ] Regular security assessments
- [ ] Staff security training
- [ ] Incident response plan
- [ ] Backup verification

## Quick Reference

### Emergency Commands

```bash
# Who's logged in now
w

# Recent logins
last -n 20

# Kill all sessions for user
sudo pkill -u username

# Lock account
sudo usermod -L username

# Block all network
sudo iptables -I INPUT 1 -j DROP
sudo iptables -I OUTPUT 1 -j DROP

# Allow only your SSH
sudo iptables -I INPUT 1 -s YOUR_IP -p tcp --dport 22 -j ACCEPT
```

### Investigation Commands

```bash
# Processes
ps auxf
ss -anp

# Logins
last
grep -E "Accepted|Failed" /var/log/auth.log

# Files
find / -mtime -7 -type f 2>/dev/null
debsums -c

# Network
ss -tlnp
ss -anp | grep ESTABLISHED
```

## When to Call for Help

Escalate to security professionals when:

- Confirmed data breach
- Regulatory requirements (HIPAA, PCI, GDPR)
- Advanced persistent threat suspected
- Critical system compromise
- Legal evidence needed
- Beyond your expertise

## Next Steps

After incident resolution, review and implement recommendations from:

- [Security section](../security/index.md)
- [Reference Checklist](../reference/checklist.md)
