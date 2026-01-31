# WireGuard Basics

## What is WireGuard?

WireGuard is a modern VPN protocol that Tailscale uses as its underlying transport. It's known for being fast, secure, and simple.

## WireGuard vs Tailscale

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    WireGuard vs Tailscale                                    │
│                                                                              │
│   WireGuard (protocol)              Tailscale (product)                     │
│   ─────────────────────────────────────────────────────────────────         │
│   • Encryption & tunneling          • Uses WireGuard for tunnels            │
│   • Manual key exchange             • Automatic key exchange                │
│   • Manual IP assignment            • Automatic IP assignment               │
│   • Manual peer configuration       • Automatic peer discovery              │
│   • No NAT traversal                • Built-in NAT traversal                │
│   • No access controls              • ACL-based access control              │
│   • No DNS management               • MagicDNS included                     │
│                                                                              │
│   WireGuard = Engine                Tailscale = Complete Car                │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## WireGuard Cryptography

### Cipher Suite

WireGuard uses modern, well-audited cryptographic primitives:

| Component | Algorithm | Purpose |
|-----------|-----------|---------|
| Key exchange | Curve25519 | Elliptic curve Diffie-Hellman |
| Encryption | ChaCha20-Poly1305 | Authenticated encryption |
| Hashing | BLAKE2s | Fast cryptographic hash |
| Key derivation | HKDF | Deriving session keys |

### Key Pair

Each WireGuard interface has a key pair:

```bash
# Generate WireGuard keys (for reference - Tailscale does this automatically)
wg genkey | tee privatekey | wg pubkey > publickey
```

Tailscale manages keys automatically:

```bash
# View Tailscale's WireGuard interface
sudo wg show tailscale0

# Example output:
# interface: tailscale0
#   public key: ABC123...
#   private key: (hidden)
#   listening port: 41641
#
# peer: DEF456...
#   endpoint: 203.0.113.1:41641
#   allowed ips: 100.100.100.2/32
#   latest handshake: 42 seconds ago
#   transfer: 1.23 MiB received, 456.78 KiB sent
```

## WireGuard Interface

Tailscale creates a virtual network interface:

```bash
# View the interface
ip addr show tailscale0

# Example output:
# tailscale0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1280
#     inet 100.100.100.1/32 scope global tailscale0
```

### Interface Properties

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    tailscale0 Interface                                      │
│                                                                              │
│   Property          Value              Notes                                │
│   ─────────────────────────────────────────────────────────────────         │
│   Type              WireGuard          Virtual tunnel interface             │
│   IP Address        100.x.x.x/32       Tailscale-assigned                   │
│   MTU               1280               Allows for encapsulation             │
│   Flags             POINTOPOINT        Point-to-point tunnel                │
│   Protocol          UDP                WireGuard uses UDP                   │
│   Port              41641 (typical)    Can vary                             │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

## WireGuard Concepts

### Peers

In WireGuard, each device you can connect to is a "peer":

```bash
# List WireGuard peers
sudo wg show tailscale0 peers

# Detailed peer info
sudo wg show tailscale0
```

### Allowed IPs

Each peer has "allowed IPs" - the IP ranges that can be routed through that peer:

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                    Allowed IPs Example                                       │
│                                                                              │
│   Peer: server.tailnet.ts.net                                               │
│   ─────────────────────────────────────────────────────────────────         │
│   Allowed IPs:                                                               │
│     • 100.100.100.2/32    → Server's Tailscale IP                          │
│     • 192.168.10.0/24     → Subnet router for home network                 │
│                                                                              │
│   Traffic to these IPs goes through this peer's WireGuard tunnel            │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Endpoints

The endpoint is the public IP:port where a peer can be reached:

```bash
# View peer endpoints
sudo wg show tailscale0 endpoints
```

Endpoints can change as devices move networks - Tailscale handles this automatically.

### Handshakes

WireGuard performs periodic handshakes to:
- Verify peer is still reachable
- Rotate session keys
- Update endpoint if changed

```bash
# Check handshake status
sudo wg show tailscale0 latest-handshakes

# Handshakes occur every 2 minutes when active
# Stale handshake (>5 min) may indicate connection issues
```

## WireGuard Performance

### Why WireGuard is Fast

1. **Minimal code**: ~4,000 lines vs 100,000+ for OpenVPN
2. **Kernel implementation**: Runs in kernel space
3. **Modern crypto**: ChaCha20 is very fast
4. **UDP-based**: Lower overhead than TCP

### Performance Comparison

| VPN Protocol | Typical Overhead | CPU Usage |
|--------------|------------------|-----------|
| WireGuard | ~3% | Very low |
| OpenVPN (UDP) | ~15-20% | Moderate |
| OpenVPN (TCP) | ~20-30% | Higher |
| IPsec | ~10-15% | Moderate |

### Benchmarking

```bash
# Test throughput through Tailscale
iperf3 -s  # On server

# On client
iperf3 -c 100.100.100.2

# Compare with direct connection
iperf3 -c server-local-ip
```

## Raw WireGuard vs Tailscale

### Manual WireGuard Setup

What you'd need to do manually:

```bash
# 1. Generate keys on each device
wg genkey | tee /etc/wireguard/private.key | wg pubkey > /etc/wireguard/public.key

# 2. Create config on each device
cat > /etc/wireguard/wg0.conf << 'EOF'
[Interface]
PrivateKey = <your-private-key>
Address = 10.0.0.1/24
ListenPort = 51820

[Peer]
PublicKey = <peer-public-key>
AllowedIPs = 10.0.0.2/32
Endpoint = peer.example.com:51820
PersistentKeepalive = 25
EOF

# 3. Exchange public keys between all devices
# 4. Configure firewall rules
# 5. Set up DNS manually
# 6. Handle key rotation manually
# 7. Configure each new peer on all existing devices
```

### Tailscale Setup

```bash
# 1. Install and authenticate (that's it)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

## Debugging WireGuard Layer

### View WireGuard Status

```bash
# Full WireGuard status
sudo wg show tailscale0

# Just peers
sudo wg show tailscale0 peers

# Transfer statistics
sudo wg show tailscale0 transfer

# Latest handshakes
sudo wg show tailscale0 latest-handshakes
```

### Common Issues

| Symptom | WireGuard Cause | Tailscale Fix |
|---------|-----------------|---------------|
| No handshake | Endpoint unreachable | Check `tailscale netcheck` |
| Stale handshake | NAT timeout | Tailscale keepalive handles this |
| No transfer | Allowed IPs wrong | Tailscale manages automatically |
| High latency | Using DERP relay | Check `tailscale status` for relay |

### Packet Capture

```bash
# Capture WireGuard traffic (encrypted)
sudo tcpdump -i eth0 udp port 41641

# Capture decrypted traffic on tunnel
sudo tcpdump -i tailscale0
```

## Security Considerations

### WireGuard Security Properties

- **Forward secrecy**: Compromised key doesn't expose past traffic
- **Replay protection**: Built-in via nonce
- **DoS resistance**: Minimal state before authentication
- **Stealth**: Silent to unauthenticated packets

### Key Storage

```bash
# Tailscale stores keys securely
ls -la /var/lib/tailscale/

# Never share these files:
# - tailscaled.state (contains private keys)
```

### Audit Logging

```bash
# WireGuard is stateless - minimal logging
# Tailscale adds audit logging in admin console
```
