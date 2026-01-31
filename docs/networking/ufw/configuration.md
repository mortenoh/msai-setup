# UFW Configuration

## Rule Syntax

### Allow Rules

```bash
# Allow by port
sudo ufw allow 22
sudo ufw allow 22/tcp
sudo ufw allow 22/udp

# Allow by service name
sudo ufw allow ssh
sudo ufw allow http
sudo ufw allow https

# Allow port range
sudo ufw allow 6000:6100/tcp

# Allow by app profile
sudo ufw allow OpenSSH
sudo ufw allow 'Apache Full'
```

### Deny Rules

```bash
# Deny port
sudo ufw deny 23

# Deny from IP
sudo ufw deny from 10.0.0.0/8

# Deny specific combination
sudo ufw deny from 192.168.1.100 to any port 22
```

### Reject Rules

Reject sends an ICMP unreachable (client knows immediately):

```bash
sudo ufw reject 23
sudo ufw reject from 10.0.0.1
```

### Limit Rules

Rate limits connections (6 connections per 30 seconds):

```bash
sudo ufw limit ssh
sudo ufw limit 22/tcp
```

## Advanced Rule Syntax

### Source and Destination

```bash
# From specific IP
sudo ufw allow from 192.168.1.100

# From subnet
sudo ufw allow from 192.168.1.0/24

# To specific port from specific IP
sudo ufw allow from 192.168.1.100 to any port 22

# From any to specific destination
sudo ufw allow from any to 192.168.1.100 port 80
```

### Interface Restrictions

```bash
# Allow on specific interface
sudo ufw allow in on eth0 to any port 80
sudo ufw allow in on virbr0

# Output interface
sudo ufw allow out on eth0 to any port 443
```

### Protocol Specification

```bash
# TCP only
sudo ufw allow 80/tcp

# UDP only
sudo ufw allow 53/udp

# Both (default)
sudo ufw allow 80
```

### Comments

```bash
# Add comment to rule
sudo ufw allow 22/tcp comment 'SSH access'

# View comments
sudo ufw status verbose
```

## Managing Rules

### List Rules

```bash
# Basic list
sudo ufw status

# Verbose (shows policy)
sudo ufw status verbose

# Numbered (for deletion)
sudo ufw status numbered
```

### Delete Rules

```bash
# By specification
sudo ufw delete allow 80

# By number
sudo ufw status numbered
sudo ufw delete 3

# Confirm before delete
sudo ufw delete allow ssh
# Deleting:
#  allow 22/tcp
# Proceed with operation (y|n)?
```

### Insert Rules

```bash
# Insert at position
sudo ufw insert 1 deny from 10.0.0.1

# Useful when you need rule to be processed first
```

### Prepend Rules

```bash
# Add to beginning
sudo ufw prepend deny from 10.0.0.1
```

## Configuration Files

### /etc/default/ufw

Main UFW settings:

```bash
# Enable/disable
ENABLED=yes

# Default policies
DEFAULT_INPUT_POLICY="DROP"
DEFAULT_OUTPUT_POLICY="ACCEPT"
DEFAULT_FORWARD_POLICY="DROP"
DEFAULT_APPLICATION_POLICY="SKIP"

# IPv6 support
IPV6=yes

# Manage built-in chains
MANAGE_BUILTINS=no

# IPT modules
IPT_MODULES="nf_conntrack_ftp nf_conntrack_tftp"
```

### /etc/ufw/ufw.conf

Runtime configuration:

```bash
# Enable UFW
ENABLED=yes

# Logging level
LOGLEVEL=low
```

### /etc/ufw/sysctl.conf

Kernel parameters UFW sets:

```bash
# Forwarding
net/ipv4/ip_forward=0

# Source address verification
net/ipv4/conf/all/rp_filter=1
net/ipv4/conf/default/rp_filter=1

# Don't accept redirects
net/ipv4/conf/all/accept_redirects=0
net/ipv4/conf/all/send_redirects=0

# Log martians
net/ipv4/conf/all/log_martians=1
```

!!! note
    These are applied when UFW starts, potentially overriding other settings.

## Editing before.rules

### Adding NAT Rules

```bash
# /etc/ufw/before.rules

# Add NAT section at the BEGINNING of the file
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# Masquerade for VM network
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE

# Port forwarding
-A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.122.10:80

COMMIT

# Existing *filter section follows...
```

### Adding Custom Filter Rules

