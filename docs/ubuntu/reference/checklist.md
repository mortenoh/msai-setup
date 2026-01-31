# Complete Hardening Checklist

Comprehensive checklist for hardening Ubuntu Server 24.04 LTS. Use this as a verification guide after installation.

## Pre-Installation

- [ ] Hardware requirements verified
- [ ] ISO downloaded from official source
- [ ] ISO checksum verified
- [ ] ISO GPG signature verified
- [ ] Boot media created and tested
- [ ] Disk partitioning plan determined
- [ ] LUKS encryption passphrase prepared
- [ ] Network configuration planned

## BIOS/UEFI Settings

- [ ] UEFI mode enabled (not Legacy)
- [ ] Secure Boot enabled
- [ ] TPM enabled (if available)
- [ ] Boot password set
- [ ] Setup/BIOS password set
- [ ] USB boot enabled temporarily for install
- [ ] Virtualization (VT-x/AMD-V) enabled if needed

## Installation

- [ ] Full disk encryption (LUKS) enabled
- [ ] LVM configured
- [ ] Separate partitions created:
  - [ ] /boot/efi (512 MB)
  - [ ] /boot (1 GB)
  - [ ] / (root)
  - [ ] /home
  - [ ] /var
  - [ ] /tmp
  - [ ] swap
- [ ] Strong LUKS passphrase used
- [ ] SSH server installed
- [ ] SSH keys imported

## Post-Installation - Immediate

- [ ] System updated: `sudo apt update && sudo apt upgrade`
- [ ] Timezone configured: `timedatectl set-timezone`
- [ ] Hostname configured properly
- [ ] Time synchronization verified
- [ ] SSH access verified from remote

## User Management

- [ ] Root direct login disabled
- [ ] Admin user created with sudo access
- [ ] SSH keys deployed for admin user
- [ ] Unique user accounts for each admin
- [ ] No shared accounts
- [ ] Unused default accounts removed
- [ ] Home directory permissions set to 700
- [ ] Password aging configured:
  - [ ] PASS_MAX_DAYS set
  - [ ] PASS_MIN_DAYS set
  - [ ] PASS_WARN_AGE set

## sudo Configuration

- [ ] NOPASSWD avoided (or documented exception)
- [ ] sudo group membership reviewed
- [ ] Custom rules in /etc/sudoers.d/
- [ ] Timeout configured (timestamp_timeout)
- [ ] Logging enabled

## PAM Configuration

- [ ] pam_pwquality installed and configured:
  - [ ] Minimum length 14+ characters
  - [ ] Complexity requirements set
  - [ ] Dictionary check enabled
- [ ] pam_faillock configured:
  - [ ] deny = 5
  - [ ] unlock_time = 600
- [ ] Password history enforced (remember)

## SSH Hardening

- [ ] Root login disabled (PermitRootLogin no)
- [ ] Password authentication disabled
- [ ] Public key authentication enabled
- [ ] Strong key exchange algorithms only
- [ ] Strong ciphers only
- [ ] Strong MACs only
- [ ] MaxAuthTries set (3)
- [ ] LoginGraceTime set (60)
- [ ] ClientAliveInterval configured
- [ ] X11Forwarding disabled (unless needed)
- [ ] AllowTcpForwarding disabled (unless needed)
- [ ] Banner configured (optional)
- [ ] Fail2ban protecting SSH

For detailed SSH hardening, see [SSH Hardening](../security/ssh-hardening.md).

## Firewall

- [ ] UFW enabled
- [ ] Default deny incoming
- [ ] Default allow outgoing
- [ ] Only necessary ports allowed
- [ ] SSH allowed (before enabling UFW!)
- [ ] Source IP restrictions where possible
- [ ] Logging enabled

For detailed firewall configuration, see [Firewall Guide](../../networking/index.md).

## Kernel Hardening

sysctl settings in `/etc/sysctl.d/99-security.conf`:

- [ ] kernel.randomize_va_space = 2
- [ ] kernel.kptr_restrict = 2
- [ ] kernel.dmesg_restrict = 1
- [ ] fs.suid_dumpable = 0
- [ ] net.ipv4.conf.all.accept_source_route = 0
- [ ] net.ipv4.conf.all.accept_redirects = 0
- [ ] net.ipv4.conf.all.send_redirects = 0
- [ ] net.ipv4.conf.all.rp_filter = 1
- [ ] net.ipv4.conf.all.log_martians = 1
- [ ] net.ipv4.tcp_syncookies = 1
- [ ] net.ipv4.icmp_echo_ignore_broadcasts = 1

