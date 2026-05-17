# MS-S1 MAX Build — Start Here

This file is the architectural intent for the project. Implementation details live in `docs/`. If you're new, read this then `docs/getting-started/`.

Hardware: [Minisforum MS-S1 MAX](https://www.minisforum.com/products/ms-s1-max) — AMD Ryzen AI Max+ 395 (Strix Halo), Radeon 8060S iGPU (RDNA 3.5, `gfx1151`), 128 GB LPDDR5X-8000 quad-channel, 2 × M.2 NVMe (PCIe 4.0 x4 + x1), 2 × 10GbE.

Target OS: **Ubuntu Server 26.04 LTS** ("Resolute Raccoon"), headless.

## High-level intent

- **Host OS is boring.** Ubuntu Server LTS, no desktop environment, SSH-only management. Plain ext4 root, no LUKS, no LVM. Boot is uninteresting infrastructure; it can be reinstalled at any time.
- **Data lives outside containers.** ZFS is the source of truth: VM disks, container data, media, model files, backups. The host can be wiped without touching pool data.
- **Containers are disposable.** Docker + Compose for services. Bind mounts from container volumes into ZFS datasets, never named volumes for important data.
- **Virtual machines are first-class.** KVM/QEMU on the host. Windows 11 VM (TPM 2.0, Secure Boot OVMF, virtio-gpu — no GPU passthrough by default; the iGPU stays with the host for ROCm).
- **AI is the primary purpose.** ROCm 7.x on the host iGPU. Ollama + llama.cpp (HIP build) for local LLM inference, with `amd-ttm` allocating ~108 GB of the 128 GB pool as GPU-accessible (GTT) memory.
- **Everything is recoverable.** Snapshots (sanoid) for accidents and bad upgrades. Off-host replication (syncoid over Tailscale and restic to B2/S3) for disk failure and site loss. Rebuild without touching data is a known procedure, not a hope.

## Hardware assumptions (one-line each)

- One CPU: 16-core / 32-thread Zen 5 in 2 × CCX layout.
- One GPU: integrated Radeon 8060S, 40 CUs, gfx1151. **Owned by the host** for ROCm.
- One RAM pool: 128 GB LPDDR5X-8000, soldered, quad-channel (~256 GB/s peak).
- Two NVMe slots, **unequal speeds**: slot 1 is PCIe 4.0 x4 (~8 GB/s), slot 2 is PCIe 4.0 x1 (~2 GB/s).
- Two 10GbE ports (Realtek RTL8127). 320W external PSU. Single HDMI 2.1 output (rarely used; SSH is the management plane).

## Disk and filesystem layout

### Primary 2 TB NVMe (slot 1, PCIe 4.0 x4) — boot + hot data

| Partition | Size | Filesystem | Mount |
|---|---|---|---|
| EFI | 512 MB | FAT32 | `/boot/efi` |
| Boot | 1 GB | ext4 | `/boot` |
| Root | 1 TB | ext4 | `/` |
| Pool member | ~1 TB | — | (ZFS) |

### Secondary 4 TB NVMe (slot 2, PCIe 4.0 x1) — bulk cold data

Entire disk → ZFS pool member.

### ZFS pool `tank`

```
tank (single pool, no redundancy, snapshots + replication for protection)
+-- (1 TB partition on primary NVMe, PCIe 4.0 x4)
+-- (4 TB secondary NVMe, PCIe 4.0 x1)
```

ARC capped at 16 GiB so VMs and Ollama have predictable memory.

### Dataset layout (per workload)

| Dataset | Properties | Holds |
|---|---|---|
| `tank/ai` | `recordsize=1M`, `compression=off`, `primarycache=metadata` | GGUF / safetensors model files |
| `tank/media` | `recordsize=1M`, `compression=lz4`, `primarycache=metadata` | Plex / Jellyfin libraries |
| `tank/nextcloud-data` | defaults | Nextcloud user data |
| `tank/nextcloud-app` | defaults | Nextcloud config / apps |
| `tank/db` | `recordsize=16K` | Per-service databases |
| `tank/vm` | `recordsize=64K` | qcow2 VM disk images |
| `tank/containers/<svc>` | defaults | Per-service container state |
| `tank/backups` | `compression=zstd-3` | Cold archive target |

Detailed properties live in `docs/zfs/datasets.md`.

## Networking

- Netplan with the `systemd-networkd` renderer. No NetworkManager.
- UFW for firewall (nftables backend on 26.04). Reverse proxy + bind-to-127.0.0.1 for service exposure; `ufw-docker` to make UFW actually filter Docker-published ports.
- Tailscale as the remote-management plane. The host is reachable on the LAN and via Tailscale; **not** directly on the public internet.

## Backup philosophy

- **Local snapshots** (sanoid): hourly/daily/weekly/monthly retention per dataset.
- **On-site replication** (syncoid): periodic `zfs send` to a second box on the LAN.
- **Off-site (block)**: syncoid over Tailscale to a remote ZFS host.
- **Off-site (file)**: restic to B2 or S3, encrypted, for Nextcloud user data and photos.

Rebuild path: install Ubuntu → re-import pool → re-deploy compose stacks → re-define VMs (XML was captured before tear-down). Detailed in `docs/operations/rebuild-checklist.md`.

## Things this build intentionally avoids

- ZFS on root (boring ext4 root is more predictable).
- LUKS+LVM (private network, headless box; LUKS adds remote-unlock friction).
- Secure Boot (DKMS amdgpu/ROCm/ZFS make MOK enrollment its own chore; threat model doesn't justify the friction).
- iGPU passthrough to a Windows VM (mutually exclusive with host ROCm, and this build's primary purpose is local LLM inference).
- Docker named volumes for important data (bind mounts into ZFS instead).
- ZFS deduplication (not worth the RAM on a homelab).
- Manual iptables rules (UFW + nftables backend).

## Where to start reading

- `README.md` — top-level overview.
- `docs/getting-started/hardware.md` — full hardware spec.
- `docs/ubuntu/installation/installation-walkthrough.md` — actual install steps.
- `docs/zfs/concepts.md` then `docs/zfs/virtualbox-lab.md` — to practice ZFS before the real install.
- `docs/operations/rebuild-checklist.md` — what to do when the rebuild day comes.
