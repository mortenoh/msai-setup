# Nextcloud

Self-hosted cloud storage, calendar, contacts, and office collaboration with data on ZFS.

## Overview

Nextcloud provides:

- **File Sync** - Desktop and mobile clients
- **Office** - Collaborative document editing
- **Calendar/Contacts** - CalDAV/CardDAV sync
- **Talk** - Video calls and chat
- **Photos** - AI-powered photo management
- **External Storage** - Mount S3, SMB, WebDAV
- **Apps** - 400+ integrations

## Data Layout

| ZFS Dataset | Container Path | Purpose |
|-------------|----------------|---------|
| tank/nextcloud-data | /var/www/html/data | User files |
| tank/nextcloud-app | /var/www/html | App config |
| tank/db | /var/lib/mysql | Database |

## Docker Compose

```yaml
# docker-compose.yml
services:
  db:
    image: mariadb:11
    container_name: nextcloud-db
    restart: unless-stopped
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: nextcloud
      MYSQL_USER: nextcloud
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - /mnt/tank/db/nextcloud:/var/lib/mysql

  redis:
    image: redis:alpine
    container_name: nextcloud-redis
    restart: unless-stopped

  nextcloud:
    image: nextcloud:stable
    container_name: nextcloud
    restart: unless-stopped
    depends_on:
      - db
      - redis
    environment:
      MYSQL_HOST: db
      MYSQL_DATABASE: nextcloud
      MYSQL_USER: nextcloud
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
      REDIS_HOST: redis
      NEXTCLOUD_TRUSTED_DOMAINS: ${NEXTCLOUD_DOMAIN}
    volumes:
      - /mnt/tank/nextcloud-app:/var/www/html
      - /mnt/tank/nextcloud-data:/var/www/html/data
    ports:
      - "8080:80"
```

## Environment File

```bash
# .env
MYSQL_ROOT_PASSWORD=<secure-password>
MYSQL_PASSWORD=<secure-password>
NEXTCLOUD_DOMAIN=nextcloud.local
```

## Prepare ZFS Datasets

```bash
# Create datasets if not done
sudo zfs create tank/nextcloud-app
sudo zfs create tank/nextcloud-data
sudo zfs create tank/db/nextcloud

# Set permissions (www-data = UID 33)
sudo chown -R 33:33 /mnt/tank/nextcloud-app
sudo chown -R 33:33 /mnt/tank/nextcloud-data
sudo chown -R 999:999 /mnt/tank/db/nextcloud
```

## Deploy

```bash
cd ~/docker/nextcloud
docker compose up -d
```

Access at `http://server-ip:8080`.

## Initial Setup

1. Create admin account
2. Configure database (already set via environment)
3. Install recommended apps

## Maintenance

### Backup Strategy

```bash
# Snapshot before upgrade
sudo zfs snapshot tank/nextcloud-data@pre-upgrade
sudo zfs snapshot tank/nextcloud-app@pre-upgrade
sudo zfs snapshot tank/db/nextcloud@pre-upgrade
```

### Update

```bash
docker compose pull
docker compose up -d
docker exec -u www-data nextcloud php occ upgrade
```

### Scan Files

After adding files externally:

```bash
docker exec -u www-data nextcloud php occ files:scan --all
```

## Reverse Proxy / HTTPS

### Caddy Configuration

Caddy provides automatic HTTPS with Let's Encrypt.

Install Caddy on the host:

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install -y caddy
```

Configure `/etc/caddy/Caddyfile`:

```
nextcloud.example.com {
    reverse_proxy localhost:8080

    header {
        Strict-Transport-Security "max-age=31536000; includeSubDomains"
    }

    redir /.well-known/carddav /remote.php/dav 301
    redir /.well-known/caldav /remote.php/dav 301
}
```

Reload Caddy:

```bash
sudo systemctl reload caddy
```

### Trusted Domains

Update Nextcloud to trust the domain:

```bash
docker exec -u www-data nextcloud php occ config:system:set \
    trusted_domains 0 --value="nextcloud.example.com"

docker exec -u www-data nextcloud php occ config:system:set \
    overwrite.cli.url --value="https://nextcloud.example.com"

docker exec -u www-data nextcloud php occ config:system:set \
    overwriteprotocol --value="https"
