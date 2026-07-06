# Incus Quick Reference

Command cheat sheet for this build. Substitute `<render-gid>` with the host's `render` group GID (`getent group render`).

## Install & Init

```bash
# Install (Ubuntu 26.04 archive)
sudo apt install incus
sudo apt install qemu-system-x86 qemu-utils      # VM support
sudo systemctl enable --now incus.socket

# Non-root access
sudo usermod -aG incus-admin "$USER"
newgrp incus-admin

# Initialize (interactive)
sudo incus admin init

# Initialize (preseed)
cat incus-preseed.yaml | sudo incus admin init --preseed

# Version / environment
incus version
incus info
```

## Instances — Lifecycle

```bash
incus launch images:ubuntu/24.04 web           # create + start (container)
incus launch images:ubuntu/24.04 vm1 --vm      # create + start (VM)
incus init images:ubuntu/24.04 web             # create only
incus start web
incus stop web [--force]
incus restart web
incus pause web / incus resume web
incus rename web web2
incus delete web --force                        # destroys the dataset too

incus list                                      # all instances
incus info web                                  # detail + resources
incus info web --resources                      # live usage
```

## Instances — Access

```bash
incus exec web -- bash                          # shell (containers)
incus exec web -- <command>
incus exec web --user 1000 --env K=V -- <cmd>
incus console vm1                               # serial console (VMs); Ctrl-a q to detach
incus console vm1 --type=vga                    # graphical console

incus file push  ./f web/etc/f
incus file pull  web/var/log/app.log ./
incus file push -r ./dir/ web/srv/
```

## Config & Limits

```bash
incus config show web                           # full effective config
incus config set web <key> <value>
incus config get web <key>

incus config set web limits.cpu 4               # vCPU count
incus config set web limits.cpu 0-7             # pin to host cores (one CCX)
incus config set web limits.memory 8GiB
incus config set web limits.memory.swap false
incus config set web limits.processes 4096
incus config device set web root size=40GiB     # root disk quota

incus config set web security.nesting true      # Docker inside (container)
incus config set web boot.autostart true
incus config set vm1 security.secureboot false  # VM only (default true)
```

## Devices

```bash
incus config device list web
incus config device show web
incus config device add web <name> <type> [key=val ...]
incus config device remove web <name>
incus config device override web eth0 <key>=<val>   # override an inherited device
```

### GPU / ROCm (containers)

```bash
# /dev/dri (render nodes)
incus config device add ai-box gpu0 gpu gputype=physical id=0 gid=<render-gid>

# /dev/kfd (ROCm compute) — the piece the gpu device omits
incus config device add ai-box dev_kfd unix-char source=/dev/kfd path=/dev/kfd gid=<render-gid>

# Verify inside
incus exec ai-box -- ls -l /dev/kfd /dev/dri/
incus exec ai-box -- rocminfo | grep gfx1151
incus exec ai-box -- rocm-smi
```

### TPM / VM devices

```bash
incus config device add vm1 vtpm tpm            # emulated TPM 2.0 (VM, stopped)
incus config device add vm1 install disk source=/path/os.iso boot.priority=10
```

### Proxy (port forward, host-bound)

```bash
incus config device add web http proxy \
  listen=tcp:0.0.0.0:8080 connect=tcp:127.0.0.1:80 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 8080 proto tcp
```

### Disk / bind mount

```bash
incus config device add web library disk source=/tank/media path=/srv/media
incus config device add web models  disk source=/rpool/ai path=/models readonly=true
```

## Profiles

```bash
incus profile list
incus profile show <name>
incus profile create <name>
incus profile set <name> <key> <value>
incus profile device add <name> <dev> <type> [key=val ...]
incus profile edit <name>                       # YAML in $EDITOR
incus profile add web <name>                    # apply to running instance
incus profile remove web <name>

incus launch images:ubuntu/24.04 web --profile default --profile gpu --profile docker-nesting
```

## Storage

```bash
incus storage list
incus storage show default
incus storage info default
incus storage create <name> zfs source=rpool/incus     # existing dataset
incus storage volume list default
incus storage volume create default <vol> [--type=block]
incus config device add web data disk pool=default source=<vol> path=/data

# ZFS view of the same data
zfs list -r rpool/incus
zfs list -t snapshot -r rpool/incus
```

## Networking

```bash
incus network list
incus network show incusbr0
incus network info incusbr0
incus network set incusbr0 ipv4.firewall false      # let UFW filter
incus network set incusbr0 ipv6.firewall false
incus network create internal ipv4.address=10.20.0.1/24 ipv4.nat=false

# UFW for the Incus bridge
sudo ufw allow in on incusbr0
sudo ufw route allow in on incusbr0
sudo ufw route allow out on incusbr0

# IP forwarding for NAT
echo "net.ipv4.conf.all.forwarding=1" | sudo tee /etc/sysctl.d/99-incus-forwarding.conf
sudo systemctl restart systemd-sysctl

# Inspect Incus's firewall rules
sudo nft list ruleset
```

## Snapshots & Backup

```bash
incus snapshot create web before-upgrade
incus snapshot create web live --stateful       # capture running memory
incus snapshot list web
incus snapshot restore web before-upgrade
incus snapshot delete web before-upgrade

incus export web /tank/backups/web-$(date +%F).tar.gz [--instance-only]
incus import /tank/backups/web-2026-07-06.tar.gz

# Replication (instances are ZFS datasets)
syncoid -r rpool/incus backup-host:backup/incus
```

## Images & Remotes

```bash
incus image list                                # local cache
incus image list images:ubuntu
incus image list images: type=virtual-machine   # VM-capable images
incus remote list
incus remote add docker https://docker.io --protocol=oci   # OCI app containers
incus launch docker:nginx my-nginx
```

## Projects

```bash
incus project list
incus project create sandbox
incus project switch sandbox
incus project switch default
```

## This build's cheat lines

```bash
# GPU + Docker AI container
incus launch images:ubuntu/24.04 ollama --profile default --profile ai-stack

# Docker-stack service container, autostarting
incus launch images:ubuntu/24.04 media \
  --profile default --profile docker-nesting --profile autostart \
  -c limits.cpu=6 -c limits.memory=16GiB -d root,size=30GiB

# Windows 11 VM essentials
incus init win11 --vm --empty -c limits.cpu=8 -c limits.memory=16GiB -d root,size=100GiB
incus config device add win11 vtpm tpm
incus config get win11 security.secureboot          # true (leave it)
incus config device add win11 install disk source=/tank/media/iso/Win11.iso boot.priority=10
incus config device add win11 drivers disk source=/tank/media/iso/virtio-win.iso
```
