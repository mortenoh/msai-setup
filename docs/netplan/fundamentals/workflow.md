# Configuration Workflow

## The Safe Workflow

When managing network configuration, especially remotely, follow this workflow:

```
1. Edit YAML file
        ↓
2. Validate syntax
        ↓
3. Test with timeout (netplan try)
        ↓
4. Confirm or rollback
        ↓
5. Make permanent (netplan apply)
        ↓
6. Verify configuration
```

## Step 1: Edit Configuration

### Create or Modify File

```bash
# Edit existing
sudo nano /etc/netplan/00-installer-config.yaml

# Or create new
sudo nano /etc/netplan/50-custom.yaml
```

### Example Change

```yaml
# Before
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: true

# After
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1
      nameservers:
        addresses: [1.1.1.1]
```

## Step 2: Validate Syntax

### Basic Validation

```bash
sudo netplan generate
```

If no output, syntax is valid. Errors are displayed:

```
/etc/netplan/50-custom.yaml:5:3: Error in network definition:
unknown key 'adresses'
```

### Verbose Validation

```bash
sudo netplan --debug generate
```

Shows detailed processing information.

### View Generated Files

```bash
# For networkd
ls -la /run/systemd/network/

# View content
cat /run/systemd/network/10-netplan-eth0.network
```

## Step 3: Test with Timeout

### The Critical Step

!!! danger "Remote Administration Warning"
    Always use `netplan try` when making changes remotely. A misconfigured network can lock you out permanently.

```bash
sudo netplan try
```

Output:

```
Do you want to keep these settings?


Press ENTER before the timeout to accept the new configuration


Changes will revert in 120 seconds
```

### Custom Timeout

```bash
# 60 second timeout
sudo netplan try --timeout 60

# Longer for complex testing
sudo netplan try --timeout 300
```

### What Happens

1. Configuration is applied
2. Timer starts (default 120 seconds)
3. If you press ENTER, changes are kept
4. If timer expires (you lost connectivity), changes revert

## Step 4: Confirm or Rollback

### Confirm Changes

After testing connectivity:

```bash
# Press ENTER in the netplan try terminal
Configuration accepted.
```

### Automatic Rollback

If you don't confirm (can't connect):
- Original configuration is restored
- Network connectivity returns
- You can try again

### Manual Rollback

If needed:

```bash
# Restore from backup
sudo cp /etc/netplan/backup.yaml /etc/netplan/00-config.yaml
sudo netplan apply
```

## Step 5: Apply Permanently

### Full Apply

```bash
sudo netplan apply
```

This:
1. Regenerates backend configuration
2. Applies to running system
3. Persists until next change

### Verify Generation

```bash
# Check backend files were created
ls -la /run/systemd/network/
```

## Step 6: Verify Configuration

### Check IP Configuration

```bash
ip addr show eth0
```

Expected output:

```
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 ...
    inet 192.168.1.100/24 brd 192.168.1.255 scope global eth0
       valid_lft forever preferred_lft forever
```

### Check Routes

```bash
ip route show
```

Expected:

```
default via 192.168.1.1 dev eth0 proto static
192.168.1.0/24 dev eth0 proto kernel scope link src 192.168.1.100
```

### Check DNS

```bash
resolvectl status eth0
```

### Check Connectivity

```bash
# Gateway
ping -c 3 192.168.1.1

# External
ping -c 3 8.8.8.8

# DNS resolution
ping -c 3 google.com
```

## Backup and Recovery

### Before Making Changes

```bash
# Backup current config
sudo cp /etc/netplan/00-installer-config.yaml /etc/netplan/00-installer-config.yaml.backup
```

### Automated Backup Script

