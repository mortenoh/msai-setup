# Rebuild Checklist

End-to-end checklist for reinstalling Ubuntu Server 26.04 on the MS-S1 MAX without losing data. The ZFS pool is the source of truth; the host OS is rebuildable. Plan for a few hours plus restore time.

This checklist assumes the canonical architecture: **host owns the iGPU for ROCm**, Windows VM uses virtio-gpu/Spice (no passthrough), plain ext4 root, ZFS data pool spanning the leftover ~1 TB on the primary NVMe + the entire 4 TB secondary NVMe, all services in Docker with bind mounts to `/mnt/tank/`. See [Hardware](../getting-started/hardware.md) and [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) for the layout.

## When to Use

- Host OS is corrupted
- Major OS upgrade (fresh install preferred over in-place)
- Hardware replacement
- Disk-layout change

## Prerequisites

- [ ] ZFS pool is healthy (`zpool status tank`)
- [ ] Recent ZFS snapshots verified ([Backup &amp; Recovery](backup.md))
- [ ] Off-site backups verified (in case the rebuild also damages the pool)
- [ ] Ubuntu Server 26.04 LTS ISO ready, written to a USB stick
- [ ] SSH keys backed up to the off-host store
- [ ] Compose files / .env / VM XML stored somewhere outside `/` (private git repo, ZFS dataset, password manager)

---

## Phase 0 — Capture state (before you touch anything)

Run this **while the existing host still boots**. If it doesn't, fall back to the "Offline rescue" section at the bottom of this page.

```bash
# Working directory on ZFS (survives the reinstall)
mkdir -p /mnt/tank/backups/rebuild-$(date +%F)
cd /mnt/tank/backups/rebuild-$(date +%F)

# Snapshot every dataset before any further changes
sudo zfs snapshot -r tank@pre-rebuild-$(date +%F)

# ZFS layout, properties, and pool config
zfs list -o name,used,available,mountpoint > zfs-datasets.txt
zfs get all > zfs-properties.txt
zpool status -v > zpool-status.txt
zpool list -v > zpool-list.txt
sudo zpool get all tank > zpool-properties.txt

# Disk identity (helps re-import on the new install)
ls -l /dev/disk/by-id/ > disk-by-id.txt
sudo blkid > blkid.txt
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID,SERIAL > lsblk.txt

# libvirt VM definitions — these live on /, NOT in the pool
mkdir -p libvirt
for vm in $(sudo virsh list --all --name); do
    [ -z "$vm" ] && continue
    sudo virsh dumpxml "$vm" > "libvirt/${vm}.xml"
done
sudo virsh net-dumpxml default > libvirt/net-default.xml 2>/dev/null || true
sudo virsh pool-dumpxml vm-pool > libvirt/pool-vm.xml 2>/dev/null || true
sudo virsh list --all > vm-list.txt

# Docker containers, images in use, networks
docker ps -a --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}' > docker-containers.txt
docker network ls > docker-networks.txt
docker volume ls > docker-volumes.txt

# Compose files (assumes you keep them under ~/docker or /opt/compose)
# Adjust the source path if yours is different.
cp -a ~/docker docker-configs/ 2>/dev/null || true

# .env files — these contain secrets, store carefully
find ~/docker -name '.env' -exec cp --parents {} . \; 2>/dev/null || true

# System state worth preserving
sudo cp /etc/fstab fstab.bak
sudo cp /etc/hostname hostname.bak
sudo cp -r /etc/netplan netplan.bak
sudo cp -r /etc/ssh ssh-config.bak
sudo cp -r /etc/sudoers.d sudoers.d.bak 2>/dev/null || true
sudo crontab -l > root-crontab.txt 2>/dev/null || true
crontab -l > user-crontab.txt 2>/dev/null || true
systemctl list-unit-files --state=enabled --type=service > enabled-services.txt
dpkg -l > installed-packages.txt

# Tailscale state (so you don't burn a new device slot)
sudo tailscale status > tailscale-status.txt 2>/dev/null || true

# Final: copy this snapshot directory off-host as well
# (rsync to backup target, restic, or rclone to B2/S3)
```

