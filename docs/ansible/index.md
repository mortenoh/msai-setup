# Ansible

Ansible is the configuration-management half of this build's automation. **Python + VBoxManage** brings VMs into existence; **Ansible** configures what runs inside them — SSH hardening, UFW, ZFS, Docker, services.

The same playbooks that configure the VirtualBox lab VM are designed to be run, with minimal changes, against the real MS-S1 MAX after Ubuntu 26.04 is installed.

## Why Ansible for this build

- **Agentless.** SSH-only management is the only management plane on this server anyway. Ansible needs nothing on the target except OpenSSH and Python 3 (preinstalled).
- **Idempotent by design.** Every module is built around "make the system match this declared state". Re-running a playbook is safe.
- **Auditable.** Every change goes through a playbook in git. Drift detection is one `ansible-playbook --check --diff` away.
- **YAML, not bash.** Encodes intent declaratively; the tooling handles "if not already set, do X".
- **Mature ecosystem.** Existing collections (e.g. `devsec.hardening`) for CIS-style hardening if you want it, plus tens of thousands of modules for everything from `apt` to ZFS.

## What this section covers

| Page | Topic |
|---|---|
| [Concepts](concepts.md) | inventory, plays, tasks, roles, handlers, facts, idempotency — the mental model |
| [Installation](installation.md) | Installing Ansible on a Mac/Linux control node; the target needs no agent |
| [Inventory](inventory.md) | INI vs YAML formats, groups, host_vars/group_vars, dynamic inventories |
| [Playbooks](playbooks.md) | Anatomy: plays, tasks, loops, conditionals, blocks, error handling |
| [Modules](modules.md) | The modules used in this build: `apt`, `copy`, `template`, `systemd`, `ufw`, `community.general.zfs`, etc. |
| [Variables](variables.md) | Variable precedence, `--extra-vars`, `register`, facts, magic variables |
| [Templates](templates.md) | Jinja2 syntax, filters, lookups, loops in templates |
| [Roles](roles.md) | Role structure, dependencies, Galaxy collections |
| [Vault](vault.md) | `ansible-vault` for secrets, integration with 1Password / sops |
| [Handlers](handlers.md) | Notify/listen, restart-service patterns, ordering guarantees |
| [Connection](connection.md) | SSH transport, become/sudo, control-persist, jump-hosts |
| [Testing](testing.md) | `--check`, `--diff`, ansible-lint, molecule, syntax checks |
| [Integration](integration.md) | How Ansible fits with the lab automation in `scripts/lab/` and the production server |
| [Troubleshooting](troubleshooting.md) | Common errors and how to debug them with `-vvv` |

## How this section pairs with `scripts/lab/`

The lab repository has working playbooks under `scripts/lab/ansible/playbooks/`. These docs are the **reference manual**; the playbooks are the **worked examples**. Read them side-by-side:

| Lab playbook | Demonstrates |
|---|---|
| `bootstrap.yml` | `apt`, loops, `copy` with content, `community.general.timezone`, handlers |
| `ssh-hardening.yml` | template-style config via `copy` with a Jinja2 body, `command` for validation |
| `ufw.yml` | `community.general.ufw` module, loops, idempotent state |
| `zfs.yml` | shell-script-style fact gathering, `set_fact`, `assert`, complex `command` invocations, `community.general.zfs` |

The full lab path:

```bash
# 1. provision the VM (downloads ISO, creates VM, kicks off install)
python3 scripts/lab/01_provision.py

# 2. configure it with Ansible
python3 scripts/lab/02_apply.py                  # default chain: bootstrap, ssh-hardening, ufw
python3 scripts/lab/02_apply.py zfs              # just the ZFS playbook
python3 scripts/lab/02_apply.py zfs -e topology=mirror
```

See [Integration](integration.md) for the full design.

## A few opinions baked into this section

- **Use `ansible-playbook` over `ansible` for everything.** The ad-hoc `ansible` command is fine for "ping all hosts" but isn't where real work lives. Every example here is a playbook.
- **Prefer modules over `command`/`shell`.** A module knows when it's changed something; `command` doesn't. Use `shell` only when no module fits and document `changed_when`.
- **Roles are valuable but not always necessary.** For a homelab with ~10 playbooks, flat playbooks are simpler. Promote to roles when you have repeating patterns across many hosts/projects.
- **Keep secrets in vault from day one.** Even on a lab. Habits stick.

## Where to start reading

If you're new to Ansible:

1. [Installation](installation.md) — install it locally
2. [Concepts](concepts.md) — terminology and the loop
3. [Playbooks](playbooks.md) — read this carefully; it's the load-bearing page
4. [Inventory](inventory.md), [Variables](variables.md), [Modules](modules.md) — fill in the gaps
5. [Integration](integration.md) — see how it ties to this specific build

If you already know Ansible and just want this build's specifics, jump straight to [Integration](integration.md).
