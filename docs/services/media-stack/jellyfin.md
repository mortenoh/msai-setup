# Jellyfin

Jellyfin is a free, open-source media server for streaming your personal media library.

## Docker Compose Setup

### Basic Setup

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    restart: unless-stopped
    user: 1000:1000
    environment:
      - TZ=Europe/Oslo
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /data/media:/media:ro
    ports:
      - "8096:8096"
    networks:
      - proxy

networks:
  proxy:
    external: true
```

### With Hardware Transcoding

```yaml
services:
  jellyfin:
    image: jellyfin/jellyfin:latest
    container_name: jellyfin
    restart: unless-stopped
    user: 1000:1000
    environment:
      - TZ=Europe/Oslo
    volumes:
      - ./config:/config
      - ./cache:/cache
      - /data/media:/media:ro
    ports:
      - "8096:8096"
    # Intel Quick Sync
    devices:
      - /dev/dri:/dev/dri
    group_add:
      - "video"
      - "render"
    networks:
      - proxy
```

### AMD VAAPI Transcoding (MS-S1 MAX)

The Strix Halo iGPU exposes hardware video encode/decode through VAAPI.
The Compose snippet above (`/dev/dri` passthrough + `video`/`render`
groups) is the right setup — turn on VAAPI in the Jellyfin dashboard
(see [Transcoding Configuration](#transcoding-configuration)).

## Initial Setup

1. Access Jellyfin at `http://localhost:8096`
2. Create admin account
3. Add media libraries:
   - Movies: `/media/movies`
   - TV Shows: `/media/tv`
   - Music: `/media/music`

## Library Organization

### Recommended Structure

```
/media/
├── movies/
│   ├── Movie Name (2020)/
│   │   ├── Movie Name (2020).mkv
│   │   └── Movie Name (2020).srt
│   └── Another Movie (2021)/
│       └── Another Movie (2021).mp4
├── tv/
│   └── Show Name/
│       ├── Season 01/
│       │   ├── Show Name - S01E01 - Episode Title.mkv
│       │   └── Show Name - S01E02 - Episode Title.mkv
│       └── Season 02/
│           └── ...
└── music/
    └── Artist/
        └── Album/
            ├── 01 - Track.flac
            └── 02 - Track.flac
```

## Transcoding Configuration

### Enable Hardware Transcoding

1. Go to **Dashboard** > **Playback** > **Transcoding**
2. Select hardware acceleration:
   - **VAAPI** for the MS-S1 MAX (AMD Strix Halo iGPU)
3. Enable hardware decoding for supported codecs

### Codec Support (VAAPI on Strix Halo)

| Codec | Decode | Encode |
|-------|--------|--------|
| H.264 | Yes | Yes |
| HEVC  | Yes | Yes |
| AV1   | Yes | Yes |
| VP9   | Yes | No  |

## User Management

### Create Users

1. Go to **Dashboard** > **Users** > **Add User**
2. Configure permissions:
   - Library access
   - Download permission
   - Remote access

### Parental Controls

1. Edit user > **Access**
2. Set content restrictions:
   - Maximum parental rating
   - Block unrated content

## Plugins

### Recommended Plugins

1. **Open Subtitles** - Auto-download subtitles
2. **Trakt** - Sync watch history
3. **Fanart** - Enhanced artwork
4. **TMDb** - Better metadata

### Install Plugins

1. Go to **Dashboard** > **Plugins** > **Catalog**
2. Find and install plugins
3. Restart Jellyfin if required

### Open Subtitles Setup

1. Install plugin
2. Go to **Dashboard** > **Plugins** > **Open Subtitles**
3. Enter your OpenSubtitles credentials
4. Configure languages

## Remote Access

### Direct Access

Forward port 8096 on your router.

### With Reverse Proxy (Recommended)

```yaml
# Traefik labels
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.jellyfin.rule=Host(`media.example.com`)"
  - "traefik.http.routers.jellyfin.entrypoints=https"
  - "traefik.http.routers.jellyfin.tls.certresolver=letsencrypt"
  - "traefik.http.services.jellyfin.loadbalancer.server.port=8096"
```

Configure in Jellyfin:
1. **Dashboard** > **Networking**
2. Set "Base URL" if using path routing
3. Enable "Allow remote connections"

## Clients

### Official Apps

- Web browser
- Android / Android TV
- iOS / tvOS
- Roku

### Third-Party Apps

- **Infuse** (iOS/tvOS) - Premium player
- **Swiftfin** (iOS) - Native Swift client
- **Findroid** (Android) - Material Design
- **Jellyfin Media Player** (Desktop)

## Performance Tuning

### Cache Settings

```yaml
volumes:
  - ./cache:/cache
environment:
  - JELLYFIN_CACHE_DIR=/cache
```

### Memory Limits

```yaml
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 1G
```

### SSD for Metadata

Store config on SSD for faster library scans:

```yaml
volumes:
  - /ssd/jellyfin/config:/config
  - /ssd/jellyfin/cache:/cache
  - /hdd/media:/media:ro
```

## Backup

### What to Backup

- `/config` - All settings, users, metadata
- Database: `/config/data/jellyfin.db`

### Backup Script

```bash
#!/bin/bash
BACKUP_DIR="/backups/jellyfin"
DATE=$(date +%Y%m%d)

# Stop container
docker stop jellyfin

# Backup config
tar -czvf "$BACKUP_DIR/jellyfin-$DATE.tar.gz" /path/to/config

# Start container
docker start jellyfin

# Keep last 7 backups
find "$BACKUP_DIR" -name "jellyfin-*.tar.gz" -mtime +7 -delete
```

## Troubleshooting

### Check Logs

```bash
docker logs jellyfin
# Or check /config/log/
```

### Common Issues

1. **No hardware transcoding**
   - Check device permissions
   - Verify drivers installed on host
   - Check container has access to `/dev/dri`

2. **Library not scanning**
   - Check file permissions
   - Verify mount paths
   - Check naming convention

3. **Playback issues**
   - Try direct play instead of transcoding
   - Check client bandwidth settings
   - Verify codec support

### Verify Hardware Access

```bash
# Check if the GPU device is accessible
docker exec jellyfin ls -la /dev/dri

# Check VAAPI (the path used on the MS-S1 MAX)
docker exec jellyfin vainfo
```

## See Also

- [Media Stack Overview](index.md)
- [*arr Stack](arr-stack.md)
- [Reverse Proxy](../reverse-proxy/index.md)
