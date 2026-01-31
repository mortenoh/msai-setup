# Security Overview

This section covers comprehensive security hardening for Ubuntu Server 24.04 LTS, building on the foundation established in the installation and system configuration sections.

## Security Philosophy

### Defense in Depth

No single security measure is sufficient. Defense in depth layers multiple controls:

```
┌─────────────────────────────────────────────────────────────┐
│                    Physical Security                         │
│               (Data center, rack locks)                      │
├─────────────────────────────────────────────────────────────┤
│                    Network Security                          │
│           (Firewall, segmentation, IDS)                      │
├─────────────────────────────────────────────────────────────┤
│                      Host Security                           │
│        (Kernel hardening, AppArmor, auditd)                 │
├─────────────────────────────────────────────────────────────┤
│                  Application Security                        │
│          (Sandboxing, input validation)                      │
├─────────────────────────────────────────────────────────────┤
│                     Data Security                            │
│         (Encryption, access controls, backup)                │
└─────────────────────────────────────────────────────────────┘
```

### Principle of Least Privilege

Every user, process, and system component should have only the minimum privileges needed to perform its function.

### Security vs. Usability

Security measures should be proportional to risk. Over-hardening can:

- Cause operational problems
- Encourage workarounds
- Create alert fatigue

## Section Contents

| Page | Description |
|------|-------------|
| [Kernel Hardening](kernel-hardening.md) | sysctl settings, kernel parameters, ASLR |
| [SSH Hardening](ssh-hardening.md) | Ubuntu-specific SSH configuration |
| [AppArmor](apparmor.md) | Mandatory access control profiles |
| [Fail2ban](fail2ban.md) | Intrusion prevention and banning |
| [auditd](auditd.md) | Linux audit framework |
| [Integrity Monitoring](integrity.md) | AIDE, rkhunter, file integrity |
| [CIS Benchmarks](cis-benchmarks.md) | Compliance and automated scanning |

## Security Baseline

### Minimum Recommended Controls

| Control | Purpose | Page |
|---------|---------|------|
| Firewall enabled | Network access control | [Firewall](../firewall.md) |
| SSH key-only auth | Strong authentication | [SSH Hardening](ssh-hardening.md) |
| Kernel hardening | Exploit mitigation | [Kernel Hardening](kernel-hardening.md) |
| Fail2ban | Brute force protection | [Fail2ban](fail2ban.md) |
| Automatic updates | Patch management | [Unattended Upgrades](../updates/unattended-upgrades.md) |

### Enhanced Security

For higher security requirements:

| Control | Purpose | Page |
|---------|---------|------|
| AppArmor profiles | Application containment | [AppArmor](apparmor.md) |
| auditd | Activity monitoring | [auditd](auditd.md) |
| AIDE | File integrity | [Integrity](integrity.md) |
| CIS compliance | Benchmark adherence | [CIS Benchmarks](cis-benchmarks.md) |
| 2FA | Multi-factor auth | [PAM](../system/pam.md) |

## Quick Security Audit

### Basic Security Check

```bash
# Run this script to check basic security status

echo "=== Security Status Check ==="

echo -e "\n--- Firewall ---"
sudo ufw status | head -5

echo -e "\n--- SSH Config ---"
grep -E "^(PermitRootLogin|PasswordAuthentication|PubkeyAuthentication)" \
    /etc/ssh/sshd_config /etc/ssh/sshd_config.d/* 2>/dev/null

echo -e "\n--- Fail2ban ---"
systemctl is-active fail2ban 2>/dev/null || echo "Not installed"

echo -e "\n--- AppArmor ---"
sudo aa-status --enabled 2>/dev/null && echo "AppArmor: Enabled" || echo "AppArmor: Disabled"

echo -e "\n--- Kernel ---"
sysctl kernel.randomize_va_space net.ipv4.tcp_syncookies 2>/dev/null

echo -e "\n--- Open Ports ---"
sudo ss -tlnp | grep LISTEN

echo -e "\n--- Failed Logins (last 24h) ---"
sudo journalctl --since "24 hours ago" -t sshd | grep -c "Failed password" || echo "0"

echo -e "\n--- System Updates ---"
apt list --upgradable 2>/dev/null | tail -n +2 | wc -l
```

