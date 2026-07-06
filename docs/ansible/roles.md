# Roles

A role is a packaged bundle of tasks + handlers + templates + files + defaults + metadata, designed to be reused. Roles are how you scale Ansible from "a few playbooks" to "a maintainable codebase".

## When (not) to use roles

Roles solve **repetition**. If you have a snippet that you'd otherwise copy-paste across three playbooks, that snippet is a role candidate.

For a homelab with ~10 playbooks, flat playbooks under `playbooks/` are simpler and easier to follow than a directory of roles. **Don't reach for roles until repetition appears.** Premature abstraction makes Ansible code hard to read.

That said, **published roles from Galaxy** (e.g. `devsec.hardening.os_hardening`) are usually worth using as-is — you don't pay the maintenance cost.

## Role directory structure

```
roles/
  my-role/
    defaults/main.yml           # lowest-priority variables
    vars/main.yml               # high-priority variables (rarely used)
    tasks/main.yml              # the tasks
    handlers/main.yml           # handlers
    templates/                  # Jinja2 templates
    files/                      # static files
    meta/main.yml               # metadata + dependencies
    README.md                   # what this role does
```

Only `tasks/main.yml` is required. The rest are optional; Ansible auto-loads them by convention if present.

## Including a role from a playbook

```yaml
- hosts: lab
  roles:
    - common
    - { role: nginx, nginx_port: 8080 }       # with parameters
    - role: postgres
      vars:
        pg_max_connections: 200
```

Or use `import_role:` / `include_role:` inside `tasks:` (dynamic vs static):

```yaml
- hosts: lab
  tasks:
    - name: maybe configure databases
      ansible.builtin.include_role:
        name: postgres
      when: deploy_database
```

The two forms differ:

| Form | When evaluated | Loops/conditionals on the role |
|---|---|---|
| `import_role:` | parse time (static) | apply per-task inside the role |
| `include_role:` | runtime (dynamic) | apply to the whole role |

`include_role:` is what you want when "should I run this role" depends on runtime values. `import_role:` is slightly more efficient when conditions are known at parse time.

## A minimal role

```yaml
# roles/zfs-pool/defaults/main.yml
pool_name: tank
ashift: 12
compression: lz4
```

```yaml
# roles/zfs-pool/tasks/main.yml
- name: install zfsutils-linux
  ansible.builtin.apt:
    name: zfsutils-linux
    state: present

- name: ensure pool exists
  ansible.builtin.command: >
    zpool create -o ashift={{ ashift }}
                 -O compression={{ compression }}
                 {{ pool_name }} {{ devices | join(' ') }}
  args:
    creates: "/dev/zd0"          # crude — assumes a zvol shows up; better: check zpool list
```

```yaml
# Use it from a play:
- hosts: lab
  roles:
    - role: zfs-pool
      vars:
        pool_name: tank
        devices:
          - /dev/disk/by-id/disk1
          - /dev/disk/by-id/disk2
```

## Collections — installing community roles

Collections are bundles of roles, modules, and plugins. Install with `ansible-galaxy`:

```bash
ansible-galaxy collection install community.general
ansible-galaxy collection install devsec.hardening
ansible-galaxy collection install -r requirements.yml
```

```yaml
# requirements.yml
collections:
  - name: community.general
  - name: ansible.posix
  - name: community.docker      # used by services.yml
  - name: devsec.hardening
```

Pin versions for reproducibility:

```yaml
collections:
  - name: community.general
    version: ">=8.0.0,<9.0.0"
```

Galaxy collections live in `~/.ansible/collections/` by default; pin them to the project tree for reproducibility:

```bash
ansible-galaxy collection install -r requirements.yml -p ./collections
```

…and point `ansible.cfg` at that location.

## Using `devsec.hardening` (worth knowing about)

The dev-sec project maintains a vetted collection of CIS-style hardening playbooks. For a real production system, this is the path of least friction:

```yaml
- hosts: lab
  become: true
  roles:
    - devsec.hardening.os_hardening
    - devsec.hardening.ssh_hardening
```

These apply hundreds of CIS controls. Read what they do before applying — some are aggressive (disable IPv6, set strict umasks). Cherry-pick by setting `os_hardening_modify_*` variables.

For this build's lab, the playbooks under `src/msai_setup/lab/ansible/playbooks/` (`ssh-hardening.yml` and `ufw.yml`) re-implement the subset we want, so the hardening pass is auditable in this repo. For the production server, layering `devsec.hardening.*` on top is a fine choice.

## Role dependencies

A role can declare prerequisite roles in `meta/main.yml`:

```yaml
# roles/nginx/meta/main.yml
dependencies:
  - role: common
  - role: ufw
```

Dependencies run before the role itself, in order. Useful but creates implicit coupling — prefer explicit ordering in the playbook unless the dependency is truly required.

## Sharing roles via Galaxy

If you've written a role that's worth sharing:

```bash
ansible-galaxy role init my_role
# edit, test
git init
ansible-galaxy role import <your-github-username> <repo-name>
```

Then others can `ansible-galaxy role install <your>.<role>`.

## When this build might grow roles

Today the lab uses flat playbooks. Likely role candidates as it grows:

- **`common`** — apt baseline, timezone, sudoers, journald (currently `bootstrap.yml`)
- **`ssh-hardening`** — already a self-contained playbook; trivial to convert
- **`ufw`** — same
- **`zfs-pool`** — generic enough to be a role with parameters
- **`docker-host`** — Docker install + daemon.json + ufw-docker
- **`compose-service`** — given a compose dir, bring up the service (parameterised name + path)

Conversion is purely structural — the tasks themselves don't change. So feel free to start flat, refactor to roles when copy-paste appears.

## Where to go next

- [Modules](modules.md) — what tasks inside a role typically invoke.
- [Variables](variables.md) — `defaults/` vs `vars/` vs play vars.
- [Vault](vault.md) — encrypting role-level secrets (generic; not used by the shipped playbooks).
- The hands-on walkthrough: [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) — the flat playbooks this section might one day promote to roles.
