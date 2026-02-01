# External Access

Methods for accessing your homelab services from outside your local network.

## Access Methods Comparison

| Method | Complexity | Security | Latency | Use Case |
|--------|------------|----------|---------|----------|
| **Tailscale** | Low | Excellent | Low | Primary recommendation |
| **VPN (WireGuard)** | Medium | Excellent | Low | Self-hosted alternative |
| **Reverse Proxy + DDNS** | Medium | Good | Lowest | Public services |
| **Port Forwarding** | Low | Poor | Lowest | Not recommended |
| **Cloudflare Tunnel** | Medium | Good | Variable | No open ports |

## Decision Flowchart

```
Do you need public access (anyone on internet)?
│
├── YES
│   │
│   └── Do you own a domain?
│       │
│       ├── YES → Reverse Proxy + DDNS
│       │         or Cloudflare Tunnel
│       │
│       └── NO → Tailscale Funnel
│                (free subdomain)
│
└── NO (only you/trusted users)
    │
    └── Is Tailscale blocked?
        (corporate WiFi, etc.)
        │
        ├── YES → Self-hosted WireGuard VPN
        │
        └── NO → Tailscale (recommended)
```

## Tailscale (Recommended)

Best option for most homelab users.

### Why Tailscale First

- Zero configuration on router
- No exposed ports
- Works behind CGNAT
- End-to-end encrypted
- Free for personal use (100 devices)
- Works on all platforms

### Quick Setup

```bash
# Install
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate
sudo tailscale up

# Check status
tailscale status
```

### Accessing Services

```bash
# From any Tailscale device
curl http://homeserver:8080

# With MagicDNS
curl http://homeserver.tailnet-name.ts.net
```

### When Tailscale Won't Work

- Corporate WiFi blocking UDP
- Network blocking non-standard ports
- Need truly public access (no login)
- Compliance requirements for self-hosted

See [Tailscale Documentation](../../tailscale/index.md) for full setup.

## WireGuard VPN (Self-Hosted)

Alternative when Tailscale isn't an option.

### Advantages Over Tailscale

- Fully self-hosted (no third party)
- More control over configuration
- No account required

### Basic Setup

```bash
# Install
sudo apt install wireguard

# Generate keys
wg genkey | tee privatekey | wg pubkey > publickey
```

```ini
# /etc/wireguard/wg0.conf
[Interface]
Address = 10.200.200.1/24
ListenPort = 51820
PrivateKey = <server-private-key>
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE

[Peer]
PublicKey = <client-public-key>
AllowedIPs = 10.200.200.2/32
```

### Client Configuration

```ini
# Client wg0.conf
[Interface]
Address = 10.200.200.2/24
PrivateKey = <client-private-key>
DNS = 10.200.200.1

[Peer]
PublicKey = <server-public-key>
Endpoint = your-ddns-hostname.duckdns.org:51820
AllowedIPs = 0.0.0.0/0  # Route all traffic (or specific subnets)
PersistentKeepalive = 25
```

### Port Forwarding Required

```
Router: Forward UDP 51820 → homeserver:51820
```

## DDNS (Dynamic DNS)

Maps a hostname to your changing public IP.

### Why You Need DDNS

Most residential ISPs assign dynamic IPs that change periodically. DDNS keeps a hostname updated with your current IP.

### Free DDNS Providers

| Provider | Domains | Update Method |
|----------|---------|---------------|
| Duck DNS | duckdns.org | HTTP API |
| No-IP | noip.com | Client/API |
| FreeDNS | afraid.org | HTTP API |
| Dynu | dynu.com | Client/API |

### Duck DNS Setup

```bash
# Create account at duckdns.org
# Create subdomain: yourhome.duckdns.org

# Update script
cat > /opt/duckdns/duck.sh << 'EOF'
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=yourhome&token=YOUR-TOKEN&ip=" | curl -k -o /opt/duckdns/duck.log -K -
EOF

chmod 700 /opt/duckdns/duck.sh

# Run every 5 minutes
(crontab -l; echo "*/5 * * * * /opt/duckdns/duck.sh >/dev/null 2>&1") | crontab -
```

### Router-Based DDNS

Many routers support DDNS natively:

1. Login to router admin
2. Find DDNS settings (usually under WAN/Internet)
3. Select provider and enter credentials
4. Enable auto-update

## Port Forwarding

Direct port exposure from router to server.

### Security Warning

Port forwarding exposes services directly to the internet. Only use with:
- Proper firewall rules
- Strong authentication
- Regular security updates
- SSL/TLS encryption

### Basic Port Forward

```
Router Settings:
  External Port: 443
  Internal IP: 192.168.1.100
  Internal Port: 443
  Protocol: TCP
```

### Recommended Practices

