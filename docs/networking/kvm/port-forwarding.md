# VM Port Forwarding

## Overview

With NAT networking, VMs have private IPs not directly accessible from outside. Port forwarding allows external access to VM services.

## Methods

| Method | Use Case | Complexity |
|--------|----------|------------|
| iptables DNAT | Simple forwarding | Low |
| UFW before.rules | Integrated with UFW | Medium |
| libvirt hooks | Automatic with VM lifecycle | Medium |
| SSH tunneling | Temporary access | Low |

## Method 1: iptables DNAT

### Basic Port Forward

```bash
# Forward host:2222 to VM:22
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 2222 \
    -j DNAT --to-destination 192.168.122.10:22

# Allow forwarded traffic
sudo iptables -A FORWARD -p tcp -d 192.168.122.10 --dport 22 \
    -m conntrack --ctstate NEW -j ACCEPT
```

### Multiple Ports

```bash
# HTTP
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8080 \
    -j DNAT --to-destination 192.168.122.10:80

# HTTPS
sudo iptables -t nat -A PREROUTING -i eth0 -p tcp --dport 8443 \
    -j DNAT --to-destination 192.168.122.10:443

# Forward rules
sudo iptables -A FORWARD -p tcp -d 192.168.122.10 --dport 80 -j ACCEPT
sudo iptables -A FORWARD -p tcp -d 192.168.122.10 --dport 443 -j ACCEPT
```

### UDP Port Forward

```bash
# DNS
sudo iptables -t nat -A PREROUTING -i eth0 -p udp --dport 5353 \
    -j DNAT --to-destination 192.168.122.10:53

sudo iptables -A FORWARD -p udp -d 192.168.122.10 --dport 53 -j ACCEPT
```

### Remove Forward

```bash
# Remove NAT rule
sudo iptables -t nat -D PREROUTING -i eth0 -p tcp --dport 2222 \
    -j DNAT --to-destination 192.168.122.10:22

# Remove forward rule
sudo iptables -D FORWARD -p tcp -d 192.168.122.10 --dport 22 \
    -m conntrack --ctstate NEW -j ACCEPT
```

## Method 2: UFW before.rules

### Edit before.rules

```bash
# /etc/ufw/before.rules

# Add at the very beginning
*nat
:PREROUTING ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]

# VM NAT (existing)
-A POSTROUTING -s 192.168.122.0/24 ! -d 192.168.122.0/24 -o eth0 -j MASQUERADE

# Port forwarding
-A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to-destination 192.168.122.10:22
-A PREROUTING -i eth0 -p tcp --dport 8080 -j DNAT --to-destination 192.168.122.10:80
-A PREROUTING -i eth0 -p tcp --dport 3389 -j DNAT --to-destination 192.168.122.20:3389

COMMIT

*filter
# ... existing content ...

# Add before COMMIT in filter section
# Allow forwarded traffic to VMs
-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT
-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 80 -j ACCEPT
-A ufw-before-forward -p tcp -d 192.168.122.20 --dport 3389 -j ACCEPT

COMMIT
```

### Apply

```bash
sudo ufw reload
```

### Verify

```bash
sudo iptables -t nat -L PREROUTING -n -v
sudo iptables -L ufw-before-forward -n -v
```

## Method 3: libvirt Hooks

Automatically add/remove rules when VM starts/stops.

### Create Hook Script

```bash
#!/bin/bash
# /etc/libvirt/hooks/qemu

VM_NAME="$1"
ACTION="$2"

# Configuration
declare -A VM_FORWARDS
VM_FORWARDS["webserver"]="eth0:8080:192.168.122.10:80 eth0:8443:192.168.122.10:443"
VM_FORWARDS["windows"]="eth0:3389:192.168.122.20:3389"

add_forward() {
    local iface=$1 host_port=$2 vm_ip=$3 vm_port=$4

    iptables -t nat -A PREROUTING -i "$iface" -p tcp --dport "$host_port" \
        -j DNAT --to-destination "$vm_ip:$vm_port"
    iptables -A FORWARD -p tcp -d "$vm_ip" --dport "$vm_port" -j ACCEPT
}

remove_forward() {
    local iface=$1 host_port=$2 vm_ip=$3 vm_port=$4

    iptables -t nat -D PREROUTING -i "$iface" -p tcp --dport "$host_port" \
        -j DNAT --to-destination "$vm_ip:$vm_port"
    iptables -D FORWARD -p tcp -d "$vm_ip" --dport "$vm_port" -j ACCEPT
}

if [[ -n "${VM_FORWARDS[$VM_NAME]}" ]]; then
    for forward in ${VM_FORWARDS[$VM_NAME]}; do
        IFS=':' read -r iface host_port vm_ip vm_port <<< "$forward"

        case "$ACTION" in
            started)
                add_forward "$iface" "$host_port" "$vm_ip" "$vm_port"
                ;;
            stopped)
                remove_forward "$iface" "$host_port" "$vm_ip" "$vm_port"
                ;;
        esac
    done
fi
```

