# Remote Desktop — headless GNOME login over RDP

This host runs Ubuntu 26.04 **Desktop** (GNOME 50, Wayland). When it boots with no monitor and nobody logged in at the physical console, you still want to reach a full graphical session — click through a GUI installer, drive a browser, use an app that has no CLI. GNOME's built-in RDP support does this, but only if you pick the *right* one of its two modes. This page documents the mode that actually works headless, the exact configuration used on this machine, and the one non-obvious gotcha that stops it from listening.

Access is over [Tailscale](../tailscale/index.md) — the RDP port is never exposed to the LAN or the internet.

## The two modes, and why only one works headless

GNOME ships two completely separate remote-desktop paths. They are easy to confuse because the Settings UI presents them together and both speak RDP on port 3389.

| | Screen Sharing (per-user) | Remote Login (system) |
|---|---|---|
| systemd unit | `gnome-remote-desktop.service` (`--user`) | `gnome-remote-desktop.service` (system) |
| Daemon runs as | your login user | dedicated `gnome-remote-desktop` system user |
| What a client gets | a mirror of your **already-active** GNOME session | a fresh **GDM login screen** → brand-new session |
| Needs you logged in first? | **Yes** | **No** |
| Configured with | `grdctl …` | `grdctl --system …` |
| Headless boot? | **No** — nothing to mirror until someone logs in | **Yes** — this is the one you want |

!!! warning "Screen Sharing is the trap"
    Almost every "enable GNOME remote desktop" guide describes Screen Sharing. On a headless box it appears to work *only because you happen to be logged in on `tty2`* while testing. Reboot with no console login and the per-user daemon has no session to share — the connection fails or shows a black screen. For a machine that boots headless, use **Remote Login** (`--system`).

The two also both default to port **3389**, so running both means a port conflict. On this host the per-user Screen Sharing RDP is disabled and only the system Remote Login answers.

## Setup

All of this is `grdctl --system` plus a plain systemd enable. RDP requires a TLS certificate; the critical detail is **where** that certificate lives.

### 1. Free port 3389 (disable per-user screen sharing)

```bash
grdctl rdp disable
systemctl --user disable --now gnome-remote-desktop.service
```

### 2. Generate a TLS certificate the daemon can read

This is the gotcha. The system daemon runs as the unprivileged `gnome-remote-desktop` user (uid 980), **not** root. A key file left as `root:root 0600` is unreadable by the daemon, and it silently logs `RDP TLS certificate and key not yet configured properly` and never binds the port. Put the cert/key in the daemon's own state directory, owned by the daemon user:

```bash
D=/var/lib/gnome-remote-desktop/certificates
sudo install -d -o gnome-remote-desktop -g gnome-remote-desktop -m 700 "$D"

sudo openssl req -x509 -newkey rsa:4096 -nodes -days 3650 \
  -keyout "$D/rdp-key.pem" \
  -out    "$D/rdp-cert.pem" \
  -subj "/CN=$(hostname)"

sudo chown gnome-remote-desktop:gnome-remote-desktop "$D"/rdp-*.pem
sudo chmod 644 "$D/rdp-cert.pem"
sudo chmod 600 "$D/rdp-key.pem"
```

### 3. Point the system RDP backend at it and enable

```bash
sudo grdctl --system rdp set-tls-cert /var/lib/gnome-remote-desktop/certificates/rdp-cert.pem
sudo grdctl --system rdp set-tls-key  /var/lib/gnome-remote-desktop/certificates/rdp-key.pem
sudo grdctl --system rdp enable

sudo systemctl enable --now gnome-remote-desktop.service
```

### 4. Verify

```bash
sudo grdctl --system status      # RDP: enabled, cert/key/fingerprint populated
systemctl is-active gnome-remote-desktop.service   # active
systemctl is-enabled gnome-remote-desktop.service  # enabled (survives reboot)
ss -tlnp | grep :3389            # gnome-remote-de listening on *:3389
```

The journal should show `RDP server started`:

```bash
sudo journalctl -u gnome-remote-desktop.service -n 20
```

!!! note "The TPM message is harmless"
    Every `grdctl --system` call prints `Init TPM credentials failed … using GKeyFile as fallback`. That only means the config store falls back to a key file instead of the TPM. It does not affect RDP.

## Connecting over Tailscale

The daemon binds `*:3389`, which includes the `tailscale0` interface, so no extra firewall rule is needed (and on this host `ufw` is inactive anyway). Connect any RDP client to the tailnet name **`msai`** (or its tailnet IP):

```
msai:3389
```

- **macOS** — Windows App (formerly Microsoft Remote Desktop), add a PC `msai`.
- **Linux** — `xfreerdp /v:msai /u:morten` or Remmina (RDP, `msai:3389`).
- **iOS** — Windows App, add PC `msai`.

You will get the **GDM greeter**, not a session mirror. Log in with your normal `morten` account password; GDM creates a fresh Wayland session. The self-signed certificate triggers a one-time "unverified certificate" prompt in the client — expected; accept it (the fingerprint from `grdctl --system status` is what you are trusting).

!!! tip "Keep it on the tailnet"
    Do not port-forward 3389 or open it in the firewall. RDP is a persistent target for credential-stuffing; reaching it only over Tailscale means the port is invisible to everything outside the tailnet. See [Tailscale](../tailscale/index.md).

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ss` shows nothing on 3389, journal says `certificate not configured properly` | Cert/key not readable by the `gnome-remote-desktop` user | Move certs into `/var/lib/gnome-remote-desktop/certificates/` owned by that user (step 2) |
| Port 3389 already bound by another `gnome-remote-de` | Per-user Screen Sharing still enabled | `grdctl rdp disable && systemctl --user disable --now gnome-remote-desktop.service`, or give one a different port with `grdctl --system rdp set-port 3390` |
| Connection works only while you are logged in locally | You enabled Screen Sharing, not Remote Login | Use `grdctl --system …` (this page), not `grdctl …` |
| Client rejects the certificate | Self-signed cert not trusted yet | Accept the prompt once; verify the fingerprint matches `grdctl --system status` |
| Black screen after login | GPU/session issue, not RDP | Confirm the guest session is Wayland; check `journalctl -u gnome-remote-desktop.service` during connect |

## What is stored where

| Path | Purpose |
|---|---|
| `/usr/lib/systemd/system/gnome-remote-desktop.service` | The system daemon unit (`--system`) |
| `/var/lib/gnome-remote-desktop/certificates/` | TLS cert + key, owned by `gnome-remote-desktop` |
| `grdctl --system` config (GKeyFile under `/var/lib/gnome-remote-desktop/`) | Enabled state, cert paths, port, credentials |
