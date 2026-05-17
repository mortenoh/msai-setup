# Docker Integration

How Docker fits with ZFS on this build. Short version: **Docker uses `overlay2` on the ext4 root, services bind-mount their data into ZFS datasets**. The "ZFS storage driver" alternative is mentioned and then dismissed.

## The chosen pattern

```
+-------------------------------------------------+
|                Container runtime                |
|                                                 |
|  /var/lib/docker  (overlay2 layers, on ext4)    |  <- short-lived,
|                                                  |     not on ZFS
+-------------------------------------------------+
            |
            | bind mount
            v
+-------------------------------------------------+
|                ZFS datasets                     |
|  /mnt/tank/containers/<service>/...             |  <- persistent data,
|  /mnt/tank/nextcloud-data/                      |     snapshotted,
|  /mnt/tank/db/postgres/                         |     replicated
|  /mnt/tank/media/                                |
+-------------------------------------------------+
```

Why:

- **Docker on overlay2 + ext4 is the boring, well-supported configuration.** Every Docker bug report assumes this. Upgrades don't introduce storage-driver migrations.
- **Application data on ZFS gets snapshots, compression, send/receive, all the things.**
- **Bind mounts beat Docker volumes** for transparency and for the bind-mount-into-ZFS workflow. You can `ls`, `tar`, `rsync`, `zfs snapshot` the data without learning about Docker volume internals.

This is exactly the model START.md commits to. Every service compose example in this build uses it.

## Why not the Docker ZFS storage driver

Docker has a `zfs` storage driver that uses ZFS datasets for image layers, container layers, and volumes. It exists. It works. **Don't use it for this build:**

- Every Docker upgrade has the potential to introduce storage-driver-specific bugs that `overlay2` users never see.
- Container churn (image pulls, container destroys) creates and destroys many small datasets. Pool-wide dataset count grows; `zfs list` becomes slow.
- Most container debugging assumes overlay2 paths.
- Performance benefits are marginal for typical homelab workloads.

Reserve the ZFS driver for use cases like CI farms with extreme container churn where the dedup-friendly cloning matters.

## Docker daemon configuration

Confirm `overlay2`:

```bash
docker info | grep "Storage Driver"
# Storage Driver: overlay2
```

`/etc/docker/daemon.json` for this build:

```json
{
  "storage-driver": "overlay2",
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

If the box later runs out of space on `/`, you can move `/var/lib/docker` to a dedicated location (still on ext4 for the storage driver, not on ZFS):

```bash
# stop docker
sudo systemctl stop docker
sudo rsync -aHAX /var/lib/docker/ /opt/docker/
# Edit daemon.json: "data-root": "/opt/docker"
sudo systemctl start docker
```

Don't try to put `data-root` on a ZFS dataset while keeping `storage-driver=overlay2`. Overlay-on-ZFS has known issues (kernel overlay isn't supported on ZFS as a lower-layer filesystem in many kernel versions). If you ever need Docker data on ZFS, switch the storage driver to `zfs`.

## Per-service ZFS datasets

The recommended structure:

```
tank/
+-- containers/
    +-- pihole/           # Pi-hole config + DBs
    +-- traefik/          # Traefik config + ACME cert state
    +-- authentik/        # Authentik DB / media
    +-- homepage/         # Homepage config
    +-- uptime-kuma/      # Uptime Kuma data
+-- nextcloud-data/       # Nextcloud user files (separate from container state)
+-- nextcloud-app/        # Nextcloud config / apps / themes
+-- db/
    +-- postgres/         # used by Authentik etc.
    +-- mariadb/
+-- media/                # Plex / Jellyfin library
+-- ai/                   # Ollama / model files
```

Create with appropriate properties — see [Datasets](datasets.md).

## Compose patterns

### Bind mount into ZFS

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    container_name: uptime-kuma
    restart: unless-stopped
    ports:
      - "127.0.0.1:3001:3001"
    volumes:
      - /mnt/tank/containers/uptime-kuma:/app/data
```