### What to Check Regularly

| Check | Frequency | Command |
|-------|-----------|---------|
| Failed login attempts | Daily | `sudo journalctl -u ssh --since today \| grep Failed` |
| Banned IPs | Daily | `sudo fail2ban-client status sshd` |
| Available updates | Daily | `apt list --upgradable` |
| Listening ports | Weekly | `sudo ss -tlnp` |
| User accounts | Monthly | `getent passwd \| grep -v nologin` |
| sudo access | Monthly | `grep -r "sudo" /etc/sudoers*` |
| Audit logs | Weekly | `sudo aureport --summary` |

## Attack Surface Reduction

### Disable Unused Services

```bash
# List enabled services
systemctl list-unit-files --state=enabled --type=service

# Common services to evaluate
# cups.service      - Printing (disable on servers)
# avahi-daemon      - mDNS/Bonjour (often unnecessary)
# bluetooth         - Bluetooth (disable if no hardware)
# ModemManager      - Modem support (usually unnecessary)

# Disable example
sudo systemctl disable --now cups avahi-daemon
```

### Remove Unused Packages

```bash
# List manually installed packages
apt-mark showmanual

# Remove unnecessary packages
sudo apt remove --purge package-name
sudo apt autoremove
```

### Close Unnecessary Ports

```bash
# Check what's listening
sudo ss -tlnp

# Review each listening service
# Close ports that shouldn't be exposed
sudo ufw deny <port>
```

## Security Monitoring

### Log Locations

| Log | Location | Purpose |
|-----|----------|---------|
| Auth | `/var/log/auth.log` | Authentication events |
| System | `/var/log/syslog` | General system logs |
| Kernel | `/var/log/kern.log` | Kernel messages |
| UFW | `/var/log/ufw.log` | Firewall events |
| Audit | `/var/log/audit/audit.log` | auditd events |
| Fail2ban | `/var/log/fail2ban.log` | Banning events |

### Critical Events to Monitor

| Event | Log Source | Example |
|-------|------------|---------|
| Root login | auth.log | `sudo grep "root" /var/log/auth.log` |
| Failed auth | auth.log | `sudo grep "Failed" /var/log/auth.log` |
| sudo usage | auth.log | `sudo grep "sudo:" /var/log/auth.log` |
| Service changes | syslog | `sudo grep "systemd" /var/log/syslog` |
| Firewall blocks | ufw.log | `sudo grep "BLOCK" /var/log/ufw.log` |

## Incident Response Basics

### If You Suspect Compromise

1. **Don't panic** - Rash actions can destroy evidence
2. **Document** - Note what you observed and when
3. **Contain** - Isolate the system if possible (network disconnect)
4. **Preserve** - Don't modify files, collect logs
5. **Investigate** - Determine scope and method
6. **Remediate** - Fix vulnerabilities, remove access
7. **Recover** - Restore from known-good state
8. **Review** - Improve defenses based on lessons learned

### Initial Investigation Commands

```bash
# Who is logged in
w
who
last

# Recent auth activity
sudo journalctl -u ssh --since "1 hour ago"

# Running processes
ps auxf

# Network connections
sudo ss -tlnp
sudo ss -anp

# Recent file changes
sudo find / -mmin -60 -type f 2>/dev/null

# Cron jobs (persistence check)
for user in $(cut -f1 -d: /etc/passwd); do
    crontab -u $user -l 2>/dev/null
done
```

## Related Documentation

### In This Guide

| Topic | Location |
|-------|----------|
| Firewall configuration | [Firewall & Security](../../networking/index.md) |
| SSH configuration | [SSH Guide](../../ssh/index.md) |
| User management | [System Configuration](../system/index.md) |

### External Resources

| Resource | URL |
|----------|-----|
| Ubuntu Security | https://ubuntu.com/security |
| CIS Benchmarks | https://www.cisecurity.org/benchmark/ubuntu_linux |
| NIST Guidelines | https://csrc.nist.gov/publications/sp800 |
| DISA STIGs | https://public.cyber.mil/stigs/ |

## Next Steps

Begin with [Kernel Hardening](kernel-hardening.md) to implement fundamental security controls at the kernel level.