### Make Executable

```bash
sudo chmod +x /etc/libvirt/hooks/qemu
sudo systemctl restart libvirtd
```

### Test

```bash
# Start VM
virsh start webserver

# Check rules
sudo iptables -t nat -L PREROUTING -n

# Stop VM
virsh shutdown webserver

# Rules should be gone
sudo iptables -t nat -L PREROUTING -n
```

## Method 4: SSH Tunneling

For temporary access without modifying firewall.

### Forward Local Port to VM

```bash
# On your workstation
ssh -L 8080:192.168.122.10:80 user@host

# Access VM's port 80 at localhost:8080
curl http://localhost:8080
```

### Remote Forward (VM to Outside)

```bash
# On host
ssh -R 8080:192.168.122.10:80 user@external-server

# external-server:8080 now reaches VM:80
```

### Persistent Tunnel with autossh

```bash
autossh -M 0 -f -N -L 8080:192.168.122.10:80 user@host
```

## Port Forwarding Scenarios

### Gaming VM (Windows)

```bash
# RDP
-A PREROUTING -i eth0 -p tcp --dport 3389 -j DNAT --to 192.168.122.20:3389

# Steam Remote Play
-A PREROUTING -i eth0 -p tcp --dport 27036 -j DNAT --to 192.168.122.20:27036
-A PREROUTING -i eth0 -p udp --dport 27031:27036 -j DNAT --to 192.168.122.20

# Parsec (UDP)
-A PREROUTING -i eth0 -p udp --dport 8000:8010 -j DNAT --to 192.168.122.20
```

### Web Server VM

```bash
-A PREROUTING -i eth0 -p tcp --dport 80 -j DNAT --to 192.168.122.10:80
-A PREROUTING -i eth0 -p tcp --dport 443 -j DNAT --to 192.168.122.10:443
```

### Development VM

```bash
# SSH
-A PREROUTING -i eth0 -p tcp --dport 2222 -j DNAT --to 192.168.122.30:22

# Application ports (bind to localhost for security)
-A PREROUTING -i lo -p tcp --dport 3000 -j DNAT --to 192.168.122.30:3000
-A PREROUTING -i lo -p tcp --dport 5432 -j DNAT --to 192.168.122.30:5432
```

## Restricting Access

### Only From Specific IPs

```bash
-A PREROUTING -i eth0 -s 192.168.1.0/24 -p tcp --dport 3389 \
    -j DNAT --to 192.168.122.20:3389

# Or in FORWARD chain
-A ufw-before-forward -s 192.168.1.0/24 -p tcp -d 192.168.122.20 --dport 3389 -j ACCEPT
-A ufw-before-forward -p tcp -d 192.168.122.20 --dport 3389 -j DROP
```

### Rate Limiting

```bash
-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 \
    -m conntrack --ctstate NEW \
    -m recent --name SSH --set

-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 \
    -m conntrack --ctstate NEW \
    -m recent --name SSH --update --seconds 60 --hitcount 4 -j DROP

-A ufw-before-forward -p tcp -d 192.168.122.10 --dport 22 -j ACCEPT
```

## Troubleshooting

### Forward Not Working

```bash
# Check NAT rule exists
sudo iptables -t nat -L PREROUTING -n -v | grep 2222

# Check FORWARD rule
sudo iptables -L FORWARD -n -v | grep 192.168.122.10

# Check IP forwarding enabled
cat /proc/sys/net/ipv4/ip_forward

# Check VM is reachable from host
ping 192.168.122.10
nc -zv 192.168.122.10 22
```

### Connection Refused

```bash
# Service running in VM?
virsh console vmname
# Then: systemctl status sshd

# VM firewall blocking?
# In VM: sudo ufw status
```

### Hairpin NAT (Internal Access via External IP)

To access VM via external IP from internal network:

```bash
# Add hairpin NAT
-A POSTROUTING -s 192.168.122.0/24 -d 192.168.122.10 -p tcp --dport 80 -j MASQUERADE
```
