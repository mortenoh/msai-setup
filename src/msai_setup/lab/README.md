# MS-S1 MAX VirtualBox Lab

A hands-on lab for practising the MS-S1 MAX setup (ZFS, Ansible, Docker) before touching the real hardware.

Two layers:

1. **Python + VBoxManage** (this directory) creates a VirtualBox VM, builds a remastered Ubuntu install ISO with autoinstall baked into GRUB, and a cloud-init CIDATA ISO with your SSH key. Boots headless; Subiquity installs Ubuntu fully unattended.
2. **Ansible** then configures the VM: baseline packages, sudo, SSH hardening, UFW, ZFS pool + datasets, Docker, a sample compose stack.

The Ansible playbooks are the same ones you'd run against the real MS-S1 MAX once it's installed — only the inventory changes.

## Quick start

```bash
brew install ansible xorriso virtualbox
brew install hudochenkov/sshpass/sshpass

python3 scripts/lab/all.py
```

That runs:

1. `01_provision.py` - downloads Ubuntu ISO, remasters with `autoinstall` GRUB cmdline, builds a CIDATA cloud-init ISO with the lab SSH key, creates the VM, attaches everything, boots headless, waits for SSH.
2. `02_apply.py` - generates an Ansible inventory pointing at the VM, runs the playbook chain.

When done, snapshot the fresh state:

```bash
VBoxManage snapshot ms-s1-max-lab take fresh-install --pause
```

## Layout

```
scripts/lab/
  _config.py             # env-driven LabConfig
  _vbox.py               # VBoxManage wrapper (ARM + x86 aware)
  _iso.py                # ISO download, SHA256 verify, autoinstall remaster
  _cloudinit.py          # Render autoinstall YAML, build CIDATA ISO
  _ssh.py                # SSH wait, lab keypair generation
  _state.py              # JSON-backed phase state
  01_provision.py        # phase 01 - VM + Ubuntu install
  02_apply.py            # phase 02 - Ansible playbooks
  all.py                 # full pipeline
  ansible/
    ansible.cfg
    requirements.yml
    playbooks/
      bootstrap.yml      # apt baseline + sudoers + journald
      ssh-hardening.yml
      ufw.yml
      zfs.yml            # install ZFS + pool + datasets
      docker.yml
      services.yml       # Traefik + whoami smoke test
```

## Architecture-aware defaults

`_config.py` detects host arch (`uname -m`) and picks matching defaults:

| Host | Ubuntu ISO | VBox ostype | VBox platform |
|---|---|---|---|
| Apple Silicon (`arm64`) | `ubuntu-24.04.3-live-server-arm64.iso` from cdimage.ubuntu.com | `Ubuntu24_LTS_arm64` | `arm` |
| x86_64 | `ubuntu-24.04.4-live-server-amd64.iso` from releases.ubuntu.com | `Ubuntu24_LTS_64` | `x86` |

Override anything via env vars. The lab is for exercising tools and workflow; the Ubuntu point release doesn't matter — the real MS-S1 MAX still targets 26.04.

## How the autoinstall works

The Ubuntu install ISO's stock GRUB boots Subiquity in **interactive** mode. To make it run unattended, the kernel needs the `autoinstall` argument.

`01_provision.py` solves this in two steps:

1. **Remasters the install ISO**: extracts `boot/grub/grub.cfg`, patches each `linux /casper/vmlinuz...` line to insert `autoinstall` before the `---` separator, writes a new ISO. Cached at `target/<iso-name>-autoinstall.iso` so it's only built once.
2. **Builds a CIDATA cloud-init ISO**: a small (~400 KB) ISO labelled `CIDATA` containing `user-data` (autoinstall config: hostname, user, sudo, SSH key, install openssh-server) and `meta-data`. Subiquity automatically reads this when `autoinstall` is set.

When the VM boots, GRUB launches the kernel with `autoinstall`, Subiquity finds CIDATA, applies the config, installs Ubuntu, reboots. SSH is up with the lab key authorised.

## Lab keypair

`_ssh.py` auto-generates a dedicated Ed25519 keypair at `target/lab_id_ed25519{,.pub}` on first run. This keeps the lab fully isolated from your real SSH keys (1Password agent, yubikeys, etc.). The keypair is throwaway — destroying the lab destroys both the VM and the key.

Override with `SSH_PUBLIC_KEY=/path/to/your.pub` if you want to authorise a key you already have.

## Configuration

All defaults are env-driven. Common overrides:

| Var | Default | Notes |
|---|---|---|
| `VM_NAME` | `ms-s1-max-lab` | |
| `VM_HOSTNAME` | `ms-s1-max-lab.local` | |
| `VM_USER` | `morten` | |
| `VM_PASSWORD` | `changeme` | Used by Subiquity; later replaced by passwordless sudo |
| `VM_MEMORY_MB` | `8192` | |
| `VM_CPUS` | `4` | |
| `SSH_FORWARD_PORT` | `2222` | host port for the NAT forward |
| `LAB_DISK_COUNT` | `6` | extra disks for ZFS exercises |
| `LAB_DISK_SIZE_MB` | `8000` | size per lab disk |
| `UBUNTU_RELEASE` | `24.04` | |
| `UBUNTU_ISO_FILENAME` | auto-detected | |
| `VM_OSTYPE` | auto-detected | |
| `VBOX_PLATFORM` | auto-detected (`arm` or `x86`) | |

