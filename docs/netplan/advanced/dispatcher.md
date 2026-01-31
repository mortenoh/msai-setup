# Network Dispatcher Scripts

## Overview

Network dispatcher scripts run automatically when network events occur:

- Interface comes up/down
- IP address assigned/removed
- DNS changes
- Connectivity changes

## systemd-networkd Dispatcher

### Script Location

Place scripts in:
```
/etc/networkd-dispatcher/
├── carrier.d/         # Link carrier detected
├── configuring.d/     # Being configured
├── configured.d/      # Configuration complete
├── degraded.d/        # Partially configured
├── dormant.d/         # Interface waiting
├── no-carrier.d/      # Link down
├── off.d/             # Interface disabled
├── routable.d/        # Has routable address
└── unmanaged.d/       # Not managed
```

### Basic Script Structure

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/10-custom-script.sh

# Available environment variables:
# IFACE          - Interface name (e.g., eth0)
# STATE          - Current state (routable, carrier, etc.)
# ADDR           - IP address
# GATEWAY        - Gateway address
# DNS            - DNS servers

# Log event
logger "Network: $IFACE is $STATE"

# Your logic here
if [ "$IFACE" = "eth0" ] && [ "$STATE" = "routable" ]; then
    # eth0 has routable address
    /usr/local/bin/start-services.sh
fi

exit 0
```

### Make Executable

```bash
chmod +x /etc/networkd-dispatcher/routable.d/10-custom-script.sh
```

## Common Use Cases

### Start Services When Network Ready

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/50-start-services.sh

logger "Network $IFACE is routable, starting services"

case "$IFACE" in
    eth0)
        # Start services that need network
        systemctl start docker
        systemctl start nginx
        ;;
    wg0)
        # VPN is up, start VPN-dependent services
        systemctl start corporate-apps
        ;;
esac
```

### Update Dynamic DNS

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/60-ddns.sh

