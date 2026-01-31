# SSH Troubleshooting

## Quick Diagnostic

```bash
# Test connection with verbosity
ssh -vvv user@host

# Check SSH service on server
systemctl status sshd

# Check listening
ss -tlnp | grep :22

# Check firewall
ufw status
iptables -L -n | grep 22
```

## Connection Problems

### Connection Refused

```
ssh: connect to host server.example.com port 22: Connection refused
```

**Causes:**
- SSH server not running
- Firewall blocking
- Wrong port

**Solutions:**

```bash
# Check server is running (on server)
systemctl status sshd
systemctl start sshd

# Check firewall (on server)
ufw allow 22
# or
iptables -A INPUT -p tcp --dport 22 -j ACCEPT

# Check port
ssh -p 2222 user@host  # if non-standard
```

### Connection Timed Out

```
ssh: connect to host server.example.com port 22: Connection timed out
```

**Causes:**
- Network issue
- Host unreachable
- Firewall dropping packets

**Solutions:**

```bash
# Check basic connectivity
ping server.example.com
traceroute server.example.com

# Check if port is reachable
nc -zv server.example.com 22
telnet server.example.com 22
```

### No Route to Host

```
ssh: connect to host server.example.com port 22: No route to host
```

**Solutions:**

```bash
# Check routing
ip route show
ping gateway-ip

# Check DNS
nslookup server.example.com
host server.example.com
```

## Authentication Problems

### Permission Denied (publickey)

```
Permission denied (publickey).
```

**Causes:**
- Key not authorized on server
- Wrong key offered
- Permissions wrong

**Solutions:**

```bash
# Check key is offered
ssh -v user@host 2>&1 | grep "Offering"

# Specify key explicitly
ssh -i ~/.ssh/correct_key user@host

# Check permissions (local)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_ed25519
chmod 644 ~/.ssh/id_ed25519.pub

# Check permissions (server)
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys

# Verify key in authorized_keys
cat ~/.ssh/id_ed25519.pub
# Compare with server's authorized_keys
```

### Permission Denied (password)

```
Permission denied (password).
```

**Causes:**
- Wrong password
- Password auth disabled
- Account locked

**Solutions:**

```bash
# Check if password auth enabled (server)
grep PasswordAuthentication /etc/ssh/sshd_config

# Check account status (server)
passwd -S username

# Unlock account (server)
passwd -u username
```

### Too Many Authentication Failures

```
Received disconnect from server: Too many authentication failures
```

**Causes:**
- SSH agent offers too many keys
- Trying many keys before correct one

**Solutions:**

```bash
# Use specific key only
ssh -o IdentitiesOnly=yes -i ~/.ssh/correct_key user@host

# Clear agent
ssh-add -D

# Or add only needed key
ssh-add ~/.ssh/correct_key
```

## Host Key Problems

### Host Key Verification Failed

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

**Causes:**
- Server reinstalled
- Man-in-the-middle attack (verify!)
- Different server at same IP

**Solutions:**

```bash
# Remove old key (if change is expected)
ssh-keygen -R hostname
ssh-keygen -R ip-address

# Verify new key out-of-band before accepting
# Compare fingerprint with server admin
```

### Host Key Unknown

```
The authenticity of host 'server (192.168.1.1)' can't be established.
```

**Solutions:**

```bash
# First connection - verify fingerprint
# Get fingerprint from server admin

# Or get it yourself if you have other access
ssh-keyscan -t ed25519 server | ssh-keygen -lf -

# For automation (after verifying once)
ssh-keyscan server >> ~/.ssh/known_hosts
```

## Configuration Problems

### Config File Errors

```bash
# Test config syntax
ssh -G hostname

# Check what options are applied
ssh -G hostname | grep -i "option"
```

### Wrong Config Applied

```bash
# Debug which config applies
ssh -vvv hostname 2>&1 | grep "Reading configuration"

# Check specific settings
ssh -G hostname | grep -E "hostname|user|port|identityfile"
```

## Forwarding Problems

### Port Forward Not Working

```bash
# Check server allows forwarding
grep AllowTcpForwarding /etc/ssh/sshd_config
# Must be 'yes'

# Check local binding
ss -tlnp | grep 8080

# Test connection through tunnel
curl localhost:8080
```

### Agent Forwarding Failed

```bash
# Check agent is running
echo $SSH_AUTH_SOCK
ssh-add -l

# Check server allows it
grep AllowAgentForwarding /etc/ssh/sshd_config

# Connect with forwarding
ssh -A user@host
```

## Performance Problems

### Slow Connection

```bash
# Disable DNS lookup (server-side fix)
# /etc/ssh/sshd_config
UseDNS no

# Disable GSSAPI (if not needed)
ssh -o GSSAPIAuthentication=no user@host

# Use faster cipher
ssh -c aes128-gcm@openssh.com user@host
```

### Slow Login

```bash
# Debug timing
ssh -vvv user@host 2>&1 | ts

# Common causes:
# - DNS lookup (UseDNS no)
# - GSSAPI (GSSAPIAuthentication no)
# - PAM delays
```

### Connection Drops

```bash
# Add keep-alive (client)
ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 user@host

# Or in config
Host *
    ServerAliveInterval 60
    ServerAliveCountMax 3

# Server-side
ClientAliveInterval 60
ClientAliveCountMax 3
```

## Server-Side Debugging

### Check Logs

```bash
# Real-time
journalctl -u sshd -f

# Recent entries
journalctl -u sshd --since "10 minutes ago"

# Auth log
tail -f /var/log/auth.log
```

### Enable Debug Logging

```bash
# /etc/ssh/sshd_config
LogLevel DEBUG3

# Restart
systemctl restart sshd

# Watch logs
journalctl -u sshd -f
```

### Test Config

```bash
# Syntax check
sshd -t

# Show effective config
sshd -T

# Test with specific user/address
sshd -T -C user=admin,host=192.168.1.100
```

## Common Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Connection refused | `systemctl start sshd` |
| Permission denied (key) | Check permissions: 700 for .ssh, 600 for keys |
| Too many auth failures | `ssh -o IdentitiesOnly=yes -i key` |
| Host key changed | `ssh-keygen -R hostname` |
| Slow login | `UseDNS no` and `GSSAPIAuthentication no` |
| Connection drops | `ServerAliveInterval 60` |
| Forwarding fails | `AllowTcpForwarding yes` |

## Debug Command

All-in-one diagnostic:

```bash
#!/bin/bash
# ssh-debug.sh
HOST=$1

echo "=== Testing $HOST ==="

echo -e "\n--- Connectivity ---"
ping -c 1 $HOST && echo "Ping: OK" || echo "Ping: FAILED"
nc -zv -w 5 $HOST 22 2>&1

echo -e "\n--- SSH Verbose ---"
ssh -vvv -o BatchMode=yes -o ConnectTimeout=10 $HOST "echo Connected" 2>&1 | grep -E "(debug1:|Authenticated|Permission|Error|Connection)"

echo -e "\n--- Key Debug ---"
ssh-add -l
```

Usage:

```bash
./ssh-debug.sh server.example.com
```
