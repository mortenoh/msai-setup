# Policy Routing

## What is Policy Routing?

Policy routing allows routing decisions based on criteria beyond destination address:

- Source address
- Incoming interface
- Packet marks (fwmark)
- TOS/DSCP values
- Protocol

```
                    ┌─────────────────────────────────────┐
                    │         Policy Routing Database     │
                    ├─────────────────────────────────────┤
   Packet ──────────│  Rule 1: from 10.0.0.0/8 → table 100│
                    │  Rule 2: fwmark 1 → table 200       │
                    │  Rule 3: to 8.8.8.8 → table 300     │
                    │  Default: → main table              │
                    └─────────────────────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              ▼                       ▼                       ▼
        Table 100                Table 200                Table 300
     (via 10.0.0.1)           (via 172.16.0.1)          (via 1.1.1.1)
```

## Use Cases

| Use Case | Description |
|----------|-------------|
| Multi-homing | Different ISPs for different traffic |
| Source-based routing | Route based on source IP |
| VPN split tunneling | Some traffic through VPN, rest direct |
| Load balancing | Distribute traffic across links |
| Traffic engineering | Route specific traffic via specific paths |

## Basic Policy Routing

### Route Based on Source Address

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
        - 192.168.2.100/24
      routes:
        - to: default
          via: 192.168.1.1
          table: main

        - to: default
          via: 192.168.2.1
          table: 100

      routing-policy:
        - from: 192.168.2.0/24
          table: 100
```

### Route Based on Destination

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

        - to: default
          via: 192.168.1.254
          table: 100

      routing-policy:
        - to: 10.0.0.0/8
          table: 100
```

## Multi-Homed Server

### Two ISPs with Source Routing

Ensure replies go out the same interface as requests:

```yaml
network:
  version: 2
  ethernets:
    # ISP 1
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        # Default via ISP 1
        - to: default
          via: 203.0.113.1
          metric: 100

        # Full routing table for ISP 1
        - to: default
          via: 203.0.113.1
          table: 100

      routing-policy:
        # Traffic from ISP 1 IP uses ISP 1
        - from: 203.0.113.10
          table: 100

    # ISP 2
    eth1:
      addresses:
        - 198.51.100.10/24
      routes:
        # Backup default
        - to: default
          via: 198.51.100.1
          metric: 200

        # Full routing table for ISP 2
        - to: default
          via: 198.51.100.1
          table: 200

      routing-policy:
        # Traffic from ISP 2 IP uses ISP 2
        - from: 198.51.100.10
          table: 200
```

### Load Balancing Between ISPs

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24

    eth1:
      addresses:
        - 198.51.100.10/24

    lo:
      addresses:
        - 10.0.0.1/32

# Additional configuration via files or scripts:
# ip rule add from 10.0.0.1 fwmark 1 table 100
# ip rule add from 10.0.0.1 fwmark 2 table 200
# iptables -t mangle -A OUTPUT -m statistic --mode nth --every 2 -j MARK --set-mark 1
```

## VPN Split Tunneling

### Some Traffic Through VPN

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 192.168.1.100/24
      routes:
        - to: default
          via: 192.168.1.1

  tunnels:
    wg0:
      mode: wireguard
      addresses:
        - 10.10.10.2/24
      key: "PRIVATE_KEY"
      routes:
        # Corporate networks via VPN
        - to: 10.0.0.0/8
          table: 100
        - to: 172.16.0.0/12
          table: 100

      routing-policy:
        # Traffic to corporate goes via VPN table
        - to: 10.0.0.0/8
          table: 100
        - to: 172.16.0.0/12
          table: 100

      peers:
        - keys:
            public: "SERVER_KEY"
          allowed-ips:
            - 10.0.0.0/8
            - 172.16.0.0/12
          endpoint: "vpn.corp.com:51820"
```

## Policy Routing Rules

### Rule Priority

```yaml
routing-policy:
  - from: 10.0.0.0/8
    table: 100
    priority: 100        # Lower = checked first

  - from: 192.168.0.0/16
    table: 200
    priority: 200
```

### Rule with Mark

```yaml
routing-policy:
  - mark: 1
    table: 100

  - mark: 2
    table: 200
```

Set marks with iptables:

```bash
# Mark packets from specific source
iptables -t mangle -A PREROUTING -s 10.0.0.0/8 -j MARK --set-mark 1

# Mark packets to specific destination
iptables -t mangle -A OUTPUT -d 8.8.8.8 -j MARK --set-mark 2
```

### Rule with Type of Service

```yaml
routing-policy:
  - type-of-service: 8      # Minimize delay
    table: 100
```

## Routing Tables

### Named Tables

Edit `/etc/iproute2/rt_tables`:

