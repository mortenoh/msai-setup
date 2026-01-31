# Kernel Livepatch

Ubuntu Livepatch applies critical kernel security fixes without requiring a reboot, maximizing uptime while maintaining security.

## Understanding Livepatch

### How Livepatch Works

```
┌─────────────────────────────────────────────────────────────┐
│                    Running Kernel                            │
│              (with vulnerable code)                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   Livepatch Module                           │
│          (Contains fixed function code)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Running Kernel                            │
│   (Vulnerable function redirected to fixed function)         │
└─────────────────────────────────────────────────────────────┘
```

### What Livepatch Covers

| Covered | Not Covered |
|---------|-------------|
| Critical kernel vulnerabilities | Userspace packages |
| High-severity security fixes | Non-critical bugs |
| CVE patches | Feature updates |

### Benefits

- **No downtime** for kernel security patches
- **Immediate protection** against vulnerabilities
- **Compliance** with uptime requirements
- **Simplified maintenance** windows

## Requirements

### System Requirements

- Ubuntu 18.04 LTS or later (including 24.04 LTS)
- 64-bit (amd64 or arm64) architecture
- Generic or low-latency kernel
- Active internet connection
- Ubuntu Pro subscription (free for up to 5 machines)

### Supported Kernels

```bash
# Check if your kernel is supported
cat /proc/version_signature

# Should show Ubuntu-signed kernel
# Example: Ubuntu 6.5.0-21.21-generic 6.5.3
```

## Getting Ubuntu Pro

### Free Personal Subscription

Ubuntu Pro is free for personal use (up to 5 machines):

