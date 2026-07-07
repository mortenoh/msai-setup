# Integration with this build

How Ansible fits with the VirtualBox lab in `src/msai_setup/lab/` and how the same playbooks run against the real MS-S1 MAX once it's provisioned.

!!! tip "See also — the hands-on walkthrough"
    [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) is the concrete, working, do-this-see-this walkthrough of everything on this page: `msai lab create`, `msai lab apply`, snapshots, and the "From lab to real MS-S1 MAX" handoff. This page explains the design; the README shows it running.

!!! note "VirtualBox only"
    VirtualBox is the only supported provisioner in this repo. There is no Multipass support anywhere in the codebase — earlier drafts mentioned it, but it was never implemented.

## Two halves of automation

```
+--------------------------------------------+
|  Python + VBoxManage (the `msai` CLI)      |
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
brew install --cask virtualbox                    # the only supported provisioner
uv sync                                            # installs the `msai` CLI
ansible-galaxy collection install -r src/msai_setup/lab/ansible/requirements.yml

# 1. create the lab VM (downloads ISO, creates VM, waits for SSH)
msai lab create test

# 2. apply playbooks (default chain: bootstrap, ssh-hardening, ufw)
msai lab apply

# 3. apply individual playbooks for the ZFS / Docker exercises
msai lab apply zfs
msai lab apply zfs -e topology=mirror
msai lab apply docker services

# 4. snapshot before risky changes
msai lab snapshot pre-zfs-experiment

# 5. roll back to a snapshot / tear down when done
msai lab restore pre-zfs-experiment
msai lab destroy
```

## What lives where

The real automation is a Python package under `src/msai_setup/lab/`, exposed through the `msai` CLI (Typer). There is no `scripts/lab/` directory.

```
src/msai_setup/lab/
  __init__.py
  cli.py                 # `msai lab ...` Typer commands (apply, snapshot, restore, destroy, status)
  config.py              # LabConfig dataclass (env-driven defaults)
  vbox.py                # VBoxManage subprocess wrapper
  iso.py                 # Ubuntu ISO download + SHA256 verify + autoinstall remaster
  cloudinit.py           # builds the CIDATA cloud-init ISO
  ssh.py                 # SSH wait + key push helpers
  instance.py            # current-instance pointer (msai lab create / use / list)
  provision.py           # provision phase: create the VM, wait for SSH
  apply.py               # writes the generated inventory, runs ansible-playbook
  pipeline.py            # chains provision -> apply (`msai lab all`)
  state.py               # JSON state for "this phase already ran"
  README.md              # the hands-on walkthrough
  ansible/
    ansible.cfg          # lab-tuned defaults
    requirements.yml     # ansible-galaxy collections
    playbooks/
      bootstrap.yml      # apt baseline, timezone, passwordless sudoers, journald
      ssh-hardening.yml  # matches docs/ssh/server/hardening.md
      ufw.yml            # default-deny + OpenSSH
      zfs.yml            # install ZFS, ARC cap, pool + datasets
      docker.yml         # Docker CE + Compose plugin, daemon.json, smoke test
      services.yml       # Traefik + whoami Compose smoke stack (community.docker)
```

All six playbooks are real and shipped — `docker.yml` and `services.yml` included. State is JSON in `target/<vm-name>-state.json`. Each phase marks itself complete; re-running is safe.

## How this maps to the real MS-S1 MAX

After installing Ubuntu Server 26.04 on the actual MS-S1 MAX (manually, since that's how the bare-metal install works), point Ansible at it with a small production inventory:

```yaml
# ~/msai-prod-inventory.yml
all:
  children:
    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10             # or ms-s1-max.<tailnet>.ts.net
          ansible_user: morten
          ansible_become: true
          ansible_ssh_private_key_file: ~/.ssh/id_ed25519
          # no become password — passwordless sudo is configured by bootstrap.yml
```

Then:

```bash
# Push your SSH key (one-time)
ssh-copy-id morten@ms-s1-max

# Apply the same playbooks the lab uses
cd src/msai_setup/lab/ansible
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/bootstrap.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/ssh-hardening.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/ufw.yml -l production
ansible-playbook -i ~/msai-prod-inventory.yml playbooks/zfs.yml -l production \
    -e topology=stripe         # production layout: single stripe over 2 disks

# Then Docker, services...
```

Same playbooks. Different inventory. Different host. That's the point. This mirrors the "From lab to real MS-S1 MAX" section of `src/msai_setup/lab/README.md`.

## Where the playbooks intentionally don't cover

This is what `src/msai_setup/lab/ansible/playbooks/` deliberately does NOT do:

- **Bare-metal Ubuntu install.** That's a one-time manual step on the real hardware (you boot from a USB, click through Subiquity). The lab automation simulates it but doesn't replace it.
- **GPU / ROCm install.** Strix-Halo-specific kernel/firmware shenanigans don't fit Ansible's model cleanly. See `docs/ai/gpu/rocm-installation.md` for the manual procedure (which can be wrapped in Ansible later if you want).
- **Filesystem-level disaster recovery.** When the pool fails, Ansible can't help. See `docs/zfs/troubleshooting.md`.

The boundaries are deliberate. Ansible does what it's good at; other tools do the rest.

## Secrets handling end-to-end

The shipped playbooks **need no secrets at all**, so there is nothing to vault today:

- **Sudo is passwordless.** `bootstrap.yml` writes a NOPASSWD sudoers drop-in (`/etc/sudoers.d/90-<user>`), so `become` works with no `ansible_become_password`. The generated inventory `apply.py` writes contains no password field.
- **SSH is key-only.** The lab authorises a dedicated throwaway keypair via cloud-init; production authorises whatever key you `ssh-copy-id`. Either way it's an `ansible_ssh_private_key_file`, not a password.

So there is no `ansible-vault`, no `group_vars/vault.yml`, and no 1Password lookup wired into the real playbooks. In the lab the install-time password defaults to `changeme` in `config.py`, but it's only used during the unattended install — Ansible never touches it.

If you later add a playbook that genuinely needs a secret (an API token, a TLS key, a service password), `ansible-vault` is the right tool and remains available. See [Vault](vault.md) for that generic pattern — just note it is not something the current build uses.

## Why not Terraform?

Terraform's strength is "I describe cloud resources; here's their state". For a single mini-PC running Ubuntu, Terraform's state-file overhead doesn't pay back. Provisioning a VM with Python + VBoxManage (the `msai` CLI) is simpler and direct. If you ever scale to "10 boxes in AWS plus the homelab", Terraform makes sense for the cloud half — at that point pair it with Ansible as I'm doing here.

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
- [Vault](vault.md) — generic secrets workflow (not used by the shipped playbooks).
- [Troubleshooting](troubleshooting.md) — when something doesn't work.
- The hands-on walkthrough: [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md).
- The actual code: `src/msai_setup/lab/` in the repo.
