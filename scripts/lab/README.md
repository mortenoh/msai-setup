# MS-S1 MAX VirtualBox/Multipass Lab

A hands-on lab for practising the MS-S1 MAX setup (ZFS, Ansible, Docker) before touching the real hardware.

The full design is documented in `docs/zfs/virtualbox-lab.md` and `docs/ansible/integration.md`. This README is the quick reference for the code in this directory.

## Layout

```
scripts/lab/
  _config.py                 # env-driven LabConfig dataclass
  _vbox.py                   # VBoxManage subprocess wrapper
  _multipass.py              # Multipass subprocess wrapper (Apple Silicon)
  _iso.py                    # Ubuntu ISO download + SHA256 verify
  _ssh.py                    # SSH wait + key push
  _state.py                  # JSON-backed phase state
  01_provision.py            # phase 01 (VirtualBox)
  01_provision_multipass.py  # phase 01 (Multipass — Apple Silicon)
  02_apply.py                # phase 02 (Ansible playbooks)
  all.py                     # full-pipeline orchestrator
  ansible/
    ansible.cfg              # lab-tuned defaults
    requirements.yml         # ansible-galaxy collections
    playbooks/
      bootstrap.yml          # apt baseline + sudoers + journald
      ssh-hardening.yml      # matches docs/ssh/server/hardening.md
      ufw.yml                # default-deny + OpenSSH
      zfs.yml                # install ZFS, create pool, datasets
      docker.yml             # Docker CE + compose plugin
      services.yml           # Traefik + whoami end-to-end smoke
```

## Pick your path

### Apple Silicon Mac (recommended path on this hardware)

```bash
brew install ansible
brew install --cask multipass

python3 scripts/lab/all.py
```

That's it. `all.py` runs:

1. `01_provision_multipass.py` — launches an Ubuntu 24.04 VM via Multipass with cloud-init pre-installing your SSH key, sudo, etc.
2. `02_apply.py` — pushes your SSH key, then runs the full playbook chain.

### x86_64 Mac / Linux / Windows host

```bash
brew install ansible                       # or pipx install ansible
brew install --cask virtualbox             # or your platform's installer
brew install hudochenkov/sshpass/sshpass   # for the first key push

python3 scripts/lab/all.py --provisioner vbox
```

The VirtualBox path creates a VM with 6 dedicated lab disks for the ZFS exercises. The Multipass path uses one disk + loopback files (the ZFS playbook handles both automatically).

## Phases in detail

### Phase 01: provision

Two implementations, same idea:

**VirtualBox** (`01_provision.py`):

- Downloads + verifies SHA256 of `ubuntu-24.04.X-live-server-{amd64,arm64}.iso`
- Creates a VM (`ms-s1-max-lab`) with EFI firmware
- Adds 1 primary disk + N lab disks (default 6, 8 GB each)
- Forwards host `127.0.0.1:2222` → guest `22` over NAT
- Runs unattended install via `VBoxManage unattended install` when supported, falls back to interactive (VRDE) for ISOs the bundled templates don't know about
- Boots headless

**Multipass** (`01_provision_multipass.py`):

- `multipass launch 24.04 --name ms-s1-max-lab ...` with a cloud-init that:
  - Creates the lab user with passwordless sudo
  - Installs your SSH public key
  - Sets hostname, timezone, locale
- Multipass handles the rest (ISO management, network, etc.)

Both end with a fully-booted Ubuntu VM reachable on the network. State is recorded in `target/<vm-name>-state.json`.

### Phase 02: apply

`02_apply.py` is the Python orchestrator that runs Ansible:

