# Networking Concepts

## Tailscale IP Addressing

### CGNAT Range

Tailscale assigns IP addresses from the 100.64.0.0/10 range (CGNAT - Carrier-Grade NAT):

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Tailscale IP Space                                        │
│                                                                              │
│   100.64.0.0/10                                                             │
│   ├── 100.64.0.0 - 100.127.255.255                                         │
│   ├── ~4 million available IPs                                              │
│   └── Reserved for CGNAT (RFC 6598)                                         │
│                                                                              │
│   Why CGNAT?                                                                 │
│   • Unlikely to conflict with your existing networks                        │
│   • Not routable on the internet                                            │
│   • Distinct from RFC 1918 private ranges                                   │
│                                                                              │
│   Common Private Ranges (NOT used by Tailscale):                            │
│   • 10.0.0.0/8       (16 million IPs)                                      │
│   • 172.16.0.0/12    (1 million IPs)                                       │
│   • 192.168.0.0/16   (65,536 IPs)                                          │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### IP Assignment

Each device gets a unique, stable IP:

```bash
# View your Tailscale IP
tailscale ip -4

# View all your IPs (v4 and v6)
tailscale ip

# Example output:
# 100.100.100.1
# fd7a:115c:a1e0:ab12:4843:cd96:6264:6401
```

### IPv6 Support

Tailscale also assigns IPv6 addresses:

```bash
# IPv6 address format
fd7a:115c:a1e0:<tailnet-id>:<device-specific>

# View IPv6
tailscale ip -6
```

## NAT Traversal

### The NAT Problem

Most devices are behind NAT, making direct connections difficult:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    NAT Challenge                                             │
│                                                                              │
│   Device A (Home)                        Device B (Office)                  │
│   ┌─────────────────┐                    ┌─────────────────┐                │
│   │ Private IP:     │                    │ Private IP:     │                │
│   │ 192.168.1.50    │                    │ 10.0.0.25       │                │
│   └────────┬────────┘                    └────────┬────────┘                │
│            │                                      │                          │
│   ┌────────┴────────┐                    ┌────────┴────────┐                │
│   │   Home Router   │                    │  Office Router  │                │
│   │   NAT Gateway   │                    │   NAT Gateway   │                │
│   │                 │                    │                 │                │
│   │ Public IP:      │                    │ Public IP:      │                │
│   │ 203.0.113.1     │                    │ 198.51.100.1    │                │
│   └────────┬────────┘                    └────────┬────────┘                │
│            │                                      │                          │
│            └──────────── Internet ───────────────┘                          │
│                                                                              │
│   Problem: Neither device can directly reach the other's private IP         │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### NAT Types

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    NAT Types                                                 │
│                                                                              │
│   Type              Behavior                      Direct Connection?        │
│   ─────────────────────────────────────────────────────────────────         │
│   Full Cone         Any external host can         Easy ✓                    │
│                     reach mapped port                                        │
│                                                                              │
│   Restricted        Only hosts we've sent         Possible ✓                │
│   Cone              packets to can reply                                     │
│                                                                              │
│   Port Restricted   Only specific host:port       Harder ✓                  │
│   Cone              combinations allowed                                     │
│                                                                              │
│   Symmetric         Different mapping for         Very hard ✗               │
│                     each destination              (needs relay)             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### How Tailscale Traverses NAT

```bash
# Check your NAT type
tailscale netcheck
```

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    NAT Traversal Steps                                       │
│                                                                              │
│   1. STUN Discovery                                                          │
│      Device asks STUN server: "What's my public IP:port?"                   │
│                                                                              │
│   2. Exchange via Coordination Server                                        │
│      Devices share their discovered endpoints                                │
│                                                                              │
│   3. Hole Punching                                                           │
│      Both devices simultaneously send packets to each other                  │
│      NAT creates bidirectional mapping                                       │
│                                                                              │
│   4. Direct Connection (or DERP fallback)                                   │
│      If hole punch succeeds → direct WireGuard tunnel                       │
│      If it fails → traffic relayed via DERP                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## DERP Relays

### What is DERP?

DERP (Designated Encrypted Relay for Packets) is Tailscale's relay system:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    DERP Architecture                                         │
│                                                                              │
│   When direct connection fails:                                              │
│                                                                              │
│   Device A                    DERP Server                    Device B       │
│      │                            │                              │          │
│      │ ──── encrypted ──────────► │                              │          │
│      │      WireGuard packet      │ ──── encrypted ────────────► │          │
│      │                            │      WireGuard packet        │          │
│      │ ◄───────────────────────── │ ◄──────────────────────────  │          │
│      │                            │                              │          │
│                                                                              │
│   • DERP only sees encrypted WireGuard packets                              │
│   • Cannot decrypt traffic (no access to WireGuard keys)                    │
│   • Simply forwards packets between clients                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### DERP Regions

Tailscale operates DERP servers globally:

```bash
# View DERP regions and latency
tailscale netcheck

# Example output:
#     * DERP latency:
#         - nyc: 15.2ms
#         - sfo: 45.1ms
#         - ams: 85.3ms
#         - ...
```

### Direct vs Relayed

