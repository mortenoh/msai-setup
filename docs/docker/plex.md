# Plex

## Overview

Media server with ZFS-backed library.

## Data Layout

| ZFS Dataset | Container Path | Purpose |
|-------------|----------------|---------|
| tank/media | /media | Media files (read-only) |
| tank/containers/plex | /config | Plex configuration |

## Docker Compose

```yaml
# docker-compose.yml
services:
  plex:
    image: plexinc/pms-docker:latest
    container_name: plex
    restart: unless-stopped
    environment:
      TZ: Europe/Oslo
      PLEX_CLAIM: ${PLEX_CLAIM}
      PLEX_UID: 1000
      PLEX_GID: 1000
    volumes:
      - /mnt/tank/containers/plex:/config
      - /mnt/tank/media:/media:ro
    network_mode: host
```

## Environment File

```bash
# .env
PLEX_CLAIM=claim-xxxx  # Get from plex.tv/claim
```

## Prepare ZFS Datasets

```bash
# Create config dataset
sudo zfs create tank/containers/plex

# Set permissions
sudo chown -R 1000:1000 /mnt/tank/containers/plex
```

## Media Organization

```
/mnt/tank/media/
├── movies/
├── tv/
├── music/
└── photos/
```

Create nested datasets for separate snapshot policies:

```bash
sudo zfs create tank/media/movies
sudo zfs create tank/media/tv
sudo zfs create tank/media/music
```

## Deploy

```bash
cd ~/docker/plex
docker compose up -d
```

Access at `http://server-ip:32400/web`.

## Initial Setup

1. Sign in with Plex account
2. Add libraries pointing to `/media/movies`, `/media/tv`, etc.
3. Configure remote access if needed

## Network Mode

Using `network_mode: host` for:

- DLNA discovery
- GDM (Plex discovery)
- Better performance

If you need isolation, use bridge mode with explicit port mappings:

```yaml
ports:
  - "32400:32400"
  - "1900:1900/udp"
  - "32410:32410/udp"
  - "32412:32412/udp"
  - "32413:32413/udp"
  - "32414:32414/udp"
```

## Hardware Transcoding

For hardware transcoding (if not using GPU passthrough):

```yaml
devices:
  - /dev/dri:/dev/dri
```

!!! note
    If GPU is passed through to VM, hardware transcoding won't be available on the host.

## Maintenance

### Update

```bash
docker compose pull
docker compose up -d
```

### Backup

Snapshot the config dataset:

```bash
sudo zfs snapshot tank/containers/plex@backup
```

Media doesn't need frequent snapshots (it's write-once, read-many).
