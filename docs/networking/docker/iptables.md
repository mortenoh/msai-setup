# Docker and iptables

## How Docker Uses iptables

Docker manipulates iptables extensively to enable container networking. Understanding this is crucial for firewall management.

## Docker's iptables Chains

Docker creates several custom chains:

```
┌─────────────────────────────────────────────────────────────┐
│                      nat table                               │
├─────────────────────────────────────────────────────────────┤
│  PREROUTING                                                  │
│    └──▶ DOCKER (DNAT for published ports)                   │
│                                                              │
│  OUTPUT                                                      │
│    └──▶ DOCKER                                              │
│                                                              │
│  POSTROUTING                                                 │
│    └──▶ MASQUERADE (for container outbound)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                     filter table                             │
├─────────────────────────────────────────────────────────────┤
│  FORWARD                                                     │
│    ├──▶ DOCKER-USER (your custom rules go here)            │
│    ├──▶ DOCKER-ISOLATION-STAGE-1                           │
│    ├──▶ DOCKER (per-container rules)                       │
│    └──▶ DOCKER-ISOLATION-STAGE-2                           │
└─────────────────────────────────────────────────────────────┘
```

## Chain Details

### DOCKER (nat table)

Handles DNAT for port publishing:

```bash
sudo iptables -t nat -L DOCKER -n -v
```

Example output:

```
Chain DOCKER (2 references)
target     prot opt source    destination
RETURN     all  --  0.0.0.0/0 0.0.0.0/0
DNAT       tcp  --  0.0.0.0/0 0.0.0.0/0  tcp dpt:8080 to:172.17.0.2:80
DNAT       tcp  --  0.0.0.0/0 0.0.0.0/0  tcp dpt:443 to:172.17.0.3:443
```

### DOCKER-USER (filter table)

**The only safe place for your custom rules:**

```bash
sudo iptables -L DOCKER-USER -n -v
```

Default content:

```
Chain DOCKER-USER (1 references)
target     prot opt source    destination
RETURN     all  --  0.0.0.0/0 0.0.0.0/0
```

### DOCKER (filter table)

Per-container allow rules:

```bash
sudo iptables -L DOCKER -n -v
```

Example:

```
Chain DOCKER (1 references)
target     prot opt source    destination
ACCEPT     tcp  --  0.0.0.0/0 172.17.0.2  tcp dpt:80
ACCEPT     tcp  --  0.0.0.0/0 172.17.0.3  tcp dpt:443
```

### DOCKER-ISOLATION Chains

Prevent cross-network communication:

```bash
sudo iptables -L DOCKER-ISOLATION-STAGE-1 -n -v
sudo iptables -L DOCKER-ISOLATION-STAGE-2 -n -v
```

## Packet Flow Analysis

### Incoming to Published Port

```
1. Packet arrives at eth0:8080
2. PREROUTING chain (nat table)
   └─▶ DOCKER chain: DNAT to 172.17.0.2:80
3. Routing decision: forward to docker0
4. FORWARD chain (filter table)
   ├─▶ DOCKER-USER: your rules (RETURN = continue)
   ├─▶ DOCKER-ISOLATION-STAGE-1: isolation check
   └─▶ DOCKER: ACCEPT (container rule)
5. Packet delivered to container
```

### Container to Internet

```
1. Container sends to external IP
2. Routing: forward through eth0
3. FORWARD chain
   └─▶ Default rules allow established
4. POSTROUTING chain (nat table)
   └─▶ MASQUERADE: source NAT to host IP
5. Packet exits eth0
```

### Container to Container (Same Network)

```
1. Container A sends to Container B
2. Routing: stays on docker0 bridge
3. FORWARD chain
   ├─▶ DOCKER-USER
   └─▶ DOCKER: ACCEPT
4. Packet delivered to Container B
```

### Container to Container (Different Networks)

```
1. Container A (net1) sends to Container B (net2)
2. FORWARD chain
   └─▶ DOCKER-ISOLATION-STAGE-1: jump to STAGE-2
       └─▶ DOCKER-ISOLATION-STAGE-2: DROP
3. Packet blocked
```

## Viewing Docker's iptables Rules

### Complete Rule Dump

```bash
# All tables
sudo iptables-save

# Just Docker-related
sudo iptables-save | grep -i docker
```

