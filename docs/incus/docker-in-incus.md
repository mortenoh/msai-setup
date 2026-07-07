# Docker inside Incus — migrating compose stacks

This is the full migration guide for the **default** deployment shape on this build: an existing `docker-compose.yml` stack, running **nested inside a single Incus system container** with `security.nesting=true`, essentially unchanged. The [Containers](containers.md) page covers *enabling* nesting and the [`docker-nesting` profile](profiles.md); this page is the end-to-end mechanics — creating the container, installing Docker inside it, wiring ZFS datasets and the GPU through the two layers, and reaching the services from outside.

If your service is a single image with one or two volumes and no compose-internal networking between containers, a full nested-Docker container is more machinery than you need — use a native [OCI application container](oci-containers.md) instead. The [decision guide there](oci-containers.md#when-to-use-which) draws the line.

## The mental model: two layers

Docker doesn't run on the host anymore. It runs one level down:

```
Host (Ubuntu 26.04, ZFS, Incus)
  └─ Incus system container  "media" / "ai" / ...   (security.nesting=true)
       └─ Docker Engine  (installed inside the container)
            └─ your compose services  (nginx, ollama, postgres, ...)
```

Everything that used to be "on the host" for Docker — the Docker daemon, `/var/lib/docker`, the compose files, the `docker` CLI — now lives **inside** the Incus container. The host runs only Incus. This is the isolation win from `START.md`: no Docker daemon as root on the host, and the nesting is contained.

Two practical consequences run through the rest of this page:

- **Storage is a two-layer bind-mount chain.** A host ZFS dataset is exposed to the Incus container by an Incus `disk` device, and the nested `docker-compose.yml` bind-mounts that same path again into its containers.
- **Networking is one hop further out.** A nested container's published port lands on the Incus container's namespace, not the host's; an Incus `proxy` device (or the reverse proxy) bridges that last hop to the LAN.

## Step 1 — create the Incus container for Docker

Use the `docker-nesting` profile (defined in [Profiles](profiles.md)) so you don't retype `security.nesting=true` every time. Layer resource limits and autostart on top:

```bash
incus launch images:ubuntu/24.04 media \
  --profile default --profile docker-nesting \
  -c limits.cpu=6 -c limits.memory=16GiB \
  -c boot.autostart=true \
  -d root,size=30GiB
```

- `--profile docker-nesting` sets `security.nesting=true` (unprivileged nesting — do **not** reach for `security.privileged`; see the [Containers](containers.md) note on why).
- `limits.*` size the container against the [whole-host memory budget](../operations/capacity-planning.md) — this box shares 128 GB across ARC, Ollama/GTT, VMs, and containers, so pick deliberately.
- `-d root,size=30GiB` caps the container's root dataset. This is where Docker's own image layers live (next section), so give it room for the images you'll pull — not for your *data*, which stays on bind-mounted datasets.

!!! note "Docker's storage driver on a ZFS-backed container"
    The container's root is a ZFS dataset (via Incus's [ZFS driver](storage.md)), and Docker inside it uses `overlay2` on top of that. `overlay2` over an idmapped ZFS root has historically had rough edges. If Docker fails to start or images misbehave, the usual fixes are to give `/var/lib/docker` its **own** dataset (a dedicated Incus disk device), or force `fuse-overlayfs`. See [Troubleshooting](troubleshooting.md). This is the one place the nested arrangement differs from bare-host Docker, where [`docker/setup.md`](../docker/setup.md) simply uses `overlay2` on ext4.

## Step 2 — install Docker Engine inside the container