Example: bigger VM, eight lab disks:

```bash
VM_MEMORY_MB=16384 LAB_DISK_COUNT=8 LAB_DISK_SIZE_MB=16000 \
    python3 scripts/lab/all.py
```

## Apple Silicon notes

VirtualBox 7.2 on Apple Silicon is still tech-preview for ARM Linux guests. There are three platform-specific quirks the lab handles for you:

- `--platform-architecture arm` must be set at `createvm` time (can't be changed later).
- `--graphicscontroller qemuramfb` is required; the default `vboxvga` crashes with `VERR_PGM_RAM_CONFLICT`.
- The IDE controller crashes VBox firmware enumeration on ARM (`VERR_NOT_SUPPORTED`). The lab uses SATA only for ARM (lab disks on ports 1-N, install ISO on N+1, CIDATA on N+2).

These are baked into `_vbox.py` and `01_provision.py` — you don't need to think about them.

## Phases in detail

### Phase 01: `01_provision.py`

1. Verify VBoxManage + xorriso are installed.
2. Generate (or reuse) the lab SSH keypair at `target/lab_id_ed25519`.
3. Download Ubuntu ISO + verify SHA256.
4. Remaster the ISO to inject `autoinstall` into GRUB.
5. Render cloud-init `user-data` and `meta-data`, build a CIDATA ISO.
6. Create VM with platform-appropriate flags; attach disks + both ISOs.
7. Boot headless.
8. Wait for an SSH banner from inside the guest (the real handshake, not just NAT-forward TCP).

State recorded in `target/<vm-name>-state.json`.

### Phase 02: `02_apply.py`

1. Generate an Ansible inventory pointing at `127.0.0.1:2222` with the lab user.
2. Push the lab key via `ssh-copy-id` (uses `sshpass` for the first run, then key auth).
3. Run `ansible-playbook` for each named playbook.

Default chain (no arguments): `bootstrap, ssh-hardening, ufw`. Add more:

```bash
python3 scripts/lab/02_apply.py                              # default chain
python3 scripts/lab/02_apply.py zfs                          # just ZFS
python3 scripts/lab/02_apply.py zfs -e topology=mirror       # ZFS in a mirror
python3 scripts/lab/02_apply.py docker services              # docker + services
python3 scripts/lab/02_apply.py bootstrap --check --diff     # dry-run
```

### `all.py` — chain everything

```bash
python3 scripts/lab/all.py
python3 scripts/lab/all.py --stop-after provision
python3 scripts/lab/all.py --playbooks bootstrap,ssh-hardening,ufw,zfs
python3 scripts/lab/all.py --force                           # re-run everything
```

Idempotent: consults `state.json` and skips finished phases unless `--force`.

## Snapshots — your safety net

```bash
# After a fresh successful provision + Ansible run, snapshot
VBoxManage snapshot ms-s1-max-lab take fresh-install --pause

# Between risky experiments
VBoxManage snapshot ms-s1-max-lab take pre-experiment --pause

# Roll back
VBoxManage snapshot ms-s1-max-lab restorecurrent       # last one
VBoxManage snapshot ms-s1-max-lab restore fresh-install # by name
```

## Tear-down

```bash
VBoxManage controlvm ms-s1-max-lab poweroff || true
VBoxManage unregistervm ms-s1-max-lab --delete
rm -f target/ms-s1-max-lab-* target/lab_id_ed25519*
```

The Ubuntu ISO + the autoinstall-remastered ISO stay around in `target/` so the next provision is fast.

## Prerequisites

| Tool | Why | Install |
|---|---|---|
| Python 3.10+ | run the scripts | system Python or `uv` |
| ansible | configure the VM | `brew install ansible` |
| xorriso | remaster ISO + build CIDATA | `brew install xorriso` |
| sshpass | push the SSH key (first run) | `brew install hudochenkov/sshpass/sshpass` |
| VirtualBox 7.2+ | the VM itself | `brew install --cask virtualbox` |

Ansible collections used by the playbooks:

```bash
ansible-galaxy collection install -r scripts/lab/ansible/requirements.yml
```

## When you're ready for the real MS-S1 MAX

The Ansible playbooks here aren't lab-specific — they're the same playbooks you'd run against the real hardware. The only difference is the inventory:

```yaml
# inventory.yml (production)
all:
  children:
    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10       # or its Tailscale name
          ansible_user: morten
          ansible_become: true
```

Then from `scripts/lab/ansible/`:

```bash
ansible-playbook -i inventory.yml playbooks/bootstrap.yml -l production
ansible-playbook -i inventory.yml playbooks/ssh-hardening.yml -l production
ansible-playbook -i inventory.yml playbooks/ufw.yml -l production
ansible-playbook -i inventory.yml playbooks/zfs.yml -l production
ansible-playbook -i inventory.yml playbooks/docker.yml -l production
```

Same playbooks. Different inventory. That's the lab's job: prove the playbooks work before they touch your production box.
