# Integration with this build

How Ansible fits with the VirtualBox/Multipass lab in `scripts/lab/` and how the same playbooks will run against the real MS-S1 MAX once it's provisioned.

## Two halves of automation

```
+--------------------------------------------+
|  Python + VBoxManage / Multipass           |
|  Provisions: VM exists, has disks, has SSH |
+--------------------------------------------+
              |
              | SSH (with cloud-init pubkey)
              v
+--------------------------------------------+
|  Ansible playbooks                          |
|  Configures: packages, ssh, ufw, zfs,       |
|  docker, services                           |
+--------------------------------------------+
```

The split is deliberate:

- **Python's strengths**: ISO download, VM lifecycle, snapshotting, structured state. Things you'd reach for `bash` for, but Python is cleaner.
- **Ansible's strengths**: idempotent in-host configuration. Whether you ran the play once or a hundred times, the host ends in the same state.

The boundary is "the host accepts SSH". Below that line: Python. Above: Ansible.

## The lab path, end to end

```bash
# 0. once: install prerequisites on the control node (your Mac)
brew install ansible                              # or pipx install ansible
brew install --cask multipass                     # for Apple Silicon
# OR for x86_64:
# brew install --cask virtualbox

# 1. provision the lab VM
# Apple Silicon: use Multipass
python3 scripts/lab/01_provision_multipass.py
# x86_64: use VirtualBox
python3 scripts/lab/01_provision.py

# 2. apply playbooks (default chain: bootstrap, ssh-hardening, ufw)
python3 scripts/lab/02_apply.py

# 3. apply individual playbooks for the ZFS / Docker exercises
python3 scripts/lab/02_apply.py zfs
python3 scripts/lab/02_apply.py zfs -e topology=mirror

# 4. snapshot before risky changes
multipass snapshot ms-s1-max-lab --name pre-zfs-experiment
# or for VirtualBox:
# VBoxManage snapshot ms-s1-max-lab take pre-zfs-experiment --pause

# 5. tear down when done
multipass delete --purge ms-s1-max-lab
# or:
# VBoxManage unregistervm ms-s1-max-lab --delete
```

## What lives where

```
scripts/lab/
  _config.py             # LabConfig dataclass (env-driven defaults)
  _vbox.py               # VBoxManage subprocess wrapper
  _multipass.py          # Multipass subprocess wrapper
  _iso.py                # Ubuntu ISO download + SHA256 verify
  _ssh.py                # SSH wait + key push helpers
  _state.py              # JSON state for "this phase already ran"
  01_provision.py        # VirtualBox provisioner
  01_provision_multipass.py    # Multipass provisioner
  02_apply.py            # Run ansible-playbook against the VM
  ansible/
    ansible.cfg          # lab-tuned defaults
    requirements.yml     # ansible-galaxy collections
    playbooks/
      bootstrap.yml      # apt baseline, timezone, sudoers, journald
      ssh-hardening.yml  # matches docs/ssh/server/hardening.md
      ufw.yml            # default-deny + OpenSSH
      zfs.yml            # install ZFS, ARC cap, pool + datasets
      docker.yml         # (planned)
      services.yml       # (planned)
```

State is JSON in `target/<vm-name>-state.json`. Each phase marks itself complete; re-running is safe.

## How Multipass vs VirtualBox differ in this design

| Concern | VirtualBox | Multipass |
|---|---|---|
| Where it runs well | x86_64 Macs, Linux, Windows | Apple Silicon Macs, x86_64 Macs, Linux |
| Provisioning | `01_provision.py` (full unattended via VBoxManage) | `01_provision_multipass.py` (uses cloud-init) |
| Multiple lab disks | 6 separate virtual disks | 1 disk; ZFS playbook makes loopback files |
| SSH endpoint | host:2222 via NAT port-forward | VM's IP on the LAN-like Multipass network |
| Snapshots | `VBoxManage snapshot take` | `multipass snapshot` |
| Headless | yes (`--type headless`) | yes (default) |

The Ansible side is **identical** — `02_apply.py` reads `_state.json` to figure out which endpoint to put in the inventory, and the playbooks themselves don't care which provisioner ran first. `zfs.yml` does adapt (loopback files instead of `/dev/sd*`) when no real lab disks are present.

## How this maps to the real MS-S1 MAX

