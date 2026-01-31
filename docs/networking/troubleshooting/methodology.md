# Debugging Methodology

## Systematic Approach

When troubleshooting network/firewall issues, follow this systematic process:

```
1. Define the Problem
        ↓
2. Gather Information
        ↓
3. Isolate the Layer
        ↓
4. Test Hypothesis
        ↓
5. Implement Fix
        ↓
6. Verify Solution
```

## Step 1: Define the Problem

### Ask Specific Questions

- What exactly isn't working?
- What error messages appear?
- When did it stop working?
- What changed recently?

### Document Expected vs Actual

```
Expected: External client can reach web server on port 80
Actual: Connection times out
```

## Step 2: Gather Information

### Network Configuration

```bash
# IP addresses
ip addr show

# Routes
ip route show

# DNS
resolvectl status

# Listening ports
ss -tlnp
```

### Firewall State

```bash
# UFW status
ufw status verbose

# iptables rules
iptables -L -n -v
iptables -t nat -L -n -v

# Connection tracking
conntrack -L
```

### Service State

```bash
# Docker
docker ps
docker network ls

# libvirt
virsh list --all
virsh net-list --all

# LXD
lxc list
lxc network list
```

## Step 3: Isolate the Layer

### OSI Model Approach

```
Layer 7 - Application (service config)
Layer 4 - Transport (ports, firewall)
Layer 3 - Network (IP, routing)
Layer 2 - Data Link (bridges, VLANs)
Layer 1 - Physical (cables, NICs)
```

### Quick Tests by Layer

**Layer 1-2 (Physical/Link):**

```bash
# Interface up?
ip link show eth0

# Cable connected?
ethtool eth0 | grep "Link detected"

# Bridge members?
bridge link show
```

**Layer 3 (Network):**

```bash
# Can ping gateway?
ping -c 3 192.168.1.1

# Can ping destination?
ping -c 3 8.8.8.8

# Route exists?
ip route get 8.8.8.8
```

**Layer 4 (Transport/Firewall):**

```bash
# Port open locally?
ss -tlnp | grep :80

# Port reachable?
nc -zv localhost 80

# Firewall blocking?
iptables -L -n -v | grep -E "DROP|REJECT"
```

**Layer 7 (Application):**

```bash
# Service running?
systemctl status nginx

# Service responding?
curl -v http://localhost/

# Logs show errors?
journalctl -u nginx -f
```

## Step 4: Test Hypothesis

### Form a Hypothesis

Based on gathered information:

> "Traffic is being blocked by UFW because there's no allow rule for port 8080"

### Test It

```bash
# Temporarily disable UFW
sudo ufw disable

# Test again
curl http://server:8080

# If works, hypothesis confirmed
# Re-enable UFW
sudo ufw enable
```

### Alternative: Add Logging

```bash
# Add logging rule
iptables -I INPUT -p tcp --dport 8080 -j LOG --log-prefix "[TEST-8080] "

# Generate traffic
curl http://server:8080

# Check logs
journalctl -k | grep TEST-8080
```

## Step 5: Implement Fix

### Make Minimal Changes

Don't change multiple things at once.

```bash
# Add specific rule
sudo ufw allow 8080/tcp

# Verify rule added
sudo ufw status | grep 8080
```

### Document Changes

```bash
# Log what you changed
echo "$(date): Added UFW rule for port 8080" >> ~/firewall-changes.log
```

## Step 6: Verify Solution

### Test the Original Problem

```bash
curl http://server:8080
# Should work now
```

### Test for Regressions

```bash
# Verify other services still work
curl http://server:80
ssh server
```

### Verify Persistence

```bash
# Reboot and test
sudo reboot
# After reboot
curl http://server:8080
```

## Common Debugging Scenarios

### Scenario: Container Can't Reach Internet

```bash
# 1. Check container has IP
docker exec container ip addr

# 2. Check can ping gateway (docker0)
docker exec container ping -c 1 172.17.0.1

# 3. Check can ping host's external IP
docker exec container ping -c 1 192.168.1.100

# 4. Check can ping external
docker exec container ping -c 1 8.8.8.8

# 5. If step 4 fails, check NAT
sudo iptables -t nat -L POSTROUTING -n -v | grep 172.17

# 6. Check IP forwarding
cat /proc/sys/net/ipv4/ip_forward
```

### Scenario: Service Unreachable from Outside

```bash
# 1. Service listening?
ss -tlnp | grep :8080

# 2. Reachable locally?
curl localhost:8080

# 3. Reachable from host IP?
curl 192.168.1.100:8080

# 4. Check firewall
sudo iptables -L INPUT -n -v | grep 8080
sudo ufw status | grep 8080

# 5. If Docker, check Docker rules
sudo iptables -t nat -L DOCKER -n
sudo iptables -L DOCKER-USER -n
```

### Scenario: VM Has No Network

```bash
# 1. VM interface up?
virsh domiflist vmname

# 2. Bridge exists?
ip link show virbr0

# 3. libvirt network running?
virsh net-list

# 4. From VM console, check IP
# (virsh console vmname)
ip addr
ip route

# 5. Check DHCP
journalctl | grep dnsmasq

# 6. Check forwarding rules
sudo iptables -L FORWARD -n -v | grep virbr0
```

## Debugging Tools

### Essential Tools

```bash
# Install if needed
sudo apt install -y \
    net-tools \
    tcpdump \
    nmap \
    traceroute \
    dnsutils \
    conntrack
```

### tcpdump Examples

```bash
# All traffic on interface
tcpdump -i eth0

# Specific port
tcpdump -i eth0 port 80

# Specific host
tcpdump -i eth0 host 192.168.1.100

# Docker bridge
tcpdump -i docker0

# Write to file
tcpdump -i eth0 -w capture.pcap
```

### iptables Debugging

```bash
# Packet counts
iptables -L -n -v

# Trace packets
iptables -t raw -A PREROUTING -p tcp --dport 80 -j TRACE
dmesg | grep TRACE

# Log specific traffic
iptables -I INPUT -p tcp --dport 80 -j LOG --log-prefix "[HTTP] "
```

## Checklist Template

Use this checklist for systematic debugging:

```markdown
## Issue: [Description]

### Symptoms
- [ ] Error message:
- [ ] When:
- [ ] Frequency:

### Environment
- [ ] Host:
- [ ] Docker version:
- [ ] libvirt version:
- [ ] UFW status:

### Layer 1-2 (Physical/Link)
- [ ] Interface up:
- [ ] Link detected:
- [ ] Bridge OK:

### Layer 3 (Network)
- [ ] IP assigned:
- [ ] Gateway reachable:
- [ ] External reachable:

### Layer 4 (Transport)
- [ ] Port listening:
- [ ] Firewall rules:
- [ ] NAT rules:

### Layer 7 (Application)
- [ ] Service running:
- [ ] Service responding:
- [ ] Logs:

### Root Cause
[Analysis]

### Solution
[Fix applied]

### Verification
- [ ] Problem resolved:
- [ ] No regressions:
- [ ] Survives reboot:
```
