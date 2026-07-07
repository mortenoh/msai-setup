# MS-S1 MAX Build — Start Here

This file is the architectural intent for the project. Implementation details live in `docs/`. If you're new, read this then `docs/getting-started/`.

Hardware: [Minisforum MS-S1 MAX](https://www.minisforum.com/products/ms-s1-max) — AMD Ryzen AI Max+ 395 (Strix Halo), Radeon 8060S iGPU (RDNA 3.5, `gfx1151`), 128 GB LPDDR5X-8000 quad-channel, 2 x M.2 NVMe (PCIe 4.0 x4 + x1), 2 x 10GbE.

Target OS: **Ubuntu Server 26.04 LTS** ("Resolute Raccoon"), headless.

## High-level intent

- **Host OS on plain ext4 root.** Ubuntu Server LTS, no desktop environment, SSH-only management. Root is ext4 (500 GB) with a separate `/boot`, installed by Subiquity's guided installer and booted by GRUB — boring, well-understood infrastructure on the critical boot path. The host is disposable: a broken OS is a reinstall, not a rollback, because everything stateful lives on ZFS. (Root-on-ZFS via [ZFSBootMenu](https://zfsbootmenu.org/) is a [documented alternative](docs/ubuntu/installation/zfs-root-alternative.md) for those who want the OS layer snapshotted too — see the avoids-list below for why it isn't the default.)
- **Everything runs inside Incus.** [Incus](https://linuxcontainers.org/incus/) (the community fork of LXD) is the one virtualization/container layer on the host. Docker workloads run nested inside Incus system containers (existing `docker-compose.yml` stacks, largely unchanged) or as native Incus OCI application containers where that fits better; VMs (Windows 11, etc.) are Incus VM instances — QEMU/KVM under the hood, managed with `incus` instead of bare `virsh`/`virt-install` or `docker`.
- **Data lives in ZFS.** Two independent pools, one per physical drive — no striping a pool across both. `hot` (hot data + Incus's own storage backend) on the fast drive, `tank` (bulk/cold data) on the slow drive. Every container/VM's storage is a native ZFS dataset via Incus's ZFS storage driver — no bind-mount choreography needed for that layer.
- **Virtual machines are first-class, via Incus.** Windows 11 VM (TPM 2.0 and Secure Boot via Incus's built-in `tpm` device and `security.secureboot` config key, virtio — no GPU passthrough by default; the iGPU stays with the host for ROCm).
- **AI is the primary purpose.** ROCm 7.x on the host iGPU, reachable from Incus containers via `/dev/kfd` + `/dev/dri` device passthrough (Incus's `gpu` device type alone only wires up `/dev/dri` — ROCm compute needs an explicit `/dev/kfd` device too). llama.cpp (built with the ROCm/HIP backend for gfx1151) for local LLM inference — plain GGUF on disk, OpenAI-compatible `llama-server`, no custom model store — with `amd-ttm` allocating ~108 GB of the 128 GB pool as GPU-accessible (GTT) memory.
- **Everything is recoverable.** Snapshots (sanoid, on both ZFS pools) for accidents and bad upgrades to data. Off-host replication (syncoid over Tailscale and restic to B2/S3) for disk failure and site loss. The ext4 OS root is not snapshotted — it is disposable and reproducible from the install walkthrough plus captured config.

## Hardware assumptions (one-line each)

- One CPU: 16-core / 32-thread Zen 5 in 2 x CCX layout.
- One GPU: integrated Radeon 8060S, 40 CUs, gfx1151. **Owned by the host** for ROCm.
- One RAM pool: 128 GB LPDDR5X-8000, soldered, quad-channel (~256 GB/s peak).
- Two NVMe slots, **unequal speeds**: slot 1 is PCIe 4.0 x4 (~8 GB/s), slot 2 is PCIe 4.0 x1 (~2 GB/s). **The 4 TB drive is physically installed in slot 1** (fast) and the 2 TB drive in slot 2 (slow) — the reverse of this project's original layout, so the larger-capacity drive gets the faster bus.
- Two 10GbE ports (Realtek RTL8127). 320W external PSU. Single HDMI 2.1 output (rarely used; SSH is the management plane) — plus DisplayPort Alt Mode over the USB4/USB4 V2 ports.

## Disk and filesystem layout

### Primary 4 TB NVMe (slot 1, PCIe 4.0 x4) — boot + root + hot data

| Partition | Size | Filesystem | Mount |
|---|---|---|---|
| EFI | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | 500 GB | ext4 | `/` (includes `/home`) |
| Pool member | ~3.4 TB | — | `hot` |

Plain ext4 root with a separate `/boot` — the boot path is GRUB reading ext4, no ZFS involved. The separate `/boot` survives a corrupted root and gives GRUB a stable home. The leftover ~3.4 TB becomes the `hot` pool, created post-install from the running system.

### Secondary 2 TB NVMe (slot 2, PCIe 4.0 x1) — bulk cold data

Entire disk -> `tank`, a separate pool. No striping across drives — each pool is exactly one disk, consistent with this build's no-local-redundancy stance (snapshots + replication substitute for RAID either way).

### ZFS pool `hot` (hot data, fast drive)

```
hot (single pool, one disk, no redundancy — snapshots + replication for protection)
+-- incus         (Incus's ZFS storage-pool backend, mountpoint=none; Incus creates one dataset per container/VM automatically)
+-- db            (recordsize=16K — per-service databases)
+-- ai            (recordsize=1M, compression=off — GGUF / safetensors model files; on the fast pool since capacity is no longer the constraint it was)
```

No `hot/home` — `/home` lives on the ext4 root. `hot` is created post-install from the running system (default mountpoint `/hot`, no `-R /mnt` altroot and no `ROOT`/`canmount` dance).

### ZFS pool `tank` (bulk/cold data, slow drive)

```
tank (single pool, one disk, no redundancy — snapshots + replication for protection)
+-- media           (recordsize=1M, compression=lz4 — Plex / Jellyfin libraries)
+-- nextcloud-data
+-- nextcloud-app
+-- backups         (compression=zstd-3 — cold archive target)
```

ARC capped at 16 GiB (shared across both pools) so VMs and inference workloads have predictable memory.

Detailed properties live in `docs/zfs/datasets.md`.

## Virtualization and containers (Incus)

- **Incus** is the one tool for both containers and VMs, installed directly on the host — it needs the real kernel's namespaces/cgroups and KVM, so it isn't nested inside anything itself.
- **Docker workloads**: nested inside an Incus system container (`security.nesting=true`), running existing `docker-compose.yml` stacks essentially unchanged. This is the default for anything already packaged as a compose stack (Nextcloud, the media stack, monitoring, the AI stack).
- **Simple single-image services**: native Incus OCI application containers (`incus launch` from an OCI/Docker image) where a full nested-Docker container is more machinery than the service needs.
- **VMs**: Incus VM instances (Windows 11, or a Linux desktop) — QEMU/KVM under the hood, managed with `incus` instead of `virsh`/`virt-install`.
- **GPU access**: the iGPU stays with the host for ROCm by default (unchanged decision from the original design). Incus containers that need it get `/dev/dri` via Incus's `gpu` device type, plus an explicit `unix-char` device for `/dev/kfd`.
- **Storage**: Incus's ZFS storage driver points at `hot/incus` — every container/VM gets its own ZFS dataset automatically (snapshots, clones, and `zfs send`/`receive` all work per-instance, no bind-mount choreography required at this layer).

See the Incus deep-dive (`docs/incus/`) for the full story.

## Networking

- Netplan with the `systemd-networkd` renderer. No NetworkManager.
- UFW for firewall (nftables backend on 26.04). Reverse proxy + bind-to-127.0.0.1 for service exposure. Incus's own bridge (`incusbr0`, or a custom bridge) needs the same UFW-forwarding treatment `ufw-docker` gave bare Docker — see `docs/incus/networking.md`.
- Tailscale as the remote-management plane. The host is reachable on the LAN and via Tailscale; **not** directly on the public internet.

## Backup philosophy

- **Local snapshots** (sanoid): hourly/daily/weekly/monthly retention per dataset, on both ZFS pools. The ext4 OS root is not snapshotted — it is disposable and reproducible from the install walkthrough.
- **On-site replication** (syncoid): periodic `zfs send` to a second box on the LAN.
- **Off-site (block)**: syncoid over Tailscale to a remote ZFS host.
- **Off-site (file)**: restic to B2 or S3, encrypted, for Nextcloud user data and photos.

Rebuild path: reinstall the ext4 root via Subiquity onto the primary's first three partitions (leave the `hot` pool member and the 2 TB drive untouched) -> re-import both pools -> `incus admin init` pointed at the preserved `hot/incus` dataset -> Incus recreates instances from their stored configuration -> restore any file-level data from off-site backups. If only the OS is broken, a Subiquity reinstall replaces it in minutes and the data pools are never touched. Detailed in `docs/operations/rebuild-checklist.md`.

## Things this build intentionally avoids

- Root-on-ZFS + ZFSBootMenu — this project tried it as the canonical install and then reverted, so it is worth stating plainly why. Ubuntu Server's installer has no root-on-ZFS path (the whole install becomes a manual live-environment procedure, not a guided one); the upstream OpenZFS Ubuntu root-on-ZFS guides stop at 22.04; the OpenZFS + kernel 7.0 combo prints `EXPERIMENTAL` warnings and produced a live `zpool export` "pool is busy" wedge in testing; and — decisively — the ZFSBootMenu boot path cannot be rehearsed in the VirtualBox ARM lab (its firmware can't run the EFI binary), so the one component standing between you and an unbootable box is the one that can never be tested. The boot-environment rollback it buys is real, but under Incus everything stateful already lives on ZFS with snapshots — only the thin, rebuildable OS layer loses rollback. Kept as a [documented alternative](docs/ubuntu/installation/zfs-root-alternative.md), with `msai lab install-zfs-root` rehearsing the pool/dataset/debootstrap mechanics.
- Striping a single pool across both drives — the original design did this, but the bus-speed asymmetry made "which drive is my hot data actually on" unanswerable in practice. Two independent pools give a real guarantee instead.
- LUKS+LVM (private network, headless box; LUKS adds remote-unlock friction) — ZFS native encryption on the data pools is the modern equivalent if encryption is ever wanted.
- Secure Boot (DKMS amdgpu/ROCm make MOK enrollment its own chore; threat model doesn't justify the friction).
- iGPU passthrough to a Windows VM (mutually exclusive with host ROCm, and this build's primary purpose is local LLM inference).
- Docker (or Incus) named volumes for important data — ZFS datasets via Incus's storage driver, or bind mounts for the nested-Docker case, never opaque named volumes.
- ZFS deduplication (not worth the RAM on a homelab).
- Manual iptables rules (UFW + nftables backend).
- Bare libvirt/KVM or Docker directly on the host — the original design ran both this way; both now run inside Incus instead.

## Where to start reading

- `README.md` — top-level overview.
- `docs/getting-started/hardware.md` — full hardware spec.
- `docs/ubuntu/installation/installation-walkthrough.md` — actual install steps (ext4 root + GRUB, guided installer).
- `docs/incus/index.md` — the Incus deep-dive: containers, VMs, GPU passthrough, storage.
- `docs/zfs/concepts.md` then `docs/zfs/virtualbox-lab.md` — to practice ZFS before the real install.
- `docs/operations/rebuild-checklist.md` — what to do when the rebuild day comes.
