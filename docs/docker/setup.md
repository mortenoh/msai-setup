# Docker Setup

## Install Docker

### Add Docker Repository

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
```

### Install Packages

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

### Add User to Docker Group

```bash
sudo usermod -aG docker $USER
```

Log out and back in.

## Verify Installation

```bash
docker --version
docker compose version
docker run hello-world
```

## Configuration

### Docker Daemon

Create `/etc/docker/daemon.json`:

```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
```

Restart Docker:

```bash
sudo systemctl restart docker
```

## Docker and ZFS

!!! note "Storage Driver"
    Use `overlay2`, not `zfs` driver. ZFS backing comes from bind mounts.

## Docker and UFW

Docker modifies iptables directly, bypassing UFW. Published container ports are reachable on every host interface regardless of UFW rules.

For this build we use **`ufw-docker`** to make UFW actually filter Docker-published ports, plus **bind sensitive services to `127.0.0.1`** behind the reverse proxy. Setting `"iptables": false` in `daemon.json` is also an option but breaks container networking unless you replace it with your own nftables rules — not recommended.

### Recommended: install ufw-docker

```bash
# Pin a release tag rather than tracking master
sudo wget -O /usr/local/bin/ufw-docker \
    https://github.com/chaifeng/ufw-docker/raw/v0.5.0/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker

# Install ufw-docker's rules block into /etc/ufw/after.rules
sudo ufw-docker install
sudo systemctl restart ufw
```

After install, use UFW rules to allow access to specific container ports:

```bash
# Example: allow LAN access to Jellyfin on container port 8096
sudo ufw route allow proto tcp from 192.168.1.0/24 to any port 8096
```

!!! tip "Deeper UFW/Docker treatment"
    The mechanics of why Docker bypasses UFW, and the full set of mitigation
    strategies, are covered in
    [UFW/Docker Conflict](../networking/docker/ufw-conflict.md) and
    [UFW/Docker Solutions](../networking/docker/ufw-solutions.md).

### Bind internal services to localhost

For anything that doesn't need direct external access, bind to `127.0.0.1` in compose and route through your reverse proxy on 80/443:

```yaml
services:
  nextcloud:
    ports:
      - "127.0.0.1:8080:80"   # not reachable on LAN; Traefik proxies it
```

## Project Structure

Organize compose files:

```
/home/user/
└── docker/
    ├── nextcloud/
    │   └── docker-compose.yml
    ├── plex/
    │   └── docker-compose.yml
    └── .env
```

!!! note "Compose files vs. data paths"
    The compose files themselves (and the `.env`) live in your home directory
    under `~/docker/<svc>/` — small, git-trackable, disposable definitions.
    The **data** those services persist does not live here: the `volumes:`
    bind mounts point at ZFS datasets under `/mnt/tank/...`
    (e.g. `/mnt/tank/nextcloud-data`, `/mnt/tank/media`), as shown in
    [Nextcloud](nextcloud.md) and [Plex](plex.md). Keeping the two separate is
    deliberate: you can wipe and re-clone `~/docker` without touching pool
    data, and snapshot pool data without dragging in compose config.

## Common Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down

# Update images
docker compose pull
docker compose up -d
```