```yaml
# Behind reverse proxy (Traefik/Caddy)
# Only expose 80 and 443
Forward:
  - 80 → traefik:80    # HTTP (redirect to HTTPS)
  - 443 → traefik:443  # HTTPS
```

### Check Port Status

```bash
# From outside your network (use phone data)
nc -zv your-ddns.duckdns.org 443

# Or use online tools
# portchecker.co
# canyouseeme.org
```

## Cloudflare Tunnel

Zero-exposure alternative using Cloudflare's network.

### How It Works

```
Internet → Cloudflare → Tunnel → Your Server
           (edge)       (outbound only)

No ports exposed. Tunnel connects outbound.
```

### Advantages

- No port forwarding
- DDoS protection included
- Works behind CGNAT
- Free tier available

### Disadvantages

- Requires Cloudflare account
- Domain must use Cloudflare DNS
- Traffic routes through Cloudflare
- Not suitable for non-HTTP traffic

### Setup

```bash
# Install cloudflared
curl -L https://pkg.cloudflare.com/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

# Login
cloudflared tunnel login

# Create tunnel
cloudflared tunnel create homelab

# Configure
cat > ~/.cloudflared/config.yml << EOF
tunnel: <tunnel-id>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: app.example.com
    service: http://localhost:8080
  - hostname: api.example.com
    service: http://localhost:3000
  - service: http_status:404
EOF

# Run
cloudflared tunnel run homelab

# Or install as service
cloudflared service install
```

## Complete Setup: DDNS + Reverse Proxy

Most common setup for self-hosting with public access.

### Architecture

```
Internet
    │
    v
[DDNS Hostname]
    │
    v
[Your Router] ─── Port Forward 80, 443
    │
    v
[Traefik/Caddy] ─── SSL Termination
    │
    ├── service1.yourdomain.com
    ├── service2.yourdomain.com
    └── service3.yourdomain.com
```

### Step-by-Step

1. **Get a domain** (or use DDNS subdomain)

2. **Set up DDNS** if using dynamic IP
   ```bash
   # Duck DNS example
   */5 * * * * curl "https://duckdns.org/update?domains=mylab&token=TOKEN"
   ```

3. **Configure DNS**
   ```
   A     @           → your-public-ip (or CNAME to DDNS)
   CNAME service1    → @
   CNAME service2    → @
   ```

4. **Port forward** on router
   ```
   TCP 80  → traefik:80
   TCP 443 → traefik:443
   ```

5. **Configure Traefik/Caddy** with Let's Encrypt
   - HTTP challenge requires port 80 accessible
   - DNS challenge works without open ports

6. **Firewall on server**
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   ```

## Troubleshooting

### Can't Access from Outside

```bash
# 1. Verify public IP
curl ifconfig.me

# 2. Check if port is open
# From mobile data (not your WiFi)
nc -zv yourdomain.com 443

# 3. Check DDNS resolution
nslookup yourdomain.duckdns.org

# 4. Verify port forward
# Check router logs for incoming connections

# 5. Check local firewall
sudo ufw status
sudo iptables -L -n
```

### Hairpin NAT Issues

Can't access your service via public hostname from inside your network?

Solutions:
1. Use split DNS (Pi-hole returns local IP)
2. Enable hairpin NAT on router (if supported)
3. Use Tailscale/VPN internally

```yaml
# Pi-hole local DNS
yourdomain.com → 192.168.1.100
```

### CGNAT Detection

```bash
# Your public IP
curl ifconfig.me
# → 100.64.x.x or 10.x.x.x = CGNAT

# Your router's WAN IP
# Check router admin page
# If different from curl output = CGNAT
```

CGNAT solutions:
- Tailscale (works through CGNAT)
- Cloudflare Tunnel
- VPS with reverse tunnel
- Request static IP from ISP (may cost extra)

## Security Recommendations

### Minimum Requirements

1. **Always use HTTPS** - Never expose HTTP services
2. **Strong authentication** - No weak passwords
3. **Fail2ban** - Block repeated failures
4. **Regular updates** - Keep services patched
5. **Firewall** - Only open required ports

### Additional Hardening

```bash
# Fail2ban for SSH
sudo apt install fail2ban

# Rate limiting in Traefik
labels:
  - "traefik.http.middlewares.ratelimit.ratelimit.average=100"
  - "traefik.http.middlewares.ratelimit.ratelimit.burst=50"
```

### What NOT to Expose

- Database ports (3306, 5432, 27017)
- Admin panels without auth
- Development servers
- Internal monitoring
- SSH (use VPN/Tailscale instead)

## See Also

- [Tailscale Documentation](../../tailscale/index.md)
- [Reverse Proxy Setup](../../services/reverse-proxy/index.md)
- [SSL/TLS Certificates](../../services/ssl-tls/index.md)
- [UFW Configuration](../ufw/configuration.md)