```bash
# Check connection type
tailscale status

# Example output:
# 100.100.100.1  my-laptop     macOS   -
# 100.100.100.2  my-server     linux   direct 203.0.113.1:41641
# 100.100.100.3  my-phone      iOS     relay "nyc"
```

- **direct**: Peer-to-peer WireGuard connection
- **relay "region"**: Traffic going through DERP

### Checking Path

```bash
# Detailed path information
tailscale ping my-server

# Example output:
# pong from my-server (100.100.100.2) via 203.0.113.1:41641 in 12ms
# (direct connection)

# Or if relayed:
# pong from my-server (100.100.100.2) via DERP(nyc) in 45ms
```

## DNS and MagicDNS

### MagicDNS Names

Tailscale provides automatic DNS:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    MagicDNS Naming                                           │
│                                                                              │
│   Format: <device-name>.<tailnet-name>.ts.net                               │
│                                                                              │
│   Examples:                                                                  │
│   • my-server.tailnet.ts.net                                               │
│   • laptop.tailnet.ts.net                                                  │
│   • phone.tailnet.ts.net                                                   │
│                                                                              │
│   Short names also work within tailnet:                                     │
│   • ssh my-server                                                           │
│   • ping laptop                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### DNS Resolution

```bash
# Resolve MagicDNS name
tailscale status --json | jq '.Self.DNSName'

# Query DNS
dig my-server.tailnet.ts.net

# Short names work
ping my-server
```

### Split DNS

Route specific domains through Tailscale:

```bash
# In admin console, configure split DNS:
# corp.example.com → Use nameserver at 100.100.100.10
```

## Subnet Routes

### Advertising Subnets

Make entire networks accessible through Tailscale:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Subnet Router                                             │
│                                                                              │
│   Tailscale Network                   Physical Network                      │
│   ─────────────────                   ────────────────                      │
│                                                                              │
│   ┌──────────┐                        ┌──────────────────────────┐          │
│   │ Laptop   │                        │  Home Network            │          │
│   │ 100.x.1  │────┐                   │  192.168.1.0/24          │          │
│   └──────────┘    │                   │                          │          │
│                   │    ┌──────────┐   │  ┌────────┐ ┌────────┐  │          │
│   ┌──────────┐    ├───►│ Subnet   │───┼─►│ NAS    │ │ Camera │  │          │
│   │ Phone    │────┤    │ Router   │   │  │ .100   │ │ .150   │  │          │
│   │ 100.x.2  │    │    │ 100.x.10 │   │  └────────┘ └────────┘  │          │
│   └──────────┘    │    └──────────┘   │                          │          │
│                   │                   └──────────────────────────┘          │
│   ┌──────────┐    │                                                         │
│   │ Remote   │────┘    Traffic to 192.168.1.x routed through               │
│   │ Server   │         subnet router, no Tailscale needed on               │
│   │ 100.x.3  │         NAS or Camera                                        │
│   └──────────┘                                                              │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

```bash
# Advertise a subnet
sudo tailscale up --advertise-routes=192.168.1.0/24

# Then approve in admin console
```

## Exit Nodes

### Internet Routing

Route all internet traffic through a Tailscale device:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Exit Node                                                 │
│                                                                              │
│   Without Exit Node              With Exit Node                             │
│   ─────────────────              ──────────────                             │
│                                                                              │
│   You ─► Local ISP ─► Internet   You ─► Tailscale ─► Exit Node ─► Internet │
│          (your IP)                                    (exit node's IP)      │
│                                                                              │
│   Use cases:                                                                 │
│   • Privacy when on untrusted WiFi                                          │
│   • Access region-locked content                                            │
│   • Secure browsing through trusted network                                 │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

```bash
# Advertise as exit node
sudo tailscale up --advertise-exit-node

# Use an exit node
sudo tailscale up --exit-node=my-server
```

## Firewall Considerations

### Required Ports

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Firewall Requirements                                     │
│                                                                              │
│   Outbound (required):                                                       │
│   • UDP/41641: WireGuard (direct connections)                               │
│   • TCP/443: HTTPS (coordination server, DERP fallback)                     │
│   • UDP/3478: STUN (NAT discovery)                                          │
│                                                                              │
│   Inbound (optional, improves connectivity):                                 │
│   • UDP/41641: Allows incoming direct connections                           │
│                                                                              │
│   Note: Tailscale works without any inbound ports open                      │
│   (uses DERP relay as fallback)                                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### UFW Example

```bash
# Allow Tailscale outbound (usually default)
ufw allow out 41641/udp
ufw allow out 443/tcp
ufw allow out 3478/udp

# Allow inbound for better direct connections
ufw allow 41641/udp
```

## Network Performance

### Checking Connection Quality

```bash
# Full network check
tailscale netcheck

# Ping specific peer
tailscale ping my-server -c 10

# Check for relay usage
tailscale status
```

### Optimizing Performance

| Issue | Cause | Solution |
|-------|-------|----------|
| High latency | Using DERP relay | Open UDP/41641 inbound |
| Connection drops | NAT timeout | Tailscale handles keepalive |
| Slow throughput | MTU issues | Usually auto-configured |
| Intermittent | Symmetric NAT | May need relay, unavoidable |
