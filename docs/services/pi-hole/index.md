# Pi-hole

Pi-hole is a network-wide ad blocker that acts as a DNS sinkhole, blocking ads and tracking at the DNS level.

## How It Works

```
Client Request: ads.example.com
        │
        v
┌───────────────┐
│    Pi-hole    │
│   DNS Server  │
└───────────────┘
        │
        ├── In blocklist? ──> Return 0.0.0.0 (blocked)
        │
        └── Not blocked? ──> Forward to upstream DNS
                                    │
                                    v
                              ┌───────────┐
                              │ Cloudflare│
                              │   1.1.1.1 │
                              └───────────┘
```

## Docker Compose Setup

### Basic Setup

```yaml
services:
  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "80:80/tcp"
    environment:
      TZ: Europe/Oslo
      WEBPASSWORD: ${PIHOLE_PASSWORD}
      FTLCONF_LOCAL_IPV4: ${HOST_IP}
      PIHOLE_DNS_: 1.1.1.1;1.0.0.1
    volumes:
      - ./etc-pihole:/etc/pihole
      - ./etc-dnsmasq.d:/etc/dnsmasq.d
    cap_add:
      - NET_ADMIN
    dns:
      - 127.0.0.1
      - 1.1.1.1
```

### With DHCP

```yaml
services:
  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    restart: unless-stopped
    network_mode: host
    environment:
      TZ: Europe/Oslo
      WEBPASSWORD: ${PIHOLE_PASSWORD}
      PIHOLE_DNS_: 1.1.1.1;1.0.0.1
      DHCP_ACTIVE: "true"
      DHCP_START: 192.168.1.100
      DHCP_END: 192.168.1.200
      DHCP_ROUTER: 192.168.1.1
    volumes:
      - ./etc-pihole:/etc/pihole
      - ./etc-dnsmasq.d:/etc/dnsmasq.d
    cap_add:
      - NET_ADMIN
```

### With Custom Network

```yaml
services:
  pihole:
    image: pihole/pihole:latest
    container_name: pihole
    restart: unless-stopped
    ports:
      - "53:53/tcp"
      - "53:53/udp"
      - "8080:80/tcp"  # Web UI on different port
    environment:
      TZ: Europe/Oslo
      WEBPASSWORD: ${PIHOLE_PASSWORD}
      FTLCONF_LOCAL_IPV4: 192.168.1.10
      PIHOLE_DNS_: 1.1.1.1;1.0.0.1
      WEB_PORT: 80
      VIRTUAL_HOST: pihole.local
    volumes:
      - ./etc-pihole:/etc/pihole
      - ./etc-dnsmasq.d:/etc/dnsmasq.d
    cap_add:
      - NET_ADMIN
    networks:
      pihole_net:
        ipv4_address: 172.20.0.2

networks:
  pihole_net:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/24
```

## Environment Variables

```bash
# .env
PIHOLE_PASSWORD=your-secure-password
HOST_IP=192.168.1.10
```

## Initial Setup

1. Start the container:
   ```bash
   docker compose up -d
   ```

2. Access web interface:
   ```
   http://HOST_IP/admin
   ```

3. Log in with the password from `WEBPASSWORD`

## Configure Clients

### Option 1: Router DNS

Change your router's DNS to point to Pi-hole:
1. Access router admin panel
2. Find DHCP/DNS settings
3. Set primary DNS to Pi-hole IP
4. Optional: Set secondary to `1.1.1.1` as fallback

### Option 2: Per-Device

Configure DNS on individual devices:
- **Windows**: Network adapter settings > DNS
- **macOS**: System Preferences > Network > DNS
- **Linux**: `/etc/resolv.conf` or NetworkManager
- **Android/iOS**: Wi-Fi settings > DNS

### Option 3: Pi-hole DHCP

Let Pi-hole handle DHCP:
1. Disable DHCP on your router
2. Enable DHCP in Pi-hole settings
3. All clients automatically use Pi-hole

## Blocklists

### Default Lists

Pi-hole includes default blocklists. Add more at:
**Settings** > **Adlists**

### Recommended Lists

```
# Steven Black's Hosts
https://raw.githubusercontent.com/StevenBlack/hosts/master/hosts

# OISD
https://big.oisd.nl/

# Developer Dan's Ads & Tracking
https://www.github.developerdan.com/hosts/lists/ads-and-tracking-extended.txt

# Firebog Ticked Lists
https://v.firebog.net/hosts/lists.php?type=tick
```