if [ "$IFACE" = "eth0" ]; then
    logger "Updating dynamic DNS for $IFACE"

    # Get current IP
    IP=$(ip -4 addr show $IFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

    # Update Cloudflare DNS
    curl -X PUT "https://api.cloudflare.com/client/v4/zones/ZONE_ID/dns_records/RECORD_ID" \
         -H "Authorization: Bearer TOKEN" \
         -H "Content-Type: application/json" \
         --data "{\"type\":\"A\",\"name\":\"server.example.com\",\"content\":\"$IP\"}"
fi
```

### Mount Network Filesystems

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/70-mount-nfs.sh

if [ "$IFACE" = "eth0" ]; then
    logger "Mounting NFS shares"

    # Wait for NFS server to be reachable
    until ping -c 1 192.168.1.50 > /dev/null 2>&1; do
        sleep 1
    done

    # Mount shares
    mount -a -t nfs
fi
```

### VPN Auto-Connect

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/40-vpn.sh

if [ "$IFACE" = "eth0" ]; then
    logger "Primary network up, starting VPN"
    systemctl start wg-quick@wg0
fi
```

### Notify on Network Changes

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/99-notify.sh

# Send notification
curl -X POST "https://hooks.slack.com/services/xxx" \
     -H "Content-Type: application/json" \
     -d "{\"text\":\"Server network is up: $IFACE at $ADDR\"}"

# Or email
echo "Server $HOSTNAME network $IFACE is now $STATE with IP $ADDR" | \
    mail -s "Network Status Change" admin@example.com
```

## Link Down Scripts

### Handle Network Loss

```bash
#!/bin/bash
# /etc/networkd-dispatcher/no-carrier.d/50-handle-down.sh

logger "Network $IFACE lost carrier!"

case "$IFACE" in
    eth0)
        # Primary network down
        # Alert and try failover
        /usr/local/bin/send-alert.sh "Primary network down!"

        # Maybe bring up backup interface
        ip link set eth1 up
        ;;
esac
```

### Stop Dependent Services

```bash
#!/bin/bash
# /etc/networkd-dispatcher/no-carrier.d/50-stop-services.sh

if [ "$IFACE" = "eth0" ]; then
    logger "Stopping network-dependent services"

    # Stop services gracefully before network gone
    systemctl stop docker
fi
```

## NetworkManager Dispatcher

If using NetworkManager instead of networkd:

### Script Location

```
/etc/NetworkManager/dispatcher.d/
```

### Script Structure

```bash
#!/bin/bash
# /etc/NetworkManager/dispatcher.d/50-custom.sh

INTERFACE=$1
ACTION=$2

logger "NM Dispatcher: $INTERFACE is $ACTION"

case "$ACTION" in
    up)
        # Interface is up
        if [ "$INTERFACE" = "eth0" ]; then
            /usr/local/bin/network-up.sh
        fi
        ;;
    down)
        # Interface is down
        if [ "$INTERFACE" = "eth0" ]; then
            /usr/local/bin/network-down.sh
        fi
        ;;
    vpn-up)
        # VPN connected
        /usr/local/bin/vpn-connected.sh
        ;;
    vpn-down)
        # VPN disconnected
        /usr/local/bin/vpn-disconnected.sh
        ;;
esac

exit 0
```

### Subdirectories

NetworkManager also supports:

```
/etc/NetworkManager/dispatcher.d/
├── pre-up.d/       # Before interface up
├── pre-down.d/     # Before interface down
└── no-wait.d/      # Async scripts
```

## Debugging Dispatcher Scripts

### Check Script Runs

```bash
# Watch syslog
tail -f /var/log/syslog | grep -i network

# Or journal
journalctl -f -u networkd-dispatcher
```

### Test Script Manually

```bash
# Simulate environment
export IFACE=eth0
export STATE=routable
export ADDR=192.168.1.100

# Run script
bash -x /etc/networkd-dispatcher/routable.d/50-custom.sh
```

### Check Service Status

```bash
# networkd-dispatcher status
systemctl status networkd-dispatcher

# Enable if not running
systemctl enable --now networkd-dispatcher
```

### Common Issues

```bash
# Script not executable
chmod +x /etc/networkd-dispatcher/routable.d/script.sh

# Wrong shebang
# Use: #!/bin/bash
# Not: #!/bin/sh (may lack features)

# Script errors - check logs
journalctl -u networkd-dispatcher -f

# Permission issues
# Scripts run as root, but check file permissions
```

## Script Best Practices

### 1. Always Exit Successfully

```bash
#!/bin/bash
# Even if command fails, exit 0 to not block networking
some_command || true
exit 0
```

### 2. Use Logging

```bash
#!/bin/bash
logger -t "net-dispatcher" "Script started for $IFACE"
```

### 3. Be Idempotent

```bash
#!/bin/bash
# Check if already done before doing again
if ! systemctl is-active docker; then
    systemctl start docker
fi
```

### 4. Handle Multiple Interfaces

```bash
#!/bin/bash
# Only act on specific interfaces
case "$IFACE" in
    eth0|ens*)
        do_something
        ;;
    *)
        # Ignore other interfaces
        ;;
esac
```

### 5. Don't Block

```bash
#!/bin/bash
# Run long tasks in background
/usr/local/bin/long-task.sh &

exit 0
```

### 6. Use Lock Files

```bash
#!/bin/bash
LOCKFILE="/tmp/network-script.lock"

if [ -f "$LOCKFILE" ]; then
    logger "Script already running"
    exit 0
fi

touch "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

# Your code here
```

## Example: Complete Network Setup Script

```bash
#!/bin/bash
# /etc/networkd-dispatcher/routable.d/99-complete-setup.sh
# Comprehensive network ready script

set -e

log() {
    logger -t "network-setup" "$1"
}

log "Network event: $IFACE is $STATE"

# Only handle primary interface getting routable
if [ "$IFACE" != "eth0" ] || [ "$STATE" != "routable" ]; then
    exit 0
fi

log "Primary interface is up, running setup..."

# Wait for DNS to be available
for i in $(seq 1 30); do
    if host google.com > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# Update system time
log "Syncing time..."
timedatectl set-ntp true
chronyc makestep 2>/dev/null || true

# Update dynamic DNS
log "Updating dynamic DNS..."
IP=$(ip -4 addr show $IFACE | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | head -1)
if [ -n "$IP" ]; then
    /usr/local/bin/update-ddns.sh "$IP" || true
fi

# Start services
log "Starting services..."
systemctl start docker 2>/dev/null || true

# Mount network filesystems
log "Mounting network filesystems..."
mount -a -t nfs,cifs 2>/dev/null || true

# Send notification
log "Sending notification..."
/usr/local/bin/notify.sh "Server $HOSTNAME is online at $IP" || true

log "Network setup complete"
exit 0
```
