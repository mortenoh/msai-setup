# Variables

Variables in Ansible are values that get substituted into tasks at runtime. They come from many places, and the order in which Ansible resolves conflicts (precedence) is **important and famously confusing**. This page is the practical reference for where variables live and which wins.

## How variables are referenced

Anywhere a value goes, you can use a Jinja2 expression:

```yaml
- name: install
  ansible.builtin.apt:
    name: "{{ package_name }}"
    state: present
```

Inside Ansible, `{{ }}` is the Jinja2 substitution. Standalone strings consisting only of a substitution need quoting because YAML otherwise tries to parse `{{ ... }}` as a flow-style mapping.

Filters chain on with `|`:

```yaml
- name: lowercase the hostname
  ansible.builtin.debug:
    msg: "{{ inventory_hostname | lower }}"

- name: default value if undefined
  ansible.builtin.debug:
    msg: "{{ greeting | default('hello') }}"

- name: complex
  ansible.builtin.debug:
    msg: "{{ datasets | selectattr('compression', 'eq', 'lz4') | map(attribute='name') | list }}"
```

## Where variables come from

In rough order of frequency:

1. **`defaults/main.yml`** inside a role — lowest priority; supplies sensible fallback values
2. **`group_vars/<group>.yml`** — applies to every host in the group
3. **`host_vars/<host>.yml`** — applies only to one host
4. **Inventory inline `vars:`** — set on a group or host in inventory.yml
5. **Play `vars:`** — set inside the playbook
6. **`vars_files:`** — load from another file at play time
7. **`vars_prompt:`** — ask the operator interactively at play start
8. **`register:`** — runtime, from task output
9. **`set_fact:`** — runtime, computed
10. **Facts** — discovered by the `setup` module (`ansible_*` family)
11. **`--extra-vars` / `-e`** — command line; highest normal priority

Plus role params (vars passed to a role at include time), block-scoped `vars:`, and a handful of others.

## Variable precedence (simplified)

When the same name comes from multiple sources, this is **roughly** how Ansible resolves it (lowest to highest):

```
1.  role defaults (defaults/main.yml)
2.  inventory file vars (group_vars, host_vars)
3.  inventory vars: blocks (inline)
4.  playbook vars
5.  vars_files
6.  set_fact / registered
7.  block vars
8.  task vars
9.  extra vars (-e on command line)
```

