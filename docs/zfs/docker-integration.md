# Docker Integration

How Docker fits with ZFS on this build. The short version has changed since the pivot to Incus: **Docker no longer runs directly on the host.** It runs nested inside an Incus system container, and persistent service data lives on host ZFS datasets that are bind-mounted through a **two-layer chain** — host dataset → into the Incus container → into the compose service.

This page covers the ZFS side of that chain (which host datasets, what properties). The mechanics of the nesting itself — creating the Incus container, installing Docker in it, wiring the bind mounts — live in [Docker inside Incus](../incus/docker-in-incus.md), the source of truth. This page cross-references it rather than duplicating it.

## The chosen pattern

```
+-----------------------------------------------------------+
|  Host (Ubuntu, root-on-ZFS)                               |
|                                                           |
|   Incus system container "docker-host" (nesting=true)     |
|   +---------------------------------------------------+   |
|   |  Docker (overlay2, inside the container's rootfs) |   |
|   |     compose service                               |   |
|   |        ^  bind mount (layer 2, in compose file)   |   |
|   +--------|------------------------------------------+   |
|            |  bind mount (layer 1, Incus disk device) |
|   host ZFS datasets:                                      |
|     /tank/nextcloud-data   /tank/media                    |
|     /rpool/db              /rpool/ai                       |
|        ^ snapshotted, compressed, replicated              |
+-----------------------------------------------------------+
```

Why this shape:

- **Incus is the one virtualization layer.** Docker workloads nest inside an Incus system container (`security.nesting=true`), running the existing `docker-compose.yml` stacks essentially unchanged. See the repo-root `START.md` for the intent and [Docker inside Incus](../incus/docker-in-incus.md) for the how.
- **The container's own root filesystem is a ZFS dataset** under `rpool/incus` (Incus's storage driver) — so Docker's overlay2 layers, images, and build cache sit on ZFS via the instance's rootfs, managed by Incus, not on a separate host ext4 root.
- **Persistent service data stays on dedicated host datasets** (`tank/nextcloud-data`, `tank/media`, `rpool/db`, `rpool/ai`) that get ZFS snapshots, compression, and send/receive — bind-mounted *in*, never copied into the disposable container rootfs.
- **Bind mounts beat named volumes** for transparency: you can `ls`, `tar`, `rsync`, `zfs snapshot` the data on the host without touching Docker or Incus internals.

## The two-layer bind-mount chain

This is the one genuinely new idea versus bare-host Docker. A host dataset reaches a compose service through **two** bind mounts, not one:

1. **Layer 1 (Incus `disk` device):** expose the host dataset inside the `docker-host` container at a path.
   ```bash
   incus config device add docker-host nextcloud-data disk \
     source=/tank/nextcloud-data path=/data/nextcloud
   ```
2. **Layer 2 (compose `volumes:`):** the compose file inside the container bind-mounts that in-container path into the service, exactly as it would have on bare host.
   ```yaml
   volumes:
     - /data/nextcloud:/var/www/html/data
   ```

Full worked examples (including the idmap/permission handling) are in [Docker inside Incus → the two-layer bind-mount chain](../incus/docker-in-incus.md). The rest of *this* page is about the host-dataset end of layer 1.

## Host datasets for services

The persistent-data datasets, per [Datasets](datasets.md):

```
rpool/                  # fast 4 TB NVMe
+-- db/                 # Postgres / MariaDB data; recordsize=16K
+-- ai/                 # Ollama / model files; recordsize=1M, compression=off

tank/                   # slow 2 TB NVMe
+-- nextcloud-data/     # Nextcloud user files (snapshot-critical)
+-- nextcloud-app/      # Nextcloud config / apps / themes
+-- media/              # Plex / Jellyfin library
+-- backups/            # cold archive target
```

There is intentionally **no `tank/containers/<svc>` tree** anymore. Under the old bare-host design each service got its own `tank/containers/<svc>` bind-mount target; now the disposable container state lives in the Incus container's rootfs (`rpool/incus`), and only the data that's worth snapshotting/replicating gets a dedicated host dataset above. Create those with the properties in [Datasets](datasets.md).

!!! note "What the lab automation creates"
    The shipped lab Ansible playbook (`src/msai_setup/lab/ansible/playbooks/zfs.yml`) provisions a teaching pool for the VirtualBox lab, not the real-hardware `rpool`/`tank` split. Treat the lab's dataset layout as ZFS practice; the canonical production datasets are the ones in [Datasets](datasets.md).

## Recordsize per workload — the cheat-sheet

What to set on each **host** dataset before bind-mounting it in:

| Dataset | Recordsize | Compression | Notes |
|---|---|---|---|
| `rpool/db` | 16 K | `lz4` | Match Postgres/MariaDB page size. |
| `rpool/ai` | 1 M | `off` | GGUF/safetensors already compressed; skip the test. |
| `tank/nextcloud-data` | 128 K (default) | `lz4` | Mixed file sizes; default works. |
| `tank/nextcloud-app` | 128 K (default) | `lz4` | Code/config; default works. |
| `tank/media` | 1 M | `lz4` | Large sequential reads. |

