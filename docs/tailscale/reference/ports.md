# Network Ports

## Tailscale Network Requirements

### Outbound Ports (Required)

These ports must be allowed outbound for Tailscale to function:

| Port | Protocol | Destination | Purpose |
|------|----------|-------------|---------|
| 41641 | UDP | Any | WireGuard (peer-to-peer) |
| 443 | TCP | Tailscale servers | Control plane, DERP fallback |
| 3478 | UDP | STUN servers | NAT discovery |

### Inbound Ports (Recommended)

Opening inbound improves performance:

| Port | Protocol | Purpose |
|------|----------|---------|
| 41641 | UDP | Direct peer connections |

!!! info "Without Inbound"
    Tailscale works without inbound ports by using DERP relays, but with higher latency.

## Port Details

### WireGuard (UDP 41641)

Primary data transport:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│   Your Device                                              Peer Device      │
│   ┌─────────────┐        UDP 41641                   ┌─────────────┐       │
│   │ WireGuard   │◄──────────────────────────────────►│ WireGuard   │       │
│   │ :41641      │        encrypted                   │ :41641      │       │
│   └─────────────┘                                    └─────────────┘       │
│                                                                              │
│   Note: Port may vary. 41641 is default, not fixed.                        │
└──────────────────────────────────────────────────────────────────────────────┘
```

- Encrypted peer-to-peer traffic
- Port may vary per device
- Firewall should allow any source port

### Control Plane (TCP 443)

Communication with Tailscale servers:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│   Your Device                                    Tailscale Servers          │
│   ┌─────────────┐        TCP 443                 ┌───────────────────┐     │
│   │ tailscaled  │───────────────────────────────►│ controlplane.     │     │
│   └─────────────┘        HTTPS                   │ tailscale.com     │     │
│                                                   └───────────────────┘     │
│   Used for:                                                                 │
│   • Authentication                                                          │
│   • Key exchange                                                            │
│   • Configuration sync                                                      │
│   • DERP relay fallback                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### STUN (UDP 3478)

NAT discovery:

```bash
# STUN servers used
stun.tailscale.com:3478
```

Helps determine:
- Your public IP
- NAT type
- Port mapping

## DERP Relay Servers

When direct connection fails, traffic routes through DERP:

| Region | Server |
|--------|--------|
| NYC | derp1.tailscale.com |
| SFO | derp2.tailscale.com |
| AMS | derp3.tailscale.com |
| ... | (many more globally) |

DERP uses:
- TCP 443 (HTTPS)
- TCP 80 (HTTP fallback)

## Firewall Configuration

### UFW

```bash
# Outbound (usually default allow)
sudo ufw allow out 41641/udp
sudo ufw allow out 443/tcp
sudo ufw allow out 3478/udp

# Inbound (for better direct connections)
sudo ufw allow 41641/udp
```

### iptables

```bash
# Outbound
sudo iptables -A OUTPUT -p udp --dport 41641 -j ACCEPT
sudo iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT
sudo iptables -A OUTPUT -p udp --dport 3478 -j ACCEPT

# Inbound
sudo iptables -A INPUT -p udp --dport 41641 -j ACCEPT
```

### nftables

```bash
# /etc/nftables.conf
table inet filter {
    chain input {
        udp dport 41641 accept
    }
    chain output {
        udp dport 41641 accept
        tcp dport 443 accept
        udp dport 3478 accept
    }
}
```

### firewalld

```bash
# Outbound (usually open)
sudo firewall-cmd --permanent --add-port=41641/udp

# Inbound
sudo firewall-cmd --permanent --add-port=41641/udp
sudo firewall-cmd --reload
```

### Windows Firewall

```powershell
# Allow Tailscale
New-NetFirewallRule -DisplayName "Tailscale UDP" -Direction Inbound -Protocol UDP -LocalPort 41641 -Action Allow
```

## Corporate Firewall Requirements

### Minimum (DERP relay only)

- TCP 443 outbound to *.tailscale.com
- Performance will be limited

### Recommended

- UDP 41641 outbound to any
- UDP 3478 outbound to stun.tailscale.com
- TCP 443 outbound to *.tailscale.com

### Best Performance

Add inbound:
- UDP 41641 from any (for direct connections)

## Cloud Provider Security Groups

### AWS

```hcl
# Terraform example
resource "aws_security_group_rule" "tailscale_udp" {
  type              = "ingress"
  from_port         = 41641
  to_port           = 41641
  protocol          = "udp"
  cidr_blocks       = ["0.0.0.0/0"]
  security_group_id = aws_security_group.instance.id
}
```

### GCP

```yaml
# Firewall rule
name: allow-tailscale
network: default
direction: INGRESS
allowed:
  - IPProtocol: udp
    ports:
      - "41641"
sourceRanges:
  - "0.0.0.0/0"
```

### Azure

```json
{
  "name": "Tailscale-UDP",
  "properties": {
    "protocol": "Udp",
    "sourcePortRange": "*",
    "destinationPortRange": "41641",
    "sourceAddressPrefix": "*",
    "destinationAddressPrefix": "*",
    "access": "Allow",
    "priority": 100,
    "direction": "Inbound"
  }
}
```

## Verifying Connectivity

```bash
# Check what's working
tailscale netcheck

# Output shows:
# * UDP: true/false
# * IPv4/IPv6: yes/no
# * Nearest DERP
# * Port mapping: UPnP/NAT-PMP/none
```

## Troubleshooting Port Issues

### UDP Blocked

```bash
# Symptom
tailscale netcheck
# UDP: false

# Solution
# Open UDP 41641 outbound on firewall
```

### Always Using DERP

```bash
# Symptom
tailscale status
# Shows "relay" for all peers

# Solutions
# 1. Open UDP 41641 inbound
# 2. Check for symmetric NAT
tailscale netcheck | grep MappingVaries
```

### Can't Reach Control Plane

```bash
# Symptom
# Can't authenticate

# Test
curl -I https://controlplane.tailscale.com/

# Solution
# Ensure TCP 443 outbound is allowed
```
