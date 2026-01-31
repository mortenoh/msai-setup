# Uptime Kuma

Uptime Kuma is a self-hosted monitoring tool for tracking service availability and creating status pages.

## Features

- Multiple monitor types (HTTP, TCP, Ping, DNS, etc.)
- Status pages
- Notifications (Slack, Discord, Email, etc.)
- Multi-language support
- Certificate expiration monitoring

## Docker Compose Setup

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - "3001:3001"
    volumes:
      - ./data:/app/data
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - proxy

networks:
  proxy:
    external: true
```

## Initial Setup

1. Access at `http://localhost:3001`
2. Create admin account
3. Add monitors
4. Configure notifications

## Monitor Types

### HTTP(s)

Monitor web endpoints:

```
URL: https://example.com
Method: GET
Expected Status: 200
Interval: 60 seconds
Retries: 3
```

### TCP Port

Check if a port is open:

```
Hostname: database.local
Port: 5432
Interval: 60 seconds
```

### Ping

ICMP ping check:

```
Hostname: server.local
Interval: 60 seconds
```

### DNS

Monitor DNS records:

```
Hostname: example.com
DNS Server: 1.1.1.1
Record Type: A
Expected Value: 93.184.216.34
```

### Docker Container

Monitor container status:

```
Container Name: nginx
Docker Host: /var/run/docker.sock
```

### Database

Check database connectivity:

**MySQL:**
```
Connection String: mysql://user:pass@host:3306/database
```

**PostgreSQL:**
```
Connection String: postgres://user:pass@host:5432/database
```

**MongoDB:**
```
Connection String: mongodb://user:pass@host:27017/database
```

### Keywords

Check page contains/doesn't contain text:

```
URL: https://example.com/status
Keyword: "operational"
Should Contain: Yes
```

### JSON Query

Validate JSON API response:

```
URL: https://api.example.com/health
JSON Path: $.status
Expected Value: "ok"
```

## Status Pages

### Create Status Page

1. Go to **Status Pages**
2. Click **New Status Page**
3. Configure:
   - Title and description
   - Add monitor groups
   - Custom domain (optional)

### Public URL

Status pages are accessible at:
```
http://uptime-kuma:3001/status/page-slug
```

### Custom Domain

Add to your reverse proxy:

```yaml
# Traefik
labels:
  - "traefik.http.routers.status.rule=Host(`status.example.com`)"
```

## Notifications

### Discord

1. Create Discord webhook
2. In Uptime Kuma: **Settings** > **Notifications**
3. Add Discord notification:
   - Webhook URL: `https://discord.com/api/webhooks/...`

### Slack

```
Webhook URL: https://hooks.slack.com/services/...
Channel: #alerts
```

### Email (SMTP)

```
SMTP Host: smtp.gmail.com
SMTP Port: 587
SMTP Security: STARTTLS
Username: your@email.com
Password: app-password
From: alerts@example.com
To: admin@example.com
```

### Telegram

```
Bot Token: 123456:ABC-DEF...
Chat ID: -1001234567890
```

### Pushover

```
User Key: your-user-key
API Token: your-api-token
```

### Generic Webhook

```
URL: https://your-webhook-endpoint.com
Method: POST
Headers:
  Content-Type: application/json
Body: {"status": "{{status}}", "monitor": "{{name}}"}
```

## Maintenance Windows

Schedule maintenance:

1. Go to **Maintenance**
2. Click **Add Maintenance**
3. Configure:
   - Title
   - Affected monitors
   - Start/end time
   - Recurrence

During maintenance, monitors won't trigger alerts.

## Grouping Monitors

### Create Groups

1. Add group in monitor settings
2. Group monitors by:
   - Service type
   - Environment
   - Location

### Status Page Groups

```
Infrastructure
├── Proxmox
├── TrueNAS
└── Router

Services
├── Jellyfin
├── Nextcloud
└── Pi-hole

External
├── GitHub
└── Cloudflare
```

## API

### API Token

1. **Settings** > **API Keys**
2. Generate new key

### Get Monitors

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://uptime-kuma:3001/api/monitors
```

### Get Status

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
  http://uptime-kuma:3001/api/status-page/heartbeat/slug
```

## Docker Integration

### Monitor Containers

Mount Docker socket:

```yaml
volumes:
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

Then add Docker Container monitors.

### Remote Docker

For remote Docker hosts, use TCP:

```yaml
# On remote host, enable Docker TCP
# /etc/docker/daemon.json
{
  "hosts": ["unix:///var/run/docker.sock", "tcp://0.0.0.0:2375"]
}
```

## Reverse Proxy

### Traefik

```yaml
services:
  uptime-kuma:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.uptime.rule=Host(`status.example.com`)"
      - "traefik.http.routers.uptime.entrypoints=https"
      - "traefik.http.routers.uptime.tls.certresolver=letsencrypt"
      - "traefik.http.services.uptime.loadbalancer.server.port=3001"
```

### Caddy

```
status.example.com {
    reverse_proxy uptime-kuma:3001
}
```

## Backup

### Export Settings

1. **Settings** > **Backup**
2. Click **Export**
3. Save JSON file

### Docker Volume Backup

```bash
# Stop container
docker stop uptime-kuma

# Backup data
tar -czvf uptime-kuma-backup.tar.gz ./data

# Start container
docker start uptime-kuma
```

### Restore

1. **Settings** > **Backup**
2. Click **Import**
3. Upload JSON file

## High Availability

### Multiple Instances

For redundancy, run multiple instances:

```yaml
services:
  uptime-kuma-1:
    image: louislam/uptime-kuma:latest
    volumes:
      - ./data-1:/app/data

  uptime-kuma-2:
    image: louislam/uptime-kuma:latest
    volumes:
      - ./data-2:/app/data
```

Note: Data doesn't sync between instances. Configure same monitors on both.

## Troubleshooting

### Logs

```bash
docker logs uptime-kuma
```

### Common Issues

1. **Monitor shows DOWN incorrectly**
   - Increase retry count
   - Check network connectivity
   - Verify URL/hostname is accessible from container

2. **Notifications not sending**
   - Test notification in settings
   - Check notification service credentials
   - Verify network access to notification service

3. **High memory usage**
   - Reduce monitor intervals
   - Limit heartbeat retention

### Reset Password

```bash
docker exec -it uptime-kuma node extra/reset-password.js
```

## See Also

- [Services Overview](../index.md)
- [Homepage](../homepage/index.md)
- [Reverse Proxy](../reverse-proxy/index.md)