```bash
#!/bin/bash
# /usr/local/bin/netplan-edit.sh

CONFIG_FILE="${1:-/etc/netplan/00-installer-config.yaml}"
BACKUP_DIR="/etc/netplan/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup current config
cp "$CONFIG_FILE" "$BACKUP_DIR/$(basename $CONFIG_FILE).$TIMESTAMP"

# Edit
${EDITOR:-nano} "$CONFIG_FILE"

# Validate
echo "Validating..."
if sudo netplan generate; then
    echo "Syntax OK"
    echo "Running netplan try (120s timeout)..."
    sudo netplan try
else
    echo "Syntax error! Restoring backup..."
    cp "$BACKUP_DIR/$(basename $CONFIG_FILE).$TIMESTAMP" "$CONFIG_FILE"
fi
```

### Recovery from Console

If you're locked out, access via:
- Physical console
- IPMI/iLO/iDRAC
- Cloud console

Then restore:

```bash
# List backups
ls /etc/netplan/backups/

# Restore
sudo cp /etc/netplan/backups/00-installer-config.yaml.TIMESTAMP /etc/netplan/00-installer-config.yaml
sudo netplan apply
```

## Complex Change Workflow

### Multi-File Changes

```bash
# 1. Backup all configs
sudo cp -r /etc/netplan /etc/netplan.backup

# 2. Edit files
sudo nano /etc/netplan/00-base.yaml
sudo nano /etc/netplan/10-bridge.yaml

# 3. Validate all
sudo netplan generate

# 4. Test
sudo netplan try

# 5. If something goes wrong
sudo rm -rf /etc/netplan
sudo mv /etc/netplan.backup /etc/netplan
sudo netplan apply
```

### Adding a Bridge

Workflow for converting an interface to a bridge:

```bash
# 1. Current config
cat /etc/netplan/00-config.yaml
# network:
#   version: 2
#   ethernets:
#     eth0:
#       addresses: [192.168.1.100/24]

# 2. Create new config with bridge
cat << 'EOF' | sudo tee /etc/netplan/00-config.yaml.new
network:
  version: 2
  ethernets:
    eth0:
      dhcp4: false
  bridges:
    br0:
      interfaces: [eth0]
      addresses: [192.168.1.100/24]
      routes:
        - to: default
          via: 192.168.1.1
EOF

# 3. Backup and swap
sudo cp /etc/netplan/00-config.yaml /etc/netplan/00-config.yaml.backup
sudo mv /etc/netplan/00-config.yaml.new /etc/netplan/00-config.yaml

# 4. Validate
sudo netplan generate

# 5. Apply with try
sudo netplan try

# 6. Test from another terminal
ssh user@192.168.1.100

# 7. Confirm
# Press ENTER in netplan try terminal
```

## Troubleshooting Workflow Issues

### netplan try Hangs

```bash
# Check for existing netplan processes
ps aux | grep netplan

# Kill if stuck
sudo pkill -9 netplan
```

### Changes Don't Apply

```bash
# Force regeneration
sudo rm /run/systemd/network/*netplan*
sudo netplan generate
sudo systemctl restart systemd-networkd
```

### Configuration Conflicts

```bash
# Check for multiple configs defining same interface
grep -r "eth0" /etc/netplan/

# Ensure only one file configures each interface
```

### Service Not Restarting

```bash
# Manually restart backend
sudo systemctl restart systemd-networkd

# Or for NetworkManager
sudo systemctl restart NetworkManager
```

## CI/CD Workflow

For automated deployments:

```bash
#!/bin/bash
# deploy-network-config.sh

set -e

NEW_CONFIG="$1"

# Validate first
netplan generate --root-dir=/tmp/netplan-test || exit 1

# Backup
cp /etc/netplan/*.yaml /backup/

# Deploy
cp "$NEW_CONFIG" /etc/netplan/

# Apply with timeout for automated rollback
timeout 120 netplan apply || {
    # Restore on failure
    cp /backup/*.yaml /etc/netplan/
    netplan apply
    exit 1
}

# Verify connectivity
ping -c 1 8.8.8.8 || {
    cp /backup/*.yaml /etc/netplan/
    netplan apply
    exit 1
}

echo "Network configuration deployed successfully"
```
