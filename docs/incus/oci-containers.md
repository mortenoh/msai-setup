# OCI application containers — Docker images without a Docker daemon

Incus can launch a Docker/OCI image **directly as an Incus instance**, with no nested Docker daemon in between. This is the lighter-weight alternative to [Docker-in-Incus](docker-in-incus.md): where that approach runs a full Docker Engine inside a system container to host a whole `docker-compose.yml`, an OCI application container runs *one image* as a first-class Incus instance — same `incus` CLI, same ZFS dataset per instance, same `incusbr0` networking, no Docker anywhere.

Use it for the simple single-image services on this build. Reach for [nested Docker](docker-in-incus.md) when the service is really a multi-container compose stack. The [decision guide](#when-to-use-which) at the bottom draws the line.

!!! note "This is a newer path than nested Docker"
    OCI support landed in Incus 6.3 and is younger and less battle-tested than the nested-Docker route the rest of these docs treat as the default. The [Incus index](index.md) flags it as the "newer, less-proven path" for exactly this reason. Prefer it where it fits cleanly; fall back to nested Docker when a service leans on compose features OCI containers don't have (below).

## Host prerequisite: skopeo and umoci

OCI support needs **`skopeo`** and **`umoci`** present on the host `PATH` — Incus uses them to pull and unpack OCI images. Some Incus packagings bundle them; if `incus launch docker:...` fails complaining it can't fetch the image, install them:

```bash
sudo apt install -y skopeo umoci
```

Verified against the [Incus OCI image documentation](https://linuxcontainers.org/incus/docs/main/) — these are the two external commands the feature depends on.

## The commands

### Add the OCI remote (once)

The syntax is the one already established in [Core concepts](concepts.md) and the [Quick reference](reference/quick-reference.md):

```bash
incus remote add docker https://docker.io --protocol=oci
incus remote list                                    # 'docker' now listed, protocol oci
```

`--protocol=oci` is what tells Incus to treat `docker.io` as an image registry rather than another Incus server. You add it once; it persists.

### Launch an image

```bash
# Launch (pull + unpack + start) a single image as an Incus instance
incus launch docker:nginx my-nginx

# Try one ephemerally with a console attached (auto-deletes on stop) — good for testing
incus launch docker:hello-world --ephemeral --console
```

The instance shows up in `incus list` like any other, gets a `incusbr0` IP, and is a ZFS dataset under `hot/incus` — all the [Storage](storage.md) and [Networking](networking.md) machinery applies unchanged.

### Environment variables

Set the image's environment with `-c environment.<KEY>=<value>` (the OCI equivalent of compose's `environment:`):

```bash
incus launch docker:mysql mysql-db \
  -c environment.MYSQL_DATABASE=appdb \
  -c environment.MYSQL_USER=app \
  -c environment.MYSQL_PASSWORD=changeme
```

### Persistent data

An OCI container's writable layer is ephemeral just like a Docker container's, so persistent data goes on a `disk` device backed by a host ZFS dataset — the **same bind-mount-into-ZFS convention** the rest of this build uses (see [Storage](storage.md) and [`zfs/docker-integration.md`](../zfs/docker-integration.md)):

```bash
# Expose a host dataset at the path the image writes to
incus config device add my-nginx site disk \
  source=/mnt/tank/containers/my-nginx path=/usr/share/nginx/html
```

This is a single bind mount, not the two-layer chain of the [nested-Docker case](docker-in-incus.md#step-3-compose-zfs-storage-the-two-layer-bind-mount-chain) — there is no inner Docker to bind through. Pre-create and `chown` the dataset to the image's UID, minding the unprivileged-container idmap ([Storage](storage.md) covers this).

### Exposing a port

OCI containers attach to `incusbr0` like every other instance, so exposure is the standard [proxy-device pattern](networking.md#exposing-an-instance-service-to-the-lan) — no Docker port-publishing involved:

```bash
incus config device add my-nginx http proxy \
  listen=tcp:0.0.0.0:8080 connect=tcp:127.0.0.1:80 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 8080 proto tcp
```

Because `bind=host`, the listener is in the host namespace and UFW filters it — consistent with how [Networking](networking.md) exposes any instance.

## What this pattern is and isn't good for

Be honest about the boundary. OCI application containers give you Incus-native single images with real environment variables, persistent volumes (disk devices), and network access. They do **not** reproduce `docker compose`'s orchestration.

**Good fit — reach for OCI containers when:**

- The service is **one image, one process** (a dashboard, a status page, a single reverse-proxied web app).
- Its state is **one or two volumes** and a handful of environment variables.
- It doesn't need other containers started alongside it with dependency ordering.

**Poor fit — use [nested Docker](docker-in-incus.md) instead when:**

- The stack is **multiple containers wired together** — an app plus its database plus Redis — that resolve each other by service name over a compose-internal network. OCI containers don't provide compose's automatic inter-container DNS network; you'd be hand-building links between separate Incus instances.
- The compose file uses **`depends_on`, container `links`, or `restart:` directives** — Incus OCI does not honor these. Startup ordering and restart policy are managed the Incus way (`boot.autostart`, `boot.autostart.priority`) or not at all.
- The service ships and expects to be run **as a compose bundle** (Nextcloud + MariaDB + Redis, the monitoring stack, the Ollama + Open WebUI + nginx stack) — those belong in a nesting-enabled container running their `docker-compose.yml` unchanged.

The rule of thumb: if you'd otherwise write a `docker-compose.yml` with **one service block**, an OCI container fits. If it has **two or more service blocks that talk to each other**, use nested Docker.

## Worked example: Uptime Kuma as an OCI container

[Uptime Kuma](../services/uptime-kuma/index.md) is an ideal fit — a single image, a single persistent volume (`/app/data`), no companion database, no compose-internal networking. Its documented compose file is effectively one service:

```yaml
# The existing docker-compose.yml (from services/uptime-kuma/index.md)
services:
  uptime-kuma:
    image: louislam/uptime-kuma:latest
    ports:
      - "127.0.0.1:3001:3001"
    volumes:
      - ./data:/app/data
```

As a native OCI container that becomes:

```bash
# Once: add the OCI remote (if not already added)
incus remote add docker https://docker.io --protocol=oci

# Persistent data on a ZFS dataset, chowned for the image's user
sudo zfs create tank/containers/uptime-kuma
sudo chown -R 1000:1000 /mnt/tank/containers/uptime-kuma

# Launch the image as an Incus instance, autostart with the host
incus launch docker:louislam/uptime-kuma uptime-kuma \
  --profile default \
  -c boot.autostart=true

# Attach the data volume (the image stores its DB under /app/data)
incus config device add uptime-kuma data disk \
  source=/mnt/tank/containers/uptime-kuma path=/app/data

# Expose the web UI to the LAN through a UFW-filtered proxy device
incus config device add uptime-kuma web proxy \
  listen=tcp:0.0.0.0:3001 connect=tcp:127.0.0.1:3001 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 3001 proto tcp
```

Notes on the translation:

- The Docker `./data:/app/data` bind mount becomes an Incus `disk` device onto `tank/containers/uptime-kuma` — the same dataset and UID (1000) the [`zfs/docker-integration.md`](../zfs/docker-integration.md) convention would use for it under bare-host Docker.
- The compose `ports: 127.0.0.1:3001:3001` (localhost-only, fronted by the reverse proxy) becomes the Incus `proxy` device plus a UFW rule — same intent, Incus-native mechanism.
- The compose file's optional `/var/run/docker.sock` mount (for Uptime Kuma's Docker-container monitors) is dropped: there is no Docker daemon here to monitor. If you specifically want container monitoring, that's a reason to run it under [nested Docker](docker-in-incus.md) instead — a concrete example of the boundary above.

Front it with the existing reverse proxy the same way as any other service ([Traefik](../services/reverse-proxy/traefik.md) / [Caddy](../services/reverse-proxy/caddy.md)); from the proxy's perspective it's just a host-reachable port on `3001`.

## When to use which

Rather than restate the [index's comparison table](index.md), the one-line decision:

- **One image, one or two volumes, no inter-container networking** → **OCI application container** (this page).
- **A `docker-compose.yml` with multiple services talking to each other, `depends_on`, or GPU-plus-ZFS stacks** → **[nested Docker in an Incus container](docker-in-incus.md)** (the build default).

Both give you per-instance ZFS datasets and `incusbr0` networking; the difference is whether you need Docker's compose orchestration *inside* the instance or can let Incus be the whole runtime.

## Verification

```bash
incus list                                   # OCI instance running, has an IP?
incus config show uptime-kuma                # image source, env, disk + proxy devices
incus config device show uptime-kuma
curl -sI http://<host-ip>:3001 | head -1     # reachable through the proxy device (once UFW allows)
```

## Next steps

- [Docker-in-Incus](docker-in-incus.md) — the nested-Docker route for full compose stacks.
- [Core concepts](concepts.md) — remotes, images, and where OCI fits.
- [Networking](networking.md) — proxy devices and UFW for exposing instances.
- [Quick reference](reference/quick-reference.md) — the OCI remote/launch commands at a glance.
