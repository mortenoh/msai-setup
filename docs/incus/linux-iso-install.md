# Installing other Linux distros from ISO

The community `images:` remote already publishes ready-to-boot VM images for the mainstream distros, so most of the time you never touch an ISO. But when you need a distro that isn't on `images:`, a specific point release, or a **reproducible, fully unattended** build, you create a blank VM and boot it from the distribution's own installer ISO. This page is the multi-distro companion to [VMs](vms.md): that page covers the generic ISO boot and Ubuntu's autoinstall; here we cover the *other* families' unattended mechanisms — Debian preseed, the RHEL/anaconda Kickstart family, openSUSE AutoYaST, Arch, and Alpine — and how to deliver each one on Incus in the restricted `user-1000` project.

!!! note "Incus VMs are UEFI + virtio + agent by default — modern Linux just works"
    Every Incus VM boots OVMF (UEFI) firmware and presents its disk and NIC as **virtio** devices. Unlike Windows ([Windows VM](windows-vm.md)), essentially every current Linux installer already ships the `virtio_blk`/`virtio_scsi`/`virtio_net` modules in its initrd, so the installer sees the disk and network with **no driver injection**. There is no Linux equivalent of the `distrobuilder repack-windows` dance — point a stock ISO at a blank VM and it boots straight to a working installer.

## The generic flow (recap)