## Mount Options

fstab entries with security options:

- [ ] /home mounted with nodev,nosuid
- [ ] /var mounted with nodev,nosuid
- [ ] /var/log mounted with nodev,nosuid,noexec
- [ ] /tmp mounted with nodev,nosuid,noexec
- [ ] /dev/shm mounted with nodev,nosuid,noexec

## Automatic Updates

- [ ] unattended-upgrades installed
- [ ] Automatic security updates enabled
- [ ] Email notifications configured (optional)
- [ ] Automatic reboot configured or Livepatch enabled

## Logging

- [ ] journald configured for persistent storage
- [ ] rsyslog configured
- [ ] Log rotation configured
- [ ] Remote logging configured (optional)
- [ ] auditd installed and configured
- [ ] Audit rules for:
  - [ ] User/group changes
  - [ ] Authentication events
  - [ ] sudo usage
  - [ ] File changes in /etc
  - [ ] Time changes

## AppArmor

- [ ] AppArmor enabled
- [ ] Profiles in enforce mode
- [ ] Custom profiles for applications
- [ ] No unconfined processes (unless required)

## Fail2ban

- [ ] Fail2ban installed and enabled
- [ ] SSH jail configured
- [ ] Reasonable ban times
- [ ] Email notifications (optional)
- [ ] Jails for other services as needed

## Services

- [ ] Unnecessary services disabled:
  - [ ] cups (unless printing needed)
  - [ ] avahi-daemon (unless mDNS needed)
  - [ ] bluetooth (unless hardware present)
  - [ ] snapd (unless using snaps)
- [ ] Running services reviewed
- [ ] Service hardening applied (systemd options)
- [ ] Network services bound to specific interfaces

## File Integrity

- [ ] AIDE installed and initialized
- [ ] AIDE database baseline created
- [ ] Daily AIDE checks scheduled
- [ ] rkhunter installed
- [ ] rkhunter database updated
- [ ] Rootkit checks scheduled

## Disk Encryption

- [ ] LUKS encryption active
- [ ] Strong passphrase used
- [ ] Recovery key created and stored securely
- [ ] LUKS header backed up

## Backup

- [ ] Backup solution configured
- [ ] Critical data backed up:
  - [ ] /etc
  - [ ] /home
  - [ ] Application data
  - [ ] Databases
- [ ] Backup restoration tested
- [ ] Off-site backup configured

## Network

- [ ] Static IP configured (for servers)
- [ ] DNS servers configured
- [ ] IPv6 disabled (if not used)
- [ ] Network interfaces reviewed

## Documentation

- [ ] System configuration documented
- [ ] Changes logged
- [ ] Recovery procedures documented
- [ ] Contact information recorded

## Verification Commands

Run these to verify hardening:

```bash
# Security scan
sudo lynis audit system

# Service security scores
systemd-analyze security

# Listening ports
sudo ss -tlnp

# Failed services
systemctl --failed

# Users with login shells
grep -v nologin /etc/passwd

# SUID files
sudo find / -type f -perm -4000 2>/dev/null

# World-writable files
sudo find / -type f -perm -0002 2>/dev/null

# Firewall status
sudo ufw status verbose

# SSH configuration test
sudo sshd -t

# AppArmor status
sudo aa-status

# Fail2ban status
sudo fail2ban-client status

# Update status
apt list --upgradable
```

## Regular Maintenance

### Daily

- [ ] Review failed login attempts
- [ ] Check fail2ban bans
- [ ] Verify backup completion
- [ ] Monitor disk space

### Weekly

- [ ] Apply security updates
- [ ] Review system logs
- [ ] Check AIDE reports
- [ ] Run rkhunter

### Monthly

- [ ] Full system update
- [ ] Review user accounts
- [ ] Review sudo access
- [ ] Test backup restoration
- [ ] Review firewall rules
- [ ] Update AIDE baseline after changes

### Quarterly

- [ ] Security audit (Lynis)
- [ ] Review and rotate credentials
- [ ] Test disaster recovery
- [ ] Review and update documentation

## CIS Benchmark Reference

For comprehensive CIS compliance, run:

```bash
# OpenSCAP assessment
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --report /var/log/cis-report.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

## Notes

Use this space to document exceptions and custom configurations:

```
Date: _______________
Reviewed by: _______________
Exceptions:


Custom configurations:


Follow-up items:


```
