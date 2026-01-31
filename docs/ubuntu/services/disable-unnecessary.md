# Disable Unnecessary Services

Every running service increases attack surface. This page guides you through identifying and safely disabling unneeded services.

## Identifying Services

### List All Running Services

```bash
# Running services
systemctl list-units --type=service --state=running

# All services (including stopped)
systemctl list-units --type=service --all

# Enabled at boot
systemctl list-unit-files --type=service --state=enabled
```

### Analyze Boot Services

```bash
# Services started at boot with timing
systemd-analyze blame

# Critical boot chain
systemd-analyze critical-chain

# Services that delay boot
systemd-analyze blame | head -20
```

### Check Listening Ports

```bash
# TCP listeners
sudo ss -tlnp

# UDP listeners
sudo ss -ulnp

# All listeners with service names
sudo ss -tulnp
```

## Common Unnecessary Services

### Desktop/GUI Services

These are unnecessary on servers:

| Service | Description | Disable? |
|---------|-------------|----------|
| cups | Printing | Yes |
| cups-browsed | Printer discovery | Yes |
| avahi-daemon | mDNS/Bonjour | Usually |
| bluetooth | Bluetooth stack | Yes |
| colord | Color management | Yes |
| accounts-daemon | User account service | Maybe |

```bash
# Disable desktop services
sudo systemctl disable --now cups cups-browsed avahi-daemon bluetooth
```

### Hardware Services

Disable if hardware not present:

| Service | Description | Disable If |
|---------|-------------|------------|
| bluetooth | Bluetooth | No BT hardware |
| ModemManager | Modem support | No modem |
| wpa_supplicant | WiFi | No wireless |
| thermald | Thermal management | VM guest |
| irqbalance | IRQ balancing | Single CPU |
| fwupd | Firmware updates | VM guest |
| udisks2 | Disk management | Server/no GUI |

```bash
# Disable hardware services (check first!)
sudo systemctl disable --now ModemManager bluetooth wpa_supplicant
```

### Snap Services

If not using Snap packages:

```bash
# Check snap usage
snap list

# If empty or unused
sudo systemctl disable --now snapd snapd.socket
sudo apt remove snapd
```

### Cloud-Init (Non-Cloud)

On physical servers or non-cloud VMs:

```bash
# Disable cloud-init
sudo systemctl disable --now cloud-init cloud-init-local cloud-config cloud-final
sudo touch /etc/cloud/cloud-init.disabled
```

### Multipathd

For servers without SAN storage:

```bash
# Check if multipath is in use
sudo multipath -ll

# If empty
sudo systemctl disable --now multipathd
```

## Service Analysis

### Check Dependencies

Before disabling, check what depends on a service:

```bash
# What depends on this service
systemctl list-dependencies --reverse avahi-daemon

# What this service requires
systemctl list-dependencies avahi-daemon
```

### Check Recent Activity

```bash
# Has this service been used recently?
journalctl -u cups --since "1 month ago" | head

# Never used = safe to disable
```

### Test Disabling

```bash
# Stop first (reversible)
sudo systemctl stop service-name

# Monitor for issues
# If no problems after a few hours/days:
sudo systemctl disable service-name
```

## Safe Disable Process

### Step-by-Step

1. **Identify** - List the service and its purpose
2. **Research** - Check dependencies and usage
3. **Stop** - Stop the service temporarily
4. **Test** - Verify nothing breaks
5. **Disable** - Prevent start at boot
6. **Document** - Record what was disabled and why

### Disable Commands

```bash
# Stop and disable
sudo systemctl disable --now service-name

# Mask (prevent any start, even manual)
sudo systemctl mask service-name

# Unmask if needed later
sudo systemctl unmask service-name
```

### Masking vs Disabling

| Action | Effect |
|--------|--------|
| disable | Won't start at boot, can start manually |
| mask | Cannot be started by any means |
| stop | Stops now but may restart at boot |

## Server-Specific Guidance

### Minimal Server

Essential services only:

```bash
# Keep these
# - systemd-journald
# - systemd-networkd (or NetworkManager)
# - systemd-resolved
# - sshd
# - dbus
# - cron
# - rsyslog

# Typically disable
sudo systemctl disable --now \
    cups cups-browsed \
    avahi-daemon \
    bluetooth \
    ModemManager \
    wpa_supplicant \
    snapd snapd.socket
```

### Web Server

```bash
# Keep
# - nginx or apache2
# - php-fpm (if PHP)
# - sshd

# Disable
sudo systemctl disable --now \
    cups \
    avahi-daemon \
    bluetooth \
    postfix  # Unless sending mail
```

### Database Server

```bash
# Keep
# - postgresql or mysql
# - sshd

# Disable
sudo systemctl disable --now \
    cups \
    avahi-daemon \
    bluetooth \
    nginx  # Unless also web server
```

### Docker Host

```bash
# Keep
# - docker
# - containerd
# - sshd

# Disable
sudo systemctl disable --now \
    cups \
    avahi-daemon \
    bluetooth \
    snapd  # Docker from apt, not snap
```

## Verification

### After Disabling

```bash
# Verify service is stopped and disabled
systemctl status service-name
# Should show: disabled; dead

# Verify not listening
sudo ss -tlnp | grep service-name
# Should be empty

# Check boot impact
systemd-analyze blame | grep service-name
# Should not appear
```

### Periodic Review

```bash
#!/bin/bash
# Review enabled services quarterly

echo "=== Enabled Services ==="
systemctl list-unit-files --type=service --state=enabled --no-pager

echo -e "\n=== Listening Ports ==="
sudo ss -tlnp

echo -e "\n=== Review each service ==="
echo "Is it needed? Is it hardened?"
```

## Troubleshooting

### Service Won't Stop

```bash
# Find dependent services
systemctl list-dependencies --reverse service-name

# Force stop
sudo systemctl kill service-name

# Check why it's running
systemctl status service-name
```

### Something Broke After Disabling

```bash
# Re-enable quickly
sudo systemctl unmask service-name
sudo systemctl enable --now service-name

# Check logs
journalctl -u service-name --since "10 minutes ago"
```

### Identify What Started a Service

```bash
# Why did this service start?
systemctl status service-name
# Look for "Triggered by:" or dependencies
```

## Quick Reference

### Commands

```bash
# List services
systemctl list-units --type=service --state=running
systemctl list-unit-files --type=service --state=enabled

# Analyze
systemd-analyze blame
systemctl list-dependencies service-name

# Disable
sudo systemctl stop service-name
sudo systemctl disable service-name
sudo systemctl disable --now service-name
sudo systemctl mask service-name

# Re-enable
sudo systemctl unmask service-name
sudo systemctl enable --now service-name
```

### Common Services to Evaluate

| Service | Keep If |
|---------|---------|
| sshd | Remote access needed |
| cron | Scheduled tasks used |
| rsyslog | Log forwarding needed |
| cups | Printing needed |
| avahi-daemon | mDNS discovery needed |
| bluetooth | BT hardware present |
| ModemManager | Modem present |
| snapd | Using snap packages |
| multipathd | SAN storage in use |
| postfix | Sending email |

## Next Steps

Continue to [Service Isolation](service-isolation.md) to apply security sandboxing to remaining services.
