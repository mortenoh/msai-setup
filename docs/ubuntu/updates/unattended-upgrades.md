# Unattended Upgrades

Unattended-upgrades automatically installs security updates, ensuring your system stays patched without manual intervention.

## Installation and Setup

### Install Package

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Enable automatic updates
sudo dpkg-reconfigure -plow unattended-upgrades
```

This creates `/etc/apt/apt.conf.d/20auto-upgrades`:

```
APT::Periodic::Update-Package-Lists "1";
APT::Periodic::Unattended-Upgrade "1";
```

### Verify Installation

```bash
# Check status
systemctl status unattended-upgrades

# Test (dry run)
sudo unattended-upgrade --dry-run --debug
```

## Configuration

### Main Configuration File

Edit `/etc/apt/apt.conf.d/50unattended-upgrades`:

```bash
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

### Allowed Origins

Control which repositories get automatic updates:

```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    // Extended Security Maintenance (ESM)
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
    // "${distro_id}:${distro_codename}-updates";     // Enable for all updates
    // "${distro_id}:${distro_codename}-proposed";    // Testing
    // "${distro_id}:${distro_codename}-backports";   // Backports
};
```

For Ubuntu 24.04 (noble), this expands to:

- Ubuntu:noble
- Ubuntu:noble-security
- UbuntuESMApps:noble-apps-security
- UbuntuESM:noble-infra-security

### Blacklist Packages

Prevent specific packages from being auto-upgraded:

```
Unattended-Upgrade::Package-Blacklist {
    // Regex patterns supported
    "linux-";          // All kernel packages
    "libc6";           // C library (risky)
    "nginx";           // Custom web server config
    "docker-ce";       // Container runtime
    "mysql-server-.*"; // Database
};
```

### Email Notifications

```
// Send email notifications
Unattended-Upgrade::Mail "admin@example.com";

// Only send on errors (recommended)
Unattended-Upgrade::MailReport "only-on-error";
// Options: "always", "only-on-error", "on-change"

// Or use MailOnlyOnError (deprecated but still works)
// Unattended-Upgrade::MailOnlyOnError "true";
```

### Automatic Reboot

```
// Automatically reboot if required
Unattended-Upgrade::Automatic-Reboot "true";

// Reboot time (server time)
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Reboot with users logged in
Unattended-Upgrade::Automatic-Reboot-WithUsers "false";
```

!!! warning "Production Considerations"
    Automatic reboots can cause service disruption. Consider:

    - Using Livepatch instead for kernel updates
    - Setting reboot time during maintenance windows
    - Coordinating with load balancers for HA setups

### Remove Unused Dependencies

```
// Remove unused automatically installed packages
Unattended-Upgrade::Remove-Unused-Dependencies "true";

// Remove unused kernel packages
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";

// Remove new unused dependencies after upgrade
Unattended-Upgrade::Remove-New-Unused-Dependencies "true";
```

### Download Settings

```
// Download but don't install
// Unattended-Upgrade::Download-Only "true";

// Minimum free disk space required (MB)
Unattended-Upgrade::MinimalSteps "true";

// Keep packages downloaded during upgrade
Unattended-Upgrade::Keep-Debs-After-Install "false";
```

## Complete Configuration Example

```
// /etc/apt/apt.conf.d/50unattended-upgrades

// Automatically upgrade packages from these origins
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};

// Do not upgrade these packages
Unattended-Upgrade::Package-Blacklist {
    "linux-image-";
    "linux-headers-";
    "nginx";
    "docker-ce";
};

// Email notifications
Unattended-Upgrade::Mail "admin@example.com";
Unattended-Upgrade::MailReport "only-on-error";

// Automatic reboot
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Automatic-Reboot-Time "02:00";

// Clean up
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";

// Logging
Unattended-Upgrade::SyslogEnable "true";
Unattended-Upgrade::SyslogFacility "daemon";

// Bandwidth limiting (KB/s, 0 = unlimited)
Acquire::http::Dl-Limit "0";
```

## Scheduling

### APT Periodic Settings

Edit `/etc/apt/apt.conf.d/20auto-upgrades`:

```
// Update package lists every N days
APT::Periodic::Update-Package-Lists "1";

// Download upgradable packages every N days
APT::Periodic::Download-Upgradeable-Packages "1";

// Run unattended-upgrade every N days
APT::Periodic::Unattended-Upgrade "1";

// Clean package cache every N days
APT::Periodic::AutocleanInterval "7";
```

### systemd Timers

Unattended-upgrades uses systemd timers:

```bash
# View timer status
systemctl status apt-daily.timer
systemctl status apt-daily-upgrade.timer

# List all apt timers
systemctl list-timers | grep apt
```

Default schedule:

- `apt-daily.timer`: 6:00 AM ± 12h (updates package lists)
- `apt-daily-upgrade.timer`: 6:00 AM ± 12h (applies upgrades)

### Custom Schedule

Override timer schedule:

