# Docker UFW Conflict

## The Problem Explained

!!! danger "Critical Security Issue"
    When you publish a Docker container port, it becomes accessible from anywhere on the network, completely bypassing your UFW rules.

### The False Sense of Security

Many administrators believe this workflow is secure:

```bash
# "Secure" server setup
sudo ufw default deny incoming
sudo ufw allow ssh
sudo ufw enable

# Deploy a database
docker run -d -p 3306:3306 mysql

# WRONG: You think only SSH is accessible
# REALITY: MySQL is accessible from anywhere
```

### Why This Happens

Docker and UFW both manipulate iptables, but at different levels:

```
Incoming packet to port 3306
          │
          ▼
┌─────────────────────────────────┐
│   PREROUTING chain (nat table)  │
│                                 │
│   Docker DNAT rule:             │
│   DNAT to 172.17.0.2:3306      │◀── Packet redirected HERE
│                                 │
└─────────────────────────────────┘
          │
          ▼ (packet now destined for 172.17.0.2)
┌─────────────────────────────────┐
│    Routing Decision: FORWARD    │
│    (not INPUT - container IP)   │
└─────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────┐
│   FORWARD chain (filter table)  │
│                                 │
│   Docker rules: ACCEPT          │◀── Packet accepted HERE
│                                 │
│   UFW rules: Never evaluated    │◀── UFW is bypassed!
│                                 │
└─────────────────────────────────┘
          │
          ▼
    Container receives packet
```

### Key Points

1. **DNAT happens first** - In PREROUTING, before any filtering
2. **Packet destination changes** - From host IP to container IP
3. **FORWARD chain, not INPUT** - UFW user rules are in INPUT
4. **Docker's FORWARD rules accept** - Before UFW gets a chance

## Demonstrating the Vulnerability

### Test Setup

```bash
# On server (192.168.1.100)
sudo ufw status
# Status: active
# Default: deny (incoming)
# 22/tcp ALLOW Anywhere

# Start container
docker run -d --name test -p 8080:80 nginx
```

### From Another Machine

```bash
# This should be blocked by UFW, but works!
curl http://192.168.1.100:8080
# Returns nginx welcome page

# Verify UFW has no rule for 8080
ssh user@192.168.1.100 "sudo ufw status | grep 8080"
# (no output - no UFW rule exists)
```

### Check iptables

```bash
# Docker's NAT rule
sudo iptables -t nat -L PREROUTING -n -v
# DOCKER chain with DNAT rules

sudo iptables -t nat -L DOCKER -n
# DNAT tcp -- 0.0.0.0/0 0.0.0.0/0 tcp dpt:8080 to:172.17.0.2:80

# Docker's FORWARD rules
sudo iptables -L FORWARD -n -v
# DOCKER-USER, DOCKER-ISOLATION, DOCKER chains
# All process BEFORE ufw-before-forward
```

## The Chain Order Problem

View the actual rule order:

```bash
sudo iptables -L FORWARD -n --line-numbers
```

Typical output:

```
num  target                  prot opt source    destination
1    DOCKER-USER             all  --  anywhere  anywhere
2    DOCKER-ISOLATION-STAGE-1 all --  anywhere  anywhere
3    ACCEPT                  all  --  anywhere  anywhere  ctstate RELATED,ESTABLISHED
4    DOCKER                  all  --  anywhere  anywhere
5    ACCEPT                  all  --  anywhere  anywhere
6    ACCEPT                  all  --  anywhere  anywhere
7    ufw-before-forward      all  --  anywhere  anywhere  ◀── UFW rules start here
8    ufw-user-forward        all  --  anywhere  anywhere
9    ufw-after-forward       all  --  anywhere  anywhere
```

Docker's chains (1-6) process packets before UFW (7-9).

## Common Misconceptions

### "I'll just add a UFW rule to block it"

```bash
sudo ufw deny 8080
```

This adds a rule to `ufw-user-input`, but:
- Container traffic goes to FORWARD, not INPUT
- The rule never gets evaluated

### "I'll block the container IP"

```bash
sudo ufw deny from any to 172.17.0.2
```

This doesn't work because:
- The DNAT happens before UFW rules
- By the time UFW sees it, packet is already accepted

### "Docker should respect UFW"

Docker intentionally manages its own rules because:
- Container networking is complex
- NAT requires specific rule ordering
- Docker predates UFW's popularity

## What Actually Works

### Quick Reference

| Solution | Complexity | Effectiveness | Recommendation |
|----------|------------|---------------|----------------|
| Bind to localhost | Low | High | Use for services behind proxy |
| Use DOCKER-USER | Medium | High | Use for filtering |
| ufw-docker utility | Medium | High | Best general solution |
| iptables: false | High | High | Only for experts |
| Host network mode | Low | Medium | Use selectively |

### Why UFW's Before.rules Doesn't Help

Even adding rules to `/etc/ufw/before.rules` often doesn't work:

```bash
# This in before.rules:
-A ufw-before-forward -p tcp --dport 8080 -j DROP
```

Doesn't work because Docker's chains are inserted with higher priority.

### The DOCKER-USER Solution

Docker specifically created DOCKER-USER for custom rules:

```bash
# This works!
iptables -I DOCKER-USER -i eth0 -p tcp --dport 8080 -j DROP
```

But DOCKER-USER isn't managed by UFW, creating a split-brain situation.

## Security Implications

### Exposed Services

Common accidentally-exposed services:

| Service | Default Port | Risk |
|---------|--------------|------|
| MySQL | 3306 | Database access |
| PostgreSQL | 5432 | Database access |
| MongoDB | 27017 | Database access |
| Redis | 6379 | Cache/data store |
| Elasticsearch | 9200 | Search data |
| Memcached | 11211 | Cache |
| RabbitMQ | 5672, 15672 | Message queue |

### Real-World Scenarios

**Scenario 1: Development Database**

```yaml
# docker-compose.yml
services:
  db:
    image: postgres
    ports:
      - "5432:5432"  # Exposed to entire network!
    environment:
      POSTGRES_PASSWORD: development
```

**Scenario 2: Admin Interface**

```yaml
services:
  app:
    ports:
      - "8080:8080"  # App is fine
  admin:
    ports:
      - "9090:9090"  # Admin panel exposed!
```

### Network Scanning

Attackers regularly scan for these ports:

```bash
# What attackers do
nmap -p 3306,5432,27017,6379,9200 your-server-ip

# They find open ports you thought were blocked
```

## Temporary Workarounds

### While You Implement a Real Solution

```bash
# Block everything external to DOCKER-USER
iptables -I DOCKER-USER -i eth0 -j DROP
iptables -I DOCKER-USER -i eth0 -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# Then whitelist what you need
iptables -I DOCKER-USER -i eth0 -p tcp --dport 80 -j ACCEPT
iptables -I DOCKER-USER -i eth0 -p tcp --dport 443 -j ACCEPT
```

### Verify It's Working

```bash
# From external machine
nmap -p 3306,5432,27017 your-server-ip
# Should all show "filtered" or "closed"
```

## Affected Configurations

This problem affects you if:

1. ✅ Using Docker with `-p` or `ports:` in compose
2. ✅ Using UFW for firewall management
3. ✅ Server is network-accessible (not just localhost)
4. ✅ Any service besides the web-facing ones

This problem does NOT affect you if:

1. ❌ Only running containers without published ports
2. ❌ Using host network mode (UFW works normally)
3. ❌ Using macvlan/ipvlan (different issue)
4. ❌ Server is behind another firewall that blocks everything
