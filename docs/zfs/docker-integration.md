# Docker Integration

## Overview

Two approaches for Docker storage with ZFS:

| Approach | How It Works | Best For |
|----------|--------------|----------|
| overlay2 + bind mounts | Docker uses overlay2; data on ZFS via bind mounts | Most setups (recommended) |
| ZFS storage driver | Docker stores images/containers directly on ZFS | Advanced use cases |

## Recommended: overlay2 + Bind Mounts

This approach keeps Docker simple while still benefiting from ZFS for persistent data.

### How It Works

```
Docker (overlay2)           ZFS (tank)
+------------------+        +------------------+
| Images           |        | /mnt/tank/       |
| Containers       |   <--> |   nextcloud-data |
| Build cache      |  bind  |   db             |
+------------------+  mount |   media          |
/var/lib/docker             +------------------+
```

- Docker manages images and containers on the root filesystem
- Application data lives on ZFS datasets
- Containers access ZFS via bind mounts

### Configuration

Docker daemon config (`/etc/docker/daemon.json`):

```json
{
  "storage-driver": "overlay2"
}
```

See [Docker Setup](../docker/setup.md) for full configuration.

### Bind Mount Example

docker-compose.yml:

```yaml
services:
  nextcloud:
    image: nextcloud:latest
    volumes:
      - /mnt/tank/nextcloud-app:/var/www/html
      - /mnt/tank/nextcloud-data:/var/www/html/data
```

### Benefits

- Simple Docker upgrades (no storage driver issues)
- ZFS features (snapshots, compression) for application data
- Separation of concerns: Docker handles containers, ZFS handles data

## Alternative: ZFS Storage Driver

Docker can use ZFS directly for all storage. Each image layer and container becomes a ZFS dataset.

### When to Consider

- Container-heavy workflows with many short-lived containers
- Want ZFS features for image layers (deduplication potential)
- Advanced ZFS management requirements

### Setup

1. Create a dataset for Docker:

```bash
sudo zfs create tank/docker
```

2. Configure Docker:

```json
{
  "storage-driver": "zfs",
  "storage-opts": [
    "zfs.fsname=tank/docker"
  ]
}
```

3. Restart Docker:

```bash
sudo systemctl restart docker
```

### Drawbacks

- More complex troubleshooting
- Docker version upgrades may have storage driver compatibility issues
- Many small datasets (one per layer/container)

## Directory Structure

Organize container data on ZFS:

```
/mnt/tank/
├── nextcloud-data/     # Nextcloud user files
├── nextcloud-app/      # Nextcloud application
├── db/                 # Database files
│   ├── postgres/
│   └── mariadb/
├── media/              # Plex/Jellyfin media
└── containers/         # Misc container state
    ├── homeassistant/
    └── grafana/
```

Create datasets as needed:

```bash
sudo zfs create tank/containers
sudo zfs create tank/containers/homeassistant
sudo zfs create tank/containers/grafana
```

## Snapshot Strategy

### Per-Service Snapshots

Before updating a service:

```bash
# Snapshot the data
sudo zfs snapshot tank/nextcloud-data@pre-update
sudo zfs snapshot tank/nextcloud-app@pre-update

# Update the container
docker compose pull
docker compose up -d
```

### Automated Snapshots

Create a script for pre-update snapshots:

```bash
#!/bin/bash
# /usr/local/bin/docker-snapshot.sh

SERVICE=$1
DATE=$(date +%Y%m%d-%H%M)

case $SERVICE in
  nextcloud)
    zfs snapshot tank/nextcloud-data@${DATE}
    zfs snapshot tank/nextcloud-app@${DATE}
    ;;
  plex)
    zfs snapshot tank/media@${DATE}
    ;;
  *)
    zfs snapshot tank/containers/${SERVICE}@${DATE}
    ;;
esac
```

Usage:

```bash
sudo docker-snapshot.sh nextcloud
docker compose pull
docker compose up -d
```

### Recovery

If an update breaks something:

```bash
# Stop containers
docker compose down

# Rollback
sudo zfs rollback tank/nextcloud-data@pre-update
sudo zfs rollback tank/nextcloud-app@pre-update

# Restore previous image
docker compose up -d
```

## Permissions

Docker containers often run as non-root users. Set ownership accordingly:

```bash
# Nextcloud runs as www-data (UID 33)
sudo chown -R 33:33 /mnt/tank/nextcloud-data
sudo chown -R 33:33 /mnt/tank/nextcloud-app

# Plex runs as plex user
sudo chown -R 997:997 /mnt/tank/media
```

Check container documentation for the expected UID/GID.

## Comparison Summary

| Feature | overlay2 + bind mounts | ZFS driver |
|---------|------------------------|------------|
| Setup complexity | Low | Medium |
| Snapshot granularity | Per dataset | Per container |
| Docker upgrades | Simple | May need migration |
| Troubleshooting | Standard Docker | ZFS knowledge needed |
| Recommended | Yes | Special cases |

For most deployments, **overlay2 with bind mounts** provides the best balance of simplicity and ZFS benefits.