```

### nginx-proxy Alternative

Using nginx-proxy with companion for HTTPS:

```yaml
services:
  nginx-proxy:
    image: nginxproxy/nginx-proxy
    container_name: nginx-proxy
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/tmp/docker.sock:ro
      - certs:/etc/nginx/certs
      - html:/usr/share/nginx/html
      - vhost:/etc/nginx/vhost.d

  acme-companion:
    image: nginxproxy/acme-companion
    container_name: acme-companion
    volumes_from:
      - nginx-proxy
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - acme:/etc/acme.sh
    environment:
      DEFAULT_EMAIL: admin@example.com

  nextcloud:
    # ... existing config ...
    environment:
      # ... existing vars ...
      VIRTUAL_HOST: nextcloud.example.com
      LETSENCRYPT_HOST: nextcloud.example.com
```

## Troubleshooting

### Common occ Commands

```bash
# Run any occ command
docker exec -u www-data nextcloud php occ <command>

# Check status
docker exec -u www-data nextcloud php occ status

# Maintenance mode
docker exec -u www-data nextcloud php occ maintenance:mode --on
docker exec -u www-data nextcloud php occ maintenance:mode --off

# Repair
docker exec -u www-data nextcloud php occ maintenance:repair

# Database maintenance
docker exec -u www-data nextcloud php occ db:add-missing-indices
docker exec -u www-data nextcloud php occ db:add-missing-columns
docker exec -u www-data nextcloud php occ db:add-missing-primary-keys
```

### Database Issues

**Connection refused**:

```bash
# Check database container is running
docker ps | grep nextcloud-db

# Check logs
docker logs nextcloud-db

# Test connection
docker exec nextcloud-db mysql -u nextcloud -p -e "SELECT 1"
```

**Locked database**:

```bash
# Check for locks
docker exec nextcloud-db mysql -u root -p -e \
    "SHOW PROCESSLIST"

# Kill long-running queries if needed
docker exec nextcloud-db mysql -u root -p -e \
    "KILL <process_id>"
```

**Corrupted database**:

```bash
# Check tables
docker exec nextcloud-db mysqlcheck -u root -p --all-databases

# Repair tables
docker exec nextcloud-db mysqlcheck -u root -p --repair nextcloud
```

### File Locking Problems

**Locked files that won't unlock**:

```bash
# View locks
docker exec -u www-data nextcloud php occ files:scan --all

# Clear all file locks
docker exec nextcloud-db mysql -u root -p -e \
    "DELETE FROM nextcloud.oc_file_locks WHERE 1"

# Restart
docker compose restart nextcloud
```

### Upgrade Failures

**Upgrade stuck in maintenance mode**:

```bash
# Disable maintenance mode
docker exec -u www-data nextcloud php occ maintenance:mode --off

# Check version
docker exec -u www-data nextcloud php occ status

# Retry upgrade
docker exec -u www-data nextcloud php occ upgrade
```

**Failed upgrade (need to rollback)**:

```bash
# Stop containers
docker compose down

# Rollback to pre-upgrade snapshot
sudo zfs rollback tank/nextcloud-app@pre-upgrade
sudo zfs rollback tank/nextcloud-data@pre-upgrade
sudo zfs rollback tank/db/nextcloud@pre-upgrade

# Start with previous image version
# Edit docker-compose.yml to pin previous version
docker compose up -d
```

### Performance Issues

```bash
# Check cron job is running
docker exec -u www-data nextcloud php occ background:cron

# Clear caches
docker exec -u www-data nextcloud php occ maintenance:repair

