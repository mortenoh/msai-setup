# UFW Advanced Usage

## Custom Chains

### When to Use Custom Chains

- Organize rules logically
- Share rules between multiple entry points
- Implement complex matching

### Creating Custom Chains in before.rules

```bash
# /etc/ufw/before.rules (in *filter section)

# Define custom chain
:ufw-custom-ssh - [0:0]

# Populate custom chain
-A ufw-custom-ssh -s 192.168.1.0/24 -j ACCEPT
-A ufw-custom-ssh -s 10.0.0.0/8 -j ACCEPT
-A ufw-custom-ssh -m recent --name ssh-block --rcheck --seconds 60 --hitcount 4 -j DROP
-A ufw-custom-ssh -m recent --name ssh-block --set
-A ufw-custom-ssh -j ACCEPT

# Jump to custom chain from before-input
-A ufw-before-input -p tcp --dport 22 -j ufw-custom-ssh
```

## Rate Limiting Deep Dive

### Built-in Limit

UFW's built-in limit is simple:

```bash
sudo ufw limit ssh
```

This creates:
- 6 connections per 30 seconds
- No per-IP tracking

### Custom Rate Limiting

More sophisticated limiting in before.rules:

```bash
# Per-IP rate limiting
-A ufw-before-input -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --set
-A ufw-before-input -p tcp --dport 22 -m conntrack --ctstate NEW \
    -m recent --name SSH --update --seconds 60 --hitcount 4 -j DROP

# Using hashlimit for per-IP limits
-A ufw-before-input -p tcp --dport 80 -m hashlimit \
    --hashlimit-name http-limit \
    --hashlimit-mode srcip \
    --hashlimit-above 50/second \
    --hashlimit-burst 100 \
    --hashlimit-srcmask 32 \
    -j DROP
```

### Connection Limits

```bash
# Limit concurrent connections per IP
-A ufw-before-input -p tcp --dport 80 -m connlimit \
    --connlimit-above 50 --connlimit-mask 32 -j DROP
```

## Port Knocking

### Simple Port Knock

```bash
# /etc/ufw/before.rules

# Create sets for tracking
# (Requires manual iptables, UFW doesn't support sets directly)

# Alternative: Use recent module
-N ufw-port-knock
-A ufw-before-input -j ufw-port-knock

# Stage 1: Knock on port 7000
-A ufw-port-knock -p tcp --dport 7000 -m recent --name KNOCK1 --set -j DROP

# Stage 2: Knock on port 8000 (must have knocked 7000)
-A ufw-port-knock -p tcp --dport 8000 -m recent --name KNOCK1 --rcheck \
    -m recent --name KNOCK2 --set -j DROP

# Stage 3: Knock on port 9000 (must have knocked 8000)
-A ufw-port-knock -p tcp --dport 9000 -m recent --name KNOCK2 --rcheck \
    -m recent --name KNOCK3 --set -j DROP

# Allow SSH after completing knock sequence
-A ufw-port-knock -p tcp --dport 22 -m recent --name KNOCK3 --rcheck \
    --seconds 30 -j ACCEPT
```

### Using knockd (Better Approach)

Install knockd for proper port knocking:

```bash
sudo apt install knockd

# /etc/knockd.conf
[options]
    UseSyslog

[openSSH]
    sequence    = 7000,8000,9000
    seq_timeout = 5
    command     = /usr/sbin/ufw allow from %IP% to any port 22
    tcpflags    = syn

[closeSSH]
    sequence    = 9000,8000,7000
    seq_timeout = 5
    command     = /usr/sbin/ufw delete allow from %IP% to any port 22
    tcpflags    = syn
```

## GeoIP Blocking

UFW doesn't natively support GeoIP, but you can use xtables-addons:

```bash
# Install xtables-geoip
sudo apt install xtables-addons-common libtext-csv-xs-perl

# Download GeoIP database
sudo /usr/lib/xtables-addons/xt_geoip_dl
sudo /usr/lib/xtables-addons/xt_geoip_build
```

Add to before.rules:

```bash
# Block specific countries
-A ufw-before-input -m geoip --src-cc CN,RU,KP -j DROP
```

## IP Sets Integration

### Why Use IP Sets

- Efficient for large lists (thousands of IPs)
- O(1) lookup vs O(n) for rule chains
- Dynamic updates without rule reload

### Setup

```bash
# Install ipset
sudo apt install ipset

# Create set
sudo ipset create blocklist hash:net

# Add entries
sudo ipset add blocklist 10.0.0.0/8
sudo ipset add blocklist 192.168.50.0/24
```

### Use in before.rules

```bash
# Reference ipset
-A ufw-before-input -m set --match-set blocklist src -j DROP
```

### Persist IP Sets

