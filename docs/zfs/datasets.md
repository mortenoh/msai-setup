# Datasets

## Dataset Hierarchy

```
tank/
├── media/              # Plex / Jellyfin (large, read-heavy)
├── nextcloud-data/     # User files
├── nextcloud-app/      # App config, apps, themes
├── db/                 # Databases (MariaDB/Postgres)
├── containers/         # Misc container state
├── vm/                 # VM disks
└── backups/
```

## Create Datasets

```bash
# Media (large files, read-heavy)
sudo zfs create -o recordsize=1M tank/media

# Nextcloud user data
sudo zfs create tank/nextcloud-data

# Nextcloud app config
sudo zfs create tank/nextcloud-app

# Databases (small records)
sudo zfs create -o recordsize=16K tank/db

# Container state
sudo zfs create tank/containers

# VM disks
sudo zfs create -o recordsize=64K tank/vm

# Backups
sudo zfs create tank/backups
```

## Dataset Properties

### View Properties

```bash
zfs get all tank/media
zfs get compression,recordsize,quota tank/media
```

### Per-Dataset Tuning

| Dataset | recordsize | Notes |
|---------|------------|-------|
| media | 1M | Large sequential files |
| db | 16K | Small random I/O |
| vm | 64K | Balance for VM workloads |
| (others) | 128K | Default, general purpose |

## Permissions

Set ownership for services:

```bash
# Nextcloud (www-data is UID 33 in container)
sudo chown -R 33:33 /mnt/tank/nextcloud-data
sudo chown -R 33:33 /mnt/tank/nextcloud-app

# Plex (plex user is UID 997)
sudo chown -R 997:997 /mnt/tank/media
```

## List Datasets

```bash
# List all datasets
zfs list

# Show with properties
zfs list -o name,used,avail,refer,mountpoint
```

## Nested Datasets

Create nested datasets for finer control:

```bash
sudo zfs create tank/media/movies
sudo zfs create tank/media/tv
sudo zfs create tank/media/music
```

Each inherits parent properties but can override them.