```bash
sudo mkdir -p /etc/systemd/system/apt-daily-upgrade.timer.d/
sudo nano /etc/systemd/system/apt-daily-upgrade.timer.d/override.conf
```

```ini
[Timer]
OnCalendar=
OnCalendar=*-*-* 02:00
RandomizedDelaySec=0
```

Apply:

```bash
sudo systemctl daemon-reload
```

## Testing

### Dry Run

```bash
# See what would be upgraded
sudo unattended-upgrade --dry-run

# Verbose output
sudo unattended-upgrade --dry-run --debug
```

### Force Run

```bash
# Run immediately
sudo unattended-upgrade

# Verbose
sudo unattended-upgrade -v

# Debug mode
sudo unattended-upgrade -d
```

## Monitoring

### Log Files

| File | Contents |
|------|----------|
| /var/log/unattended-upgrades/unattended-upgrades.log | Main log |
| /var/log/unattended-upgrades/unattended-upgrades-dpkg.log | dpkg output |
| /var/log/unattended-upgrades/unattended-upgrades-shutdown.log | Shutdown log |
| /var/log/apt/history.log | APT history |

### View Logs

```bash
# Recent activity
sudo tail -f /var/log/unattended-upgrades/unattended-upgrades.log

# Last upgrade
sudo grep "Packages that will be upgraded" /var/log/unattended-upgrades/unattended-upgrades.log | tail -1

# Check for errors
sudo grep -i error /var/log/unattended-upgrades/*.log
```

### Check Reboot Status

```bash
# Check if reboot required
if [ -f /var/run/reboot-required ]; then
    echo "Reboot required"
    cat /var/run/reboot-required.pkgs
else
    echo "No reboot required"
fi
```

## Email Configuration

### Using sendmail/postfix

```
Unattended-Upgrade::Mail "admin@example.com";
Unattended-Upgrade::MailReport "only-on-error";
```

### Using msmtp (External SMTP)

Install msmtp:

```bash
sudo apt install msmtp msmtp-mta
```

Configure `/etc/msmtprc`:

```ini
account default
host smtp.gmail.com
port 587
from server@example.com
auth on
user username@gmail.com
password app-password
tls on
tls_starttls on
logfile /var/log/msmtp.log
```

Set permissions:

```bash
sudo chmod 600 /etc/msmtprc
```

Test:

```bash
echo "Test" | mail -s "Test from server" admin@example.com
```

## Troubleshooting

### Updates Not Running

```bash
# Check timer status
systemctl status apt-daily-upgrade.timer

# Check if package lists are updating
ls -la /var/lib/apt/lists/

# Manually trigger
sudo systemctl start apt-daily-upgrade.service

# View journal
sudo journalctl -u apt-daily-upgrade
```

### Package Conflicts

```bash
# Check for held packages
apt-mark showhold

# Check for broken packages
sudo apt --fix-broken install

# Simulate upgrade
sudo apt upgrade --dry-run
```

### Lock Issues

```bash
# Check for running apt processes
ps aux | grep apt

# Wait for lock (or remove if stale)
# sudo rm /var/lib/dpkg/lock-frontend
# sudo rm /var/lib/apt/lists/lock
```

### Debug Mode

```bash
# Full debug output
sudo unattended-upgrade -d 2>&1 | tee /tmp/unattended-debug.log

# Check output
less /tmp/unattended-debug.log
```

## Security Considerations

### What Gets Updated

By default, only security updates from trusted Ubuntu repositories are applied. This is the safest configuration.

### Risks of Auto-Updates

| Risk | Mitigation |
|------|------------|
| Breaking changes | Use Package-Blacklist for critical apps |
| Unexpected reboots | Disable Automatic-Reboot or use Livepatch |
| Storage exhaustion | Enable Remove-Unused-Dependencies |
| Update failures | Monitor logs and email notifications |

### Recommended Settings

For production servers:

```
// Conservative settings for production
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};

Unattended-Upgrade::Package-Blacklist {
    "linux-";     // Manual kernel updates with Livepatch
    "nginx";      // Custom config
    "mysql-";     // Database
    "postgresql"; // Database
};

Unattended-Upgrade::Mail "admin@example.com";
Unattended-Upgrade::MailReport "on-change";
Unattended-Upgrade::Automatic-Reboot "false";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
```

## Quick Reference

### Commands

```bash
# Install and enable
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

# Test
sudo unattended-upgrade --dry-run
sudo unattended-upgrade --dry-run --debug

# Run manually
sudo unattended-upgrade -v

# Check status
systemctl status unattended-upgrades
systemctl status apt-daily-upgrade.timer

# View logs
sudo tail -f /var/log/unattended-upgrades/unattended-upgrades.log
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/apt/apt.conf.d/50unattended-upgrades | Main config |
| /etc/apt/apt.conf.d/20auto-upgrades | Schedule config |
| /var/log/unattended-upgrades/*.log | Logs |
| /var/run/reboot-required | Reboot flag |

## Next Steps

Continue to [Livepatch](livepatch.md) to learn about kernel live patching for reboot-free kernel updates.