Verify everything you need is in `/mnt/tank/backups/rebuild-<date>/` and that it's mirrored off-host. **Do not skip the off-host copy** — a rebuild that also damages the pool is rare but not impossible.

Export the pool cleanly:

```bash
sudo zpool export tank
```

If export fails (busy mount, container still bind-mounting), find and stop the culprit (`sudo lsof /mnt/tank`, `docker stop $(docker ps -q)`).

---

## Phase 1 — Install Ubuntu Server 26.04

1. Boot from USB (UEFI, Secure Boot disabled — see [BIOS Setup](../getting-started/bios-setup.md))
2. Pick "Try or Install Ubuntu Server"
3. Follow the [Installation Walkthrough](../ubuntu/installation/installation-walkthrough.md). Key points:
    - **Custom storage layout** — don't let guided mode touch the secondary NVMe
    - Primary NVMe partitions: 512 MB EFI / 1 GB `/boot` (ext4) / 1 TB `/` (ext4)
    - Leave ~1 TB free on the primary, **leave the 4 TB drive entirely untouched**
    - Same hostname and same username as before (simplifies restore)
4. Enable SSH at the installer's "Featured Server Snaps" / SSH prompt
5. Reboot, log in over SSH

## Phase 2 — Base configuration

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Timezone, hostname (re-set if installer differed)
sudo timedatectl set-timezone Europe/Oslo
# sudo hostnamectl set-hostname ms-s1-max

# Essentials
sudo apt install -y vim htop tmux git curl wget rsync ca-certificates \
    build-essential pkg-config

# Restore SSH keys + authorized_keys
# (copy from /mnt/tank/backups/.../ssh-config.bak after Phase 3)
```

## Phase 3 — Import the ZFS pool

```bash
# Install ZFS
sudo apt install -y zfsutils-linux

# Import — try the by-id path first
sudo zpool import -d /dev/disk/by-id tank

# Verify
sudo zpool status tank
zfs list

# At this point /mnt/tank/backups/rebuild-<date>/ should be visible again
ls /mnt/tank/backups/
```

Cap ARC so it doesn't fight VMs for RAM (default is ~50% = 64 GB on this box; way too greedy when you also have VMs and Ollama):

```bash
echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf
sudo update-initramfs -u
# Takes effect on next reboot.
```

## Phase 3b — Reconfigure with the Ansible playbooks (preferred)

The same Ansible playbooks that build the box in the first place are the intended reconfiguration mechanism for a rebuild — they're idempotent and reproduce base config, SSH hardening, the firewall, ZFS properties, Docker, and the service smoke-test in one pass. This is the documented "from lab to real MS-S1 MAX" flow in `src/msai_setup/lab/README.md`; running them here **replaces most of the hand-rolled steps in Phases 4, 7, 8, and 10** below (fall back to the manual steps only if you don't have the repo/inventory to hand).

From a machine that has the repo checked out (your laptop), pointing at the production inventory described in `src/msai_setup/lab/README.md` (same one used for the initial build):

```bash
cd src/msai_setup/lab/ansible

# Same production inventory as the initial build (see src/msai_setup/lab/README.md).
INV=~/msai-prod-inventory.yml

ansible-playbook -i "$INV" playbooks/bootstrap.yml            -l production   # base packages, user, sudoers, timezone
ansible-playbook -i "$INV" playbooks/ssh-hardening.yml        -l production   # key-only auth, PermitRootLogin no, hardened ciphers
ansible-playbook -i "$INV" playbooks/ufw.yml                 -l production   # default-deny firewall + SSH
ansible-playbook -i "$INV" playbooks/zfs.yml -e topology=stripe -l production # ARC cap + dataset layout/properties
ansible-playbook -i "$INV" playbooks/docker.yml              -l production   # Docker CE + daemon.json
ansible-playbook -i "$INV" playbooks/services.yml            -l production   # bring up the Compose stack
```

!!! note "zfs.yml on an already-imported pool"
    You imported `tank` in Phase 3, so `zfs.yml` detects the existing pool and **skips pool creation** — it only reasserts the ARC cap and ensures the dataset layout/properties. It will not repartition disks or destroy data. If you'd rather keep pool/dataset management entirely manual on the real box, skip `zfs.yml` and rely on the imported pool as-is.

After the playbooks finish, you can jump straight to Phase 5 (ROCm) and Phase 6 (KVM/libvirt), which the playbooks don't cover, then use Phase 8's ordering to verify the Compose stack came up cleanly. The manual Phases 4/7/10 remain below for the no-Ansible fallback.

## Phase 4 — Restore host config from snapshot

```bash
SNAP=/mnt/tank/backups/rebuild-$(date +%F)  # adjust if dated differently

