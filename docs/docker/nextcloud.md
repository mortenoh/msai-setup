# Nextcloud

## Overview

Self-hosted cloud storage with data on ZFS.

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