# Check preview generation
docker exec -u www-data nextcloud php occ preview:generate-all
```

## Restore Procedure

### From ZFS Snapshot

1. Stop services:
   ```bash
   cd ~/docker/nextcloud
   docker compose down
   ```

2. Identify target snapshot:
   ```bash
   zfs list -t snapshot | grep nextcloud
   ```

3. Rollback all datasets:
   ```bash
   sudo zfs rollback tank/nextcloud-data@target-snapshot
   sudo zfs rollback tank/nextcloud-app@target-snapshot
   sudo zfs rollback tank/db/nextcloud@target-snapshot
   ```

4. Restart services:
   ```bash
   docker compose up -d
   ```

5. Verify:
   ```bash
   docker exec -u www-data nextcloud php occ status
   ```

### From Database Dump

1. Stop Nextcloud (keep database running):
   ```bash
   docker compose stop nextcloud
   ```

2. Restore database:
   ```bash
   docker exec -i nextcloud-db mysql -u root -p"${MYSQL_ROOT_PASSWORD}" nextcloud < /mnt/tank/backups/nextcloud-db-YYYYMMDD.sql
   ```

3. Restart:
   ```bash
   docker compose start nextcloud
   ```

4. Run maintenance:
   ```bash
   docker exec -u www-data nextcloud php occ maintenance:repair
   docker exec -u www-data nextcloud php occ files:scan --all
   ```

### Verifying Restored Data

After any restore:

1. Check status:
   ```bash
   docker exec -u www-data nextcloud php occ status
   ```

2. Verify file counts:
   ```bash
   docker exec -u www-data nextcloud php occ files:scan --all
   ```

3. Test login and file access via web UI

4. Check logs for errors:
   ```bash
   docker logs nextcloud 2>&1 | tail -50
   ```

## Performance Optimization

### Enable Memory Caching

Add APCu for local caching:

```bash
docker exec -u www-data nextcloud php occ config:system:set memcache.local --value="\OC\Memcache\APCu"
```

Redis is already configured in the compose file for distributed caching:

```bash
docker exec -u www-data nextcloud php occ config:system:set memcache.distributed --value="\OC\Memcache\Redis"
docker exec -u www-data nextcloud php occ config:system:set redis host --value="redis"
docker exec -u www-data nextcloud php occ config:system:set redis port --value="6379" --type=integer
```

### Enable Locking with Redis

```bash
docker exec -u www-data nextcloud php occ config:system:set memcache.locking --value="\OC\Memcache\Redis"
```

### Database Optimization

Enable database indices:

```bash
docker exec -u www-data nextcloud php occ db:add-missing-indices
docker exec -u www-data nextcloud php occ db:add-missing-columns
docker exec -u www-data nextcloud php occ db:add-missing-primary-keys
docker exec -u www-data nextcloud php occ db:convert-filecache-bigint
```

### PHP Configuration

Create optimized PHP config:

```bash
cat << 'EOF' > php-custom.ini
memory_limit = 512M
upload_max_filesize = 16G
post_max_size = 16G
max_execution_time = 3600
max_input_time = 3600

opcache.enable = 1
opcache.interned_strings_buffer = 16
opcache.max_accelerated_files = 10000
opcache.memory_consumption = 128
opcache.save_comments = 1
opcache.revalidate_freq = 1
EOF
```

Mount in docker-compose.yml:

```yaml
volumes:
  - ./php-custom.ini:/usr/local/etc/php/conf.d/zzz-custom.ini:ro
```

### Preview Generation

Pre-generate previews for faster browsing:

```bash
# One-time generation for all files
docker exec -u www-data nextcloud php occ preview:generate-all

# Configure preview sizes
docker exec -u www-data nextcloud php occ config:system:set preview_max_x --value="2048"
docker exec -u www-data nextcloud php occ config:system:set preview_max_y --value="2048"
```

## Background Jobs (Cron)

### Configure Cron (Recommended)

Use system cron instead of AJAX or Webcron:

```bash
# Set cron as background job method
docker exec -u www-data nextcloud php occ background:cron
```

Add host cron job:

```bash
# /etc/cron.d/nextcloud
*/5 * * * * root docker exec -u www-data nextcloud php cron.php
```

Or use a dedicated cron container:

```yaml
services:
  cron:
    image: nextcloud:stable
    container_name: nextcloud-cron
    restart: unless-stopped
    depends_on:
      - db
      - redis
    volumes:
      - /mnt/tank/nextcloud-app:/var/www/html
      - /mnt/tank/nextcloud-data:/var/www/html/data
    entrypoint: /cron.sh
```

### Verify Cron is Working

```bash
# Check last cron run
docker exec -u www-data nextcloud php occ background:cron

# Check status
docker exec -u www-data nextcloud php occ status
```

## Essential Apps

### Install Recommended Apps

```bash
# Office suite (requires Collabora or OnlyOffice)
docker exec -u www-data nextcloud php occ app:install richdocuments

# Calendar and contacts
docker exec -u www-data nextcloud php occ app:install calendar
docker exec -u www-data nextcloud php occ app:install contacts

# External storage
docker exec -u www-data nextcloud php occ app:install files_external

# Two-factor authentication
docker exec -u www-data nextcloud php occ app:install twofactor_totp

# Photos with AI
docker exec -u www-data nextcloud php occ app:install memories
docker exec -u www-data nextcloud php occ app:install recognize

# Talk (video calls)
docker exec -u www-data nextcloud php occ app:install spreed

# Notes
docker exec -u www-data nextcloud php occ app:install notes
```

### Collabora Online (Office)

Add to docker-compose.yml:

```yaml
services:
  collabora:
    image: collabora/code:latest
    container_name: collabora
    restart: unless-stopped
    environment:
      - domain=nextcloud\\.example\\.com  # Escape dots
      - username=admin
      - password=${COLLABORA_PASSWORD}
      - extra_params=--o:ssl.enable=false --o:ssl.termination=true
    ports:
      - "9980:9980"
    cap_add:
      - MKNOD