The bind mount is just a host path. ZFS handles the rest (compression, snapshots, etc.).

### Multi-volume service (Nextcloud)

```yaml
services:
  nextcloud:
    image: nextcloud:31-apache
    container_name: nextcloud
    restart: unless-stopped
    volumes:
      - /mnt/tank/nextcloud-app:/var/www/html             # app code + config
      - /mnt/tank/nextcloud-data:/var/www/html/data        # user data
    # ...
```

Splitting `nextcloud-app` and `nextcloud-data` is deliberate:

- `nextcloud-data` is the snapshot-critical, replication-critical dataset.
- `nextcloud-app` changes during app upgrades but is recoverable by reinstalling the container.

This split lets you set different snapshot retention per dataset (frequent for data, weekly for app).

### Database container

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: postgres-authentik
    restart: unless-stopped
    volumes:
      - /mnt/tank/db/postgres:/var/lib/postgresql/data
    environment:
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: authentik
```

For Postgres specifically, set the bind-mount target's dataset to `recordsize=16K` and **don't** set `sync=disabled` (Postgres relies on fsync). Optionally `primarycache=metadata` if the DB is bigger than ARC and you want to avoid double-caching.

## Recordsize per workload — the cheat-sheet

What to set on each bind-mount target:

| Dataset | Recordsize | Compression | Notes |
|---|---|---|---|
| `tank/containers/*` | 128 K (default) | `lz4` | Default is fine for most. |
| `tank/db/postgres` | 16 K | `lz4` | Match Postgres page size. |
| `tank/db/mariadb` | 16 K | `lz4` | Match MariaDB InnoDB page size. |
| `tank/nextcloud-data` | 128 K | `lz4` | Mixed file sizes; default works. |
| `tank/nextcloud-app` | 128 K | `lz4` | Code/config; default works. |
| `tank/media` | 1 M | `lz4` | Large sequential reads. |
| `tank/ai` | 1 M | `off` | GGUF/safetensors already compressed; skip the test. |

See [Datasets → Per-dataset properties](datasets.md#per-dataset-properties-for-this-build) for the canonical setup commands.

## Permissions

Each container image documents the UID/GID it runs as. Pre-create the bind-mount target with the right ownership:

```bash
sudo mkdir -p /mnt/tank/containers/uptime-kuma
sudo chown -R 1000:1000 /mnt/tank/containers/uptime-kuma

# Nextcloud (UID 33 = www-data)
sudo mkdir -p /mnt/tank/nextcloud-{data,app}
sudo chown -R 33:33 /mnt/tank/nextcloud-data /mnt/tank/nextcloud-app

# Postgres (UID 999 in the official image)
sudo mkdir -p /mnt/tank/db/postgres
sudo chown -R 999:999 /mnt/tank/db/postgres
chmod 700 /mnt/tank/db/postgres
```

For images that respect `PUID`/`PGID` env vars (linuxserver.io family — Sonarr, Radarr, Jellyfin, etc.), the container takes care of `chown` at startup; you just need to set `PUID=1000` `PGID=1000` (or whatever your host user is) in the compose `environment`.

## Snapshot before risky operations

Built into the workflow:

```bash
# Before pulling a new container image
sudo zfs snapshot tank/nextcloud-data@before-update-$(date +%F)
sudo zfs snapshot tank/nextcloud-app@before-update-$(date +%F)

cd /path/to/compose/nextcloud
docker compose pull
docker compose up -d

# If the update breaks Nextcloud:
docker compose down
sudo zfs rollback tank/nextcloud-data@before-update-2026-05-17
sudo zfs rollback tank/nextcloud-app@before-update-2026-05-17
docker compose up -d
```

Wrapping this in a small script is worth it:

```bash
# /usr/local/bin/docker-snapshot
#!/bin/bash
set -euo pipefail

SERVICE=${1:?usage: docker-snapshot <service>}
DATE=$(date +%F-%H%M)

case "$SERVICE" in
  nextcloud)
    sudo zfs snapshot "tank/nextcloud-data@before-${DATE}"
    sudo zfs snapshot "tank/nextcloud-app@before-${DATE}"
    ;;
  postgres-*)
    sudo zfs snapshot "tank/db/postgres@before-${DATE}"
    ;;
  *)
    sudo zfs snapshot "tank/containers/${SERVICE}@before-${DATE}"
    ;;
esac
```

```bash
docker-snapshot nextcloud
docker compose pull && docker compose up -d
```

## sanoid policy for containers

Different services want different snapshot retention:

```ini
# /etc/sanoid/sanoid.conf

[template_data]
    hourly = 24
    daily = 30
    weekly = 4
    monthly = 6
    autosnap = yes
    autoprune = yes

[template_db]
    frequently = 6
    hourly = 48
    daily = 30
    autosnap = yes
    autoprune = yes

[template_disposable]
    autosnap = no
    autoprune = yes
    daily = 7

[tank/nextcloud-data]
    use_template = data

[tank/nextcloud-app]
    use_template = data

[tank/db]
    use_template = db
    recursive = yes

[tank/containers]
    use_template = disposable
    recursive = yes

[tank/media]
    autosnap = no   # snapshot manually before big imports
    autoprune = no

[tank/ai]
    autosnap = no   # models are big; snapshots are rarely useful
    autoprune = no
```

The `disposable` template only prunes — sanoid doesn't take new snapshots automatically, but old ones eventually go away.

## What about Docker volumes (named)?

A named volume (`docker volume create`) lives under `/var/lib/docker/volumes/` by default. It's just another directory on ext4. For this build, prefer bind mounts because:

- Bind mounts are transparent — you `ls /mnt/tank/...` and see your data.
- Bind mounts let you set the host-side path explicitly (snapshot/replicate target is obvious).
- Named volumes inherit Docker's lifecycle; they survive `docker rm` but get destroyed by `docker volume prune`.

There's nothing wrong with named volumes for ephemeral state (the Postgres data of a CI scratch service, etc.). For anything you care about: bind mount.

## What about the Docker network state, images, build cache?

That lives in `/var/lib/docker/` on ext4 root. It's all rebuildable:

- Images can be re-pulled.
- Networks are recreated by `docker compose up`.
- Build cache is rebuilt by the next build.

Don't snapshot `/var/lib/docker`. It would be a huge waste of space and confusing on restore. If the host's root filesystem dies, the rebuild path is: reinstall OS → re-import ZFS → `docker compose up -d` for each service, which re-creates containers and re-pulls images. The data is all on ZFS already.

## Watch out for these footguns

### Bind-mounted into the wrong place

If the dataset isn't mounted yet when Docker starts, the bind mount creates an empty directory **on root** at `/mnt/tank/nextcloud-data/`. The container happily writes to it. ZFS later mounts the dataset over the top, hiding the data.

Mitigation: `zfs-mount.service` runs before `docker.service` on a normal boot. If you're doing manual restore work, **mount the dataset first**, then start Docker. Worth checking after a reboot:

```bash
findmnt /mnt/tank
mountpoint /mnt/tank/nextcloud-data
```

### Container image upgrade changes UID

Some images bump their internal user UID between versions (rare but it happens). After upgrade, the running container can't write to the bind-mount because the host directory is owned by the old UID. Symptom: container starts, complains about permissions, restart-loops.

Mitigation: read changelogs before major version bumps; `chown -R` the bind target if you upgrade through such a change.

### `docker compose down -v` destroys named volumes

That `-v` flag does what it says: removes named volumes. Bind mounts are untouched (they're on ZFS, not in Docker's namespace). Knowing the difference matters.

## Next steps

- [Operations](operations.md) — scrubs, replace, expand the pool.
- [Backup & Recovery](../operations/backup.md) — high-level strategy.
- Service docs:
  - [Docker setup](../docker/setup.md)
  - [Nextcloud](../docker/nextcloud.md)
  - [Plex](../docker/plex.md)
  - [Pi-hole](../services/pi-hole/index.md)
