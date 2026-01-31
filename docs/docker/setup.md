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

# Add repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
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

Docker modifies iptables directly, bypassing UFW.

### Solution: Disable Docker's iptables

```json
{
  "iptables": false
}
```

Then manage rules manually or use `ufw-docker` utility.

### Alternative: Accept It

If your server isn't directly exposed to the internet, the default Docker networking may be acceptable.

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