Run the **exact same apt-repo install** this build uses for bare-host Docker (from [`docker/setup.md`](../docker/setup.md#install-docker)), just executed inside the container instead of on the host. Nothing about the install method changes — only *where* it runs.

```bash
incus exec media -- bash
# ...now inside the container:
```

```bash
# Add Docker's GPG key
sudo apt update
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add repository — fall back to 'noble' if Docker hasn't published a
# 'resolute' channel yet (common in the first weeks after Ubuntu LTS release).
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
if ! curl -sfI "https://download.docker.com/linux/ubuntu/dists/${CODENAME}/Release" >/dev/null; then
    echo "Docker repo for '$CODENAME' not published; falling back to noble"
    CODENAME=noble
fi
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install packages
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Verify Docker works nested:

```bash
docker info | grep -i 'storage driver'
docker run --rm hello-world
```

!!! note "The `ufw-docker` dance is a host concern that mostly disappears here"
    On bare-host Docker, [`docker/setup.md`](../docker/setup.md#docker-and-ufw) installs `ufw-docker` because Docker rewrites the host's iptables and bypasses UFW. Nested, Docker only rewrites the **Incus container's** firewall — it never touches the host's nftables. The host-side exposure decision moves to the Incus `proxy` device and UFW on the host (see [Networking](#step-6-reaching-the-services-from-outside) below), which is exactly the model [Incus networking](networking.md) already uses for every instance. You still keep the in-compose `127.0.0.1:` port-binding habit; it now binds the *container's* loopback.

## Step 3 — compose ZFS storage: the two-layer bind-mount chain

This is the part that needs to be right. The container's own rootfs is already a ZFS dataset, so **Docker's image layers (`/var/lib/docker`) are on ZFS for free** — inside the container's root dataset under `hot/incus/containers/media`. That is Docker's ephemeral, rebuildable state (images, container layers, build cache); it is *not* where your persistent data should live, exactly as [`zfs/docker-integration.md`](../zfs/docker-integration.md) argues for the bare-host case.

Your persistent data lives on the same tuned host datasets as always — `tank/containers/<svc>`, `tank/nextcloud-data`, `tank/db/postgres`, `tank/media`, and so on (canonical paths in [`zfs/datasets.md`](../zfs/datasets.md)). Getting that data to the innermost Docker container is a **chain of two bind mounts**:

```
Host dataset            Incus disk device            Docker bind mount
tank/containers/svc  →  (layer 1)               →    (layer 2)
mounted at              source=/mnt/tank/...          volumes:
/mnt/tank/...           path=/mnt/tank/...              - /mnt/tank/...:/app/data
                        on the Incus container         in docker-compose.yml
```

- **Layer 1 — Incus `disk` device.** Expose the host dataset's mountpoint into the Incus container. Point `path=` at the *same* path the compose file expects, so the compose file stays unchanged:

    ```bash
    # Host dataset tank/containers/uptime-kuma is mounted at /mnt/tank/containers/uptime-kuma
    incus config device add media uptime-data disk \
      source=/mnt/tank/containers/uptime-kuma \
      path=/mnt/tank/containers/uptime-kuma
    ```

- **Layer 2 — Docker bind mount.** The nested `docker-compose.yml` bind-mounts that path into the service, verbatim from the existing docs:

    ```yaml
    services:
      uptime-kuma:
        image: louislam/uptime-kuma:1
        volumes:
          - /mnt/tank/containers/uptime-kuma:/app/data
    ```

Because layer 1's `path=` matches what the compose file already writes, **the compose file needs no edit** — it bind-mounts the same host path it always did; that path just happens to be an Incus-provided view of the ZFS dataset now.

!!! note "Unprivileged idmap: expect a permissions step"
    The Incus container is unprivileged, so its root maps to a high host UID and a plain bind mount can show up `nobody:nogroup` inside the container (and therefore inside Docker). On 26.04's kernel Incus uses idmapped mounts automatically, but if you see permission surprises, that mapping is the cause — the same idmap caveat [Storage](storage.md) documents. Pre-create and `chown` the host dataset to the UID the image runs as (the [`zfs/docker-integration.md` permissions table](../zfs/docker-integration.md) lists them: www-data 33, postgres 999, PUID/PGID 1000 for linuxserver images), and confirm the mapping lands correctly inside the container.

!!! danger "Snapshot ordering is unchanged, but happens on the host"
    The [`zfs/docker-integration.md`](../zfs/docker-integration.md) footgun still applies: if the dataset isn't mounted when the mount is set up, data gets written to an empty directory that ZFS later hides. On this build `zfs-mount.service` runs before Incus starts, and the Incus `disk` device follows the host mount — so mount host datasets first, then start the container, then bring up Docker. `incus config set media boot.autostart=true` plus host `zfs-mount` ordering handles this on a normal boot.

## Step 4 — GPU passthrough for the AI stack

For an Ollama/llama.cpp container the Incus container needs the iGPU. Do **not** re-derive this — the [GPU passthrough](gpu-passthrough.md) page is the source of truth. In short, the container needs **both**:

1. a `gpu` device for `/dev/dri`, and
2. an explicit `unix-char` device for `/dev/kfd` (the ROCm compute interface the `gpu` device omits).

The cleanest path is to launch the AI container with the `gpu` profile (or the composite `ai-stack` profile that bundles GPU + nesting + generous limits) from [Profiles](profiles.md):

```bash
incus launch images:ubuntu/24.04 ai --profile default --profile ai-stack
```

Once the Incus container has the devices, **nested Docker sees them automatically** — the `docker-compose.yml` requests them with `devices: [/dev/kfd, /dev/dri]` and `group_add: [video, render]` exactly as it does on bare-host Docker, because the nested daemon inherits the device nodes the Incus container was given. The [GPU passthrough reusable-profile section](gpu-passthrough.md#a-reusable-gpu-profile) spells out this "devices visible to the nested Docker" behavior. Remember the in-container group-membership step from that page: the device nodes carry the host `render`/`video` GID, and the container user must be *in* those groups.

## Step 5 — worked example: the Ollama stack, unchanged

This is the most illustrative migration because it exercises GPU passthrough **and** ZFS bind mounts together. The goal: run [`docker/ollama-stack.md`](../docker/ollama-stack.md)'s "Complete Production Stack" compose file inside an Incus container, unchanged.

That compose file (from the Ollama Stack page) mounts two host paths and requests the GPU:

```yaml
services:
  ollama:
    image: ollama/ollama:rocm
    devices: [/dev/kfd, /dev/dri]
    group_add: [video, render]
    volumes:
      - /mnt/tank/ai/ollama:/root/.ollama
    # ...
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    ports:
      - "3000:8080"
    volumes:
      - /mnt/tank/containers/open-webui:/app/backend/data
    environment:
      - OLLAMA_BASE_URL=http://ollama:11434
    # ...
```

### Create the container with GPU + both datasets

```bash
# GPU + nesting + resources in one profile stack
incus launch images:ubuntu/24.04 ai \
  --profile default --profile ai-stack \
  -c boot.autostart=true \
  -d root,size=40GiB

# Layer 1 bind mounts — expose both host datasets at the paths the compose file expects.
# (hot/ai is this build's tuned model dataset; the compose file references /mnt/tank/ai/ollama,
#  so mount whichever host dataset holds the models at that path — the compose file stays unchanged.)
incus config device add ai ollama-models disk \
  source=/mnt/tank/ai/ollama path=/mnt/tank/ai/ollama
incus config device add ai webui-data disk \
  source=/mnt/tank/containers/open-webui path=/mnt/tank/containers/open-webui
```

The `ai-stack` profile already added the `gpu` + `/dev/kfd` devices, so `incus config device show ai` shows both alongside the two disks.

### Confirm the GPU before Docker

```bash
incus exec ai -- bash -c 'apt update && apt install -y rocminfo'
incus exec ai -- rocminfo | grep -i gfx1151     # must show the agent, as on the host
```

If that fails, fix it at the Incus layer first (see [GPU passthrough troubleshooting](gpu-passthrough.md)) — nested Docker cannot see a GPU the Incus container can't.

### Install Docker (Step 2) and bring the stack up

```bash
incus file push -r ./ollama-stack/ ai/opt/ollama-stack/
incus exec ai -- bash -c 'cd /opt/ollama-stack && docker compose up -d'

# The GPU is visible to the nested Docker container exactly as on bare host:
incus exec ai -- docker exec ollama rocminfo | grep gfx1151
```

The compose file ran **unchanged**: its `devices:`/`group_add:` found the passed-in GPU, and its `volumes:` found the two bind-mounted datasets at the paths it already referenced. The only new artifacts are the Incus container and its device config — the stack itself is identical to the bare-host version.

## Step 6 — reaching the services from outside

Inside one Incus container, the nested Docker services talk to each other **exactly as before** — Docker's own bridge networks and service-name DNS are untouched by nesting, so `OLLAMA_BASE_URL=http://ollama:11434` and any compose `networks:` block work unchanged. The reverse proxy pattern this build already uses — [Traefik](../services/reverse-proxy/traefik.md) or [Caddy](../services/reverse-proxy/caddy.md) as a Docker container on the shared external `proxy` network — also keeps working unchanged, because it and the services it fronts are siblings in the same nested Docker.

What changes is only the **last hop to the LAN**. A nested container that publishes `127.0.0.1:3000` (the localhost-binding habit from [`docker/setup.md`](../docker/setup.md#bind-internal-services-to-localhost) and [Nextcloud](../docker/nextcloud.md)) is now reachable only on the *Incus container's* loopback. Bridge that to the host with an Incus `proxy` device (the [pattern-1 approach in Networking](networking.md#exposing-an-instance-service-to-the-lan)), which keeps the exposed port under host UFW:

```bash
# Forward host port 3000 to Open WebUI, published on the Incus container's loopback
incus config device add ai openwebui proxy \
  listen=tcp:0.0.0.0:3000 \
  connect=tcp:127.0.0.1:3000 \
  bind=host

# Gate it with UFW like any host port
sudo ufw allow from 192.168.0.0/24 to any port 3000 proto tcp
```

Because `bind=host`, the listener runs in the host's network namespace, so **UFW filters it** — you keep one firewall front-end, exactly as [Networking](networking.md) requires. For a stack fronted by a reverse proxy inside the container, forward only the proxy's 80/443 this way and let it route to the rest by service name; for a Tailscale-reachable box, the [subnet-router option](networking.md#tailscale-reachability-for-instances) reaches the Incus container's `incusbr0` IP directly without per-port proxying.

## Verification

```bash
incus list                                        # container up, has an incusbr0 IP?
incus config show ai                              # nesting, limits, GPU devices, disk devices
incus config device show ai | grep -E 'kfd|dri|disk'
incus exec ai -- docker compose -f /opt/ollama-stack/docker-compose.yml ps
incus exec ai -- docker exec ollama rocminfo | grep gfx1151
```

Snapshot before risky in-container changes with `incus snapshot create ai before-upgrade`, and let sanoid cover `hot/incus/containers/ai` on schedule (see [Storage](storage.md)). Your *data* is on the host `tank`/`hot` datasets and is snapshotted/replicated there independently — the Incus container itself is disposable.

## Next steps

- [OCI application containers](oci-containers.md) — the lighter-weight alternative for simple single-image services.
- [Containers](containers.md) — nesting, limits, and profiles in general.
- [GPU passthrough](gpu-passthrough.md) — the ROCm device story these AI containers depend on.
- [Networking](networking.md) — proxy devices, UFW, and reaching instances.
- [Storage](storage.md) — the ZFS driver, bind mounts, and idmap.