```
#
# reserved values
#
255     local
254     main
253     default
0       unspec
#
# custom
#
100     isp1
200     isp2
300     vpn
```

Then use in netplan:

```yaml
routes:
  - to: default
    via: 203.0.113.1
    table: 100      # Uses table "isp1" (ID 100)
```

### View Routing Tables

```bash
# Main table
ip route show table main

# Custom table
ip route show table 100
ip route show table isp1

# All tables
ip route show table all

# Rules
ip rule show
```

## Complex Multi-Path Setup

### Three Networks with Policies

```yaml
network:
  version: 2
  ethernets:
    # Public network (Internet via ISP)
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1
          table: main

        - to: default
          via: 203.0.113.1
          table: 100

    # Private corporate network
    eth1:
      addresses:
        - 10.0.0.10/24
      routes:
        - to: 10.0.0.0/8
          via: 10.0.0.1
          table: main

        - to: 0.0.0.0/0
          via: 10.0.0.1
          table: 200

    # Storage network (no external routing)
    eth2:
      addresses:
        - 192.168.100.10/24

  routing-policy:
    # Traffic from public IP uses ISP
    - from: 203.0.113.10
      table: 100

    # Traffic from corporate IP uses corporate gateway
    - from: 10.0.0.10
      table: 200

    # Traffic to corporate always uses corporate
    - to: 10.0.0.0/8
      table: 200
```

## Failover with Policy Routing

### Active-Passive ISP Failover

```yaml
network:
  version: 2
  ethernets:
    eth0:
      addresses:
        - 203.0.113.10/24
      routes:
        - to: default
          via: 203.0.113.1
          metric: 100

    eth1:
      addresses:
        - 198.51.100.10/24
      routes:
        - to: default
          via: 198.51.100.1
          metric: 200
```

For active failover monitoring, use a script:

```bash
#!/bin/bash
# /usr/local/bin/isp-failover.sh

PRIMARY_GW="203.0.113.1"
BACKUP_GW="198.51.100.1"
CHECK_HOST="8.8.8.8"

while true; do
    if ! ping -c 3 -W 2 $PRIMARY_GW > /dev/null 2>&1; then
        # Primary down, ensure backup is active
        ip route replace default via $BACKUP_GW metric 50
    else
        # Primary up, restore normal metrics
        ip route replace default via $PRIMARY_GW metric 100
        ip route replace default via $BACKUP_GW metric 200
    fi
    sleep 10
done
```

## Verifying Policy Routing

### Check Rules

```bash
# List all rules
ip rule show

# Example output:
# 0:      from all lookup local
# 100:    from 10.0.0.0/8 lookup 100
# 200:    from 192.168.0.0/16 lookup 200
# 32766:  from all lookup main
# 32767:  from all lookup default
```

### Check Tables

```bash
# Specific table
ip route show table 100

# Which table handles a destination
ip route get 8.8.8.8
ip route get 8.8.8.8 from 10.0.0.10
```

### Trace Policy Decision

```bash
# See which rule matches
ip route get 8.8.8.8 from 10.0.0.10

# Output shows table used:
# 8.8.8.8 from 10.0.0.10 via 10.0.0.1 dev eth1 table 200
```

## Troubleshooting

### Rules Not Taking Effect

```bash
# Check rule exists
ip rule show | grep "from 10.0.0.0"

# Check rule priority (lower checked first)
# Ensure custom rules are before main (32766)

# Check table has routes
ip route show table 100
```

### Asymmetric Routing

```bash
# Verify return path
ip route get <source-of-packet> from <your-ip>

# Ensure source-based rules exist for all IPs
```

### Policy Not Applied After Reboot

```bash
# Verify netplan generated rules
cat /run/systemd/network/*.network | grep -A5 "RoutingPolicyRule"

# Manually check
ip rule show
```

### Conntrack Issues

Policy routing can cause conntrack issues with multiple paths:

```bash
# Disable strict reverse path filtering
echo 0 > /proc/sys/net/ipv4/conf/all/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/eth0/rp_filter
echo 0 > /proc/sys/net/ipv4/conf/eth1/rp_filter
```

Or use loose mode:

```bash
echo 2 > /proc/sys/net/ipv4/conf/all/rp_filter
```

## Best Practices

1. **Document your tables** - Use `/etc/iproute2/rt_tables` for named tables
2. **Set explicit priorities** - Don't rely on insertion order
3. **Always have fallback** - Ensure main table has a working default route
4. **Test thoroughly** - Policy routing is complex and easy to break
5. **Monitor connectivity** - Use scripts to detect and handle failures
6. **Consider conntrack** - Multi-path setups can confuse connection tracking
7. **Use netplan try** - Always test changes safely