The mechanics of booting *any* ISO are identical and are covered in full on the [VMs page](vms.md#installing-a-vm-from-an-iso) — read that once. In short:

```bash
# 1. A blank VM: firmware, a disk, no OS
incus init debian-vm --vm --empty \
  -c limits.cpu=4 -c limits.memory=8GiB -d root,size=40GiB

# 2. Import the ISO as a managed volume, then attach it (see the warning below)
incus storage volume import lab /data/iso/debian-13.iso debian-iso --type=iso
incus config device add debian-vm install disk \
  pool=lab source=debian-iso boot.priority=10

# 3. Boot and drive the installer over the graphical console
incus start debian-vm
incus console debian-vm --type=vga

# 4. After install, detach the media so the VM boots from disk
incus stop debian-vm
incus config device remove debian-vm install
incus start debian-vm
```

!!! warning "Managed-volume ISO import is mandatory in the `user-1000` project"
    This build runs instances in the restricted **`user-1000` project**, which **forbids raw host-path disk devices** — the `source=/data/iso/foo.iso` form you'll see in generic Incus guides will simply not attach. Import the ISO as an **iso-type storage volume** on the `lab` pool (`--type=iso` matters; a plain custom volume isn't treated as bootable optical media) and attach *that*. The pool is **`lab`** (source dataset `lab/incus`), not `default`. List imported ISOs with `incus storage volume list lab type=iso`. This is the same gotcha documented on the [VMs](vms.md#the-restricted-project-iso-gotcha-managed-volumes) and [Windows VM](windows-vm.md) pages.

The rest of this page is about the **unattended** config for each family and, crucially, **how to feed the installer its boot arguments and config file on Incus** — where you have no PXE server and can't easily hand-edit a managed ISO's bootloader at boot.

### Passing installer boot arguments on Incus

Most unattended mechanisms need a **kernel command-line argument** (`auto url=`, `inst.ks=`, `autoyast=` …). On this headless host you have two practical ways to set it:

- **Edit the boot menu at the VGA console.** Open `incus console <vm> --type=vga`, and at the distro's GRUB/isolinux menu press `e` (GRUB) or `Tab` (isolinux) to edit the highlighted entry, append the argument to the `linux`/`append` line, and boot it (`Ctrl-x` / `Enter`). One-off, but hands-on.
- **Repack the ISO** with the argument baked into the bootloader config (and, where relevant, the config file embedded on the media or on a second labelled volume). This is the reproducible path and mirrors the Ubuntu autoinstall repack on the [VMs page](vms.md#wiring-the-seed-to-the-iso-nocloud-kernel-arg). Import the repacked ISO as a managed volume as above.

For config files served **over HTTP**, a throwaway web server on the host bridge works well — the VM can reach the host over `incusbr0`:

```bash
# Serve the current directory (holding preseed.cfg / ks.cfg / autoinst.xml) to the VM
cd /data/unattended && python3 -m http.server 8000
# The installer fetches e.g. http://<incusbr0-host-ip>:8000/preseed.cfg
```

## Debian — preseed

Debian's installer (`debian-installer`, "d-i") is driven by a **preseed** file. A minimal `preseed.cfg`:

```text
# Locale and keyboard
d-i debian-installer/locale string en_US.UTF-8
d-i keyboard-configuration/xkb-keymap select us

# Network + mirror
d-i netcfg/get_hostname string debian-vm
d-i netcfg/get_domain string local
d-i mirror/country string manual
d-i mirror/http/hostname string deb.debian.org
d-i mirror/http/directory string /debian
d-i mirror/http/proxy string

# Clock
d-i clock-setup/utc boolean true
d-i time/zone string Etc/UTC

# Root disabled; create an admin user with a crypted password
d-i passwd/root-login boolean false
d-i passwd/user-fullname string Morten
d-i passwd/username string morten
# Generate with: mkpasswd --method=sha-512  (do NOT commit a real hash)
d-i passwd/user-password-crypted password $6$REPLACE_WITH_A_REAL_HASH

# Whole-disk automatic partitioning (atomic recipe = one root partition)
d-i partman-auto/disk string /dev/vda
d-i partman-auto/method string regular
d-i partman-auto/choose_recipe select atomic
d-i partman-partitioning/confirm_write_new_label boolean true
d-i partman/choose_partition select finish
d-i partman/confirm boolean true
d-i partman/confirm_nooverwrite boolean true

# Package selection: standard system + OpenSSH server
tasksel tasksel/first multiselect standard, ssh-server
d-i pkgsel/include string qemu-guest-agent

# GRUB to the disk
d-i grub-installer/only_debian boolean true
d-i grub-installer/bootdev string /dev/vda
d-i finish-install/reboot_in_progress note
```

!!! warning "The crypted password is a secret — keep it out of git"
    `passwd/user-password-crypted` is a real SHA-512 hash; anyone with the preseed can crack or reuse it. Commit only a placeholder and inject the hash at build time, exactly as the [Windows autounattend](windows-vm.md#a-complete-autounattendxml) page insists for its plaintext password. Prefer SSH-key login and disable password auth after first boot. The disk here is `/dev/vda` because Incus presents the virtio disk as `vda`, not `sda`.

**Delivery — two options:**

- **HTTP (`auto url=`).** Serve `preseed.cfg` from the host (snippet above) and boot the installer with the `auto url=` argument. Choosing **"Automated install"** from the boot menu, or appending the argument yourself, pulls the file and runs non-interactively:

  ```text
  auto=true priority=critical url=http://<host-ip>:8000/preseed.cfg
  ```

  The `auto=true priority=critical` pair suppresses the early prompts (language/keyboard/network) that would otherwise appear *before* the preseed is fetched.

- **Baked into the ISO / initrd.** For a self-contained image, place `preseed.cfg` inside the installer's initrd (d-i reads `/preseed.cfg` from the initrd automatically) or on the ISO, and add `auto=true priority=critical file=/cdrom/preseed.cfg` to the isolinux/GRUB append line, then import the repacked ISO as a managed volume. Initrd-preseeding is the most robust because the file is present before networking even starts.

See the official [Debian preseed appendix](https://www.debian.org/releases/stable/amd64/apbs02.en.html) for the full key list — recipes and task names drift slightly between releases, so pin your examples to the release you're installing.

## RHEL family (RHEL / AlmaLinux / Rocky / CentOS Stream) — Kickstart

The RHEL family — and Fedora — all use **anaconda**, driven by a **Kickstart** file. A minimal `ks.cfg`:

```text
# Non-interactive text install
text
# Keyboard / language / timezone
keyboard us
lang en_US.UTF-8
timezone Etc/UTC --utc

# Networking: DHCP, set hostname
network --bootproto=dhcp --device=link --activate
network --hostname=rhel-vm

# Root login locked; create an admin user (see the warning about --plaintext)
rootpw --lock
user --name=morten --groups=wheel --iscrypted --password=$6$REPLACE_WITH_A_REAL_HASH
sshkey --username=morten "ssh-ed25519 AAAA... your-key"

# Whole-disk automatic partitioning on the virtio disk
clearpart --all --initlabel --drives=vda
autopart --type=lvm
bootloader --location=mbr --boot-drive=vda

# Packages
%packages
@^minimal-environment
openssh-server
qemu-guest-agent
%end

# Reboot when done
reboot
```

!!! warning "Use a crypted password, never `--plaintext`, and keep the hash private"
    `user --iscrypted --password=<hash>` takes a SHA-512 hash (`openssl passwd -6` or `mkpasswd`). Anaconda also accepts `--plaintext` — don't use it, and don't commit a real hash regardless. Same rule as every other config on this page: placeholder in git, real secret injected at build time, rotate after first boot.

**Delivery — two options:**

- **`inst.ks=` kernel argument.** Modern anaconda (RHEL 8+, current AlmaLinux/Rocky/CentOS Stream/Fedora) reads Kickstart from `inst.ks=`. Serve it over HTTP and append to the boot line:

  ```text
  inst.ks=http://<host-ip>:8000/ks.cfg
  ```

  You can also point at the ISO itself (`inst.ks=cdrom:/ks.cfg`) if you baked it in. Note the `inst.` prefix — older RHEL 6/7 used a bare `ks=`; verify against your release's docs.

- **The OEMDRV volume trick (no kernel arg needed).** Anaconda automatically loads a Kickstart from a file named `ks.cfg` on any block device whose **filesystem label is `OEMDRV`**. Build a tiny labelled image and attach it as a second managed volume — the installer finds it with no boot-argument editing at all:

  ```bash
  # Build a small ext4/vfat image labelled OEMDRV containing ks.cfg
  truncate -s 4M oemdrv.img
  mkfs.ext4 -L OEMDRV oemdrv.img          # label MUST be exactly OEMDRV
  # ...mount, copy ks.cfg to its root, unmount...

  # Import and attach it alongside the installer ISO
  incus storage volume import lab /data/iso/oemdrv.img rhel-oemdrv --type=iso
  incus config device add rhel-vm ksdrv disk pool=lab source=rhel-oemdrv
  ```

This is the same anaconda mechanism Fedora uses. For a **detailed, worked Fedora walkthrough** — Kickstart plus the OEMDRV image build step by step — see the sibling page [Fedora VM](fedora-vm.md); this section is the generic RHEL-family version of it. Official reference: the [RHEL Kickstart command list](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/9/html/automatically_installing_rhel/kickstart-commands-and-options-reference_rhel-installer). Command availability varies by major version — pin examples to your target release.

## openSUSE — AutoYaST

openSUSE (Leap and Tumbleweed) and SUSE use **AutoYaST**, an XML control file. A minimal `autoinst.xml` skeleton:

```xml
<?xml version="1.0"?>
<!DOCTYPE profile>
<profile xmlns="http://www.suse.com/1.0/yast2ns"
         xmlns:config="http://www.suse.com/1.0/configns">
  <partitioning config:type="list">
    <drive>
      <device>/dev/vda</device>
      <use>all</use>                <!-- take the whole virtio disk -->
    </drive>
  </partitioning>

  <users config:type="list">
    <user>
      <username>morten</username>
      <!-- Generate: mkpasswd --method=sha-512 ; do NOT commit a real hash -->
      <user_password>$6$REPLACE_WITH_A_REAL_HASH</user_password>
      <encrypted config:type="boolean">true</encrypted>
    </user>
  </users>

  <software>
    <patterns config:type="list">
      <pattern>base</pattern>
      <pattern>enhanced_base</pattern>
    </patterns>
    <packages config:type="list">
      <package>openssh</package>
      <package>qemu-guest-agent</package>
    </packages>
  </software>

  <services-manager>
    <services config:type="list">
      <service>
        <service_name>sshd</service_name>
        <service_status>enable</service_status>
      </service>
    </services>
  </services-manager>
</profile>
```

!!! warning "The `<user_password>` hash is a secret"
    Set `<encrypted>true</encrypted>` and supply a SHA-512 hash, never a cleartext password in the profile. Placeholder in git, real hash at build time, rotate after first boot — same discipline as the Debian and Kickstart sections.

**Delivery — the `autoyast=` boot parameter.** Append it to the installer boot line, pointing either at HTTP or a file on an attached volume:

```text
autoyast=http://<host-ip>:8000/autoinst.xml
# or, if baked onto a labelled volume/ISO:
autoyast=device://sr1/autoinst.xml
```

The XML schema is large and version-sensitive; build a starting profile from a manual install's generated `/root/autoinst.xml`, and consult the [AutoYaST documentation](https://doc.opensuse.org/projects/autoyast/) rather than hand-writing large sections.

## Arch Linux

Arch has **no traditional unattended installer** — no preseed/Kickstart equivalent. Two realistic paths:

- **`archinstall` with config files.** The official live ISO ships the `archinstall` guided installer, which accepts JSON configs for a non-interactive run:

  ```bash
  # From the Arch live environment (drive it via incus console --type=vga)
  archinstall --config user_configuration.json --creds user_credentials.json
  ```

  A minimal `user_configuration.json`:

  ```json
  {
    "archinstall-language": "English",
    "keyboard-layout": "us",
    "harddrives": ["/dev/vda"],
    "disk_config": { "config_type": "default_layout" },
    "bootloader": "systemd-boot",
    "hostname": "arch-vm",
    "packages": ["openssh", "qemu-guest-agent"],
    "services": ["sshd"],
    "profile_config": { "profile": { "main": "Minimal" } }
  }
  ```

  Credentials (root password, user + password) go in a separate `user_credentials.json` so they stay out of the main config. `archinstall`'s JSON schema **changes frequently** between releases — generate a current template with `archinstall --dry-run` and save its config rather than copying an old one.

  !!! warning "`user_credentials.json` holds real passwords in cleartext"
      Keep it out of git entirely, deliver it over the network or on a throwaway volume, and delete it after install. Prefer seeding an SSH key and locking password login.

- **Fully manual.** The classic `pacstrap`/`arch-chroot` install driven by hand over `incus console --type=vga`, following the [Arch installation guide](https://wiki.archlinux.org/title/Installation_guide). Slower, but the reference path when `archinstall` doesn't fit.

Deliver the JSON either over HTTP (host web server above) or on a small managed volume attached as a second disk, then reference its mount path from the `archinstall` command.

## Alpine

Alpine's `setup-alpine` script runs **non-interactively from an answer file** — ideal for tiny VMs (a 256 MiB Alpine guest is entirely reasonable). Generate a template with `setup-alpine -c answerfile` inside the live ISO, then trim it. A minimal `answerfile`:

```sh
KEYMAPOPTS="us us"
HOSTNAMEOPTS="alpine-vm"
# DHCP on the virtio NIC
INTERFACESOPTS="auto lo
iface lo inet loopback

auto eth0
iface eth0 inet dhcp"
TIMEZONEOPTS="UTC"
PROXYOPTS="none"
APKREPOSOPTS="-1"                 # pick the first/fastest mirror
SSHDOPTS="openssh"
# Wipe and use the whole virtio disk as a 'sys' (installed) system
DISKOPTS="-m sys /dev/vda"
```

Run it, then reboot onto the disk:

```sh
# From the Alpine live environment (via incus console --type=vga)
setup-alpine -f answerfile
```

!!! warning "The answer file's `ROOTSSHKEY` / passwords are secrets"
    A full answer file can carry the root password and SSH keys. Don't commit real credentials; seed an SSH key and set a strong root password out-of-band. `setup-alpine` prompts interactively for the root password unless you preseed it — check the [Alpine setup-alpine docs](https://wiki.alpinelinux.org/wiki/Alpine_setup_scripts#setup-alpine) for the current answer-file keys, which change across releases.

Deliver the answer file over HTTP (`wget http://<host-ip>:8000/answerfile`) from within the live environment, or on a small attached volume.

## Summary table

| Distro | Unattended mechanism | Boot arg / keyword | Delivery on Incus |
|---|---|---|---|
| Debian | preseed (`preseed.cfg`) | `auto=true priority=critical url=` or `file=` | HTTP from host, or baked into initrd/ISO |
| RHEL / Alma / Rocky / CentOS Stream | Kickstart (`ks.cfg`) | `inst.ks=` **or** OEMDRV-labelled volume | HTTP, ISO, or a second managed volume labelled `OEMDRV` |
| Fedora | Kickstart (`ks.cfg`) | `inst.ks=` / OEMDRV — see [Fedora VM](fedora-vm.md) | second managed volume (OEMDRV) |
| openSUSE / SUSE | AutoYaST (`autoinst.xml`) | `autoyast=` | HTTP, or `device://` on an attached volume |
| Arch | `archinstall --config` (no native unattended) | n/a (run in live env) | JSON on HTTP or a managed volume |
| Alpine | `setup-alpine -f answerfile` | n/a (run in live env) | answer file on HTTP or a managed volume |

## Verify

```bash
incus list                              # the new VM shows TYPE VIRTUAL-MACHINE, RUNNING
incus info <name>                       # vCPUs, memory, disk
incus config device show <name>         # confirm the install ISO is DETACHED post-install
incus exec <name> -- uname -a           # works once the incus-agent (qemu-guest-agent) is up
incus exec <name> -- systemctl is-active sshd    # ssh-server enabled by the unattended config
```

If `incus exec` fails but `incus console <name>` logs in, the guest agent isn't running — confirm `qemu-guest-agent` was in your package list. Reach the VM over the network with SSH (Linux guests) via a **proxy device + UFW**, restricted to LAN/Tailscale exactly as [Networking](networking.md) describes:

```bash
incus config device add <name> ssh proxy \
  listen=tcp:0.0.0.0:22 connect=tcp:127.0.0.1:22 bind=host
sudo ufw allow from 192.168.0.0/24 to any port 22 proto tcp
```

!!! note "GPU and graphics on these VMs"
    The single iGPU stays with the host for ROCm, so these VMs run on **2D virtio graphics only** — never GPU passthrough. If a workload truly needs the GPU it belongs in a container, the only GPU path on this build ([GPU passthrough](gpu-passthrough.md)). For a graphical desktop in one of these Linux VMs, see [Graphical access](graphical-access.md); day-to-day you'll drive them headless over SSH.

## Next steps

- [VMs](vms.md) — the general VM model, the generic ISO boot, and the Ubuntu autoinstall path this page complements.
- [Fedora VM](fedora-vm.md) — the detailed Fedora Kickstart + OEMDRV walkthrough referenced above.
- [Graphical access](graphical-access.md) — the SPICE/VGA console for driving installers and Linux desktops.
- [Networking](networking.md) — proxy devices, UFW forwarding, and Tailscale reachability for SSH to the guest.