After installing Ubuntu Server 26.04 on the actual MS-S1 MAX (manually, since that's how the bare-metal install works):

```yaml
# scripts/lab/ansible/inventory.yml (or move out of lab/ for production)
all:
  children:
    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10        # or its Tailscale name
          ansible_user: morten
          ansible_become: true
          # no password — passwordless sudo configured by bootstrap.yml
```

Then:

```bash
# Push your SSH key (one-time)
ssh-copy-id morten@ms-s1-max

# Apply the same playbooks the lab uses
cd scripts/lab/ansible
ansible-playbook -i inventory.yml playbooks/bootstrap.yml -l production
ansible-playbook -i inventory.yml playbooks/ssh-hardening.yml -l production
ansible-playbook -i inventory.yml playbooks/ufw.yml -l production
ansible-playbook -i inventory.yml playbooks/zfs.yml -l production \
    -e topology=stripe         # production layout: single stripe over 2 disks

# Then Docker, services...
```

Same playbooks. Different inventory. Different host. That's the point.

## Where the playbooks intentionally don't cover

This is what `scripts/lab/ansible/playbooks/` deliberately does NOT do:

- **Bare-metal Ubuntu install.** That's a one-time manual step on the real hardware (you boot from a USB, click through Subiquity). The lab automation simulates it but doesn't replace it.
- **GPU / ROCm install.** Strix-Halo-specific kernel/firmware shenanigans don't fit Ansible's model cleanly. See `docs/ai/gpu/rocm-installation.md` for the manual procedure (which can be wrapped in Ansible later if you want).
- **Filesystem-level disaster recovery.** When the pool fails, Ansible can't help. See `docs/zfs/troubleshooting.md`.

The boundaries are deliberate. Ansible does what it's good at; other tools do the rest.

## Secrets handling end-to-end

In the lab the password is `changeme` from `_config.py`. For production:

```bash
# 1. Set a real password and store in 1Password (not in plaintext anywhere)
op item create --category=password --title='ms-s1-max sudo' password='real-secret'

# 2. Vault file references it (committed to git, encrypted)
ansible-vault create scripts/lab/ansible/group_vars/production/vault.yml
# Contents:
#   vault_become_password: "{{ lookup('community.general.onepassword', 'ms-s1-max sudo') }}"

# 3. main.yml in group_vars/production/ pulls the value
# scripts/lab/ansible/group_vars/production/main.yml:
#   ansible_become_password: "{{ vault_become_password }}"

# 4. Ansible vault password itself comes from 1Password too
echo '#!/bin/bash
op read "op://Private/ansible-vault/password"' > ~/.bin/ansible-vault-pass
chmod +x ~/.bin/ansible-vault-pass

# 5. Ansible looks it all up at runtime — no plaintext on disk
ansible-playbook -i inventory.yml playbook.yml \
    --vault-password-file ~/.bin/ansible-vault-pass
```

See [Vault](vault.md) for the full pattern.

## Why not Terraform?

Terraform's strength is "I describe cloud resources; here's their state". For a single mini-PC running Ubuntu, Terraform's state-file overhead doesn't pay back. Provisioning a VM with Python + VBoxManage or Multipass is simpler and direct. If you ever scale to "10 boxes in AWS plus the homelab", Terraform makes sense for the cloud half — at that point pair it with Ansible as I'm doing here.

## Why not Salt / Chef / Puppet?

Ansible's agentless SSH model is a much better fit for a homelab than any of those. Salt-master, Chef-server, etc. are designed for larger fleets and assume an agent on every node, which is overkill for a few hosts.

## A few more useful commands

```bash
# Run a playbook against ALL hosts (lab + production)
ansible-playbook -i inventory.yml playbook.yml

# Limit to specific hosts
ansible-playbook -i inventory.yml playbook.yml -l production
ansible-playbook -i inventory.yml playbook.yml -l 'lab:!ms-s1-max-lab-old'

# Tag-based partial runs
ansible-playbook -i inventory.yml playbook.yml --tags ssh
ansible-playbook -i inventory.yml playbook.yml --skip-tags slow

# See what would change
ansible-playbook -i inventory.yml playbook.yml --check --diff

# Time how long each task takes
ANSIBLE_CALLBACKS_ENABLED=profile_tasks ansible-playbook -i inventory.yml playbook.yml
```

## Where to go next

- [Connection](connection.md) — SSH and become specifics.
- [Vault](vault.md) — full secrets workflow.
- [Troubleshooting](troubleshooting.md) — when something doesn't work.
- The actual code: `scripts/lab/` in the repo.
