# *arr Stack

The *arr stack automates media library management - finding, downloading, and organizing content.

## Components

| Service | Purpose |
|---------|---------|
| Prowlarr | Indexer manager |
| Sonarr | TV show management |
| Radarr | Movie management |
| Lidarr | Music management |
| Readarr | Book/audiobook management |

## Docker Compose Setup

### Full Stack

```yaml
services:
  prowlarr:
    image: lscr.io/linuxserver/prowlarr:latest
    container_name: prowlarr
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - ./config/prowlarr:/config
    ports:
      - "9696:9696"
    networks:
      - arr

  sonarr:
    image: lscr.io/linuxserver/sonarr:latest
    container_name: sonarr
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
    volumes:
      - ./config/sonarr:/config
      - /data:/data
    ports:
      - "8989:8989"
    networks:
      - arr
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
      - ./config/radarr:/config
      - /data:/data
    ports:
      - "7878:7878"
    networks:
      - arr
      - proxy

  transmission:
    image: lscr.io/linuxserver/transmission:latest
    container_name: transmission
    restart: unless-stopped
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
      - TRANSMISSION_WEB_HOME=/config/flood-for-transmission/
    volumes:
      - ./config/transmission:/config
      - /data/downloads:/downloads
    ports:
      - "9091:9091"
      - "51413:51413"
      - "51413:51413/udp"
    networks:
      - arr

networks:
  arr:
  proxy:
    external: true
```

## Directory Structure

```bash
# Critical: Use a unified data structure
/data/
├── downloads/
│   ├── complete/
│   │   ├── movies/
│   │   └── tv/
│   └── incomplete/
├── media/
│   ├── movies/
│   └── tv/
└── config/
    ├── prowlarr/
    ├── sonarr/
    ├── radarr/
    └── transmission/
```

Mount `/data` to all containers so hardlinks work:

```yaml
volumes:
  - /data:/data
```

## Setup Order

1. **Prowlarr** - Configure indexers first
2. **Download Client** - Set up Transmission/qBittorrent
3. **Sonarr/Radarr** - Connect to Prowlarr and download client
4. **Jellyfin** - Point to media directories

## Prowlarr Setup

### Add Indexers

1. Go to **Indexers** > **Add Indexer**
2. Search for your indexer
3. Configure credentials/API keys
4. Test and save

### Connect to *arr Apps

1. Go to **Settings** > **Apps**
2. Add Sonarr:
   - Prowlarr Server: `http://prowlarr:9696`
   - Sonarr Server: `http://sonarr:8989`
   - API Key: from Sonarr settings
3. Add Radarr similarly

## Sonarr Configuration

### Root Folders

1. Go to **Settings** > **Media Management**
2. Add Root Folder: `/data/media/tv`

### Quality Profiles

1. Go to **Settings** > **Profiles**
2. Recommended profile:
   - HDTV-1080p and above
   - Prefer WEBDL/BluRay

### Download Client

1. Go to **Settings** > **Download Clients**
2. Add Transmission:
   - Host: `transmission`
   - Port: `9091`
   - Category: `tv`

### Import Lists (Optional)

1. Go to **Settings** > **Import Lists**
2. Add Trakt, Plex, or custom lists

## Radarr Configuration

### Root Folders

1. Go to **Settings** > **Media Management**
2. Add Root Folder: `/data/media/movies`

### Quality Profiles

Similar to Sonarr, customize for movies.

### Download Client

Same as Sonarr, use category `movies`.

## Download Client Setup

### Transmission

```yaml
environment:
  - TRANSMISSION_WEB_HOME=/config/flood-for-transmission/  # Better UI
  - USER=admin
  - PASS=adminpassword
```

Settings in Transmission:
1. Download directory: `/downloads/complete`
2. Incomplete directory: `/downloads/incomplete`

### qBittorrent Alternative

```yaml
services:
  qbittorrent:
    image: lscr.io/linuxserver/qbittorrent:latest
    container_name: qbittorrent
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Oslo
      - WEBUI_PORT=8080
    volumes:
      - ./config/qbittorrent:/config
      - /data/downloads:/downloads
    ports:
      - "8080:8080"
      - "6881:6881"
      - "6881:6881/udp"
```

## Hardlinks vs Copies

With proper directory structure, *arr apps use hardlinks (instant, no extra space).

**Requirements:**
- Same filesystem for downloads and media
- Same mount point in all containers
- Correct PUID/PGID

**Verify hardlinks work:**
```bash
# After import, check inode
ls -i /data/downloads/complete/movies/Movie.mkv
ls -i /data/media/movies/Movie\ \(2020\)/Movie.mkv
# Should show same inode number
```

## Recyclarr (Quality Profiles)

Automatically sync quality profiles from TRaSH Guides:

```yaml
services:
  recyclarr:
    image: ghcr.io/recyclarr/recyclarr:latest
    container_name: recyclarr
    volumes:
      - ./config/recyclarr:/config
    environment:
      - TZ=Europe/Oslo
```

```yaml
# config/recyclarr/recyclarr.yml
sonarr:
  sonarr:
    base_url: http://sonarr:8989
    api_key: your-api-key

    quality_definition:
      type: series

    quality_profiles:
      - name: WEB-1080p
        reset_unmatched_scores: true

radarr:
  radarr:
    base_url: http://radarr:7878
    api_key: your-api-key

    quality_definition:
      type: movie

    quality_profiles:
      - name: HD Bluray + WEB
        reset_unmatched_scores: true
```

## Reverse Proxy

### Traefik Labels

```yaml
services:
  sonarr:
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.sonarr.rule=Host(`sonarr.${DOMAIN}`)"
      - "traefik.http.routers.sonarr.entrypoints=https"
      - "traefik.http.routers.sonarr.tls.certresolver=letsencrypt"
      - "traefik.http.routers.sonarr.middlewares=authelia@docker"
      - "traefik.http.services.sonarr.loadbalancer.server.port=8989"
```

## Backup

### What to Backup

- `/config/*/` - All config directories
- Databases are in config directories

### Automated Backup

Each *arr app has built-in backup:
1. **System** > **Backup**
2. Configure schedule
3. Backup stored in `/config/Backups/`

## Troubleshooting

### Logs

```bash
docker logs sonarr
docker logs radarr
docker logs prowlarr
```

### Common Issues

1. **Import fails**
   - Check permissions (PUID/PGID)
   - Verify directory structure
   - Check disk space

2. **No indexers in Sonarr/Radarr**
   - Sync from Prowlarr: Settings > Apps > Sync

3. **Downloads stuck**
   - Check download client connection
   - Verify category matches

4. **Hardlinks not working**
   - Same filesystem required
   - Check mount paths match

### API Keys

Find API keys at:
- Sonarr: Settings > General
- Radarr: Settings > General
- Prowlarr: Settings > General

## See Also

- [Media Stack Overview](index.md)
- [Jellyfin Setup](jellyfin.md)
- [Reverse Proxy](../reverse-proxy/index.md)