### Update Lists

```bash
docker exec pihole pihole -g
```

## Whitelist

Common domains that may need whitelisting:

```bash
# Microsoft
docker exec pihole pihole -w s.youtube.com
docker exec pihole pihole -w www.googleadservices.com

# Common services
docker exec pihole pihole -w cdn.optimizely.com
docker exec pihole pihole -w api.ipify.org
```

Or add via web UI: **Whitelist** > **Add domain**

## Local DNS Records

Add local DNS entries for your services:

1. **Local DNS** > **DNS Records**
2. Add entries:
   ```
   server.local     192.168.1.10
   nas.local        192.168.1.20
   printer.local    192.168.1.30
   ```

Or via file:
```bash
# etc-pihole/custom.list
192.168.1.10 server.local
192.168.1.20 nas.local
```

## CNAME Records

Point subdomains to services:

```bash
# etc-dnsmasq.d/05-custom-cname.conf
cname=jellyfin.local,server.local
cname=pihole.local,server.local
```

## Upstream DNS

### Configure Upstream

**Settings** > **DNS** > **Upstream DNS Servers**

Recommended:
- Cloudflare: `1.1.1.1`, `1.0.0.1`
- Google: `8.8.8.8`, `8.8.4.4`
- Quad9: `9.9.9.9`

### DNS over HTTPS (DoH)

Use Cloudflared for encrypted DNS:

```yaml
services:
  cloudflared:
    image: cloudflare/cloudflared:latest
    container_name: cloudflared
    restart: unless-stopped
    command: proxy-dns
    environment:
      TUNNEL_DNS_UPSTREAM: "https://1.1.1.1/dns-query,https://1.0.0.1/dns-query"
      TUNNEL_DNS_PORT: 5053
      TUNNEL_DNS_ADDRESS: "0.0.0.0"
    networks:
      - pihole_net

  pihole:
    environment:
      PIHOLE_DNS_: cloudflared#5053
    depends_on:
      - cloudflared
```

## Unbound (Recursive DNS)

Run your own recursive resolver:

```yaml
services:
  unbound:
    image: mvance/unbound:latest
    container_name: unbound
    restart: unless-stopped
    volumes:
      - ./unbound:/opt/unbound/etc/unbound
    networks:
      pihole_net:
        ipv4_address: 172.20.0.3

  pihole:
    environment:
      PIHOLE_DNS_: 172.20.0.3#5053
```

## Statistics and Logging

### Query Log

View at **Query Log** in web UI.

### Long-Term Data

**Settings** > **Privacy** to configure:
- Log level
- Data retention
- Client privacy

### Disable Logging

For privacy:
```yaml
environment:
  FTLCONF_PRIVACYLEVEL: 3  # Anonymous
```

## Backup

### Config Backup

```bash
# Backup
docker exec pihole pihole -a -t

# Files are in /etc/pihole/
tar -czvf pihole-backup.tar.gz etc-pihole/
```

### Teleporter

Use built-in Teleporter:
1. **Settings** > **Teleporter**
2. Click **Backup**
3. Download `.tar.gz` file

## High Availability

### Gravity Sync

Sync blocklists between multiple Pi-holes:

```bash
# On secondary Pi-hole
curl -sSL https://raw.githubusercontent.com/vmstan/gravity-sync/master/gravity-sync.sh | bash
gravity-sync config
gravity-sync pull
```

## Troubleshooting

### Check Status

```bash
docker exec pihole pihole status
```

### Debug Queries

```bash
docker exec pihole pihole -t
```

### Common Issues

1. **Port 53 in use**
   ```bash
   # Disable systemd-resolved
   sudo systemctl disable systemd-resolved
   sudo systemctl stop systemd-resolved
   ```

2. **Clients not using Pi-hole**
   - Check router DNS settings
   - Verify Pi-hole IP is reachable
   - Flush client DNS cache

3. **Too many false positives**
   - Review query log
   - Whitelist affected domains
   - Use less aggressive blocklists

### Logs

```bash
docker logs pihole

# FTL logs
docker exec pihole cat /var/log/pihole/pihole-FTL.log
```

## See Also

- [Services Overview](../index.md)
- [Docker Compose](../../docker/compose.md)
- [Netplan DNS](../../netplan/routing/dns.md)
