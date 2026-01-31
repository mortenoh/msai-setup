# Media Stack

Self-hosted media server and automation for your library.

## Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Media Stack                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌───────────┐    ┌───────────┐    ┌───────────┐          │
│   │  Prowlarr │───>│  Sonarr   │───>│  Download │          │
│   │ (Indexers)│    │   (TV)    │    │  Client   │          │
│   └───────────┘    └───────────┘    └───────────┘          │
│        │                                  │                 │
│        │           ┌───────────┐          │                 │
│        └──────────>│  Radarr   │──────────┤                 │
│                    │ (Movies)  │          │                 │
│                    └───────────┘          │                 │
│                                           v                 │
│                    ┌───────────────────────────┐            │
│                    │     Media Library         │            │
│                    │   /data/media/movies      │            │
│                    │   /data/media/tv          │            │
│                    └───────────────────────────┘            │
│                              │                              │
│                              v                              │
│                    ┌───────────────────────────┐            │
│                    │        Jellyfin           │            │
│                    │    (Media Server)         │            │
│                    └───────────────────────────┘            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## In This Section

| Document | Description |
|----------|-------------|
| [Jellyfin](jellyfin.md) | Open-source media server |
| [*arr Stack](arr-stack.md) | Automated media management |

## Quick Start

### Directory Structure

```bash
# Create directory structure
mkdir -p /data/media/{movies,tv,music}
mkdir -p /data/downloads/{complete,incomplete}
mkdir -p /data/config/{jellyfin,sonarr,radarr,prowlarr}

# Set permissions
chown -R 1000:1000 /data
```

### Storage Layout

```
/data/
├── media/           # Final media library
│   ├── movies/
│   ├── tv/
│   └── music/
├── downloads/       # Download client
│   ├── complete/
│   └── incomplete/
└── config/          # Application configs
    ├── jellyfin/
    ├── sonarr/
    ├── radarr/
    └── prowlarr/
```

## Complete Stack

### docker-compose.yml

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - /data/config/jellyfin:/config
      - /data/media:/media:ro
    ports:
      - "8096:8096"
    networks:
      - media
      - proxy

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - /data/config/sonarr:/config
      - /data:/data
    ports:
      - "8989:8989"
    networks:
      - media
      - proxy

  radarr:
    image: lscr.io/linuxserver/radarr:latest
    container_name: radarr
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - /data/config/radarr:/config
      - /data:/data
    ports:
      - "7878:7878"
    networks:
      - media
      - proxy

  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    container_name: prowlarr
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - /data/config/prowlarr:/config
    ports:
      - "9696:9696"
    networks:
      - media
      - proxy

  transmission:
    image: lscr.io/linuxserver/transmission:latest
    container_name: transmission
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - /data/config/transmission:/config
      - /data/downloads:/downloads
    ports:
      - "9091:9091"
      - "51413:51413"
      - "51413:51413/udp"
    networks:
      - media

networks:
  media:
  proxy:
    external: true
```

## Reverse Proxy Configuration

### Traefik Labels

```yaml
services:
  jellyfin:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.jellyfin.rule=Host(`media.${DOMAIN}`)"
      - "traefik.http.routers.jellyfin.entrypoints=https"
      - "traefik.http.routers.jellyfin.tls.certresolver=letsencrypt"
      - "traefik.http.services.jellyfin.loadbalancer.server.port=8096"

  sonarr:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sonarr.rule=Host(`sonarr.${DOMAIN}`)"
      - "traefik.http.routers.sonarr.entrypoints=https"
      - "traefik.http.routers.sonarr.tls.certresolver=letsencrypt"
      - "traefik.http.routers.sonarr.middlewares=authelia@docker"
```

## Hardware Transcoding

### Intel Quick Sync

```yaml
services:
  jellyfin:
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - "video"
      - "render"
```

### NVIDIA GPU

```yaml
services:
  jellyfin:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
```

## See Also

- [Jellyfin Setup](jellyfin.md)
- [*arr Stack Setup](arr-stack.md)
- [Docker GPU Access](../../docker/gpu.md)
