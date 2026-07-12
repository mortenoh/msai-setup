# Remote Desktop — headless GNOME login over RDP

This host runs Ubuntu 26.04 **Desktop** (GNOME 50, Wayland). When it boots with no monitor and nobody logged in at the physical console, you still want to reach a full graphical session — click through a GUI installer, drive a browser, use an app that has no CLI. GNOME's built-in RDP support does this, but only if you pick the *right* one of its two modes. This page documents the mode that actually works headless, the exact configuration used on this machine, the two non-obvious gotchas that silently break it (a certificate the daemon can't read, and login credentials it requires but the guides never mention), and how session reconnection actually behaves.

Access is over [Tailscale](../tailscale/index.md) — the RDP port is never exposed to the LAN or the internet.

## The two modes, and why only one works headless

GNOME ships two completely separate remote-desktop paths. They are easy to confuse because the Settings UI presents them together and both speak RDP on port 3389.

| | Screen Sharing (per-user) | Remote Login (system) |
|---|---|---|
| systemd unit | `gnome-remote-desktop.service` (`--user`) | `gnome-remote-desktop.service` (system) |
| Daemon runs as | your login user | dedicated `gnome-remote-desktop` system user |
| What a client gets | a mirror of your **already-active** GNOME session | authenticates with stored RDP credentials → a brand-new headless session |
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

### 4. Set the login credentials (the second gotcha)

The system backend's default authentication method is `credentials`, and **until you set a username and password it denies every client** — the journal shows `[RDP] Credentials are not set, denying client` while the client just sees a generic connection failure. The certificate work above gets the port *listening*; this gets it *accepting*. The daemon validates the RDP client against these credentials and then hands the login to GDM as that user, so set them to a **real local account** — your own:

```bash
# Omit the password to be prompted for it (keeps it out of shell history):
sudo grdctl --system rdp set-credentials morten
# If it does not prompt, pass it explicitly:
#   sudo grdctl --system rdp set-credentials morten 'your-login-password'

sudo systemctl restart gnome-remote-desktop.service
```

!!! warning "The password must match the real account"
    These credentials are handed to GDM to perform the actual login. If the password does not match `morten`'s real account password, the RDP handshake succeeds but the session login fails afterwards — the Mac Windows App reports this as the misleading *"This might be due to an expired password."*

### 5. Verify

