# Update Management Overview

Keeping Ubuntu Server updated is critical for security. This section covers APT configuration, automatic security updates, and kernel live patching.

## Update Philosophy

### Balance Security and Stability

| Priority | Approach |
|----------|----------|
| Security patches | Apply immediately or automatically |
| Bug fixes | Test in staging, apply promptly |
| Feature updates | Evaluate, test, schedule maintenance |
| Distribution upgrades | Plan carefully, test thoroughly |

### Ubuntu Release Support

| Release | Support Period | Security Updates |
|---------|----------------|------------------|
| 24.04 LTS | 5 years standard | Until April 2029 |
| 24.04 LTS + ESM | 12 years total | Until April 2036 |

## Section Contents

| Page | Description |
|------|-------------|
| [APT Management](apt-management.md) | Package management, repositories, pinning |
| [Unattended Upgrades](unattended-upgrades.md) | Automatic security updates |
| [Livepatch](livepatch.md) | Kernel updates without reboot |

## Quick Start

### Check for Updates

```bash
# Update package lists
sudo apt update

# See what needs updating
apt list --upgradable

# Full system upgrade
sudo apt upgrade -y

# Upgrade with new dependencies
sudo apt full-upgrade -y
```

### Enable Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades

# Enable
sudo dpkg-reconfigure -plow unattended-upgrades
```

### Check Reboot Requirements

```bash
# Check if reboot needed
cat /var/run/reboot-required 2>/dev/null || echo "No reboot required"

# See which packages require reboot
cat /var/run/reboot-required.pkgs 2>/dev/null
```

## Update Types

### Security Updates

Security updates fix vulnerabilities:

```bash
# View available security updates
apt list --upgradable 2>/dev/null | grep -i security

# Install security updates only
sudo unattended-upgrade --dry-run
sudo unattended-upgrade
```

### Regular Updates

Bug fixes and minor improvements:

```bash
# All updates
sudo apt update && sudo apt upgrade
```

### Distribution Upgrade

Move to new Ubuntu release:

```bash
# Within same LTS series (e.g., point releases)
sudo apt update && sudo apt full-upgrade

# To new LTS release
sudo do-release-upgrade
```

## Update Sources

### Default Repositories

| Repository | Contents |
|------------|----------|
| main | Canonical-supported free software |
| restricted | Proprietary drivers |
| universe | Community-maintained |
| multiverse | Non-free software |

### Security Repository

Security updates come from:

```
deb http://security.ubuntu.com/ubuntu noble-security main restricted
```

This is the primary source for unattended-upgrades.

## Monitoring Updates

### Check System Status

```bash
# Last update
stat /var/cache/apt/pkgcache.bin

# Update history
cat /var/log/apt/history.log | tail -50

# Security update status
sudo unattended-upgrade --dry-run -v
```

### Notification Setup

Configure email notifications in unattended-upgrades (see [Unattended Upgrades](unattended-upgrades.md)).

## Best Practices

### Regular Maintenance

| Task | Frequency | Command |
|------|-----------|---------|
| Check updates | Daily (automated) | `apt update` |
| Apply security updates | Daily (automated) | unattended-upgrades |
| Full system upgrade | Weekly | `apt upgrade` |
| Clean old packages | Monthly | `apt autoremove` |
| Review held packages | Monthly | `apt-mark showhold` |

### Change Management

For production systems:

1. **Monitor** - Know what updates are available
2. **Test** - Apply to staging first
3. **Schedule** - Plan maintenance windows
4. **Document** - Record what was updated
5. **Verify** - Confirm services work after update

### Handling Kernel Updates

Kernel updates typically require reboot:

```bash
# Check running vs. installed kernel
uname -r                              # Running
dpkg -l | grep linux-image | tail -1  # Installed

# Schedule reboot if different
# Or use Livepatch (see livepatch.md)
```

## Quick Reference

### Essential Commands

```bash
# Update package list
sudo apt update

# Upgrade packages
sudo apt upgrade

# Full upgrade (handles new dependencies)
sudo apt full-upgrade

# Security updates only
sudo unattended-upgrade

# Clean up
sudo apt autoremove
sudo apt autoclean

# Check reboot needed
cat /var/run/reboot-required
```

### Key Files

| File | Purpose |
|------|---------|
| /etc/apt/sources.list | Repository configuration |
| /etc/apt/sources.list.d/*.list | Additional repositories |
| /etc/apt/apt.conf.d/ | APT configuration |
| /var/log/apt/history.log | Update history |
| /var/log/unattended-upgrades/ | Auto-update logs |

## Next Steps

Start with [APT Management](apt-management.md) to understand Ubuntu's package management system.
