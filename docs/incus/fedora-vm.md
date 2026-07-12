# Fedora VM

Fedora runs as an Incus VM instance — either **Fedora Server** (headless, SSH-driven) or **Fedora Workstation** (a GNOME desktop reached over SPICE). Unlike the [Windows 11 VM](windows-vm.md), Fedora needs no special firmware and no driver injection: its kernel already carries virtio, so the installer sees the virtio disk on the first boot. This page is the Fedora-specific layer on top of [VMs](vms.md); read that first for the general VM model, the resource/TPM knobs, and the restricted-project ISO workflow this page reuses.

!!! note "The iGPU stays with the host — no passthrough to this VM"
    Same unchanged rule as every VM on this build: the single Strix Halo iGPU (Radeon 8060S) stays with the **host** for ROCm, and cannot be cleanly PCI-passed-through to a guest without tearing it away from host inference. So a Fedora VM is a **2D / virtio-graphics desktop only** — perfectly fine for GNOME, a server console, or development, but there is no hardware 3D acceleration inside it. If you need the GPU for compute, that path is a **container** with the iGPU passed through ([GPU passthrough](gpu-passthrough.md)), never a VM. See [Graphical access](graphical-access.md#virtual-gpu-options-and-performance) for the honest performance ceiling.

## Two quick paths

There are two ways to get a Fedora guest, depending on whether the community image server has what you want.

### Path A — launch from the `images:` remote

The community `images:` remote publishes Fedora as both container and VM images. This is the fastest route when you just want a current Fedora and do not care about a specific spin:

```bash
# Check what Fedora images exist and which types (container vs VM) they carry.
# The release number and the type availability BOTH change over time — verify first.
incus image list images: fedora

# A Fedora system CONTAINER (shares the host kernel, no --vm)
incus launch images:fedora/41 fedora

# A Fedora VM (its own kernel/firmware) — note the --vm flag
incus launch images:fedora/41 fedora --vm
```

!!! note "The `fedora/41` tag is version-dependent — do not assume it"
    The exact Fedora release on `images:` (41, 42, ...) and whether it is published as a VM image, a container image, or both moves with each release. Run `incus image list images: fedora` and pick a tag that actually lists the `type` you need — `CONTAINER` for a system container, `VIRTUAL-MACHINE` for a VM. If `incus launch <image> --vm` complains the image has no VM variant, filter with `incus image list images: type=virtual-machine` and choose one that does. A container rootfs is not a bootable disk.

A container is lighter and ssh-able and is the right choice for most Fedora *server* workloads; reach for the VM only when you need a Fedora with its own kernel, kernel modules, or a full Workstation desktop with UEFI. The rest of this page assumes the **VM** path.

### Path B — install from the official Fedora ISO

When you want a specific spin (Workstation, a particular Server release, KDE, or an image not on `images:`), install from Fedora's own ISO. This is the [restricted-project managed-volume workflow](vms.md#the-restricted-project-iso-gotcha-managed-volumes) — read on.

## The virtio difference from Windows

!!! note "Fedora ships virtio drivers in its kernel — no driver-injection step"
    This is the key contrast with the [Windows VM](windows-vm.md). Windows Setup carries **no** virtio drivers, so a stock Windows ISO boots to an installer that sees *no disk* until you load `viostor` (or repack the ISO). Fedora is the opposite: `virtio_blk`, `virtio_net`, `virtio_scsi`, and friends are built into the Fedora kernel and its Anaconda initramfs. Boot the plain Fedora ISO on an Incus VM and Anaconda sees the virtio disk and NIC immediately. There is **no `distrobuilder repack-windows` equivalent** and no manual driver load — this is one of the reasons Linux guests "just work" on Incus.

## Create the VM and boot the ISO

Create a blank VM, then attach the Fedora ISO as a managed volume. In the restricted **`user-1000` project** you **cannot** attach a raw host path such as `source=/data/iso/Fedora-Server.iso` — the project policy rejects a host path as a disk source. Import the ISO as an `iso`-type storage volume on the `lab` pool first, then attach *that volume*, exactly as the [VMs page](vms.md#the-restricted-project-iso-gotcha-managed-volumes) and [Windows VM page](windows-vm.md#4-attach-install-media-and-virtio-drivers-managed-volumes) do.

```bash
# 1. A blank VM — firmware, a disk, no OS yet
incus init fedora --vm --empty \
  -c limits.cpu=4 -c limits.memory=8GiB -d root,size=40GiB

# 2. Import the Fedora ISO into the 'lab' pool as an iso-type volume
incus storage volume import lab /data/iso/Fedora-Server.iso fedora-iso --type=iso

# 3. Attach the managed ISO volume as a boot device, high boot.priority so firmware boots it first
incus config device add fedora install disk \
  pool=lab source=fedora-iso boot.priority=10

# 4. Start and open the graphical console to run Anaconda
incus start fedora
incus console fedora --type=vga
```

!!! warning "Managed-volume ISO import is mandatory in the `user-1000` project"
    `--type=iso` and `pool=lab` both matter, and the raw-host-path form (`source=/path/to.iso`) you will see in generic Fedora-on-Incus guides will **not** attach in this project. List imported ISOs with `incus storage volume list lab type=iso`. This is the same restricted-project gotcha documented on the [VMs page](vms.md).

Fedora's installer refuses nothing here — no TPM or Secure Boot is required. If you want a TPM for LUKS measured-boot or just parity with a hardware machine, add one while the VM is stopped (`incus config device add fedora vtpm tpm`); it is optional for Fedora. Secure Boot (`security.secureboot`, on by default for VMs) is fine to leave enabled — Fedora ships shim signed by Microsoft's key.

After the install finishes, detach the ISO so the VM boots from disk, per [VMs](vms.md#detach-the-iso-after-install):

```bash
incus stop fedora
incus config device remove fedora install
incus start fedora
incus storage volume delete lab fedora-iso   # reclaim the volume once no VM needs it
```

## Fedora Server — SSH access

A Fedora Server install boots to a text `getty`. Drive the install itself through the console — Anaconda offers a **text mode** on the serial console (`incus console fedora`) and its full **GUI** on the VGA console (`incus console fedora --type=vga`); the GUI is easier for partitioning and user creation. See [Graphical access — the two consoles](graphical-access.md#the-two-consoles-text-vs-graphical) for which console is which.

### Enable and verify sshd

Fedora Server enables `sshd` by default, but confirm it and set up key-based login:

```bash
# In the guest (via the console, or incus exec once the agent is up)
sudo systemctl enable --now sshd
systemctl status sshd

# Install your public key for key-based login (do this instead of passwords)
mkdir -p ~/.ssh && chmod 700 ~/.ssh
# paste your key into ~/.ssh/authorized_keys, chmod 600

# Then harden: disable password auth in /etc/ssh/sshd_config.d/*.conf
#   PasswordAuthentication no
sudo systemctl reload sshd
```

!!! note "`incus exec` needs the Fedora incus-agent"
    Fedora VM images from `images:` ship the **incus-agent**, so `incus exec fedora -- ...` and `incus file` work without SSH. A VM installed from the **official ISO** may not have it until you install/enable it — if `incus exec` fails but `incus console` works, that split is diagnostic (the agent is missing, not the network). Use the console or SSH in that case. See [VMs — the incus agent](vms.md#the-incus-agent-linux-guests).

### Reach SSH from your client

The VM is on `incusbr0` (NAT) by default. Expose port 22 with a proxy device bound on the host, then gate it with UFW — the same pattern the [Windows VM page](windows-vm.md#reach-rdp-from-your-client) uses for RDP, and documented in full on the [Networking page](networking.md):

```bash
# Forward host:22222 to the VM's SSH port (pick a host port that does not clash with the host's own sshd)
incus config device add fedora ssh proxy \
  listen=tcp:0.0.0.0:22222 \
  connect=tcp:127.0.0.1:22 \
  bind=host

# Restrict to the LAN / Tailscale, never the public internet
sudo ufw allow from 192.168.0.0/24 to any port 22222 proto tcp
```

Then `ssh -p 22222 user@host` over the LAN, or reach it over Tailscale by the host's MagicDNS name. Never port-forward SSH from the router — LAN and Tailscale only, gated by UFW, exactly as the rest of this build does.

## Fedora Workstation — GNOME desktop

Fedora Workstation boots straight into **GNOME on Wayland**. It renders to the emulated virtio-gpu and streams over SPICE as a 2D desktop; that works fine — GNOME/Wayland over SPICE is a supported, usable 2D session on this box (just not accelerated). Reach it through the graphical console:

```bash
incus console fedora --type=vga     # opens a local remote-viewer / SPICE window
```

For remote access to that console (from your laptop rather than the host's own screen), use the SSH-socket-forward or remote-Incus-client paths — do not duplicate them here, they are covered in full on the graphical-access page:

- [Accessing the desktop remotely](graphical-access.md#accessing-the-desktop-remotely) — SSH-forward the SPICE socket (Option A) or run a remote Incus client (Option C).
- [VNC as an alternative path](graphical-access.md#vnc-as-an-alternative-path) — a tunnelled in-guest VNC server for a *running* Linux desktop, cross-platform.

### The guest agents

Two separate agents matter for a good desktop — the same distinction drawn in [Graphical access](graphical-access.md#the-incus-agent-in-vms):

```bash
# In the Fedora guest — spice-vdagent is the SPICE agent:
#   clipboard sharing + dynamic resolution (resize the viewer, the desktop follows)
sudo dnf install -y spice-vdagent
sudo systemctl enable --now spice-vdagentd

# qemu-guest-agent gives the host clean shutdown/freeze hooks (fsfreeze for snapshots)
sudo dnf install -y qemu-guest-agent
sudo systemctl enable --now qemu-guest-agent
```

`spice-vdagent` is Fedora's equivalent of Windows' spice-guest-tools: with it running, copy/paste flows both ways and resizing the `remote-viewer` window resizes the GNOME session live. Without it you are stuck picking a fixed mode in GNOME display settings. Workstation images usually include `spice-vdagent` already — verify with `systemctl status spice-vdagentd`.

## Unattended install with Kickstart

Clicking through Anaconda over the SPICE console is fine once; for reproducibility you want a **fully unattended** install. Fedora/Anaconda's mechanism is **Kickstart** — the analogue of Ubuntu's autoinstall (which [VMs](vms.md#unattended-autoinstall) documents) and Windows' `autounattend.xml`.

### A minimal working `ks.cfg`

```kickstart
# ks.cfg — minimal unattended Fedora install
lang en_US.UTF-8
keyboard us
timezone --utc UTC

# Networking: DHCP on the virtio NIC, set the hostname
network --bootproto=dhcp --device=link --activate --hostname=fedora

# Accounts — see the WARNING below about plaintext secrets
rootpw --plaintext ChangeMe123!
user --name=morten --groups=wheel --plaintext --password=ChangeMe123! \
     --sshkey="ssh-ed25519 AAAA... your-key"

# Disk: wipe and auto-partition the virtio disk
clearpart --all --initlabel
autopart
bootloader --location=mbr

# Packages (@^...-environment picks a base environment)
%packages
@^server-product-environment
openssh-server
qemu-guest-agent
%end

# Post-install: make sure sshd is on
%post
systemctl enable sshd
%end

reboot
```

Adjust `@^server-product-environment` to the environment you want (for Workstation, `@^workstation-product-environment`). Verify option spellings against the current [Fedora Kickstart / Anaconda documentation](https://docs.fedoraproject.org/en-US/fedora/latest/install-guide/) — Kickstart command names and defaults shift between releases (for example the move to `--plaintext` vs a hashed `--iscrypted` password).

!!! warning "This file contains a plaintext password — do not commit real secrets"
    `rootpw --plaintext` and `user --plaintext` put the literal password in the file, exactly like the plaintext password in Windows' [`autounattend.xml`](windows-vm.md#a-complete-autounattendxml). Keep a real `ks.cfg` out of git — use `--iscrypted` with a hash from `python3 -c 'import crypt; print(crypt.crypt("pw"))'` (or `openssl passwd -6`), rely on the `--sshkey` for login and set no interactive password, or inject the secret at build time. Change any password immediately after first boot.

### Delivering the Kickstart to Anaconda

Two delivery methods; both hand Anaconda the same `ks.cfg`.

**Method 1 — `inst.ks=` kernel boot argument.** Point Anaconda at a Kickstart served over HTTP:

```
inst.ks=http://192.168.0.10/ks.cfg
```

You add this to the installer's kernel command line. In a headless Incus flow the practical way to bake it in is to remaster the Fedora ISO's GRUB config with the `inst.ks=` argument on the `linux` line, then import the repacked ISO as a managed volume and boot it (the same remaster-and-`storage volume import` dance the [Ubuntu autoinstall section](vms.md#wiring-the-seed-to-the-iso-nocloud-kernel-arg) describes). Serving `ks.cfg` from any HTTP server the VM can reach on `incusbr0` — including one on the host — is enough.

**Method 2 — the OEMDRV volume (no kernel edit).** Anaconda auto-detects a Kickstart named `ks.cfg` in the root of any volume whose filesystem **label is `OEMDRV`** — no kernel argument, no ISO remaster. Build a small labelled image and attach it as a second disk:

```bash
# Build a tiny ext4 (or vfat) image labelled OEMDRV containing ks.cfg
truncate -s 4M oemdrv.img
mkfs.ext4 -L OEMDRV oemdrv.img       # the LABEL must be exactly OEMDRV
mkdir -p mnt && sudo mount oemdrv.img mnt
sudo cp ks.cfg mnt/ks.cfg
sudo umount mnt

# Import it as a managed block volume and attach it alongside the install ISO
incus storage volume import lab ./oemdrv.img fedora-oemdrv --type=iso
incus config device add fedora oemdrv disk pool=lab source=fedora-oemdrv
```

!!! note "OEMDRV is the headless-friendly method here"
    Because editing a managed ISO's kernel cmdline at boot is awkward in a headless flow (the same problem Ubuntu autoinstall hits), the **OEMDRV** label is usually the least-friction path on this build: no ISO remaster, just a 4 MB labelled volume attached next to the installer. Anaconda scans attached block devices for the `OEMDRV` label at startup and loads `ks.cfg` automatically. If your Incus build will not import a raw `.img` as a volume, wrap it as an ISO image (`mkisofs`/`xorriso` with the volume/label set) and import that instead. Detach and delete the OEMDRV volume after install, like any managed volume.

## Verify

```bash
incus list                                   # fedora, VIRTUAL-MACHINE, RUNNING
incus info fedora                            # vCPUs, memory, disk
incus config device show fedora              # root disk, install ISO / oemdrv, ssh proxy
incus exec fedora -- cat /etc/fedora-release # confirm the release (agent must be up)
incus console fedora --type=vga              # GNOME desktop (Workstation) or console login
# From a client: ssh -p 22222 user@host over LAN/Tailscale
incus exec fedora -- systemctl status spice-vdagentd sshd qemu-guest-agent
```

## Next steps

- [VMs](vms.md) — the general VM model, the restricted-project ISO workflow, TPM, the incus agent, unattended install.
- [Graphical access](graphical-access.md) — the SPICE/VGA console in depth, reaching a desktop remotely, VNC, the virtual-GPU performance reality.
- [Linux ISO installs](linux-iso-install.md) — unattended installs for other distros: Debian preseed, openSUSE AutoYaST, and friends.
- [Networking](networking.md) — proxy devices and UFW gating for the SSH/console ports.
- [GPU passthrough](gpu-passthrough.md) — why real GPU compute lives in *containers*, not VMs, on this host.
