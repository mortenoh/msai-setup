# Rebuild Checklist

Recovery runbook for the MS-S1 MAX. This build runs **root-on-ZFS via [ZFSBootMenu](https://zfsbootmenu.org/)** on two independent pools — `rpool` (root + hot data + Incus's storage backend at `rpool/incus`, on the fast 4 TB NVMe) and `tank` (media, backups, cold data, on the slow 2 TB NVMe) — with **[Incus](../incus/index.md) as the single virtualization layer** (Docker nests inside Incus system containers, VMs are Incus VM instances). See [Hardware](../getting-started/hardware.md) and [Disk Partitioning](../ubuntu/installation/disk-partitioning.md) for the layout, and the repo-root `START.md` for the architectural intent.

Because root lives on ZFS, **"my OS is broken" and "my hardware is gone" are now two very different jobs.** Pick the scenario before you touch anything:

| Scenario | What happened | What it actually is |
|---|---|---|
| **A — OS broken, pools fine** | Bad kernel, bad `apt upgrade`, corrupted root dataset | A [ZFSBootMenu boot-environment rollback](#scenario-a-os-broken-pools-fine-boot-environment-rollback) — one keystroke, not a rebuild |
| **B — full rebuild** | Hardware replaced, both drives gone, starting over | A [full root-on-ZFS reinstall + Incus re-init](#scenario-b-full-rebuild) |

Most "the box won't come up right" incidents are Scenario A. Try that first; only fall through to Scenario B when the pools themselves are gone.

---

## Scenario A — OS broken, pools fine (boot-environment rollback)

If `rpool` and `tank` are healthy and only the running OS is broken (a bad kernel, a failed `apt upgrade`, a corrupted `rpool/ROOT/ubuntu`), **do not reinstall.** Roll back to a previous boot environment. The kernel, the packages, and everything else the bad change touched revert together in one atomic step.

The commands and hotkeys live in one place — the [ZFSBootMenu Recovery section of the ZFS Root alternative](../ubuntu/installation/zfs-root-alternative.md#zfsbootmenu-recovery). The short version:

1. **Interrupt the ZFSBootMenu countdown** — press a key (Esc/Space/arrow) as the box boots to stay in the menu.
2. **Pick a healthy environment or snapshot** — highlight a previous boot environment, or an older snapshot of `rpool/ROOT/ubuntu`, with the arrow keys.
3. **Boot it (`Enter`) or roll back (`Ctrl+S`)** — boot once to confirm it's good, then `Ctrl+A` to make it the persistent default, or use the `Ctrl+S` snapshot menu to clone/roll a snapshot back into the live environment. Full hotkey table and the recovery-shell path are in [ZFS Root (Alternative)](../ubuntu/installation/zfs-root-alternative.md#zfsbootmenu-hotkeys).

### Verify and move on

Once booted into a known-good environment:

```bash
# You are on the environment you expect
zfs list -o name,mountpoint rpool/ROOT/ubuntu

# Both pools are still ONLINE and error-free
zpool status -v rpool
zpool status -v tank

# Incus and its instances came back with the pool (they live on rpool/incus)
incus list
incus storage info default

# Services inside the instances are healthy (spot-check the ones that matter)
incus exec docker-host -- docker ps
```

Then confirm the generic health items in the [Verification Checklist](#verification-checklist) (DNS resolves, Tailscale reconnected, backups resumed) and you're done — no reinstall, no data restore. Take a fresh snapshot to mark the known-good state:

```bash
sudo zfs snapshot rpool/ROOT/ubuntu@post-recovery-$(date +%F)
```

!!! note "This is the whole point of boot environments"
    A bad upgrade is a rollback, not a rebuild. Keep a few boot environments around and snapshot `rpool/ROOT/ubuntu` before risky changes — sanoid does this automatically (see [Backup &amp; Recovery](backup.md)). Only proceed to Scenario B if the pool itself is damaged or gone.

---

## Scenario B — full rebuild

Use this only when a boot-environment rollback can't help: **hardware replaced, `rpool` destroyed, or both drives gone.** Plan for a few hours plus restore time. If `tank` survived but `rpool` did not (or vice versa), you still run this path but skip the parts that recreate the pool that's intact.

The source of truth is what survived on the pools plus your off-host backups. The host OS is rebuildable; the data is not.

### When to use

- `rpool` is destroyed or the primary NVMe was replaced (a broken *OS* is Scenario A, not this)
- Both drives replaced / starting on fresh hardware
- Deliberate disk-layout change (repartition, repool)

### Prerequisites

- [ ] Both pools' health known before you started (`zpool status rpool`, `zpool status tank`)
- [ ] Recent snapshots verified on both pools ([Backup &amp; Recovery](backup.md))
- [ ] Off-site backups verified (in case the rebuild also damages a pool)
- [ ] Ubuntu Server 26.04 LTS ISO written to a USB stick
- [ ] SSH keys backed up to the off-host store
- [ ] Preserved **Incus preseed** (`incus-preseed.yaml`), instance profiles, and any `docker-compose.yml` stacks stored outside `/` (private git repo, `tank/backups`, password manager) — see [Incus installation](../incus/installation.md#the-equivalent-preseed-file)

---

### Phase 0 — Capture state (before you touch anything)

Run this **while the existing host still boots**. If it doesn't, but the pools are intact, do the [offline capture](#offline-rescue-when-the-host-wont-boot) at the bottom instead.

```bash
# Working directory on the cold-archive dataset (survives the reinstall)
sudo mkdir -p /tank/backups/rebuild-$(date +%F)
cd /tank/backups/rebuild-$(date +%F)

# Snapshot both pools before any further changes
sudo zfs snapshot -r rpool@pre-rebuild-$(date +%F)
sudo zfs snapshot -r tank@pre-rebuild-$(date +%F)

# ZFS layout, properties, and pool config — BOTH pools
zfs list -o name,used,available,mountpoint > zfs-datasets.txt
zfs get all > zfs-properties.txt
zpool status -v > zpool-status.txt
zpool list -v > zpool-list.txt
sudo zpool get all rpool > zpool-rpool-properties.txt
sudo zpool get all tank  > zpool-tank-properties.txt

# Disk identity + EFI / ZFSBootMenu boot entries (needed to reinstall the bootloader)
ls -l /dev/disk/by-id/ > disk-by-id.txt
sudo blkid > blkid.txt
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINT,UUID,SERIAL > lsblk.txt
sudo efibootmgr -v > efi-boot-entries.txt
zfs get org.zfsbootmenu:commandline rpool/ROOT/ubuntu > zbm-commandline.txt
sudo cp -a /boot/efi/EFI/ZBM zbm-efi-binary 2>/dev/null || true

# Incus configuration — the SHAPE of the deployment (instances are datasets on rpool/incus)
sudo incus admin init --dump > incus-preseed.yaml 2>/dev/null || true
incus list > incus-instances.txt
incus profile list > incus-profiles.txt
for p in $(incus profile list -f csv -c n); do
    incus profile show "$p" > "incus-profile-${p}.yaml"
done
incus storage list > incus-storage.txt
incus network list > incus-networks.txt

# Optional but recommended: portable per-instance exports (self-contained tarballs).
# For bulk/incremental off-host backup, syncoid on rpool/incus is more efficient —
# see docs/incus/snapshots-backup.md. Export is for portability / one-off archives.
for inst in $(incus list -f csv -c n); do
    incus export "$inst" "instance-${inst}.tar.gz" --optimized-storage 2>/dev/null || true
done

# Compose stacks live INSIDE the Docker-in-Incus container, not on the host.
# If you keep the compose files in a git repo, note the remote here; otherwise
# pull them out of the container so they're captured off the instance too:
# incus file pull -r docker-host/opt/compose ./compose-configs 2>/dev/null || true

# Host system state worth preserving
sudo cp /etc/fstab fstab.bak                # only the /boot/efi line matters on this build
sudo cp /etc/hostname hostname.bak
sudo cp -r /etc/netplan netplan.bak
sudo cp -r /etc/ssh ssh-config.bak
sudo cp -r /etc/sudoers.d sudoers.d.bak 2>/dev/null || true
sudo cp /etc/sanoid/sanoid.conf sanoid.conf.bak 2>/dev/null || true
sudo cp -r /etc/modprobe.d modprobe.d.bak
crontab -l > user-crontab.txt 2>/dev/null || true
systemctl list-unit-files --state=enabled --type=service > enabled-services.txt
dpkg -l > installed-packages.txt

# Tailscale state (so you don't burn a new device slot)
sudo tailscale status > tailscale-status.txt 2>/dev/null || true

# Final: mirror this directory off-host as well (rsync / restic / rclone to B2/S3)
```

Verify everything is in `/tank/backups/rebuild-<date>/` and that it's mirrored off-host. **Do not skip the off-host copy** — a rebuild that also damages a pool is rare but not impossible.

Export both pools cleanly before you reinstall (skip the pool you are about to destroy on purpose):

```bash
sudo zpool export tank
sudo zpool export rpool   # only if you're preserving rpool across the reinstall
```

If an export fails (busy mount, a running Incus instance still holding a dataset), stop the culprit first: `sudo incus stop --all`, then retry. `sudo lsof /tank` helps find stray mounts.

---

### Phase 1 — Reinstall Ubuntu Server 26.04 (root-on-ZFS + ZFSBootMenu)

There is **no guided-installer path** for root-on-ZFS — Subiquity can't do it. Follow the manual process end to end; it's the same one that built the box originally:

1. Boot from USB (UEFI, Secure Boot disabled — see [BIOS Setup](../getting-started/bios-setup.md)).
2. Work through the [Installation Walkthrough](../ubuntu/installation/installation-walkthrough.md) — it covers partitioning the 4 TB primary (EFI + `rpool`), creating `rpool/ROOT/ubuntu` and the sibling datasets, debootstrapping Ubuntu into the dataset, and installing the ZFSBootMenu EFI binary + `efibootmgr` entry. **Do not** duplicate those steps here; that page is the source of truth and stays current.
3. Recreate the `rpool` child datasets (`home`, `incus`, `db`, `ai`) with their tuned properties per [ZFS Datasets](../zfs/datasets.md) if the walkthrough left them for this stage.
4. Use the **same hostname and username** as before (simplifies restore).
5. Reboot into the fresh root-on-ZFS system over SSH.

If `rpool` survived and you only replaced the OS-side of the drive, importing the existing `rpool` and re-registering the ZFSBootMenu entry (see [Reinstall / Repair ZFSBootMenu](../ubuntu/installation/zfs-root-alternative.md#reinstall-repair-zfsbootmenu)) is faster than a clean debootstrap — but that edges back toward Scenario A.

### Phase 2 — Base configuration and re-import `tank`

```bash
# Update
sudo apt update && sudo apt upgrade -y

# Timezone / hostname (re-set if the install differed)
sudo timedatectl set-timezone Europe/Oslo

# Essentials + ZFS userland (zfsutils-linux is already present on a root-on-ZFS install)
sudo apt install -y vim htop tmux git curl wget rsync ca-certificates \
    build-essential pkg-config sanoid

# Re-import the DATA pool (rpool is already the running root). by-id paths are stablest.
sudo zpool import -d /dev/disk/by-id tank
sudo zpool status tank
zfs list

# Your capture directory is visible again
ls /tank/backups/
```

Re-assert the ARC cap (shared across both pools) so Incus VMs and Ollama get predictable memory:

```bash
sudo cp /tank/backups/rebuild-*/modprobe.d.bak/zfs.conf /etc/modprobe.d/zfs.conf 2>/dev/null \
  || echo 'options zfs zfs_arc_max=17179869184' | sudo tee /etc/modprobe.d/zfs.conf
sudo update-initramfs -c -k all
# Takes effect on next reboot.
```

### Phase 3 — Restore host config from the capture

```bash
SNAP=/tank/backups/rebuild-$(date +%F)   # adjust if dated differently

# Netplan (review before applying — interface names may have changed)
sudo cp $SNAP/netplan.bak/*.yaml /etc/netplan/
sudo netplan generate && sudo netplan apply

# sudoers.d
sudo cp -r $SNAP/sudoers.d.bak/* /etc/sudoers.d/ 2>/dev/null || true

# SSH host keys (preserves the host fingerprint for clients)
sudo cp $SNAP/ssh-config.bak/ssh_host_* /etc/ssh/
sudo systemctl restart ssh

# sanoid schedule
sudo cp $SNAP/sanoid.conf.bak /etc/sanoid/sanoid.conf 2>/dev/null || true

# Restore user SSH keys + authorized_keys
mkdir -p ~/.ssh && chmod 700 ~/.ssh
cp $SNAP/ssh-config.bak/authorized_keys ~/.ssh/ 2>/dev/null || true
# Plus your own private keys from off-host backup
```

### Phase 4 — Install ROCm and verify the iGPU

The iGPU stays with the host for ROCm (no passthrough). Follow [ROCm Quick Start](../ai/gpu/quick-start.md):

```bash
sudo apt install -y rocm
sudo usermod -aG video,render $USER
newgrp render

rocminfo | grep gfx1151
rocm-smi
```

If you allocate a larger GTT pool with `amd-ttm` (see [Memory Configuration](../ai/gpu/memory-configuration.md)):

```bash
pipx install amd-debug-tools
amd-ttm --set 108
sudo reboot
```

### Phase 5 — Install Incus and re-attach `rpool/incus`

Incus is the one virtualization/container layer — it installs directly on the host (it needs the real kernel's namespaces/cgroups and KVM). Follow [Incus installation](../incus/installation.md); the rebuild-relevant part is pointing `incus admin init` at the **preserved `rpool/incus` dataset** rather than creating a new pool.

```bash
sudo apt install -y incus
sudo usermod -aG incus-admin $USER
newgrp incus-admin

# Reproducible init from the captured preseed — this re-attaches Incus to
# source: rpool/incus (the existing dataset) and recreates the default profile,
# storage pool, and incusbr0 bridge. See docs/incus/installation.md.
cat /tank/backups/rebuild-*/incus-preseed.yaml | sudo incus admin init --preseed

# Verify Incus adopted the existing storage backend
incus storage list
incus storage info default    # driver: zfs, source: rpool/incus
```

!!! note "The instance datasets survived on `rpool/incus`"
    If `rpool` was preserved (or reimported), re-attaching Incus to `source: rpool/incus` re-adopts every instance dataset that was already there — the containers and VMs come back with the pool. You only *recreate* instances when `rpool/incus` itself was lost. See [Storage](../incus/storage.md#the-rebuild-path) and [Snapshots &amp; backup](../incus/snapshots-backup.md#the-rebuild-path-instances) for the full instance-recovery detail — don't re-derive it here.

### Phase 6 — Restore the Incus instances

Choose the path that matches what you have. Full detail (and the stop-before-you-receive warning) is in [Incus Snapshots &amp; backup — Restore workflows](../incus/snapshots-backup.md#restore-workflows); the summary:

- **`rpool/incus` survived** → nothing to restore. `incus list` already shows the instances; `boot.autostart` brings service instances up.
- **`rpool/incus` was lost, you have syncoid replicas** → pull each instance's datasets back from the backup host, then let Incus re-adopt them:
  ```bash
  syncoid -r backup-host:backup/incus rpool/incus
  # Instances re-appear once their datasets are back; recreate any missing
  # config from the preseed/profiles captured in Phase 0.
  ```
- **You only have portable exports** → import the tarballs:
  ```bash
  for f in /tank/backups/rebuild-*/instance-*.tar.gz; do incus import "$f"; done
  incus list
  ```
- **Recreate from scratch** (no instance backup, only profiles/compose) → launch fresh instances from the captured profiles, then rebuild the Docker stacks inside them (next phase).

### Phase 7 — Rebuild the Docker-in-Incus stacks (if recreating)

Compose stacks are **not** deployed on the host anymore — they live nested inside an Incus system container (`security.nesting=true`). If you're recreating rather than restoring an instance wholesale, follow [Docker inside Incus](../incus/docker-in-incus.md) to build the container, install Docker Engine in it, wire up the two-layer bind-mount chain (host dataset → container → compose service), and bring the stacks up. Bring services up in dependency order inside the container:

1. **Reverse proxy** (Traefik/Caddy) — owns 80/443
2. **Auth** (Authentik) — needed by everything behind SSO
3. **DNS** (Pi-hole) — if other LAN services depend on it
4. **Data services** — Nextcloud, databases
5. **Media** — Jellyfin/Plex, *arr stack
6. **Dashboards** — Homepage, Uptime Kuma
7. **AI** — Ollama / Open WebUI (once ROCm is verified and `/dev/kfd` + `/dev/dri` are passed into the container)

```bash
# Example: inside the docker-host container
incus exec docker-host -- bash
cd /opt/compose/traefik   && docker compose up -d && sleep 5
cd /opt/compose/authentik && docker compose up -d && sleep 10
# ... and so on, in the order above
```

VMs (Windows 11, Linux desktop) are Incus VM instances — they came back with their datasets in Phase 6, or are recreated with `incus launch --vm` per [VMs](../incus/vms.md) / [Windows VM](../incus/windows-vm.md). There is **no libvirt XML to redefine** on this build.

### Phase 8 — Firewall and Tailscale

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow OpenSSH
# Incus's bridge needs the same UFW-forwarding treatment ufw-docker gave bare
# Docker — see docs/incus/networking.md. Prefer routing services through a
# reverse proxy on 80/443 over opening per-service ports.
sudo ufw enable
sudo ufw status verbose

# Tailscale management plane
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh
```

---

## Verification Checklist

Tick these off before declaring the rebuild done.

### Storage
- [ ] `zpool status rpool` is `ONLINE` with no errors
- [ ] `zpool status tank` is `ONLINE` with no errors
- [ ] Root is a boot environment: `zfs list rpool/ROOT/ubuntu` mounts `/`
- [ ] All `rpool` datasets present (`home`, `incus`, `db`, `ai`) and all `tank` datasets present (`media`, `nextcloud-data`, `nextcloud-app`, `backups`)
- [ ] `zfs_arc_max` set (`cat /sys/module/zfs/parameters/zfs_arc_max` shows ~16 GB or your chosen value)
- [ ] ZFSBootMenu boots: interrupt the countdown once and confirm the boot-environment list looks right (`efibootmgr -v` shows the ZBM entry first)

### Incus
- [ ] `incus storage info default` shows `driver: zfs`, `source: rpool/incus`
- [ ] `incus list` shows every instance from Phase 0 (`RUNNING` for the autostart ones)
- [ ] `incus info <instance>` clean for the service containers and any VM
- [ ] GPU passthrough works where needed: `/dev/kfd` + `/dev/dri` visible inside the AI container (`incus exec ai-stack -- rocminfo | grep gfx1151`)

### Networking
- [ ] Static IP / DHCP reservation as expected
- [ ] DNS resolves outbound (`getent hosts github.com`)
- [ ] Tailscale shows the host online with the same name as before
- [ ] SSH host key fingerprint unchanged (clients don't get a host-key warning)
- [ ] Incus bridge (`incusbr0`) forwarding filtered by UFW per [networking](../incus/networking.md)

### GPU / AI
- [ ] `rocminfo` shows `gfx1151` on the host
- [ ] `rocm-smi` shows the GPU, no errors
- [ ] Ollama / llama.cpp runs a small model end-to-end at the expected token rate (inside its Incus container)

### Services (per-service smoke test, inside the Docker-in-Incus container)
- [ ] Traefik dashboard reachable, ACME certs renewed
- [ ] Authentik login works; identities preserved
- [ ] Pi-hole serving DNS; query log populating
- [ ] Nextcloud login works; files visible; trusted_domains correct
- [ ] Jellyfin/Plex sees libraries (on `tank/media`)
- [ ] *arr stack: indexers reachable, downloads working
- [ ] Homepage widgets green; Uptime Kuma monitors green

### Virtualization (VMs)
- [ ] Windows 11 Incus VM boots, RDP reachable
- [ ] TPM / Secure Boot devices intact on the VM (`incus config show win11`)

### Backups
- [ ] sanoid timer running: `systemctl status sanoid.timer`
- [ ] syncoid replicating `rpool/incus`, `rpool/db`, and the `tank` datasets ([backup.md](backup.md))
- [ ] Off-site target reachable
- [ ] At least one fresh snapshot taken post-rebuild on both pools

---

## Offline rescue — when the host won't boot

If Phase 0 wasn't possible because the host is already broken, but the pools are intact, this is often **Scenario A** in disguise — try a [ZFSBootMenu boot-environment rollback](#scenario-a-os-broken-pools-fine-boot-environment-rollback) first, or the [ZFSBootMenu recovery shell](../ubuntu/installation/zfs-root-alternative.md#drop-to-the-emergency-shell). If you genuinely need a full rebuild and want to capture state off the surviving pools first:

1. Boot the Ubuntu Server 26.04 USB in "Try Ubuntu" mode.
2. `sudo apt install -y zfsutils-linux`.
3. Import both pools read-only-ish into `/mnt` (by-id paths survive enumeration reshuffles):
   ```bash
   sudo zpool import -f -d /dev/disk/by-id -R /mnt rpool
   sudo zfs mount rpool/ROOT/ubuntu
   sudo zpool import -f -d /dev/disk/by-id -R /mnt tank
   ```
4. Recover whatever you can from `/mnt/tank/backups/`, `/mnt/rpool`, and the Incus datasets under `/mnt/rpool/incus`, plus host config from the mounted root (`/mnt/etc/netplan`, `/mnt/etc/ssh`, sanoid config).
5. Proceed with Phase 1 onwards; substitute "whatever you could recover" for the Phase 0 capture.

The full offline chroot procedure (bind-mounting `/dev`, `/proc`, `/sys`, mounting the EFI partition, re-running `efibootmgr`) is in [ZFS Root (Alternative) — Live USB Recovery](../ubuntu/installation/zfs-root-alternative.md#live-usb-recovery). Anything that lived only on a destroyed `rpool` (host `/etc` config, Incus's database) is why Phase 0 normally writes the capture to `tank` and an off-site target.
