# Graphical access — desktops and consoles in Incus

Incus is happiest headless. But VMs frequently need a *screen*: to click through a Windows installer, to run a Linux desktop, to see a boot-time error that never reaches the serial console. This page is the exhaustive guide to getting pixels out of an Incus instance — the console model, the SPICE stack underneath `--type=vga`, how to reach a desktop locally on this host's own display versus remotely over the network, the virtual GPU options and their honest performance ceiling on this hardware, and the switch from SPICE to RDP once a Windows guest is up.

Read [VMs](vms.md) first for the general VM model; this page is the graphics layer on top of it.

!!! note "The hard hardware truth up front"
    This host is an **AMD Strix Halo APU** whose Radeon 8060S iGPU is the host's *only* display adapter and drives the host's own screen. It **cannot be cleanly PCI-passed-through to a VM** — doing so would tear the GPU away from the host (and from host-side ROCm/Vulkan inference, the entire reason this box exists). So every VM here renders to a **virtual GPU emulated by QEMU and streamed over SPICE**. There is no hardware 3D acceleration inside any VM on this machine. Plan for "perfectly fine 2D desktop," not "gaming rig." Everything below is written around that constraint honestly — see [Virtual GPU options and performance](#virtual-gpu-options-and-performance).

## The two consoles: text vs graphical

Every Incus VM exposes **two** completely separate console channels. Knowing which one you want saves a lot of confusion.

| | Text/serial console | Graphical console |
|---|---|---|
| Command | `incus console <inst>` | `incus console <inst> --type=vga` |
| Transport | serial port (virtio-console) over the API | SPICE over a unix socket |
| What you see | boot messages, a `getty` login, kernel panics | the actual framebuffer — GRUB, the installer GUI, a desktop |
| Needs a viewer? | No — renders in your terminal | Yes — `remote-viewer` (virt-viewer) locally |
| Good for | scripting, servers, rescue, reading a stuck boot | installers, desktops, anything that draws | 
| Detach | `Ctrl-a` then `q` | close the viewer window |

```bash
# Text serial console — renders right in the terminal
incus console ubuntu-server
# detach with:  Ctrl-a  q

# Graphical console — spawns a local SPICE viewer window
incus console ubuntu-desktop --type=vga
```

!!! warning "`Ctrl-a q` detaches; it does not stop the VM"
    Detaching from the text console leaves the VM running. Only `incus stop` stops it. New users routinely think they closed the VM by leaving the console — check `incus list`.

Both consoles work whether or not the guest runs the incus agent — they operate below the guest OS, at the virtual-hardware level. The agent (covered [below](#the-incus-agent-in-vms)) is a *third*, separate channel for exec and file transfer, not a console.

## SPICE — what actually happens under `--type=vga`

SPICE (Simple Protocol for Independent Computing Environments) is the remote-display protocol QEMU speaks for graphical output. When you run `incus console <inst> --type=vga`, a specific chain of events fires:

1. **QEMU is already listening.** When a VM starts, Incus launches its QEMU with a SPICE server bound to a **unix domain socket** inside the instance's runtime directory — not a TCP port. For a normal system-wide daemon that is under `/var/lib/incus/…`; for this build's **`user-1000` project** (a rootless/per-user project) it lives under the user runtime tree, e.g. `~/.local/share/incus/virtual-machines/<name>/qemu.spice` (exact path varies by Incus build — treat it as "a unix socket owned by the VM," not a fixed string).
2. **The client asks the API for a VGA console.** `incus console --type=vga` calls the Incus API's console endpoint requesting the SPICE stream, and the daemon proxies that unix socket to the client.
3. **The client re-exposes it as a local socket and launches a viewer.** The `incus` client writes the SPICE connection to a temporary local unix socket and spawns your configured viewer — by default `remote-viewer` (part of **virt-viewer**) — pointed at `spice+unix:///…`. The viewer window appears; that is your VM's screen.

So there is no TCP, no password, and nothing on the network by default: the whole path is unix sockets and the local Incus client. That is exactly why it is secure by default and also why "accessing it remotely" (below) takes real work.

### Install the viewer

`--type=vga` needs a SPICE client on whatever machine runs the `incus` command:

```bash
# Debian/Ubuntu (this host)
sudo apt install -y virt-viewer     # provides remote-viewer

# Fedora
sudo dnf install -y virt-viewer

# macOS (if you run the incus client on a Mac)
brew install virt-viewer            # remote-viewer via XQuartz, or use RDP/VNC instead
```

`virt-viewer` provides both `virt-viewer` and `remote-viewer`; Incus uses `remote-viewer`. On this host it is already installed (see the build's tooling notes). Confirm:

```bash
which remote-viewer && remote-viewer --version
```

### Point Incus at a different viewer

Incus lets you override the command it spawns for a VGA console with an environment variable, useful if you prefer a different SPICE client or want to script it:

```bash
# Override the viewer Incus launches for --type=vga
export INCUS_CONSOLE=remote-viewer          # the default
incus console ubuntu-desktop --type=vga
```

If the viewer is missing, `--type=vga` fails with a "could not find remote-viewer" style error rather than a black screen — install virt-viewer and retry.

### The GSpice-CRITICAL usbredir warning is harmless

The first time you open a VGA console you will almost certainly see something like:

```
(remote-viewer:12345): GSpice-CRITICAL **: 10:14:22.031: usbredir: ...
```

This is `remote-viewer` complaining that the SPICE **USB-redirection** channel is present but the `usbredirect`/`usbredirhost` plumbing on your client isn't wired up. **It is cosmetic.** The display, keyboard, and mouse all work fine; only USB pass-through-over-SPICE is affected (see [USB redirection](#usb-redirection-over-spice)). Ignore it, or install `usbredir`/`usbutils` on the client if you actually want USB redirection.

## Accessing the desktop locally (on this host's own screen)

If you are physically at this machine (or in a graphical session on it — a local X/Wayland session, or an X session forwarded to you), the simplest path is just:

```bash
incus console ubuntu-desktop --type=vga
```

`remote-viewer` opens as a normal window on the host's desktop. Because the SPICE socket is local, there is zero network involved and latency is as low as it gets — this is the best-quality graphical experience available for a VM on this box.

!!! note "This host is normally headless / remote-administered"
    In practice you rarely sit at this machine's physical keyboard. The realistic day-to-day is: SSH in, and either forward the SPICE socket to your laptop (below), or — for a running desktop — drive the guest over RDP/VNC/SSH instead of the SPICE console. The VGA console's core jobs are **initial OS install** and **rescue when the network path is broken**.

## Accessing the desktop remotely

The SPICE socket is a **local unix socket** on the host. Getting to it from your laptop means bridging that socket across the network. Three approaches, from most to least secure.

### Option A (recommended): SSH-forward the SPICE unix socket

Modern OpenSSH forwards unix sockets directly (`-L localsocket:remotesocket`). This keeps SPICE unauthenticated-but-unix-local on both ends while the *transport* is your existing SSH (and thus Tailscale-gated) session. No new listening port on the host, no SPICE-over-TCP, no TLS to manage.

The wrinkle: `incus console --type=vga` wants to *launch a viewer on the host*. For remote use you instead want the raw socket, which you forward and open with a local `remote-viewer`. Two ways:

**A1 — forward the port Incus proxies.** Ask Incus to proxy the console to a local *port* on the host, then SSH-forward that port:

```bash
# On the HOST: proxy the VGA console to a localhost TCP port (foreground; keep it running)
#   Some Incus versions accept a --address for the VGA console; if yours does not,
#   use A2 below, which needs no such flag.
# Then, from the CLIENT, tunnel it:
ssh -L 5900:127.0.0.1:5900 user@host-over-tailscale
# and on the client:
remote-viewer spice://127.0.0.1:5900
```

**A2 — run the incus client remotely against the daemon (cleanest).** Add this host as a remote to the Incus client on your laptop and run `--type=vga` there; the client spawns *your laptop's* `remote-viewer` and the display streams over the authenticated Incus API. This is the intended remote path — see [Option C](#option-c-remote-incus-client-over-the-api).

!!! note "Why unix-socket forwarding is the safe default"
    SPICE with `disable-ticketing` (no password) is fine on a **local unix socket** because filesystem permissions gate it. The moment you put it on TCP without TLS+password you have an unauthenticated remote framebuffer — anyone who can reach the port gets your desktop, keyboard, and mouse. Keeping the socket unix-local and tunnelling over SSH/Tailscale is why this build never exposes raw SPICE TCP.

### Option B: expose SPICE over TCP (insecure without TLS — avoid)

You *can* make QEMU's SPICE server listen on a TCP port. Do not, unless you fully understand the exposure. Plain SPICE-over-TCP is **unauthenticated and unencrypted**: the framebuffer, every keystroke, and mouse input traverse the network in the clear and accept any connection.

If you must (lab-only, never routable):

```bash
# Conceptually: bind SPICE to TCP via raw QEMU args on the instance.
# raw.qemu injects arguments into the VM's QEMU command line.
incus config set ubuntu-desktop raw.qemu -- \
  '-spice port=5924,addr=127.0.0.1,disable-ticketing=on'
# 127.0.0.1 only, then SSH-forward 5924 — never bind 0.0.0.0 with disable-ticketing.
```

!!! danger "disable-ticketing on a routable address is a remote desktop for the whole network"
    Never combine `disable-ticketing=on` with a non-loopback `addr`. If you genuinely need SPICE on the wire, use **SPICE TLS with a password** (below) or, far simpler, tunnel the unix socket over SSH (Option A). For a *running* desktop, RDP/VNC are better remote protocols than raw SPICE anyway.

### SPICE TLS (if you insist on SPICE on the network)

QEMU/SPICE supports TLS with x509 certs and a password ticket. This is the only safe way to put SPICE directly on the wire. It means generating a CA and server certs, pointing QEMU at them, and setting a ticket:

```bash
# Sketch only — full cert generation omitted. TLS SPICE via raw.qemu:
incus config set ubuntu-desktop raw.qemu -- \
  '-spice tls-port=5959,x509-dir=/path/to/certs,password=SECRET'
# client:
remote-viewer 'spice://host?tls-port=5959'   # with the CA trusted client-side
```

In practice, on this build, **do not do this** — SSH/Tailscale tunnelling (Option A) or a remote Incus client (Option C) achieves the same securely with far less ceremony. TLS SPICE is documented here only so you know the safe-on-the-wire option exists.

### Option C: remote Incus client over the API

The most Incus-native remote path. Install the `incus` client on your laptop, add this host as a remote (authenticated with a client certificate over the Incus HTTPS API, ideally reached over Tailscale), then run the VGA console *from the laptop* — the client launches your laptop's local `remote-viewer` and streams SPICE inside the authenticated API connection.

```bash
# On the CLIENT (laptop), one-time: trust + add the remote
incus remote add lab-host https://host-over-tailscale:8443   # follow the cert/token prompt
incus remote switch lab-host

# Then the VGA console works exactly as if local — viewer opens on the laptop
incus console ubuntu-desktop --type=vga --project user-1000
```

This gives you: authentication (client cert), encryption (HTTPS API), no extra listening ports beyond the Incus API, and the normal `--type=vga` UX. It is the recommended remote graphical path for a *pre-network* task (installer, GRUB, rescue). Once the guest is network-up, switch to RDP (Windows) or SSH/VNC (Linux).

!!! note "Requires the Incus API to be reachable"
    Option C needs the daemon's HTTPS listener (`core.https_address`) enabled and reachable — gate it to the Tailscale CIDR (`100.64.0.0/10`), never the public internet, exactly as [Networking](networking.md) gates everything else. If you only ever administer this box over SSH, Option A (socket forwarding) avoids exposing the API at all.

## Access-method comparison — pick the right tool

| Method | Encrypted | Auth | Best for | Clipboard | Dynamic resize | Notes |
|---|---|---|---|---|---|---|
| **Text console** (`incus console`) | via API/SSH | yes | servers, scripting, rescue, boot logs | n/a | n/a | no viewer needed |
| **SPICE VGA console** (`--type=vga`, local) | local socket | fs perms | installers, pre-network GUI, rescue | with agent | with agent | best latency, host-local |
| **SPICE via SSH tunnel** (Option A) | SSH/Tailscale | SSH key | remote installer/rescue | with agent | with agent | no new ports |
| **SPICE via remote client** (Option C) | HTTPS API | client cert | remote installer/rescue, native UX | with agent | with agent | needs API exposed |
| **RDP** (Windows guest) | yes (RDP) | Windows creds | day-to-day Windows desktop | excellent | excellent | see [Windows VM](windows-vm.md) |
| **RDP / xrdp** (Linux guest) | yes (RDP) | Linux/PAM | day-to-day Linux desktop, native RDP client, WAN | good | good | in-guest xrdp; proxy device to expose |
| **VNC** (in-guest server) | tunnel it | VNC/PAM | day-to-day Linux desktop, cross-platform | server-dependent | server-dependent | proxy device to expose |
| **SSH / SSH X11** (Linux guest) | yes | SSH key | Linux CLI, single GUI apps | n/a / X11 | n/a | no full desktop |

The short rule this build follows:

- **Installing / rescuing / pre-network** -> SPICE VGA console (local, or Option A/C remote).
- **Running Windows desktop** -> RDP.
- **Running Linux desktop** -> RDP via [xrdp](#xrdp-rdp-into-a-linux-desktop) or VNC (or just SSH if you only need a shell / one app).

## Virtual GPU options and performance

Every VM here draws to an **emulated GPU** that QEMU exposes and SPICE streams. Incus's default is `virtio-gpu`; the guest sees a paravirtual display adapter. The realistic options:

| Emulated GPU | 3D (virgl) | Driver in guest | Notes on this host |
|---|---|---|---|
| **virtio-gpu** (default) | optional (virgl) | virtio-gpu / virtio-dri | modern default; efficient 2D; virgl 3D only if the **host** can back it |
| **virtio-vga** | optional (virgl) | virtio + VGA compat | virtio-gpu plus legacy VGA BIOS — helps guests that need VGA early (some installers) |
| **qxl** | no | qxl / spice | older SPICE-native adapter; solid 2D, good SPICE integration, no 3D |
| **stdvga / VGA** | no | generic VESA | last-resort fallback; low res, no acceleration |

```bash
# Incus does not expose a first-class "gpu model" knob for the virtual display;
# the virtual display adapter is chosen by Incus/QEMU. To force a specific model or
# enable virgl you inject QEMU args. Example: force qxl (good SPICE 2D, no 3D):
incus config set ubuntu-desktop raw.qemu -- '-vga qxl'

# Example: virtio-gpu with virgl 3D (only meaningful if the HOST can provide GL) :
incus config set ubuntu-desktop raw.qemu -- \
  '-device virtio-vga-gl -display egl-headless'
```

!!! warning "virgl 3D will not give you real GPU acceleration on this box"
    virgl proxies guest OpenGL to a host GL context. That host context would have to run on the Strix Halo iGPU — the same GPU you are deliberately keeping for ROCm/Vulkan inference and the host display. Even where virgl initialises, you get software-ish or contended GL, not a passed-through GPU. **Treat every VM here as a 2D desktop.** For anything needing real GPU compute, use a **container** with the iGPU passed through ([GPU passthrough](gpu-passthrough.md)), not a VM. This is the single most important performance fact on the page.

### Resolution, multi-monitor, and smoothness

- **Resolution** is negotiated between the SPICE viewer window and the guest. With the guest-side SPICE agent installed (`spice-vdagent` on Linux, spice-guest-tools on Windows), **resizing the `remote-viewer` window resizes the guest desktop automatically** — the single biggest quality-of-life win. Without the agent you are stuck picking a fixed mode inside the guest (`xrandr`, display settings).
- **Multi-monitor** is supported by SPICE/`remote-viewer` (View -> Displays) when the guest agent and enough virtual video memory are present; on an emulated GPU this is usable for 2D but not something to lean on.
- **Smoothness**: 2D desktop movement, scrolling, and video-as-pixels are fine over a local socket; full-screen video and any 3D are soft because there is no hardware accel. Lower the guest's color depth/resolution if a remote link feels laggy.

## The incus agent (in VMs)

Linux VM images from the `images:` remote ship **`incus-agent`**, a small daemon that runs *inside* the guest and talks to the host over a **virtio-vsock** channel. It is separate from both consoles and from SPICE. It provides:

- `incus exec <vm> -- <cmd>` — run commands in the VM without SSH (there is no shared kernel, so this goes through the agent, unlike a container's namespace injection).
- `incus file push/pull` — move files in and out.
- Dynamic config application (some `incus config` changes land live via the agent).

```bash
incus exec ubuntu-desktop -- uname -a        # works only if incus-agent is running
incus exec ubuntu-desktop -- systemctl status incus-agent
```

Its relationship to graphics: the agent is what makes **out-of-band management** possible while you also have a SPICE window open — but the agent does **not** provide the display. You can have a perfect SPICE desktop and a dead agent, or a working agent and no display; they are independent. Custom-built images and Windows do not run the Linux agent (Windows has its own incus-agent MSI in spice-guest-tools; see [Windows VM](windows-vm.md)).

!!! note "SPICE guest agent vs incus agent — two different agents"
    Do not confuse them. **`spice-vdagent`** (Linux) / spice-guest-tools (Windows) is the *SPICE* agent — it enables clipboard sharing, dynamic resolution, and better cursor handling *inside the graphical console*. **`incus-agent`** is the *Incus* agent — exec and file transfer. A desktop can want both: spice-vdagent for a nice console, incus-agent for management. They are installed and run separately.

## Clipboard, dynamic resolution, folder sharing, USB over SPICE

These are all features of the **SPICE guest agent**, not of Incus itself. Install it in the guest to unlock them.

### Clipboard sharing and dynamic resolution

```bash
# Inside a Linux guest desktop
sudo apt install -y spice-vdagent
sudo systemctl enable --now spice-vdagentd
```

With `spice-vdagent` running: copy/paste flows both ways between host and guest, and resizing the `remote-viewer` window resizes the guest desktop live. On Windows, the equivalent ships in **spice-guest-tools** (install it inside Windows).

### Folder sharing

Two distinct mechanisms — do not confuse them:

- **Incus `disk` device (virtiofs)** — share a host directory into a **Linux** VM. This is the robust, high-performance path and is an Incus feature, not a SPICE one:
  ```bash
  # In the restricted user-1000 project, raw host paths are NOT allowed as disk
  # sources — you must share via a managed storage volume instead. See vms.md.
  incus config device add ubuntu-desktop shared disk \
    pool=lab source=shared-vol path=/mnt/shared
  ```
- **SPICE folder sharing (WebDAV)** — `remote-viewer`'s "shared folder" streams a folder over the SPICE channel via `spice-webdavd` in the guest. Convenient for ad-hoc file drops from a *remote* viewer where virtiofs isn't reachable; slower and flakier than virtiofs. Install `spice-webdavd` in the guest to use it.

!!! warning "virtiofs host-path sharing is blocked in the restricted `user-1000` project"
    This build's `user-1000` project forbids raw host-path disk devices. You cannot `source=/data/whatever` a host directory straight into a VM. Share data by first creating a **managed storage volume** on the `lab` pool and attaching *that* (`source=<volume-name>`), or use SPICE WebDAV for small ad-hoc transfers. See [VMs -> restricted-project storage](vms.md).

### USB redirection over SPICE

`remote-viewer` can redirect a physical USB device from the *client* into the guest over SPICE (menu: File -> USB device selection). This is what the harmless `GSpice-CRITICAL usbredir` warning refers to. To make it work you need `usbredir` support on both ends:

```bash
# Client side (where remote-viewer runs)
sudo apt install -y usbredir usbutils
# Guest side (Linux): spice-vdagent + the usbredir channel, already present on modern SPICE
```

Then the USB device selector in `remote-viewer` lists client USB devices you can attach into the guest. Useful for a YubiKey or USB installer inside a VM; irrelevant to normal desktop use.

## Audio in VMs

Incus does not expose a first-class audio device knob; audio in a VM comes from QEMU's emulated sound routed over SPICE. To get guest audio to your SPICE viewer you generally inject an audio device via `raw.qemu` and let SPICE carry it:

```bash
# Emulated audio routed through SPICE (guest needs a matching sound driver)
incus config set ubuntu-desktop raw.qemu -- \
  '-audiodev spice,id=snd0 -device ich9-intel-hda -device hda-duplex,audiodev=snd0'
```

Realistically on this build: audio-over-SPICE is fiddly and low-priority. For a Windows guest you actually use day to day, **RDP carries audio** cleanly — enable audio redirection in the RDP client and skip SPICE audio entirely. For a Linux desktop, PulseAudio/PipeWire over the network (or just not needing guest audio) is usually simpler than QEMU SPICE audio.

## Windows-specific graphical access: SPICE to install, RDP to live

Windows on Incus has a clean two-phase graphics story, and getting it right is the difference between a painful and a pleasant Windows VM.

### Phase 1 — SPICE VGA console for installation

Windows Setup is a GUI; you drive it through the SPICE console before Windows has any network or RDP:

```bash
incus console win11 --type=vga
```

You use this console to click through Setup, load the virtio storage driver, and reach the desktop. See [Windows 11 VM](windows-vm.md) for the TPM/Secure Boot/virtio-driver specifics that Setup requires.

### Phase 2 — install spice-guest-tools, then switch to RDP

Once Windows is up:

1. Inside Windows, install **spice-guest-tools** (from the virtio-win / SPICE tools ISO). This gives you the QXL/virtio display driver, `spice-vdagent` (clipboard + dynamic resolution in the SPICE console), and the **Windows incus-agent**.
2. Enable **Remote Desktop** and connect with an RDP client. From then on, **RDP is the daily driver** and the SPICE console becomes rescue-only.

**Why RDP beats SPICE for a running Windows desktop:**

| | SPICE console | RDP |
|---|---|---|
| Clipboard | works with spice-vdagent | excellent, native |
| Dynamic resolution / multi-mon | usable | excellent, native |
| Performance on a 2D desktop | good locally, soft remote | RDP is tuned for exactly this; better over the network |
| Audio | fiddly (QEMU/SPICE) | clean redirection |
| Printer / drive redirection | no | yes |
| Reconnect after network blip | reconnect the console | RDP session persists |
| Encryption/auth on the wire | needs tunnel/TLS | built-in |

```bash
# Reach RDP: proxy 3389 on the host, gate with UFW (see windows-vm.md / networking.md)
incus config device add win11 rdp proxy \
  listen=tcp:0.0.0.0:3389 connect=tcp:127.0.0.1:3389 bind=host
```

Connect from a client with **`xfreerdp`** or **Remmina** (Linux), or the Microsoft Remote Desktop app (macOS/Windows):

```bash
xfreerdp /v:host-over-tailscale:3389 /u:User /dynamic-resolution /clipboard +audio
# or use Remmina's GUI with the same host/credentials
```

Full RDP-enablement, NLA, and Tailscale-CIDR restriction live in [Windows VM](windows-vm.md) and the build's RDP convention. The rule: **SPICE installs Windows; RDP runs it.**

## Linux VM graphical desktop

A stock `images:ubuntu/24.04` VM is a **server** image — it boots to a text `getty`, has no desktop, and `--type=vga` shows you a console login, not a GUI. To get a graphical Linux desktop you install one in the guest.

```bash
# Inside the Linux VM (via incus exec or SSH)
sudo apt update
sudo apt install -y ubuntu-desktop-minimal    # or: gnome-core, task-xfce-desktop, kde-plasma-desktop
sudo apt install -y spice-vdagent             # clipboard + dynamic resolution in the SPICE console
sudo systemctl enable --now spice-vdagentd
sudo systemctl set-default graphical.target   # boot into the GUI
sudo reboot
```

After the reboot, `incus console ubuntu-desktop --type=vga` shows the display manager and a full desktop.

### Autologin (optional, for a kiosk / always-on desktop)

For a VM whose whole purpose is a desktop you reach graphically, skip the login prompt with GDM autologin:

```bash
# /etc/gdm3/custom.conf inside the guest
[daemon]
AutomaticLoginEnable = true
AutomaticLogin = your-user
```

!!! note "Why a server image has no desktop — and pick a light one"
    Community VM images are minimal server rootfs by design (small, fast, headless-first). A desktop is hundreds of extra packages you add deliberately. On this box, because there is **no GPU acceleration in the VM**, a **lightweight desktop (XFCE, LXQt)** feels noticeably crisper than GNOME/KDE for the same emulated GPU. If you just need to run one graphical app, consider SSH X11 forwarding (`ssh -X`) instead of a whole desktop environment.

### SSH X11 forwarding — one app, no desktop

If you only need a single GUI application, you do not need a desktop environment or SPICE at all:

```bash
# From a client with an X server; forwards a single app's window over SSH
ssh -X user@guest-ip
xterm            # or the one GUI app you need
```

Clean, encrypted, no desktop install. Not a substitute for a full session, but perfect for the "I just need to run one X app in this VM" case.

## VNC as an alternative path

SPICE is Incus's built-in graphical console, but **VNC** is a fine alternative for a *running* Linux desktop — it is cross-platform, every OS has a client, and it is easy to tunnel. Incus has no built-in VNC server for VMs, so VNC means **running a VNC server inside the guest** and exposing its port.

```bash
# Inside a Linux guest: a VNC server (TigerVNC example)
sudo apt install -y tigervnc-standalone-server
vncserver :1 -geometry 1600x900 -localhost yes   # bind to loopback, tunnel it out

# Expose the guest's VNC port on the host with an Incus proxy device
incus config device add ubuntu-desktop vnc proxy \
  listen=tcp:127.0.0.1:5901 connect=tcp:127.0.0.1:5901 bind=host

# From a client: SSH-tunnel and connect
ssh -L 5901:127.0.0.1:5901 user@host-over-tailscale
# then point a VNC viewer at 127.0.0.1:5901
```

!!! warning "VNC is unauthenticated/weak by default — always tunnel it"
    Bind the in-guest VNC server to `-localhost yes` and reach it only through an SSH/Tailscale tunnel, exactly like SPICE-over-TCP. Never expose 590x to the LAN, let alone the internet. VNC's built-in "password" is weak; the tunnel is the real security boundary.

VNC vs SPICE for a Linux desktop: SPICE has better clipboard/resize integration via `spice-vdagent` and is already wired into `incus console`; VNC wins on client ubiquity and simplicity of tunnelling. For Windows, ignore both and use RDP.

## xrdp — RDP into a Linux desktop

RDP is not just for Windows. **xrdp** is an open-source RDP server for Linux: install it in the guest and you reach the Linux desktop with the exact same native RDP clients you already use for the Windows VM. Prefer this over SPICE/VNC when:

- You want a **native RDP client** on Windows/macOS (the built-in Microsoft Remote Desktop app, or [a macOS RDP client](../remote-desktop/rdp/macos-clients.md)) rather than installing a SPICE viewer or hunting for a decent VNC client.
- The link is a **WAN / higher-latency** path — RDP is tuned for 2D desktops over the network and generally feels crisper remotely than raw SPICE or VNC.
- You already run RDP for the Windows VM and want **one protocol, one client** for every desktop on this box.

### Guest-side setup

Install a desktop and `xrdp`, then point xrdp at the session you want it to launch:

```bash
# Inside the Linux VM (via incus exec or SSH)
sudo apt update
sudo apt install -y xfce4 xfce4-goodies      # or ubuntu-desktop-minimal / gnome-core
sudo apt install -y xrdp

# Tell xrdp which session to start. xrdp runs ~/.xsession (or ~/.xsessionrc) if present,
# otherwise falls back to /etc/xrdp/startwm.sh. For XFCE:
echo "startxfce4" > ~/.xsession
# For GNOME the fallback in startwm.sh usually works, but an explicit session is safest:
#   echo "gnome-session" > ~/.xsession

# Enable and start the service
sudo systemctl enable --now xrdp
sudo systemctl status xrdp        # should be active (listening on 3389)
```

!!! note "The `xrdp` user and the `ssl-cert` group"
    The `xrdp` package creates a system user `xrdp` that needs read access to the RDP key material; the postinst adds it to the **`ssl-cert`** group for you. If xrdp fails to start with a TLS/key error, confirm the membership (`id xrdp` shows `ssl-cert`) and restart the service. Package specifics vary slightly across Debian/Ubuntu releases, so treat the group name as "whatever owns `/etc/xrdp` key material on your release" if it differs.

!!! note "A GNOME session under xrdp can be fiddly"
    GNOME's Wayland session does not serve over xrdp; xrdp drives an **X11** session. On some releases you must select "GNOME on Xorg" or set the `.xsession` explicitly as above. A **lightweight desktop (XFCE, LXQt)** is the path of least resistance under xrdp on this box — and, because there is no GPU acceleration in the VM anyway, the one you want regardless.

### Reach xrdp from your client

The VM is on `incusbr0` (NAT) by default, so expose port 3389 with a proxy device bound on the host, then gate it with UFW (per [Networking](networking.md)) — the same pattern the [Windows VM](windows-vm.md) uses:

```bash
# Forward host:3389 to the Linux VM's xrdp port
incus config device add ubuntu-desktop rdp proxy \
  listen=tcp:0.0.0.0:3389 \
  connect=tcp:127.0.0.1:3389 \
  bind=host

# Restrict to the LAN / Tailscale, never the public internet
sudo ufw allow from 192.168.0.0/24 to any port 3389 proto tcp
```

Then connect from a [macOS RDP client](../remote-desktop/rdp/macos-clients.md) (or `xfreerdp` / Remmina on Linux) to the host's address — or its MagicDNS name over Tailscale — on port 3389, and log in with the guest's Linux username and password.

!!! warning "Never expose 3389 to the internet"
    Same rule as the Windows RDP proxy: xrdp is reachable on the LAN and over Tailscale only, gated by UFW. Do not port-forward 3389 from your router. Only one desktop can bind 3389 on the host — if the Windows VM already claims it, give the Linux VM a different `listen` port (e.g. `listen=tcp:0.0.0.0:3390`).

!!! note "xrdp gives you a 2D desktop only"
    xrdp streams a software-rendered X11 desktop — there is **no GPU acceleration**, exactly as with SPICE and VNC. The Strix Halo iGPU stays with the host (see [Virtual GPU options and performance](#virtual-gpu-options-and-performance)). RDP's advantage here is protocol/client quality over the network, not rendering speed; full-screen video and 3D remain soft.

## Headless and automation

You can drive and observe a VM's graphical console without ever opening a window.

### Screenshot a VM's console

Incus can grab the current framebuffer of a running VM to an image file — invaluable for "why is this installer stuck" in a headless/CI context:

```bash
# Capture the VM's current screen to a PNG (no viewer needed)
incus console ubuntu-desktop --type=vga --show-log 2>/dev/null || true
# Screenshot support: capture the framebuffer to a file
incus query --request GET /1.0/instances/ubuntu-desktop/console?screenshot   # if supported by your build
```

!!! note "Screenshot support varies by Incus version"
    Framebuffer-screenshot support has moved around across Incus releases. If your build lacks a direct screenshot verb, the portable fallback is to open the SPICE socket with a scriptable SPICE client (e.g. `spice-vdagent` tooling, or a headless `remote-viewer` capture) over the forwarded socket. For fully headless *provisioning* you should not be watching a screen at all — use [unattended install](vms.md) so no console interaction is needed.

### Drive a VM without a GUI

- **Provisioning**: use cloud-init (Linux) or autounattend.xml (Windows) so install needs zero clicks — see [VMs -> unattended install](vms.md) and [Windows VM](windows-vm.md).
- **Post-boot control**: `incus exec` (agent) or SSH for Linux; WinRM/PowerShell-remoting or RDP-scripting for Windows.
- **Boot/GRUB interaction**: the *text* console (`incus console`) is scriptable in a way the graphical one is not — prefer serial-console workflows for automation whenever the guest can be configured to use them.

## Troubleshooting

### Black screen / no picture in the VGA console

- The VM may simply be at a blank stage (post before GRUB, or a headless target with nothing drawing). Confirm it is actually running and progressing: `incus list`, then check the **text** console `incus console <inst>` for boot messages.
- A Linux **server** image has no desktop — a VGA console showing a text login is correct, not a bug. Install a desktop ([above](#linux-vm-graphical-desktop)).
- Guest booted to `multi-user.target`: `sudo systemctl set-default graphical.target` and reboot.

### `remote-viewer` window never opens

- virt-viewer not installed on the machine running `incus`: `which remote-viewer` — install `virt-viewer`.
- Running `--type=vga` over plain SSH with no display: `remote-viewer` needs an X/Wayland display to draw into. Use `ssh -X`, or better, run the console from a **remote Incus client** on a graphical machine ([Option C](#option-c-remote-incus-client-over-the-api)).
- Check for the actual error: `incus console <inst> --type=vga` prints why the viewer failed to spawn.

### "Console not available" / "Instance is not running"

- VMs only: the graphical console needs a **running VM**. `incus start <inst>` first.
- Containers do not have a VGA console at all — `--type=vga` is VM-only. For a container you use `incus exec <c> -- bash`, not a graphical console.
- In the `user-1000` project, make sure you are operating in the right project: add `--project user-1000` or `incus project switch user-1000`.

### Wrong / stuck resolution

- Install `spice-vdagent` (Linux) or spice-guest-tools (Windows) in the guest, then resizing the viewer window resizes the guest live.
- Without the agent, set a mode inside the guest: `xrandr --output Virtual-1 --mode 1920x1080` (name varies), or the desktop's display settings.
- Some installers force a low VGA mode until the real driver loads — that is expected during install and clears once the virtio/qxl driver is in.

### Laggy / soft desktop

- Expected ceiling: **no GPU acceleration in the VM on this host.** Full-screen video and 3D will be soft. Lower resolution/color depth, use a lightweight desktop (XFCE), and prefer a *local* socket or short-latency tunnel.
- For a *running* Windows desktop, switch to **RDP** — it is dramatically better than SPICE over a network link.
- For a *running* Linux desktop, [xrdp](#xrdp-rdp-into-a-linux-desktop) or VNC may feel better than SPICE remotely; locally, SPICE is best.

### `incus exec` fails but the console works (agent not running)

- `incus exec` needs **incus-agent** in the guest; the console does not. A working console + failing exec = dead/missing agent. `incus console <inst>` in, then `systemctl status incus-agent` and enable it. Custom/Windows images may lack the Linux agent entirely — use SSH/RDP.

### Cursor doubled / offset / laggy

- Classic "no guest agent" symptom: two cursors (host + guest) or an offset. Install `spice-vdagent` / spice-guest-tools; the agent enables client-side cursor and fixes the doubling and offset.

### Keyboard grabbed / can't get the mouse back

- `remote-viewer` may grab keyboard/pointer. Release with the configured **ungrab hotkey** (default `Shift+F12`, or `Ctrl+Alt`), or leave full-screen (`Shift+F11`). Set it under `remote-viewer` preferences if the default clashes.

### The GSpice-CRITICAL usbredir warning

- Cosmetic. See [above](#the-gspice-critical-usbredir-warning-is-harmless) — it does not affect the display. Install `usbredir` on the client only if you actually want USB redirection.

## Verify

```bash
incus list                                   # target VM is RUNNING
which remote-viewer                          # SPICE viewer present
incus console ubuntu-desktop --type=vga       # graphical console opens
incus console ubuntu-server                   # text console (Ctrl-a q to detach)
incus exec ubuntu-desktop -- systemctl status incus-agent   # agent (Linux guests)
# In-guest: spice-vdagent running for clipboard/resize
incus exec ubuntu-desktop -- systemctl status spice-vdagentd
```

## Next steps

- [VMs](vms.md) — the general VM model, ISO installs, hardware config, TPM, the agent, unattended install.
- [Windows 11 VM](windows-vm.md) — full Windows install and the SPICE-to-RDP switch.
- [Networking](networking.md) — proxy devices and UFW gating for RDP/VNC ports.
- [GPU passthrough](gpu-passthrough.md) — why real GPU acceleration lives in *containers*, not VMs, on this host.