See [Datasets → Per-dataset properties](datasets.md#per-dataset-properties-for-this-build) for the canonical setup commands. The Incus container's rootfs (where Docker's overlay2 actually lives) inherits `rpool/incus`'s properties — you don't tune that per-service.

## Compose patterns (inside the Docker-in-Incus container)

The compose files themselves are nearly identical to bare-host Docker — they just bind-mount the **in-container** path that Incus's layer-1 device exposed, not the raw host path.

### Single-volume service

```yaml
services:
  uptime-kuma:
    image: louislam/uptime-kuma:1
    restart: unless-stopped
    ports:
      - "127.0.0.1:3001:3001"
    volumes:
      - /data/uptime-kuma:/app/data      # /data/uptime-kuma = an Incus disk device -> a host dataset
```

### Multi-volume service (Nextcloud)

```yaml
services:
  nextcloud:
    image: nextcloud:31-apache
    restart: unless-stopped
    volumes:
      - /data/nextcloud-app:/var/www/html        # <- host tank/nextcloud-app
      - /data/nextcloud-data:/var/www/html/data  # <- host tank/nextcloud-data
```

Splitting `nextcloud-app` and `nextcloud-data` is still deliberate: `nextcloud-data` is the snapshot- and replication-critical dataset; `nextcloud-app` is recoverable by reinstalling the container. Different snapshot retention per dataset (frequent for data, weekly for app).

### Database container

```yaml
services:
  postgres:
    image: postgres:16-alpine
    restart: unless-stopped
    volumes:
      - /data/db-postgres:/var/lib/postgresql/data   # <- host rpool/db
    environment:
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
```

The host `rpool/db` dataset is `recordsize=16K`; **don't** set `sync=disabled` on it (Postgres relies on fsync). It's on the fast drive precisely so database IO isn't stuck behind the slow x1 link.

## Permissions and the idmap wrinkle

Each service's container image documents the UID/GID it runs as. Pre-own the **host** dataset to match:

```bash
# Nextcloud (UID 33 = www-data)
sudo chown -R 33:33 /tank/nextcloud-data /tank/nextcloud-app

# Postgres (UID 999 in the official image)
sudo chown -R 999:999 /rpool/db
sudo chmod 700 /rpool/db
```

But there's an extra layer now: an **unprivileged Incus container remaps UIDs**, so the ownership the nested Docker service ultimately needs may not be the raw host UID. Incus bridges this with idmapped mounts automatically on 26.04's kernel; if a bind-mounted dataset shows up as `nobody:nogroup` inside the container, that mapping is the cause — see [Incus storage → bind mounts and idmap](../incus/storage.md#bind-mounting-host-datasets-into-containers) and [Docker inside Incus](../incus/docker-in-incus.md). For `linuxserver.io` images, `PUID`/`PGID` env vars still let the container chown at startup.

## Snapshot before risky operations

The workflow is unchanged except that `docker compose` runs *inside* the Incus container:

```bash
# Snapshot the host data datasets first
sudo zfs snapshot tank/nextcloud-data@before-update-$(date +%F)
sudo zfs snapshot tank/nextcloud-app@before-update-$(date +%F)

# Pull + restart inside the Docker-in-Incus container
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose pull && docker compose up -d'

# If the update breaks it:
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose down'
sudo zfs rollback tank/nextcloud-data@before-update-$(date +%F)
sudo zfs rollback tank/nextcloud-app@before-update-$(date +%F)
incus exec docker-host -- sh -c 'cd /opt/compose/nextcloud && docker compose up -d'
```

## sanoid policy for service data

Retention per host dataset (mirrors the canonical [backup config](../operations/backup.md#zfs-snapshots)):

```ini
# /etc/sanoid/sanoid.conf

[tank/nextcloud-data]
    use_template = data

[tank/nextcloud-app]
    use_template = data

[rpool/db]
    use_template = db
    recursive = yes

[rpool/incus]
    use_template = data
    recursive = yes      # covers the container rootfs (Docker overlay2 lives here)

[tank/media]
    autosnap = no        # snapshot manually before big imports
    autoprune = no

[rpool/ai]
    autosnap = no        # models are big; snapshots rarely useful
    autoprune = no
```

`rpool/incus` is included so the `docker-host` container's rootfs (and thus Docker's overlay2 state) has retained snapshots — but that's sanoid's job, not a per-service concern. Let sanoid own the `rpool/incus` schedule and leave Incus's own `snapshots.schedule` unset — see [Incus storage → composing with sanoid](../incus/storage.md#composing-with-sanoid-and-syncoid).

## Named volumes vs bind mounts

Prefer bind mounts (transparent, obvious snapshot/replicate target) for anything you care about. Named Docker volumes live inside the container's rootfs on `rpool/incus` — fine for genuinely ephemeral state, but opaque. This build's rule (from `START.md`): **ZFS datasets bind-mounted in, never opaque named volumes for important data.**

## Footguns

### Dataset not mounted before the container starts

If a host dataset isn't mounted when Incus starts the `docker-host` container, its layer-1 `disk` device can expose an empty directory, and the nested service writes into nothing. On a normal boot `zfs-mount.service` runs before Incus; after manual restore work, confirm the host mounts first:

```bash
findmnt /tank/nextcloud-data
mountpoint /rpool/db
```

### Container image upgrade changes UID

Rare, but an image can bump its internal UID between versions, breaking access to the bind-mounted data. Read changelogs before major bumps; `chown -R` the host dataset (and re-check the idmap) if you upgrade through such a change.

### Don't snapshot the container's throwaway layers separately

Docker's images, networks, and build cache live in the `docker-host` container's rootfs — rebuildable (`docker compose up` re-pulls images, recreates networks). You don't need a special snapshot strategy for them beyond `rpool/incus`'s retention; the data that matters is on the dedicated host datasets already.

## Next steps

- [Docker inside Incus](../incus/docker-in-incus.md) — the nesting, GPU passthrough, and full two-layer chain.
- [Incus storage](../incus/storage.md) — the `rpool/incus` backend and bind-mount idmap details.
- [Operations](operations.md) — scrubs, replace, expand the pools.
- [Backup & Recovery](../operations/backup.md) — high-level strategy.