1. Go to [ubuntu.com/pro](https://ubuntu.com/pro)
2. Create an Ubuntu One account
3. Get your free personal token
4. Token covers 5 machines

### Commercial Subscription

For organizations:

- Ubuntu Pro Desktop/Server licenses
- Available through Canonical or partners
- Includes enterprise support

## Installation

### Attach Ubuntu Pro

```bash
# Attach with your token
sudo pro attach YOUR_TOKEN_HERE
```

After attaching, you'll see enabled services:

```
SERVICE          ENTITLED  STATUS    DESCRIPTION
esm-apps         yes       enabled   Extended Security Maintenance for Applications
esm-infra        yes       enabled   Extended Security Maintenance for Infrastructure
livepatch        yes       enabled   Canonical Livepatch service
```

### Verify Status

```bash
# Check Ubuntu Pro status
pro status

# Check Livepatch specifically
canonical-livepatch status
```

### Manual Livepatch Enable

If Livepatch isn't auto-enabled:

```bash
# Enable Livepatch
sudo pro enable livepatch

# Or with standalone tool
sudo snap install canonical-livepatch
sudo canonical-livepatch enable YOUR_TOKEN
```

## Using Livepatch

### Check Status

```bash
# Detailed status
canonical-livepatch status --verbose

# Output example:
# client-version: "10.1.0"
# architecture: x86_64
# cpu-model: Intel(R) Core(TM) i7-9750H
# last-check: 2024-01-15T10:30:00Z
# boot-time: 2024-01-01T00:00:00Z
# uptime: 14d 10h 30m 0s
# status:
#   - kernel: 6.5.0-21.21-generic
#     running: true
#     livepatch:
#       state: applied
#       version: "94.1"
#       fixes:
#         - CVE-2024-1234
#         - CVE-2024-5678
```

### Key Status Fields

| Field | Meaning |
|-------|---------|
| state | nothing-to-apply, applying, applied, unapplied |
| version | Livepatch version number |
| fixes | List of CVEs patched |

### Check Applied Patches

```bash
# List applied patches
canonical-livepatch status --verbose | grep -A 20 "fixes:"

# Alternative: Check kernel module
lsmod | grep livepatch
```

## Configuration

### Livepatch Configuration

View current configuration:

```bash
canonical-livepatch config
```

Available settings:

```bash
# HTTP proxy
sudo canonical-livepatch config http-proxy=http://proxy:3128

# HTTPS proxy
sudo canonical-livepatch config https-proxy=http://proxy:3128

# No proxy for specific hosts
sudo canonical-livepatch config no-proxy=localhost,127.0.0.1

# Remote server (enterprise)
sudo canonical-livepatch config remote-server=https://livepatch.example.com
```

### Disable/Enable

```bash
# Temporarily disable
sudo canonical-livepatch disable

# Re-enable
sudo canonical-livepatch enable

# Check if enabled
canonical-livepatch status | grep -i state
```

## Monitoring

### View Logs

```bash
# Systemd journal
sudo journalctl -u snap.canonical-livepatch.canonical-livepatchd

# Follow logs
sudo journalctl -u snap.canonical-livepatch.canonical-livepatchd -f
```

### Automation-Friendly Status

```bash
# JSON output for scripts
canonical-livepatch status --format json

# Check specific field
canonical-livepatch status --format json | jq '.status[0].livepatch.state'
```

### Monitoring Script

```bash
#!/bin/bash
# Check Livepatch status for monitoring

STATUS=$(canonical-livepatch status --format json 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "CRITICAL: Livepatch not running"
    exit 2
fi

STATE=$(echo "$STATUS" | jq -r '.status[0].livepatch.state')

case "$STATE" in
    "applied")
        echo "OK: Livepatch applied"
        exit 0
        ;;
    "nothing-to-apply")
        echo "OK: No patches needed"
        exit 0
        ;;
    "applying")
        echo "WARNING: Patches being applied"
        exit 1
        ;;
    *)
        echo "CRITICAL: Unexpected state: $STATE"
        exit 2
        ;;
esac
```

## Best Practices

### Livepatch and Regular Updates

Livepatch is not a replacement for regular updates:

| Task | Why |
|------|-----|
| Run unattended-upgrades | Userspace security updates |
| Run apt upgrade | Non-critical bug fixes |
| Plan kernel reboots | Cumulative kernel updates |
| Keep Livepatch enabled | Critical kernel patches |

### Recommended Workflow

1. **Enable Livepatch** for immediate kernel protection
2. **Enable unattended-upgrades** for userspace security
3. **Schedule monthly maintenance** for full kernel updates + reboot
4. **Monitor status** via scripts or monitoring tools

### Blacklist Kernels in unattended-upgrades

When using Livepatch, blacklist kernel packages:

```
// /etc/apt/apt.conf.d/50unattended-upgrades
Unattended-Upgrade::Package-Blacklist {
    "linux-image-";
    "linux-headers-";
    "linux-modules-";
};
```

This ensures kernel updates are manual and planned.

## Troubleshooting

### Common Issues

**"Machine is not entitled to Livepatch":**

```bash
# Re-attach Pro subscription
sudo pro detach
sudo pro attach YOUR_TOKEN
```

**"Kernel not supported":**

```bash
# Check kernel
uname -r

# Install generic kernel if using custom
sudo apt install linux-generic
```

**Livepatch not applying:**

```bash
# Check connectivity
curl -I https://livepatch.canonical.com

# Check for proxy issues
canonical-livepatch config

# Restart service
sudo snap restart canonical-livepatch
```

**"Supplementary key" errors:**

```bash
# Refresh Livepatch
sudo canonical-livepatch refresh
```

### Debug Mode

```bash
# Enable debug logging
sudo snap set canonical-livepatch log-level=debug

# View detailed logs
sudo journalctl -u snap.canonical-livepatch.canonical-livepatchd -n 100

# Reset log level
sudo snap set canonical-livepatch log-level=info
```

## Enterprise Deployment

### On-Premises Livepatch Server

For air-gapped or enterprise environments:

1. Deploy Livepatch on-premises server
2. Configure clients to use internal server:

```bash
sudo canonical-livepatch config remote-server=https://livepatch.internal.example.com
```

### Mass Deployment

Using Ansible:

```yaml
- name: Enable Ubuntu Pro and Livepatch
  hosts: all
  become: yes
  tasks:
    - name: Attach Ubuntu Pro
      command: pro attach {{ ubuntu_pro_token }}
      args:
        creates: /var/lib/ubuntu-advantage/private/machine-token.json

    - name: Enable Livepatch
      command: pro enable livepatch
      when: ansible_distribution == "Ubuntu"
```

## When to Reboot

Despite Livepatch, some scenarios still require reboot:

| Scenario | Action |
|----------|--------|
| Kernel feature updates | Reboot required |
| Livepatch accumulation | Periodic reboot recommended |
| Major kernel version change | Reboot required |
| Cumulative patch threshold | Reboot recommended |

**Recommendation:** Schedule quarterly maintenance reboots even with Livepatch enabled.

## Quick Reference

### Commands

```bash
# Status
canonical-livepatch status
canonical-livepatch status --verbose
canonical-livepatch status --format json

# Management
sudo pro enable livepatch
sudo canonical-livepatch disable
sudo canonical-livepatch enable
sudo canonical-livepatch refresh

# Configuration
canonical-livepatch config
sudo canonical-livepatch config http-proxy=http://proxy:3128

# Ubuntu Pro
pro status
sudo pro attach TOKEN
sudo pro detach
```

### Key Files

| File | Purpose |
|------|---------|
| /var/lib/ubuntu-advantage/ | Ubuntu Pro data |
| /var/snap/canonical-livepatch/ | Livepatch data |

### Useful Resources

| Resource | URL |
|----------|-----|
| Ubuntu Pro Portal | https://ubuntu.com/pro |
| Livepatch Documentation | https://ubuntu.com/security/livepatch |
| CVE Tracker | https://ubuntu.com/security/cves |

## Next Steps

With update management configured, proceed to [Logging Configuration](../logging/index.md) to set up comprehensive system logging.