There are about 22 levels in the full hierarchy. The full ordered list is in the [Ansible docs](https://docs.ansible.com/ansible/latest/playbook_guide/playbooks_variables.html#understanding-variable-precedence) — but you almost never need to think past:

- **`group_vars` is the regular place for variables.**
- **`host_vars` overrides `group_vars` for one host.**
- **`-e` overrides everything** — useful for "run this just once with X different".

For the lab, this is enough:

```yaml
# src/msai_setup/lab/ansible/group_vars/lab.yml (illustrative)
zfs_pool_name: lab
zfs_topology: stripe
arc_max_bytes: 2147483648         # 2 GiB
```

```bash
# Override per-run:
ansible-playbook zfs.yml -e zfs_topology=mirror
```

## Facts — what Ansible discovers automatically

When a play starts, the `setup` module runs against every host and gathers a large dictionary of facts. They all live under `ansible_*` names. The useful ones:

| Fact | Example |
|---|---|
| `ansible_hostname` | `ms-s1-max-lab` |
| `ansible_fqdn` | `ms-s1-max-lab.local` |
| `ansible_distribution` | `Ubuntu` |
| `ansible_distribution_version` | `26.04` |
| `ansible_distribution_release` | `resolute` |
| `ansible_os_family` | `Debian` |
| `ansible_architecture` | `aarch64` |
| `ansible_processor_cores` | `4` |
| `ansible_memtotal_mb` | `7956` |
| `ansible_default_ipv4.address` | `10.0.2.15` |
| `ansible_all_ipv4_addresses` | `[...]` |
| `ansible_interfaces` | `[...]` |
| `ansible_mounts` | `[...]` |
| `ansible_kernel` | `7.0.0-15-generic` |

See them all:

```bash
ansible -i inventory.yml lab -m setup
ansible -i inventory.yml lab -m setup -a 'filter=ansible_distribution*'
```

Disable fact gathering when not needed (slight speedup):

```yaml
- hosts: lab
  gather_facts: false
  tasks: [...]
```

## Magic variables — Ansible's internals

A few names come from Ansible itself, not facts:

| Variable | Meaning |
|---|---|
| `inventory_hostname` | The host's name as it appears in inventory |
| `groups` | Dict of group name -> list of hosts |
| `group_names` | List of groups this host belongs to |
| `hostvars` | Dict of hostname -> that host's vars (cross-host references) |
| `play_hosts` / `ansible_play_hosts` | All hosts in the current play |
| `ansible_loop` | Inside a `loop:`, info about the current iteration |
| `playbook_dir` | Directory where the playbook lives |
| `inventory_dir` | Directory where the inventory file lives |
| `inventory_file` | Path to the inventory file |
| `ansible_user` | The remote user we're running as |
| `ansible_managed` | A standard "this file is managed by Ansible" string for templates |

Cross-host references are powerful:

```yaml
- name: tell every host about the primary node's IP
  ansible.builtin.copy:
    dest: /etc/primary-node
    content: "{{ hostvars['ms-s1-max'].ansible_default_ipv4.address }}\n"
```

## `register` — capturing task results

```yaml
- name: run something
  ansible.builtin.command: cat /etc/os-release
  register: os_release_result
  changed_when: false

- name: use it
  ansible.builtin.debug:
    msg: "We're on {{ os_release_result.stdout }}"
```

Registered values are scoped to the host they ran on. They live for the rest of the play (and the playbook, if you don't overwrite them).

Common fields after `register:`:

```yaml
result:
  changed: bool
  failed: bool
  skipped: bool
  rc: int                   # for command/shell
  stdout: str
  stderr: str
  stdout_lines: [str]
  stderr_lines: [str]
  start: str                # ISO timestamp
  end: str
  delta: str                # duration
  # module-specific fields beyond these
```

Use `failed_when:` / `changed_when:` to override the module's own judgement:

```yaml
- name: a thing that's allowed to "fail"
  ansible.builtin.command: maybe-not-installed
  register: maybe
  failed_when: false             # never mark as failed
  changed_when: maybe.rc == 0    # only "changed" if it actually ran
```

## `set_fact` — compute and persist

```yaml
- name: compute pool name
  ansible.builtin.set_fact:
    pool_name: "tank-{{ environment }}-{{ inventory_hostname | replace('.', '-') }}"

- name: use it
  ansible.builtin.debug:
    msg: "Pool will be {{ pool_name }}"
```

`set_fact` writes a variable that lives for the rest of the play **on that host**. Combine with conditionals to build up structure:

```yaml
- ansible.builtin.set_fact:
    is_lab: "{{ 'lab' in group_names }}"

- ansible.builtin.set_fact:
    zfs_arc_max_bytes: "{{ 2 * 1024 * 1024 * 1024 if is_lab else 16 * 1024 * 1024 * 1024 }}"
```

`cacheable: true` on `set_fact` writes it through to the fact cache (if configured), so it persists across runs.

## Loops bind a special variable

Inside `loop:`, the magic name `item` is the current iteration:

```yaml
- name: install packages
  ansible.builtin.apt:
    name: "{{ item }}"
  loop: ['htop', 'tmux']
```

Rename `item` if you want:

```yaml
- name: install
  ansible.builtin.apt:
    name: "{{ pkg }}"
  loop: ['htop', 'tmux']
  loop_control:
    loop_var: pkg
```

This is essential when looping inside an `include_tasks:` that itself loops — `item` collides.

## `--extra-vars` (`-e`) on the command line

The highest-priority normal source. Useful for one-off overrides:

```bash
# string
ansible-playbook play.yml -e environment=staging

# multiple
ansible-playbook play.yml -e environment=staging -e debug=true

# YAML/JSON inline
ansible-playbook play.yml -e '{"datasets": ["foo", "bar"]}'

# From a file
ansible-playbook play.yml -e @custom-vars.yml
```

`-e` wins over essentially everything else, so it's useful but also dangerous: never bake values into `-e` flags you can't easily audit. Prefer `group_vars`/`host_vars` for stable settings, `-e` for genuine one-offs.

## `vars_prompt` — ask the operator

```yaml
- hosts: lab
  vars_prompt:
    - name: db_password
      prompt: "New database password"
      private: true             # don't echo
      confirm: true             # ask twice and compare
      encrypt: sha512_crypt     # store hashed
  tasks:
    - ansible.builtin.user:
        name: postgres
        password: "{{ db_password }}"
```

Reasonable for interactive one-shot plays. For automation, prefer vault.

## Defaults and `default()`

Make a variable optional by giving it a default at use time:

```yaml
- name: drop a config
  ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
  vars:
    worker_processes: "{{ nginx_workers | default(ansible_processor_cores) }}"
    keepalive: "{{ nginx_keepalive | default(75) }}"
```

In roles, set defaults in `defaults/main.yml`. Anywhere else, `default()` filter at the point of use.

## Empty / undefined / falsy

Three states to know:

- **Defined and falsy** (`false`, `0`, `""`, `[]`) — these all evaluate false in `when:`.
- **Defined and truthy** — evaluate true.
- **Undefined** — `when: undefined_var` raises an error; `when: undefined_var is defined` is the safe test. `undefined_var | default('x')` substitutes.

```yaml
- when: nginx_extras is defined and nginx_extras | length > 0
```

## Vault: encrypted variables

```yaml
# group_vars/all/vault.yml (encrypted with ansible-vault)
$ANSIBLE_VAULT;1.1;AES256
3565363762363266633165613961383139666264663366393234653236616533613961323239
...
```

After decryption, this looks like:

```yaml
ansible_become_password: super-secret
postgres_password: also-secret
```

See [Vault](vault.md) for the full workflow.

## Variable scoping cheat-sheet

| Where | Scope | Persistence |
|---|---|---|
| `defaults/main.yml` (role) | role-wide | only while playbook runs |
| `group_vars/`, `host_vars/` | inventory-wide | always |
| `vars:` on play | the play | the play |
| `vars:` on task | the task | the task |
| `register:` | the host | for rest of the playbook |
| `set_fact:` (cacheable=false) | the host | for rest of the playbook |
| `set_fact:` (cacheable=true) | the host | persisted to fact cache |
| `-e` on command line | global | the current run |

## Common gotchas

### Booleans inside YAML

`yes`, `no`, `true`, `false`, `on`, `off` are all booleans in YAML. Surprising values:

```yaml
foo: yes        # bool True
bar: "yes"      # string "yes"
baz: 1.0        # float
```

For Ansible, use bare `true`/`false` for booleans. Quote everything else.

### Quoting Jinja in YAML

```yaml
# WRONG — YAML parser tries to read {{ ... }} as a dict
foo: {{ bar }}

# RIGHT
foo: "{{ bar }}"
```

### Variable inside another variable

Jinja substitution is **lazy** — variables resolve at the moment of use, not at definition. So:

```yaml
defaults:
  base_dir: /opt/foo
  config_path: "{{ base_dir }}/config"

# usage works fine — config_path resolves base_dir at use time
```

But if `base_dir` itself contains a Jinja expression that wasn't defined yet, you get an error at use time, not definition time. Debug with `-vvv` to see the resolution chain.

### Mutating a variable

Ansible variables are not really mutable in the imperative sense. `set_fact` rebinds them. There's no `append to a list` operator — you do `set_fact: foo: "{{ foo + [new_item] }}"`. Verbose but explicit.

## Where to go next

- [Templates](templates.md) — Jinja2 in detail.
- [Vault](vault.md) — encrypting variables (generic; not used by the shipped playbooks).
- [Inventory](inventory.md) — group_vars/host_vars in context.
- [Playbooks](playbooks.md) — how variables flow into tasks.
- The hands-on walkthrough: [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) — `-e` overrides (e.g. `msai lab apply zfs -e topology=mirror`) in action.