### NAT Table

```bash
# All NAT rules
sudo iptables -t nat -L -n -v

# Just DOCKER chain
sudo iptables -t nat -L DOCKER -n -v --line-numbers
```

### Filter Table

```bash
# All filter rules
sudo iptables -L -n -v

# FORWARD chain (most relevant)
sudo iptables -L FORWARD -n -v --line-numbers

# Docker-specific chains
sudo iptables -L DOCKER -n -v
sudo iptables -L DOCKER-USER -n -v
sudo iptables -L DOCKER-ISOLATION-STAGE-1 -n -v
```

## Rule Insertion Order

Docker inserts rules at specific positions:

```bash
# FORWARD chain order:
1. DOCKER-USER (your rules)
2. DOCKER-ISOLATION-STAGE-1
3. ACCEPT for established/related
4. DOCKER
5. ACCEPT for outbound from containers
```

This order means:

1. Your DOCKER-USER rules are checked first
2. Isolation rules prevent cross-network
3. Established connections fast-path
4. Per-container rules for published ports

## Docker iptables on Restart

When Docker restarts:

1. Removes all Docker-created rules
2. Recreates chains
3. Re-adds rules for running containers

**Your custom iptables rules outside DOCKER-USER may be lost!**

## Monitoring Rule Changes

```bash
# Watch for iptables changes
watch -d 'iptables -L DOCKER -n'

# Log rule changes (requires auditd)
auditctl -w /sbin/iptables -p x
```

## Docker and nftables

Docker still uses iptables, even on systems with nftables:

```bash
# Check which iptables
update-alternatives --query iptables
# Points to iptables-nft (translation layer)

# Docker rules appear in nftables
nft list ruleset | grep -i docker
```

## Disabling Docker's iptables

```json
// /etc/docker/daemon.json
{
  "iptables": false
}
```

**Consequences:**

- No automatic NAT for containers
- No port publishing
- No network isolation between networks
- You must configure everything manually

### Manual Configuration When Disabled

```bash
# Enable forwarding
echo 1 > /proc/sys/net/ipv4/ip_forward

# NAT for container network
iptables -t nat -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

# Allow forwarding
iptables -A FORWARD -i docker0 -o eth0 -j ACCEPT
iptables -A FORWARD -i eth0 -o docker0 -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# For published ports (manual DNAT)
iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 172.17.0.2:80
iptables -A FORWARD -p tcp -d 172.17.0.2 --dport 80 -j ACCEPT
```

## DOCKER-USER Best Practices

### Allow Specific Sources

```bash
# Only allow from local network
iptables -I DOCKER-USER -i eth0 ! -s 192.168.1.0/24 -j DROP
```

### Block Specific Ports

```bash
# Block external access to port 3306 (MySQL)
iptables -I DOCKER-USER -i eth0 -p tcp --dport 3306 -j DROP
```

### Rate Limiting

```bash
# Rate limit connections to container
iptables -I DOCKER-USER -p tcp --dport 80 -m connlimit --connlimit-above 100 -j DROP
```

### Logging

```bash
# Log dropped packets
iptables -I DOCKER-USER -j LOG --log-prefix "[DOCKER-USER] "
```

## Persisting DOCKER-USER Rules

DOCKER-USER rules aren't managed by Docker, so they need persistence:

```bash
# Save to file
iptables-save | grep -A 100 "DOCKER-USER" > /etc/iptables/docker-user.rules

# Restore script (/usr/local/bin/docker-user-rules.sh)
#!/bin/bash
iptables -I DOCKER-USER -i eth0 ! -s 192.168.1.0/24 -j DROP
# ... other rules ...

# systemd service
[Unit]
Description=Docker User iptables rules
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/docker-user-rules.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## Debugging Docker Networking

### Rule Hit Counts

```bash
# Reset counters
iptables -Z

# Generate traffic, then check
iptables -L -n -v
# Check 'pkts' column
```

### Packet Tracing

```bash
# Enable tracing
iptables -t raw -A PREROUTING -p tcp --dport 8080 -j TRACE

# View trace
dmesg | grep TRACE
```

### Connection Tracking

```bash
# View active connections
conntrack -L | grep 172.17

# Watch connections
conntrack -E
```