1. Generates `ansible/inventory.generated.yml` from the lab config (and reads the VM's IP from state if Multipass was used)
2. Pushes the user's SSH public key with `ssh-copy-id` (requires `sshpass`)
3. Runs `ansible-playbook` for each named playbook

Default chain (no arguments): `bootstrap, ssh-hardening, ufw`. Add more on the command line:

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
python3 scripts/lab/all.py --provisioner multipass
python3 scripts/lab/all.py --stop-after provision
python3 scripts/lab/all.py --playbooks bootstrap,ssh-hardening,ufw,zfs   # custom set
python3 scripts/lab/all.py --force                                       # re-run everything
```

`all.py` is idempotent: it consults `state.json` and skips phases already marked complete.

## Configuration via env vars

`_config.py` reads from these env vars:

| Var | Default | Notes |
|---|---|---|
| `VM_NAME` | `ms-s1-max-lab` | |
| `VM_HOSTNAME` | `ms-s1-max-lab.local` | |
| `VM_USER` | `morten` | |
| `VM_PASSWORD` | `changeme` | OVERRIDE in production |
| `VM_FULLNAME` | `Morten Hansen` | |
| `VM_MEMORY_MB` | `8192` | 8 GiB |
| `VM_CPUS` | `4` | |
| `VM_OSTYPE` | auto-detected | `Ubuntu24_LTS_64` or `Ubuntu24_LTS_arm64` |
| `SSH_FORWARD_PORT` | `2222` | host port for the VBox NAT forward |
| `TARGET_DIR` | `target/` | where disks + ISO + state live |
| `PRIMARY_DISK_SIZE_MB` | `80000` | primary disk size |
| `LAB_DISK_COUNT` | `6` | extra disks for ZFS exercises (VBox path) |
| `LAB_DISK_SIZE_MB` | `8000` | size per lab disk |
| `UBUNTU_RELEASE` | `24.04` | |
| `UBUNTU_ISO_FILENAME` | auto-detected | depends on host arch |
| `UBUNTU_ISO_BASE_URL` | auto-detected | depends on host arch |
| `SSH_PUBLIC_KEY` | `~/.ssh/id_ed25519.pub` | the key Ansible pushes |

Example: bump RAM, use more lab disks:

```bash
VM_MEMORY_MB=16384 LAB_DISK_COUNT=8 LAB_DISK_SIZE_MB=16000 \
    python3 scripts/lab/all.py
```

## Snapshots — your safety net

Take a snapshot after the fresh install completes:

```bash
# Multipass
multipass stop ms-s1-max-lab
multipass snapshot ms-s1-max-lab --name fresh-install
multipass start ms-s1-max-lab

# VirtualBox
VBoxManage snapshot ms-s1-max-lab take fresh-install --pause
```

Then between lab exercises, restore to that clean state:

```bash
# Multipass
multipass restore --destructive ms-s1-max-lab.fresh-install

# VirtualBox
VBoxManage snapshot ms-s1-max-lab restorecurrent
# or by name:
VBoxManage snapshot ms-s1-max-lab restore fresh-install
```

## Tear-down

```bash
# Multipass
multipass delete ms-s1-max-lab && multipass purge

# VirtualBox
VBoxManage controlvm ms-s1-max-lab poweroff || true
VBoxManage unregistervm ms-s1-max-lab --delete

# Clean state for both
rm -f target/ms-s1-max-lab-*
```

## Prerequisites

| Tool | Why | Install |
|---|---|---|
| Python 3.10+ | run the scripts | system Python or `uv` |
| ansible | configure the VM | `brew install ansible` |
| sshpass | push the SSH key (first run) | `brew install hudochenkov/sshpass/sshpass` (macOS) |
| nc (`netcat`) | wait for SSH (VBox path) | bundled on macOS/Linux |
| VirtualBox 7.x **or** Multipass | the VM itself | `brew install --cask virtualbox` or `brew install --cask multipass` |

Ansible collections used by the playbooks:

```bash
ansible-galaxy collection install -r scripts/lab/ansible/requirements.yml
```

## Common operations

### Idempotency check

Run the same play twice. The second run should report `changed=0`:

```bash
python3 scripts/lab/02_apply.py zfs
python3 scripts/lab/02_apply.py zfs    # should be all 'ok', no 'changed'
```

If the second run reports changes, find the non-idempotent task and add `creates:`, `removes:`, or `changed_when:`.

### Dry-run

```bash
python3 scripts/lab/02_apply.py zfs --check --diff
```

The `--check --diff` args are forwarded to `ansible-playbook`.

### Profile timings

```bash
ANSIBLE_CALLBACKS_ENABLED=profile_tasks python3 scripts/lab/02_apply.py
```

Shows time per task; useful for finding slow steps.

## Limitations / known issues

- **VirtualBox 7.2 on Apple Silicon** has tech-preview-quality ARM Linux guest support. Firmware enumeration is buggy with current Ubuntu ARM images. Use the Multipass path on Apple Silicon Macs.
- **Multipass** uses a single primary disk; the ZFS playbook creates loopback files inside the VM for the multi-disk exercises. Behaviour is functionally identical; performance is slower (single physical disk, loopback overhead).
- **Unattended Ubuntu install** via VBoxManage only works for releases its bundled templates know (currently up to 25.04 in VBox 7.2.x). Newer ISOs fall back to interactive install; the script handles that path automatically.

## When you're ready for the real MS-S1 MAX

The Ansible playbooks here aren't lab-specific — they're the same playbooks you'd run against the real hardware. The only difference is the inventory:

```yaml
# inventory.yml (production)
all:
  children:
    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10        # or its Tailscale name
          ansible_user: morten
          ansible_become: true
```

Then:

```bash
cd scripts/lab/ansible
ansible-playbook -i inventory.yml playbooks/bootstrap.yml -l production
ansible-playbook -i inventory.yml playbooks/ssh-hardening.yml -l production
ansible-playbook -i inventory.yml playbooks/ufw.yml -l production
ansible-playbook -i inventory.yml playbooks/zfs.yml -l production
ansible-playbook -i inventory.yml playbooks/docker.yml -l production
# services.yml as-is is the lab smoke test — for production, write your real
# compose stacks under scripts/lab/ansible/playbooks/ and run them.
```

Same playbooks. Different inventory. That's the lab's job: validate that the playbooks work before they touch your production box.
