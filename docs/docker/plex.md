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

## Library Optimization

### Metadata Agents

Configure optimal metadata sources in Plex settings:

| Library Type | Recommended Agent |
|--------------|-------------------|
| Movies | Plex Movie |
| TV Shows | TheTVDB or TMDB |
| Music | Plex Music |

Access via: Settings > Libraries > (Library) > Manage > Edit

### Artwork Management

Reduce storage and improve performance:

1. **Limit artwork**: Settings > Library > Artwork
   - Disable "Include actors' images in local media"
   - Limit poster/backdrop count

2. **Optimize existing artwork**:
   ```bash
   docker exec plex /usr/lib/plexmediaserver/Plex\ Media\ Scanner --optimize
   ```

3. **Reduce transcoder temp**:
   Add to docker-compose.yml:
   ```yaml
   environment:
     PLEX_PREFERENCE_1: "TranscoderTempDirectory=/transcode"
   volumes:
     - /tmp/plex-transcode:/transcode
   ```

### Collections

Organize content with collections:

1. **Automatic collections**: Enable in library settings
   - Based on franchise (MCU, Star Wars, etc.)
   - Genre collections

2. **Smart collections**: Create via Plex UI
   - Filter by year, rating, genre
   - Recently added by type

3. **Manual collections**: Organize specific items

## Troubleshooting

### Transcoding Issues

**Transcoder crashes**:

```bash
# Check logs
docker logs plex 2>&1 | grep -i transcode

# Verify temp directory is writable
docker exec plex ls -la /transcode

# Check available disk space for transcode
df -h /tmp/plex-transcode
```

**Slow transcoding**:

1. Check hardware transcoding is enabled:
   - Settings > Transcoder > Use hardware acceleration when available

2. Verify GPU access:
   ```bash
   docker exec plex ls -la /dev/dri
   ```

3. Monitor transcoding:
   ```bash
   docker exec plex top -b -n1 | grep -i plex
   ```

**Audio transcoding only**:

- Usually due to codec mismatch
- Try different audio track
- Consider Plex Pass for hardware audio transcoding

### Remote Access Problems

**Server not accessible remotely**:

1. Check port forwarding:
   ```bash
   # From inside container
   docker exec plex curl -s https://plex.tv/api/resources | grep -i connection
   ```

2. Verify firewall:
   ```bash
   sudo ufw status | grep 32400
   ```

3. Test manual port:
   - Settings > Remote Access > Manually specify public port
   - Try 32400

**Relay mode (slow)**:

- Port forwarding not working
- Check router UPnP or manual forwarding
- Verify ISP doesn't block port

### Database Corruption

**Symptoms**: Missing items, slow library, crashes

**Repair**:

```bash
# Stop Plex
docker compose stop plex

# Backup database
cp /mnt/tank/containers/plex/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db \
   /mnt/tank/backups/plex-db-$(date +%Y%m%d).db

# Start Plex (it will repair on startup)
docker compose start plex

# Check logs for repair status
docker logs plex 2>&1 | grep -i database
```

**Full database rebuild** (last resort):

```bash
# Stop Plex
docker compose stop plex

# Remove database (metadata will be re-downloaded)
rm /mnt/tank/containers/plex/Library/Application\ Support/Plex\ Media\ Server/Plug-in\ Support/Databases/com.plexapp.plugins.library.db*

# Start Plex
docker compose start plex

# Re-scan all libraries via UI
```

### Playback Issues

**Buffering**:

1. Check network bandwidth
2. Reduce streaming quality in client
3. Enable Direct Play/Direct Stream where possible

**"Server not powerful enough"**:

1. Lower transcoding quality
2. Enable hardware transcoding
3. Pre-transcode using optimized versions

**Subtitles causing transcode**:

- Use SRT subtitles instead of image-based
- Enable "Burn subtitles" = "Automatic"

## Restore Procedure

### Config Restoration from Snapshot

1. Stop Plex:
   ```bash
   docker compose stop plex
   ```

2. Identify snapshot:
   ```bash
   zfs list -t snapshot | grep plex
   ```

3. Rollback:
   ```bash
   sudo zfs rollback tank/containers/plex@target-snapshot
   ```

4. Restart:
   ```bash
   docker compose start plex
   ```

5. Verify:
   - Access web UI
   - Check libraries are present
   - Verify watched status

### Metadata Recovery

If config is lost but media files exist:

1. Start fresh Plex container

2. Re-add libraries pointing to same media paths

3. Use Plex's "Scan Library Files" for each library

4. Watched status recovery:
   - Trakt plugin can restore watched status
   - Or restore from database backup

### Database Backup and Restore

Create regular database backups:

```bash
#!/bin/bash
# /usr/local/bin/backup-plex-db.sh

PLEX_DB="/mnt/tank/containers/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases"
BACKUP_DIR="/mnt/tank/backups/plex"

mkdir -p "$BACKUP_DIR"

# Stop Plex briefly for consistent backup
docker compose -f ~/docker/plex/docker-compose.yml stop plex

# Copy database files
cp "$PLEX_DB/com.plexapp.plugins.library.db" \
   "$BACKUP_DIR/library-$(date +%Y%m%d).db"

# Restart Plex
docker compose -f ~/docker/plex/docker-compose.yml start plex

# Keep last 7 backups
find "$BACKUP_DIR" -name "library-*.db" -mtime +7 -delete
```

Restore from database backup:

```bash
docker compose stop plex

cp /mnt/tank/backups/plex/library-YYYYMMDD.db \
   "/mnt/tank/containers/plex/Library/Application Support/Plex Media Server/Plug-in Support/Databases/com.plexapp.plugins.library.db"

docker compose start plex
```
