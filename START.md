
Perfect — below is a clean, structured README.md that turns this entire conversation into a project-grade document you can drop straight into a repo.

This is written to be:
	•	Understandable to future you
	•	Justifiable to other engineers
	•	Stable across rebuilds
	•	Free of chatty back-and-forth

You can copy-paste this verbatim into README.md.

⸻

MS-S1 MAX — Host, Storage, Virtualization & Services

This repository documents the design, rationale, and operational plan for the MS-S1 MAX mini-PC project.

The goal is to build a clean, minimal Ubuntu Server host that:
	•	Uses ZFS for all important data
	•	Runs full desktop operating systems (Windows 11, Linux) via KVM/QEMU with GPU passthrough
	•	Runs services (Nextcloud, Plex, etc.) via Docker
	•	Remains rebuildable, understandable, and low-maintenance over time

This document captures decisions and reasoning, not just commands.

⸻

High-level goals
	•	Host OS is boring
	•	Ubuntu Server LTS
	•	No desktop environment
	•	SSH-only management
	•	Data lives outside containers
	•	ZFS is the source of truth
	•	Containers are disposable
	•	Virtual machines are first-class
	•	KVM/QEMU on the host
	•	GPU passthrough for Windows/Linux VMs
	•	Services are containerized
	•	Docker + Compose
	•	Bind mounts into ZFS datasets
	•	Everything is recoverable
	•	Reinstall host without touching data
	•	Snapshot and backup at filesystem level

⸻

Hardware assumptions
	•	Minisforum MS-S1 MAX
	•	Internal NVMe: 2 TB
	•	Secondary NVMe: 4 TB
	•	Integrated AMD GPU (used for passthrough)
	•	Single HDMI output (Samsung TV as display)

⸻

Disk & filesystem layout

Internal NVMe (2 TB)

Partition	Size	FS	Mount
EFI	512 MB	FAT32	/boot/efi
Boot	1 GB	ext4	/boot
Root	1 TB	ext4	/
Free	~1 TB	—	(used later for ZFS)

Why ext4 for root
	•	Extremely stable
	•	Excellent recovery tooling
	•	Zero operational surprises
	•	Root filesystem is infrastructure, not a feature

/boot lives on the same disk as / — not on ZFS, not on a separate drive.

⸻

ZFS pool (post-install)

ZFS is created after Ubuntu installation.

Sources:
	•	Remaining ~1 TB on internal NVMe
	•	Entire 4 TB secondary NVMe

Topology:
	•	Single pool
	•	No redundancy (snapshots + backups instead)

Example datasets:

tank/
├── media/              # Plex / Jellyfin (large, read-heavy)
├── nextcloud-data/     # User files
├── nextcloud-app/      # App config, apps, themes
├── db/                 # Databases (MariaDB/Postgres)
├── containers/         # Misc container state
├── vm/                 # VM disks
└── backups/

ZFS features used:
	•	compression=lz4 (everywhere)
	•	Per-dataset snapshot policies
	•	Per-dataset tuning (recordsize, quotas)

⸻

Networking

Netplan
	•	Netplan is used for all network configuration
	•	Renderer: systemd-networkd
	•	Ethernet + DHCP
	•	No Wi-Fi on the host unless strictly necessary

Example:

network:
  version: 2
  renderer: networkd
  ethernets:
    enp5s0:
      dhcp4: true

Netplan responsibilities:
	•	Interfaces
	•	IP addressing
	•	Routes
	•	DNS (via systemd-resolved)

Netplan does not handle security or filtering.

⸻

Firewall & security

UFW (not raw iptables)
	•	UFW is used as the firewall frontend
	•	Backend is nftables
	•	No manual iptables rules

Baseline policy:

ufw default deny incoming
ufw default allow outgoing
ufw allow OpenSSH
ufw enable

Rationale:
	•	UFW expresses policy, not packet mechanics
	•	nftables is the modern kernel firewall
	•	Mixing UFW with manual iptables is avoided

Netplan and UFW are not directly connected:
	•	Netplan brings interfaces up
	•	UFW filters traffic on those interfaces

⸻

Host management model
	•	Host is headless
	•	SSH is the primary management interface
	•	No desktop, browser, or dev tooling on the host
	•	HDMI output is considered optional/emergency

Once GPU passthrough is enabled, the GPU may no longer be available to the host.

⸻

Virtualization (KVM/QEMU)

Stack
	•	KVM
	•	QEMU
	•	libvirt
	•	virt-manager (used remotely over SSH)

VM types
	•	Windows 11 (GPU passthrough, gaming capable)
	•	Linux desktop VMs (optional)
	•	Other OSes as needed

Key principles
	•	VMs run directly on the host
	•	No containers around KVM/libvirt
	•	UEFI (OVMF), Q35 chipset
	•	CPU mode: host-passthrough

⸻

GPU passthrough & display model
	•	The GPU is passed through to the Windows VM
	•	The HDMI port is owned by the VM, not the host
	•	Monitor is plugged directly into the GPU
	•	Host is managed over SSH

Important implications:
	•	VNC/RDP/SPICE are not used for gaming
	•	Fullscreen games render natively via HDMI
	•	RDP/VNC are admin tools only

Streaming (Parsec/Moonlight) is optional but secondary.

⸻

Containers & data handling

Golden rule

Containers are disposable.
Data is not.

Bind mounts vs Docker volumes

Bind mounts (default choice)
	•	Transparent paths
	•	Backed by ZFS datasets
	•	Easy snapshots and backups
	•	Human-inspectable

Docker volumes
	•	Avoided by default
	•	Used only for small, disposable state

⸻

Plex example
	•	Media stored in tank/media
	•	Bind-mounted read-only into the container

volumes:
  - /mnt/tank/media:/media:ro


⸻

Nextcloud example

Nextcloud data is split into two categories:
	1.	User data (important)
	•	Stored in tank/nextcloud-data
	•	Bind-mounted into container
	•	Fully snapshotted
	2.	Application state
	•	Config, apps, themes
	•	Stored in tank/nextcloud-app
	•	Bind-mounted for transparency and recovery

Databases:
	•	Stored in tank/db
	•	Bind-mounted
	•	Snapshotted or dumped as needed

⸻

Backup & recovery philosophy
	•	ZFS snapshots protect against:
	•	Accidental deletion
	•	Bad upgrades
	•	Backups protect against:
	•	Disk failure
	•	Host loss

Host can be reinstalled without touching ZFS data:
	1.	Reinstall Ubuntu
	2.	Re-import ZFS pool
	3.	Restart containers and VMs

⸻

What this project intentionally avoids
	•	ZFS on root
	•	Desktop environment on the host
	•	Manual iptables rules
	•	Docker volumes for critical data
	•	Nested virtualization
	•	“All-in-one” hypervisor distros

⸻

Status

This repository documents:
	•	Architecture decisions
	•	Operational principles
	•	Rationale behind choices

Implementation details (exact commands, compose files, scripts) are expected to live alongside this README in docs/ and scripts/.

⸻

Final note

This setup is intentionally boring where it should be and powerful where it matters.

The host is infrastructure.
ZFS owns data.
KVM owns hardware abstraction.
Docker owns services.

Everything else is replaceable.

⸻

If you want next, I can:
	•	Split this into multiple docs (host.md, zfs.md, vms.md, containers.md)
	•	Generate a ZFS dataset creation script
	•	Write a docker-compose for Nextcloud done the ZFS way
	•	Add a rebuild checklist

Just say what you want to tackle next.