```bash
# Save
sudo ipset save > /etc/ipset.rules

# Restore (before UFW starts)
# Create /etc/systemd/system/ipset-restore.service
[Unit]
Description=Restore ipset rules
Before=ufw.service

[Service]
Type=oneshot
ExecStart=/usr/sbin/ipset restore -f /etc/ipset.rules
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

## Fail2ban Integration

### How Fail2ban Works with UFW

Fail2ban monitors logs and adds temporary firewall rules:

```bash
sudo apt install fail2ban
```

### Configure for UFW

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
banaction = ufw
banaction_allports = ufw

[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

### UFW Ban Action

```ini
# /etc/fail2ban/action.d/ufw.conf
[Definition]
actionban = ufw insert 1 deny from <ip> to any
actionunban = ufw delete deny from <ip> to any
```

## Traffic Shaping

UFW doesn't do traffic shaping, but you can add tc rules:

```bash
# Mark traffic with iptables
-A ufw-before-output -p tcp --dport 80 -j MARK --set-mark 1

# Use tc for shaping (separate from UFW)
tc qdisc add dev eth0 root handle 1: htb default 10
tc class add dev eth0 parent 1: classid 1:1 htb rate 100mbit
tc filter add dev eth0 parent 1: protocol ip handle 1 fw flowid 1:1
```

## Multi-Path Routing

### Mark-Based Routing

```bash
# /etc/ufw/before.rules (in *mangle section - add before *filter)
*mangle
:PREROUTING ACCEPT [0:0]

# Mark traffic from specific source
-A PREROUTING -s 192.168.1.0/24 -j MARK --set-mark 1

COMMIT
```

Then configure policy routing:

```bash
# /etc/iproute2/rt_tables
100 isp2

# Routing rules
ip rule add fwmark 1 table isp2
ip route add default via 10.0.0.1 table isp2
```

## Transparent Proxy

### Redirect HTTP to Proxy

```bash
# /etc/ufw/before.rules (in *nat section)
*nat
# Redirect port 80 to local proxy
-A PREROUTING -i eth1 -p tcp --dport 80 -j REDIRECT --to-port 3128
COMMIT
```

### With Squid

```bash
# Squid intercept mode
# /etc/squid/squid.conf
http_port 3128 intercept
```

## Connection Tracking Tuning

### Timeouts

```bash
# /etc/ufw/sysctl.conf (or /etc/sysctl.d/99-conntrack.conf)

# TCP established (default 5 days, reduce for busy servers)
net.netfilter.nf_conntrack_tcp_timeout_established = 86400

# TCP time-wait
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30

# UDP
net.netfilter.nf_conntrack_udp_timeout = 30
```

### Table Size

```bash
# Increase for busy servers
net.netfilter.nf_conntrack_max = 524288

# Hash table (conntrack_max / 4)
net.netfilter.nf_conntrack_buckets = 131072
```

## Logging Configuration

### Log Levels

```bash
# /etc/ufw/ufw.conf
LOGLEVEL=low    # Match only logging rules
LOGLEVEL=medium # Log rate-limited and more
LOGLEVEL=high   # Log even more
LOGLEVEL=full   # Log everything
```

### Custom Logging Rules

```bash
# /etc/ufw/before.rules

# Log specific traffic
-A ufw-before-input -p tcp --dport 22 -j LOG --log-prefix "[UFW SSH] "

# Log with rate limit
-A ufw-before-input -m limit --limit 3/min -j LOG --log-prefix "[UFW WARN] "
```

### Log to Separate File

```bash
# /etc/rsyslog.d/20-ufw.conf
:msg,contains,"[UFW " /var/log/ufw.log
& stop
```

## Stateless Rules

By default, UFW is stateful (uses conntrack). For high-performance scenarios:

```bash
# /etc/ufw/before.rules

# Add to *raw table (before *nat)
*raw
:PREROUTING ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]

# Don't track high-volume traffic
-A PREROUTING -p udp --dport 53 -j NOTRACK
-A OUTPUT -p udp --sport 53 -j NOTRACK

COMMIT
```

Then add stateless rules in *filter:

```bash
# Must explicitly allow both directions for untracked
-A ufw-before-input -p udp --dport 53 -j ACCEPT
-A ufw-before-output -p udp --sport 53 -j ACCEPT
```

## Dynamic Rule Updates

### API-Driven Rules

Use ufw commands in scripts:

```bash
#!/bin/bash
# Add rule based on API response
NEW_IP=$(curl -s https://api.example.com/allowed-ip)
ufw allow from $NEW_IP to any port 443
```

### Webhook-Triggered

```bash
# Simple webhook endpoint (using netcat)
while true; do
    IP=$(echo -e "HTTP/1.1 200 OK\n\n" | nc -l -p 9999 | grep "X-Real-IP" | cut -d: -f2)
    ufw allow from $IP to any port 22 comment "Dynamic allow"
done
```

## Testing Rules

### Dry Run (Sort of)

```bash
# Check what rules will be added
ufw --dry-run allow 80

# Note: This still modifies user.rules but doesn't apply
```

### Test Environment

```bash
# Create network namespace for testing
sudo ip netns add firewall-test
sudo ip netns exec firewall-test iptables -L

# Test rules there before applying to production
```

### Rule Verification

```bash
# After adding rules, verify
sudo iptables -L -n -v | grep -A5 "ufw-user-input"

# Check specific rule
sudo ufw status numbered | grep 22
```
