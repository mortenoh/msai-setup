# CIS Benchmarks

The Center for Internet Security (CIS) Benchmarks provide prescriptive guidance for securing systems. This page covers implementing CIS recommendations for Ubuntu Server 24.04 LTS.

## Understanding CIS Benchmarks

### What CIS Benchmarks Are

CIS Benchmarks are:

- **Consensus-based** - Developed by security experts worldwide
- **Prescriptive** - Specific configuration recommendations
- **Scored** - Each control has a severity and scoring weight
- **Auditable** - Can be verified with automated tools

### Benchmark Levels

| Level | Description | Target |
|-------|-------------|--------|
| **Level 1** | Basic security, minimal impact | All systems |
| **Level 2** | Defense in depth, may affect functionality | High-security systems |

### Control Categories

| Section | Coverage |
|---------|----------|
| 1 | Initial Setup |
| 2 | Services |
| 3 | Network Configuration |
| 4 | Logging and Auditing |
| 5 | Access, Authentication, Authorization |
| 6 | System Maintenance |

## Obtaining the Benchmark

### Official Download

1. Visit [CIS Benchmarks](https://www.cisecurity.org/benchmark/ubuntu_linux)
2. Register for free account
3. Download Ubuntu 24.04 LTS benchmark PDF

### Ubuntu Security Guide

Ubuntu provides CIS-hardened profiles via Ubuntu Security Guide:

```bash
# Check if available
apt search ubuntu-security-guide
```

## Automated Assessment Tools

### OpenSCAP

```bash
# Install OpenSCAP
sudo apt install openscap-scanner scap-security-guide

# List available profiles
oscap info /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# Run CIS assessment
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --report cis-report.html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
```

### Lynis

```bash
# Install Lynis
sudo apt install lynis

# Run security audit
sudo lynis audit system

# CIS-focused scan
sudo lynis audit system --profile cis
```

### CIS-CAT Pro

Commercial tool from CIS:

- Comprehensive assessments
- Detailed remediation guidance
- Historical tracking
- Available from [CIS website](https://www.cisecurity.org/cybersecurity-tools/cis-cat-pro)

## Key CIS Controls by Section

### Section 1: Initial Setup

#### 1.1 Filesystem Configuration

**1.1.1 Disable unused filesystems**

```bash
# Create /etc/modprobe.d/CIS.conf
sudo tee /etc/modprobe.d/CIS.conf << 'EOF'
# CIS 1.1.1 - Disable unused filesystems
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install squashfs /bin/true
install udf /bin/true
EOF
```

**1.1.2-1.1.22 Mount options**

```bash
# /etc/fstab example with CIS options
/dev/mapper/vg-tmp   /tmp       ext4  defaults,nodev,nosuid,noexec  0 2
/dev/mapper/vg-var   /var       ext4  defaults,nodev,nosuid         0 2
/dev/mapper/vg-home  /home      ext4  defaults,nodev,nosuid         0 2
tmpfs                /dev/shm   tmpfs defaults,nodev,nosuid,noexec  0 0
```

#### 1.4 Secure Boot Settings

**1.4.1 Bootloader password**

```bash
# Generate password hash
grub-mkpasswd-pbkdf2

# Add to /etc/grub.d/40_custom
cat << 'EOF' | sudo tee -a /etc/grub.d/40_custom
set superusers="grubadmin"
password_pbkdf2 grubadmin grub.pbkdf2.sha512.HASH_HERE
EOF

sudo update-grub
```

**1.4.2 Bootloader permissions**

```bash
sudo chown root:root /boot/grub/grub.cfg
sudo chmod 400 /boot/grub/grub.cfg
```

### Section 2: Services

**2.1 Remove/disable unnecessary services**

```bash
# CIS recommends removing if not needed:
sudo systemctl disable --now xinetd
sudo systemctl disable --now avahi-daemon
sudo systemctl disable --now cups
sudo systemctl disable --now dhcpd
sudo systemctl disable --now slapd
sudo systemctl disable --now nfs-server
sudo systemctl disable --now rpcbind
sudo systemctl disable --now named
sudo systemctl disable --now vsftpd
sudo systemctl disable --now smbd
sudo systemctl disable --now squid
sudo systemctl disable --now snmpd

# Remove X Window (servers don't need GUI)
sudo apt purge xserver-xorg*
```

**2.2 Ensure only required services are running**

```bash
# List enabled services
systemctl list-unit-files --state=enabled --type=service

# Review and disable unnecessary
```

### Section 3: Network Configuration

**3.1 Network Parameters (Host Only)**

Already covered in [Kernel Hardening](kernel-hardening.md):

```bash
# /etc/sysctl.d/99-cis-network.conf
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
net.ipv6.conf.all.accept_redirects = 0
net.ipv6.conf.default.accept_redirects = 0
```

**3.4 Firewall Configuration**

```bash
# Ensure UFW is installed and enabled
sudo apt install ufw
sudo ufw enable
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
```

### Section 4: Logging and Auditing

**4.1 Configure auditd**

See [auditd](auditd.md) for full configuration.

Minimum CIS rules:

```bash
# /etc/audit/rules.d/cis.rules
-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change
-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change
-a always,exit -F arch=b64 -S clock_settime -k time-change
-a always,exit -F arch=b32 -S clock_settime -k time-change
-w /etc/localtime -p wa -k time-change
-w /etc/group -p wa -k identity
-w /etc/passwd -p wa -k identity
-w /etc/gshadow -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/security/opasswd -p wa -k identity
-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale
-a always,exit -F arch=b32 -S sethostname -S setdomainname -k system-locale
-w /etc/issue -p wa -k system-locale
-w /etc/issue.net -p wa -k system-locale
-w /etc/hosts -p wa -k system-locale
-w /etc/sysconfig/network -p wa -k system-locale
-w /var/log/faillog -p wa -k logins
-w /var/log/lastlog -p wa -k logins
-w /var/log/tallylog -p wa -k logins
-w /var/run/utmp -p wa -k session
-w /var/log/wtmp -p wa -k logins
-w /var/log/btmp -p wa -k logins
-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod
```

**4.2 Configure rsyslog/journald**

```bash
# Ensure rsyslog is installed
sudo apt install rsyslog

# Enable and start
sudo systemctl enable --now rsyslog

# Configure remote logging if required
# Edit /etc/rsyslog.conf or /etc/rsyslog.d/50-default.conf
```

### Section 5: Access, Authentication, Authorization

**5.1 Configure cron**

```bash
# Restrict cron access
sudo touch /etc/cron.allow
sudo chmod 600 /etc/cron.allow
sudo chown root:root /etc/cron.allow

# Same for at
sudo touch /etc/at.allow
sudo chmod 600 /etc/at.allow
sudo chown root:root /etc/at.allow

# Remove deny files (allow files take precedence)
sudo rm -f /etc/cron.deny /etc/at.deny

# Secure cron directories
sudo chmod 700 /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.monthly /etc/cron.weekly
sudo chown root:root /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.monthly /etc/cron.weekly
```

**5.2 SSH Configuration**

See [SSH Hardening](ssh-hardening.md). Key CIS requirements:

```bash
# /etc/ssh/sshd_config.d/cis.conf
Protocol 2
LogLevel VERBOSE
MaxAuthTries 4
IgnoreRhosts yes
HostbasedAuthentication no
PermitRootLogin no
PermitEmptyPasswords no
PermitUserEnvironment no
ClientAliveInterval 300
ClientAliveCountMax 0
LoginGraceTime 60
MaxStartups 10:30:60
MaxSessions 4
```

**5.3 Configure PAM**

See [PAM](../system/pam.md). Key requirements:

```bash
# Password requirements in /etc/security/pwquality.conf
minlen = 14
dcredit = -1
ucredit = -1
ocredit = -1
lcredit = -1

# Account lockout in /etc/security/faillock.conf
deny = 5
unlock_time = 900
```

**5.4 User Accounts and Environment**

```bash
# Set password expiration defaults
sudo sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   365/' /etc/login.defs
sudo sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   1/' /etc/login.defs
sudo sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   7/' /etc/login.defs

# Set inactive account lockout
sudo useradd -D -f 30

# Restrict root login to console
echo "tty1" | sudo tee /etc/securetty

# Set default umask
echo "umask 027" | sudo tee -a /etc/bash.bashrc
echo "umask 027" | sudo tee -a /etc/profile
```

### Section 6: System Maintenance

**6.1 File Permissions**

```bash
# Fix common permission issues
sudo chmod 644 /etc/passwd
sudo chmod 600 /etc/shadow
sudo chmod 644 /etc/group
sudo chmod 600 /etc/gshadow
sudo chmod 644 /etc/passwd-
sudo chmod 600 /etc/shadow-
sudo chmod 644 /etc/group-
sudo chmod 600 /etc/gshadow-

# Find world-writable files
sudo find / -xdev -type f -perm -0002 -exec ls -l {} \;

# Find unowned files
sudo find / -xdev \( -nouser -o -nogroup \) -exec ls -l {} \;

# Find SUID/SGID files
sudo find / -xdev \( -perm -4000 -o -perm -2000 \) -type f -exec ls -l {} \;
```

**6.2 User and Group Settings**

```bash
# Ensure no users have empty passwords
sudo awk -F: '($2 == "" ) { print $1 }' /etc/shadow

# Ensure root is only UID 0
sudo awk -F: '($3 == 0) { print $1 }' /etc/passwd

# Check root PATH
echo $PATH | grep -q "::" && echo "Empty directory in root PATH"
echo $PATH | grep -q ":$" && echo "Trailing colon in root PATH"
```

## CIS Hardening Script

Quick hardening script for common controls:

```bash
#!/bin/bash
# CIS Quick Hardening Script
# Run as root

set -e

echo "=== CIS Quick Hardening ==="

# Disable unused filesystems
cat > /etc/modprobe.d/CIS.conf << 'EOF'
install cramfs /bin/true
install freevxfs /bin/true
install jffs2 /bin/true
install hfs /bin/true
install hfsplus /bin/true
install squashfs /bin/true
install udf /bin/true
EOF

# Kernel hardening
cat > /etc/sysctl.d/99-cis.conf << 'EOF'
kernel.randomize_va_space = 2
net.ipv4.conf.all.send_redirects = 0
net.ipv4.conf.default.send_redirects = 0
net.ipv4.conf.all.accept_source_route = 0
net.ipv4.conf.default.accept_source_route = 0
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.secure_redirects = 0
net.ipv4.conf.default.secure_redirects = 0
net.ipv4.conf.all.log_martians = 1
net.ipv4.conf.default.log_martians = 1
net.ipv4.icmp_echo_ignore_broadcasts = 1
net.ipv4.icmp_ignore_bogus_error_responses = 1
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
net.ipv4.tcp_syncookies = 1
net.ipv6.conf.all.accept_ra = 0
net.ipv6.conf.default.accept_ra = 0
EOF
sysctl --system

# File permissions
chmod 644 /etc/passwd
chmod 600 /etc/shadow
chmod 644 /etc/group
chmod 600 /etc/gshadow

# Cron permissions
chmod 700 /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.monthly /etc/cron.weekly

# Login definitions
sed -i 's/^PASS_MAX_DAYS.*/PASS_MAX_DAYS   365/' /etc/login.defs
sed -i 's/^PASS_MIN_DAYS.*/PASS_MIN_DAYS   1/' /etc/login.defs
sed -i 's/^PASS_WARN_AGE.*/PASS_WARN_AGE   7/' /etc/login.defs

# Default umask
echo "umask 027" >> /etc/profile

echo "=== CIS Quick Hardening Complete ==="
echo "Review full CIS benchmark for complete hardening"
```

## Compliance Reporting

### Generate Reports

```bash
# OpenSCAP HTML report
sudo oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --report /var/log/cis-report-$(date +%Y%m%d).html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml

# Lynis report
sudo lynis audit system --auditor "Security Admin" \
    --report-file /var/log/lynis-report-$(date +%Y%m%d).txt
```

### Track Compliance Over Time

```bash
# Create compliance tracking directory
mkdir -p /var/log/compliance

# Schedule regular scans
cat > /etc/cron.weekly/compliance-scan << 'EOF'
#!/bin/bash
oscap xccdf eval \
    --profile xccdf_org.ssgproject.content_profile_cis_level1_server \
    --report /var/log/compliance/cis-$(date +%Y%m%d).html \
    /usr/share/xml/scap/ssg/content/ssg-ubuntu2204-ds.xml
EOF
chmod +x /etc/cron.weekly/compliance-scan
```

## Quick Reference

### Assessment Commands

```bash
# OpenSCAP
sudo oscap xccdf eval --profile PROFILE --report report.html DATASTREAM

# Lynis
sudo lynis audit system

# Manual checks
cat /etc/login.defs | grep PASS
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/login.defs | Login defaults |
| /etc/security/pwquality.conf | Password quality |
| /etc/sysctl.d/*.conf | Kernel parameters |
| /etc/modprobe.d/*.conf | Module blacklists |
| /etc/audit/rules.d/*.rules | Audit rules |

### Resources

| Resource | URL |
|----------|-----|
| CIS Benchmarks | https://www.cisecurity.org/benchmark/ubuntu_linux |
| OpenSCAP | https://www.open-scap.org/ |
| Ubuntu Security | https://ubuntu.com/security |

## Next Steps

With security hardening complete, proceed to:

- [Updates Management](../updates/index.md) for maintaining a secure system
- [Logging Configuration](../logging/index.md) for proper monitoring
- [Reference Checklist](../reference/checklist.md) for a complete verification list