# Netplan (review before applying — interface names may have changed)
sudo cp $SNAP/netplan.bak/*.yaml /etc/netplan/
sudo netplan generate
sudo netplan apply

# sudoers.d
sudo cp -r $SNAP/sudoers.d.bak/* /etc/sudoers.d/ 2>/dev/null || true

# SSH host keys (preserves the host fingerprint for clients)
sudo cp $SNAP/ssh-config.bak/ssh_host_* /etc/ssh/
sudo systemctl restart ssh

# Restore user SSH keys and authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp $SNAP/ssh-config.bak/authorized_keys ~/.ssh/  # if present
# Plus your own private keys from off-host backup
```

## Phase 5 — Install ROCm and verify the iGPU

The MS-S1 MAX's iGPU stays with the host; no passthrough. Follow [ROCm Quick Start](../ai/gpu/quick-start.md) — short version:

```bash
sudo apt install -y rocm
sudo usermod -aG video,render $USER
newgrp render

# Verify
rocminfo | grep gfx1151
rocm-smi
```

If you use `amd-ttm` to give ROCm a larger GTT pool, set it now (see [Memory Configuration](../ai/gpu/memory-configuration.md)):

```bash
pipx install amd-debug-tools
amd-ttm --set 108
sudo reboot
```

## Phase 6 — Install KVM/libvirt

```bash
sudo apt install -y \
    qemu-kvm libvirt-daemon-system libvirt-clients \
    bridge-utils virtinst ovmf swtpm swtpm-tools \
    libvirt-daemon-driver-storage-zfs

sudo usermod -aG libvirt $USER
sudo usermod -aG kvm $USER
sudo systemctl enable --now libvirtd

# Recreate the storage pool (matches Phase 0 dump)
sudo virsh pool-define $SNAP/libvirt/pool-vm.xml 2>/dev/null \
  || sudo virsh pool-define-as vm-pool dir - - - - /mnt/tank/vm
sudo virsh pool-start vm-pool
sudo virsh pool-autostart vm-pool

# Restore VM definitions
for xml in $SNAP/libvirt/*.xml; do
    [ "$(basename "$xml")" = "pool-vm.xml" ] && continue
    [ "$(basename "$xml")" = "net-default.xml" ] && continue
    sudo virsh define "$xml"
done
sudo virsh list --all
```

!!! note "No GPU passthrough on this build"
    Earlier drafts of this checklist had a "GPU passthrough" phase that blacklisted `amdgpu` and bound the iGPU to `vfio-pci`. That mode is incompatible with the canonical host-owns-GPU architecture (host can't run ROCm without amdgpu). If you specifically want passthrough, see [GPU Passthrough](../virtualization/gpu-passthrough.md) and understand the trade-off before adding that step here.

## Phase 7 — Install Docker

```bash
sudo apt install -y ca-certificates curl
sudo install -m 0755 -d /etc/apt/keyrings
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Try the matching Ubuntu codename first; if Docker hasn't published a
# 'resolute' channel yet, fall back to 'noble' (24.04) — Docker's CE
# repo is consistently backwards-compatible for one LTS cycle.
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")
if ! curl -sfI "https://download.docker.com/linux/ubuntu/dists/${CODENAME}/Release" >/dev/null; then
    echo "Docker repo for '$CODENAME' not published yet; falling back to noble"
    CODENAME=noble
fi

echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
    | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io \
    docker-buildx-plugin docker-compose-plugin

sudo usermod -aG docker $USER
newgrp docker

docker run hello-world
```

## Phase 8 — Restore services in dependency order

Order matters — bring up infrastructure before consumers:

1. **Reverse proxy** (Traefik or Caddy) — owns ports 80/443
2. **Auth** (Authentik) — needed by everything behind SSO
3. **DNS** (Pi-hole) — if other services on the LAN depend on it
4. **Data services** — Nextcloud, databases
5. **Media** — Jellyfin/Plex, *arr stack
6. **Dashboards** — Homepage, Uptime Kuma
7. **AI** — Ollama / Open WebUI (once ROCm is verified)

```bash
SNAP=/mnt/tank/backups/rebuild-$(date +%F)

# Restore compose configs
mkdir -p ~/docker
cp -a $SNAP/docker-configs/* ~/docker/  # or: git clone <private-configs-repo>

# Bring services up one at a time, in the order above
cd ~/docker/traefik   && docker compose up -d && sleep 5
cd ~/docker/authentik && docker compose up -d && sleep 10
cd ~/docker/pihole    && docker compose up -d && sleep 5
cd ~/docker/nextcloud && docker compose up -d && sleep 10
# … and so on
```

## Phase 9 — Restore VMs

```bash
# VM definitions were re-defined in Phase 6. Disks are still on /mnt/tank/vm.
sudo virsh list --all
sudo virsh start win11
# Open a console / RDP in to verify
```

## Phase 10 — Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
# Open additional ports only for services bound to the LAN that aren't
# behind Traefik. Prefer routing everything through 80/443 + Traefik.
sudo ufw enable
sudo ufw status verbose
```

If you use Tailscale for management, ensure it's installed and authenticated:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

## Verification Checklist

Tick these off before declaring the rebuild done.

### Storage
- [ ] `zpool status tank` is `ONLINE` with no errors
- [ ] All datasets visible under `/mnt/tank/`
- [ ] `zfs_arc_max` is set (`cat /sys/module/zfs/parameters/zfs_arc_max` shows ~16 GB or your chosen value)

### Networking
- [ ] Static IP / DHCP reservation as expected
- [ ] DNS resolves outbound (`getent hosts github.com`)
- [ ] Tailscale shows the host online with the same name as before
- [ ] SSH host key fingerprint unchanged (clients don't get a host-key warning)

### GPU / AI
- [ ] `rocminfo` shows `gfx1151`
- [ ] `rocm-smi` shows GPU, no errors
- [ ] Ollama or llama.cpp runs a small model end-to-end at expected token rate

### Virtualization
- [ ] `virsh list --all` shows every VM from Phase 0
- [ ] Windows 11 VM boots, RDP reachable

### Services (per-service smoke test)
- [ ] Traefik dashboard reachable, ACME certs renewed
- [ ] Authentik login works; identities preserved
- [ ] Pi-hole serving DNS; query log populating
- [ ] Nextcloud login works; files visible; trusted_domains correct
- [ ] Jellyfin/Plex sees libraries
- [ ] *arr stack: indexers reachable, downloads working
- [ ] Homepage shows all widgets green
- [ ] Uptime Kuma monitors all green

### Backups
- [ ] sanoid / syncoid resumed
- [ ] Off-site backup target reachable
- [ ] At least one snapshot taken post-rebuild

---

## Offline rescue — when the host won't boot

If Phase 0 wasn't possible because the host is already broken:

1. Boot from the Ubuntu Server 26.04 USB in "Try Ubuntu" mode
2. `sudo apt install zfsutils-linux`
3. `sudo zpool import -d /dev/disk/by-id -fR /mnt tank`
4. Now you can recover whatever you can from `/mnt/tank/` (compose files, .env files, anything you previously stashed under `/mnt/tank/backups/`)
5. Proceed with Phase 1 onwards; in Phase 0 substitute "whatever you could recover from the live USB"

Anything that lived only on the dead `/` (libvirt XML, sudoers.d, /etc/netplan) is gone in this scenario — which is why Phase 0 normally writes everything to the pool and an off-site target.