```bash
sudo grdctl --system status --show-credentials   # RDP enabled; cert/key AND username/password populated
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

- **macOS** — **Thincast Remote Desktop Client** (free, [thincast.com](https://thincast.com), a FreeRDP-based GUI), or the CLI: `brew install freerdp` then `sdl-freerdp /v:msai /u:morten /p:'…' /cert:ignore /dynamic-resolution` (the client binary is `sdl-freerdp`, not `xfreerdp`, on macOS; `freerdp-proxy` is a server component — do not use it).
- **Linux** — `xfreerdp3 /v:msai /u:morten` or Remmina (RDP, `msai:3389`).
- **iOS/Android** — a FreeRDP-based client; the Microsoft Windows App does **not** work (see below).

Enter the **username and password you set in step 4** (`morten` + your account password). You do **not** see an interactive GDM greeter — the daemon authenticates you with those credentials and creates a fresh headless Wayland session directly. The self-signed certificate triggers a one-time "unverified certificate" prompt — expected; accept it (the fingerprint from `grdctl --system status` is what you are trusting).

!!! danger "The Microsoft Windows App / Remote Desktop does NOT work with this mode"
    GNOME's `--system` remote login performs its login handover with an **RDP server redirection** PDU — the client authenticates to the main daemon, then must *reconnect* to a spun-up per-session daemon. Microsoft's clients (the macOS/iOS **Windows App**, formerly Microsoft Remote Desktop) **do not follow that redirection**; they treat it as a logoff and abort with *"We couldn't connect… this might be due to an expired password."* The server log shows `[RDP] Sending server redirection` → `ERRINFO_LOGOFF_BY_USER`. This is a client limitation, not a server misconfiguration.

    **Use a FreeRDP-based client instead** — `sdl-freerdp` (CLI) or **Thincast** (GUI) on macOS both follow the redirection and connect cleanly. There is no way to make the Windows App work with `--system` remote login, and the usual escape hatches are **both dead ends on this host**: per-user *screen sharing* stores its RDP password in the GNOME login keyring, which stays **locked** under headless autologin (no password is typed at boot to unlock it); and **xrdp** needs an Xorg/GNOME-on-Xorg session, but this is a **Wayland-only** install (no `/usr/share/xsessions`, no `Xorg` binary). A FreeRDP client is therefore the only workable option here.

!!! tip "Keep it on the tailnet"
    Do not port-forward 3389 or open it in the firewall. RDP is a persistent target for credential-stuffing; reaching it only over Tailscale means the port is invisible to everything outside the tailnet. See [Tailscale](../tailscale/index.md).

## Session persistence and reconnecting

Understanding this avoids a confusing failure. A remote login is a real, seatless logind session (`loginctl` shows it as `Class=user`, `Remote=yes`, no seat — distinct from a physical `seat0`/`tty` login and from any SSH session by the same user):

- **First connect** → a new headless session is created.
- **Close the client without logging out** → the session **keeps running in the background**; apps stay open. It does not end on disconnect.
- **Reconnect** → GNOME does **not** start a fresh login. It tries to **resume the existing session via RDP "server redirection."** FreeRDP-based clients follow the redirect and drop you back into your session. The **macOS/Windows App does not follow it reliably** — the connection aborts and it reports *"We couldn't connect… this might be due to an expired password."* The journal shows `[RDP] Sending server redirection` followed by `Failed to peek routing token` / `ERRINFO_LOGOFF_BY_USER`.
- **Explicitly Log Out** (menu → power → Log Out, not just closing the window) → the session ends, and the next connect is a clean fresh login.

!!! tip "Rule of thumb for the macOS Windows App"
    **Log Out before you disconnect**, so every connect is a fresh session and you never hit the redirection failure. If you want true resume-where-you-left-off, use **FreeRDP** (`xfreerdp /v:msai /u:morten`) instead, which handles server redirection correctly. If a stale session ever locks you out, terminate it server-side with `loginctl terminate-session <id>` (find it via `loginctl list-sessions`) — note this kills whatever was open in it.

!!! note "SSH and RDP by the same user do not conflict"
    Being SSH'd in as `morten` while connecting RDP as `morten` is fine — they are two independent logind sessions. SSH is a `tty` session and is never a redirection target, so it does not cause the reconnect failure above. The only real hazard is cosmetic: `loginctl` lists several `morten` sessions from the same host, so identify the right one (`Service=sshd` vs the graphical one) before terminating anything.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ss` shows nothing on 3389, journal says `certificate not configured properly` | Cert/key not readable by the `gnome-remote-desktop` user | Move certs into `/var/lib/gnome-remote-desktop/certificates/` owned by that user (step 2) |
| Client is refused, journal says `[RDP] Credentials are not set, denying client` | No RDP credentials set | `sudo grdctl --system rdp set-credentials morten` (step 4), then restart the service |
| Connects, then fails with *"…might be due to an expired password"* on a **first** login | The set password does not match the real account | Re-run `set-credentials` with the correct `morten` password |
| Same *"expired password"* error only on **reconnect** | A prior session is still running; the Windows App can't follow the resume redirection | Log Out before disconnecting, or use FreeRDP, or `loginctl terminate-session <id>` the stale session (see [Session persistence](#session-persistence-and-reconnecting)) |
| Journal shows `Sending server redirection` / `Failed to peek routing token` | Client failing RDP server redirection to an existing session | Same as above — this is the reconnect case, not a network fault |
| Extra `gdm-greeter` sessions accumulate in `loginctl` after several attempts | One orphan greeter per connect attempt | Harmless; clear with `sudo systemctl restart gnome-remote-desktop.service` **while nobody is connected** (it drops active sessions) |
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