```

Configure in Nextcloud:

1. Admin Settings > Richdocuments
2. Set Collabora URL: `http://collabora:9980`

## External Storage

### Mount SMB/CIFS Share

```bash
# Enable external storage app
docker exec -u www-data nextcloud php occ app:enable files_external

# Configure via web UI: Settings > External Storage
```

Or via occ:

```bash
docker exec -u www-data nextcloud php occ files_external:create \
    "/SMB Share" \
    smb \
    password::password \
    --config host=192.168.1.100 \
    --config share=shared \
    --config root=/ \
    --config domain=WORKGROUP \
    --config user=smbuser \
    --config password=smbpass
```

### Mount Local Folder

Mount additional host directories in docker-compose.yml:

```yaml
volumes:
  - /mnt/tank/nextcloud-app:/var/www/html
  - /mnt/tank/nextcloud-data:/var/www/html/data
  - /mnt/tank/media:/external/media:ro  # Additional mount
```

Configure as local external storage:

```bash
docker exec -u www-data nextcloud php occ files_external:create \
    "/Media" \
    local \
    null::null \
    --config datadir=/external/media
```

## Security Hardening

### Enable Brute Force Protection

```bash
docker exec -u www-data nextcloud php occ config:system:set auth.bruteforce.protection.enabled --value=true --type=boolean
```

### Set Secure Headers

Add to config.php via occ:

```bash
# Force HTTPS
docker exec -u www-data nextcloud php occ config:system:set overwriteprotocol --value="https"

# Secure cookies
docker exec -u www-data nextcloud php occ config:system:set forcessl --value=true --type=boolean
```

### Enable Two-Factor Authentication

```bash
# Install TOTP app
docker exec -u www-data nextcloud php occ app:install twofactor_totp

# Enforce for all users (optional)
docker exec -u www-data nextcloud php occ twofactorauth:enforce --on
```

### Disable Unused Features

```bash
# Disable app recommendations
docker exec -u www-data nextcloud php occ config:system:set appstoreenabled --value=false --type=boolean

# Disable check for updates (use docker pull instead)
docker exec -u www-data nextcloud php occ config:system:set updatechecker --value=false --type=boolean
```

## Client Setup

### Desktop Sync Client

Install Nextcloud Desktop on your workstation:

- [Linux](https://nextcloud.com/install/#install-clients): `flatpak install flathub com.nextcloud.desktopclient.nextcloud`
- [macOS](https://nextcloud.com/install/#install-clients): Homebrew or DMG
- [Windows](https://nextcloud.com/install/#install-clients): MSI installer

Configure:
1. Enter server URL (e.g., `https://nextcloud.example.com`)
2. Authenticate via browser
3. Select folders to sync

### Mobile Apps

- [Nextcloud Files](https://nextcloud.com/clients/) - iOS/Android
- [Nextcloud Talk](https://nextcloud.com/talk/) - Video calls
- [DAVx5](https://www.davx5.com/) - Calendar/Contacts sync on Android

### CalDAV/CardDAV URLs

For calendar/contacts sync in external apps:

| Service | URL |
|---------|-----|
| CalDAV | `https://nextcloud.example.com/remote.php/dav` |
| CardDAV | `https://nextcloud.example.com/remote.php/dav` |

## Monitoring

### Check System Status

```bash
# Full status
docker exec -u www-data nextcloud php occ status

# Security scan
docker exec -u www-data nextcloud php occ security:certificates

# App updates
docker exec -u www-data nextcloud php occ app:update --all
```

### Log Analysis

```bash
# View Nextcloud log
docker exec nextcloud tail -f /var/www/html/data/nextcloud.log

# Parse as JSON
docker exec nextcloud cat /var/www/html/data/nextcloud.log | jq .
```

### Health Check Script

```bash
#!/bin/bash
# /usr/local/bin/check-nextcloud.sh

STATUS=$(docker exec -u www-data nextcloud php occ status --output=json 2>/dev/null)

if echo "$STATUS" | jq -e '.installed == true and .maintenance == false' > /dev/null; then
    echo "Nextcloud: OK"
    exit 0
else
    echo "Nextcloud: PROBLEM"
    echo "$STATUS" | jq .
    exit 1
fi
```

## See Also

- [Docker Setup](setup.md) - Docker installation
- [Resource Limits](resources.md) - Container constraints
- [ZFS](../zfs/index.md) - Dataset management and snapshots
- [Tailscale](../tailscale/index.md) - Remote access
