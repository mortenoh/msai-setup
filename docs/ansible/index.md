# Ansible

Ansible is the configuration-management half of this build's automation. **Python + VBoxManage** brings VMs into existence; **Ansible** configures what runs inside them — SSH hardening, UFW, ZFS, Docker, services.

The same playbooks that configure the VirtualBox lab VM are designed to be run, with minimal changes, against the real MS-S1 MAX after Ubuntu 26.04 is installed.

!!! tip "Start with the hands-on walkthrough"
    These pages are the reference manual. The concrete, working, do-this-see-this walkthrough of the real automation lives at [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md). It drives the exact same tooling described here — the `msai` CLI, the six playbooks — against a throwaway VM. Read it alongside this section.

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
| [Integration](integration.md) | How Ansible fits with the lab automation in `src/msai_setup/lab/` and the production server |
| [Troubleshooting](troubleshooting.md) | Common errors and how to debug them with `-vvv` |

## How this section pairs with `src/msai_setup/lab/`

The repository has working playbooks under `src/msai_setup/lab/ansible/playbooks/`, driven by the `msai` CLI. These docs are the **reference manual**; the playbooks are the **worked examples**. The [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) walkthrough runs them end to end. Read them side-by-side:

| Lab playbook | Demonstrates |
|---|---|
| `bootstrap.yml` | `apt`, loops, `copy` with content, `community.general.timezone`, handlers, the passwordless-sudo sudoers drop-in |
| `ssh-hardening.yml` | template-style config via `copy` with a Jinja2 body, `command` for validation |
| `ufw.yml` | `community.general.ufw` module, loops, idempotent state |
| `zfs.yml` | shell-script-style fact gathering, `set_fact`, `assert`, complex `command` invocations, `community.general.zfs` |
| `docker.yml` | `apt` repo setup, GPG keyring, codename fallback logic, `user` group membership, `daemon.json`, a smoke-test `command` |
| `services.yml` | `community.docker.docker_network` + `docker_compose_v2`, deploying a Traefik + whoami stack as a bind-mount-into-ZFS smoke test |

The full lab path:

```bash
# 1. create the VM (downloads ISO, creates VM, waits for SSH)
msai create test

# 2. configure it with Ansible
msai lab apply                       # default chain: bootstrap, ssh-hardening, ufw
msai lab apply zfs                   # just the ZFS playbook
msai lab apply zfs -e topology=mirror
msai lab apply docker services       # Docker + the Compose smoke-test stack
```

See [Integration](integration.md) for the full design.

## A few opinions baked into this section

- **Use `ansible-playbook` over `ansible` for everything.** The ad-hoc `ansible` command is fine for "ping all hosts" but isn't where real work lives. Every example here is a playbook.
- **Prefer modules over `command`/`shell`.** A module knows when it's changed something; `command` doesn't. Use `shell` only when no module fits and document `changed_when`.
- **Roles are valuable but not always necessary.** For a homelab with ~10 playbooks, flat playbooks are simpler. Promote to roles when you have repeating patterns across many hosts/projects.
- **Keep secrets out of playbooks.** The shipped playbooks need none: sudo is passwordless (bootstrap.yml writes a NOPASSWD sudoers drop-in) and SSH is key-only, so nothing is vaulted today. If you add secrets later, reach for `ansible-vault` — see [Vault](vault.md).

## Where to start reading

If you're new to Ansible:

1. [Installation](installation.md) — install it locally
2. [Concepts](concepts.md) — terminology and the loop
3. [Playbooks](playbooks.md) — read this carefully; it's the load-bearing page
4. [Inventory](inventory.md), [Variables](variables.md), [Modules](modules.md) — fill in the gaps
5. [Integration](integration.md) — see how it ties to this specific build

If you already know Ansible and just want this build's specifics, jump straight to [Integration](integration.md).