```bash
# /etc/ufw/before.rules

# In the *filter section, before the COMMIT

# Allow all on VM bridge
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# Allow specific forward
-A ufw-before-forward -s 192.168.122.0/24 -d 192.168.1.0/24 -j ACCEPT
```

### Complete before.rules Example

```bash
#
# /etc/ufw/before.rules
#
# Rules that should be run before the ufw command line added rules.

# NAT table rules
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# NAT for VM network
-A POSTROUTING -s 192.168.122.0/24 -o eth0 -j MASQUERADE

# NAT for Docker (if iptables: false)
# -A POSTROUTING -s 172.17.0.0/16 ! -o docker0 -j MASQUERADE

# Port forwarding examples
# -A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to 192.168.122.10:22

COMMIT

# Filter table rules
*filter
:ufw-before-input - [0:0]
:ufw-before-output - [0:0]
:ufw-before-forward - [0:0]
:ufw-not-local - [0:0]

# Allow all on loopback
-A ufw-before-input -i lo -j ACCEPT
-A ufw-before-output -o lo -j ACCEPT

# Quickly process established connections
-A ufw-before-input -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-output -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT
-A ufw-before-forward -m conntrack --ctstate RELATED,ESTABLISHED -j ACCEPT

# Drop invalid
-A ufw-before-input -m conntrack --ctstate INVALID -j ufw-logging-deny
-A ufw-before-input -m conntrack --ctstate INVALID -j DROP

# Allow ICMP
-A ufw-before-input -p icmp --icmp-type destination-unreachable -j ACCEPT
-A ufw-before-input -p icmp --icmp-type time-exceeded -j ACCEPT
-A ufw-before-input -p icmp --icmp-type parameter-problem -j ACCEPT
-A ufw-before-input -p icmp --icmp-type echo-request -j ACCEPT

# Allow DHCP client
-A ufw-before-input -p udp --sport 67 --dport 68 -j ACCEPT

# VM bridge forwarding (libvirt)
-A ufw-before-forward -i virbr0 -j ACCEPT
-A ufw-before-forward -o virbr0 -j ACCEPT

# Docker bridge forwarding (if needed)
# -A ufw-before-forward -i docker0 -j ACCEPT
# -A ufw-before-forward -o docker0 -j ACCEPT

# ufw-not-local
-A ufw-before-input -j ufw-not-local
-A ufw-not-local -m addrtype --dst-type LOCAL -j RETURN
-A ufw-not-local -m addrtype --dst-type MULTICAST -j RETURN
-A ufw-not-local -m addrtype --dst-type BROADCAST -j RETURN
-A ufw-not-local -m limit --limit 3/min --limit-burst 10 -j ufw-logging-deny
-A ufw-not-local -j DROP

# Allow mDNS
-A ufw-before-input -p udp -d 224.0.0.251 --dport 5353 -j ACCEPT

# Allow UPnP
-A ufw-before-input -p udp -d 239.255.255.250 --dport 1900 -j ACCEPT

COMMIT
```

## Applying Changes

```bash
# Reload after editing files
sudo ufw reload

# Or restart
sudo ufw disable && sudo ufw enable

# Verify rules loaded
sudo ufw status verbose
sudo iptables -L -n -v
```

## Backup and Restore

### Backup Rules

```bash
# Backup user rules
sudo cp /etc/ufw/user.rules /etc/ufw/user.rules.backup
sudo cp /etc/ufw/user6.rules /etc/ufw/user6.rules.backup

# Backup all config
sudo cp -r /etc/ufw /etc/ufw.backup

# Export iptables (more complete)
sudo iptables-save > ~/iptables-backup.rules
```

### Restore Rules

```bash
# Restore UFW config
sudo cp -r /etc/ufw.backup/* /etc/ufw/
sudo ufw reload

# Or restore iptables directly
sudo iptables-restore < ~/iptables-backup.rules
```

## Common Configurations

### Basic Server

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw enable
```

### Web Server

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'  # 80, 443
sudo ufw enable
```

### Database Server (Internal Only)

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 5432  # PostgreSQL
sudo ufw allow from 192.168.1.0/24 to any port 3306  # MySQL
sudo ufw enable
```

### Home Server with VMs

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow from 192.168.1.0/24 to any port 8080  # Web service
sudo ufw allow from 192.168.1.0/24 to any port 32400 # Plex

# Edit before.rules for VM NAT (see above)
sudo ufw reload
sudo ufw enable
```
