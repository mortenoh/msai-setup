# Playbooks

A playbook is a YAML document of **plays**. A play targets one or more host groups with a sequence of **tasks** that converge each host to a declared state. Playbooks are the unit you actually run.

## Anatomy

```yaml
---                              # YAML document marker (optional, conventional)
- hosts: lab                     # the play targets this group
  become: true                   # run tasks via sudo (per-task by default)
  gather_facts: true             # run setup module to collect facts (default)
  vars:                          # play-scoped variables
    nginx_version: 1.27

  pre_tasks:                     # run before main tasks (rare; mostly for setup)
    - name: refresh apt cache
      ansible.builtin.apt:
        update_cache: true

  tasks:                         # the main work
    - name: install nginx
      ansible.builtin.apt:
        name: nginx
        state: present

    - name: copy nginx config
      ansible.builtin.copy:
        src: nginx.conf
        dest: /etc/nginx/nginx.conf
      notify: reload nginx       # trigger a handler if this changes

  handlers:                      # tasks that run only when notified
    - name: reload nginx
      ansible.builtin.systemd:
        name: nginx
        state: reloaded

  post_tasks:                    # run after main tasks (rare)
    - name: ping after deploy
      ansible.builtin.uri:
        url: http://localhost:80
```

A file can contain multiple plays — Ansible runs them in order, top to bottom.

## Tasks

Each task is one module invocation:

```yaml
- name: install a package      # human-readable description, shown in output
  ansible.builtin.apt:          # module name (FQCN — see below)
    name: htop                  # module arguments
    state: present
  when: ansible_os_family == "Debian"   # conditional
  tags: [packages, baseline]    # tags for selective runs
  register: install_result      # store the result in a variable
  ignore_errors: false          # default: stop the play on failure
  changed_when: install_result.rc == 0   # custom "did this change?" logic
  failed_when: false            # custom "is this a failure?" logic
```

### Fully-qualified collection names (FQCN)

Modules now have full namespaces: `ansible.builtin.apt` instead of bare `apt`, `community.general.ufw` instead of `ufw`. Older playbooks use the short form; it still works but is less explicit.

Prefer FQCN — it's unambiguous, documents which collection the module belongs to, and survives renames.

### Common task fields

| Field | Use |
|---|---|
| `name:` | What it does, for output. Always include one. |
| `<module>:` | The module, with its args as nested keys. |
| `when:` | Conditional. Task is skipped if expression is false. |
| `loop:` | Run the task once per item. |
| `register:` | Store the module's result as a variable. |
| `notify:` | Trigger one or more handlers (by name) if `changed`. |
| `tags:` | List of tags for selective runs (`--tags`/`--skip-tags`). |
| `become:` / `become_user:` | Override the play-level setting per task. |
| `ignore_errors:` | If true, failures don't stop the play (mostly for testing). |
| `changed_when:` | Override the module's "changed" detection. |
| `failed_when:` | Override the module's "failed" detection. |
| `delegate_to:` | Run the task on a different host than the play targets. |

## Loops

`loop:` runs the task once per item:

```yaml
- name: install several packages
  ansible.builtin.apt:
    name: "{{ item }}"
    state: present
  loop:
    - htop
    - tmux
    - jq
```

Loops over dicts use the dict's items:

```yaml
- name: drop config files
  ansible.builtin.copy:
    src: "{{ item.src }}"
    dest: "{{ item.dest }}"
    mode: "{{ item.mode | default('0644') }}"
  loop:
    - { src: nginx.conf,        dest: /etc/nginx/nginx.conf }
    - { src: nginx-modules.conf, dest: /etc/nginx/modules-enabled/extra.conf, mode: "0600" }
```

You can label each iteration in the output:

```yaml
- name: install packages
  ansible.builtin.apt:
    name: "{{ item }}"
  loop: ['htop', 'tmux', 'jq']
  loop_control:
    label: "{{ item }}"
```

### `loop:` vs the older `with_items:`

`with_items:` is the older syntax. `loop:` is the modern equivalent and what you should use in new playbooks. Functionally similar; `loop:` has cleaner control over labelling and behaviour.

## Conditionals — `when:`

```yaml
- name: install ufw only on Debian/Ubuntu
  ansible.builtin.apt:
    name: ufw
    state: present
  when: ansible_os_family == "Debian"

- name: install fail2ban for production only
  ansible.builtin.apt:
    name: fail2ban
    state: present
  when:
    - environment == "production"
    - install_fail2ban | default(true)
```

`when:` takes a Jinja2 expression. A list of expressions is AND'd together. Use `|` for OR inside a single expression.

## Blocks

`block:` groups tasks for shared `when:`, `become:`, or `rescue:`:

```yaml
- name: configure postgres only when role includes db
  when: "'db' in roles"
  block:
    - ansible.builtin.apt:
        name: postgresql
        state: present
    - ansible.builtin.systemd:
        name: postgresql
        enabled: true
        state: started
  rescue:
    - name: report failure
      ansible.builtin.debug:
        msg: "Postgres setup failed; see previous error."
  always:
    - name: clean up
      ansible.builtin.file:
        path: /tmp/postgres-staging
        state: absent
```

`rescue:` runs only if a task in `block:` fails. `always:` runs whether the block succeeded or not. Useful for ensuring cleanup runs even when something goes wrong.

## Error handling

By default, a task failure halts the play **on that host** but continues on other hosts. To change behaviour:

```yaml
- name: try this, it's OK if it fails
  ansible.builtin.shell: maybe-broken-command
  ignore_errors: true
  register: maybe_result

- name: react to the result
  ansible.builtin.debug:
    msg: "Recovered. Got: {{ maybe_result.stdout }}"
  when: maybe_result.rc != 0
```

For a play-wide "any one host fails = abort everyone":

```yaml
- hosts: lab
  any_errors_fatal: true
```

`max_fail_percentage: 30` is the middle-ground: abort once 30% of hosts have failed.

## `register:` and remembering output

Almost every task can capture its result:

```yaml
- name: discover something
  ansible.builtin.command: cat /etc/os-release
  register: os_release
  changed_when: false              # this is a read, not a change

- name: use the result
  ansible.builtin.debug:
    msg: "ID={{ os_release.stdout_lines | select('match', '^ID=') | first }}"
```

The shape of the registered variable depends on the module. Common fields:

- `changed`, `failed`, `skipped` — booleans.
- `stdout`, `stderr`, `rc` — for command/shell/etc.
- `stdout_lines`, `stderr_lines` — split versions of the above.
- Module-specific fields (e.g. `apt`'s `cache_updated`).

## Tags

Tag tasks to run subsets:

```yaml
tasks:
  - name: install packages
    ansible.builtin.apt:
      name: htop
    tags: [baseline, packages]

  - name: harden ssh
    ansible.builtin.copy: ...
    tags: [ssh, security]

  - name: deploy app
    ansible.builtin.copy: ...
    tags: [app]
```

Then:

```bash
ansible-playbook play.yml --tags baseline     # only baseline tasks
ansible-playbook play.yml --skip-tags app     # everything except app
ansible-playbook play.yml --tags 'never'      # nothing — useful as a default-off pattern
ansible-playbook play.yml --list-tags         # show all tags in the playbook
```

The special tag `always` runs unless `--skip-tags always` is passed; the special tag `never` is skipped unless explicitly `--tags never`'d.

## Strategies — controlling parallelism

By default Ansible's "linear" strategy runs each task on all hosts in parallel (up to `forks`), waits for completion, then moves to the next task. Alternatives:

- `strategy: free` — every host plows through its task list independently. Faster for long, host-independent runs.
- `strategy: host_pinned` — assign batches of hosts to forks; each fork chews through its hosts independently.

```yaml
- hosts: lab
  strategy: free
  tasks: [...]
```

Stick with the default `linear` for most setups; it makes failures and progress easy to read.

## Including other files

Split big playbooks into smaller files:

```yaml
# main.yml
- import_playbook: bootstrap.yml
- import_playbook: ssh-hardening.yml
- import_playbook: ufw.yml
```

```yaml
# bootstrap.yml
- hosts: lab
  tasks:
    - import_tasks: tasks/baseline-packages.yml
    - import_tasks: tasks/sudoers.yml
```

`import_tasks:` is static (resolved at parse time); `include_tasks:` is dynamic (resolved at runtime, supports `when:` on the include itself). Static is simpler; use dynamic when you actually need runtime decisions about whether to include.

## Running playbooks

```bash
# Run a playbook
ansible-playbook -i inventory.yml play.yml

# Dry-run: show what would change without changing anything
ansible-playbook -i inventory.yml play.yml --check

# Show diffs for file changes
ansible-playbook -i inventory.yml play.yml --check --diff

# Verbose levels (more v = more detail)
ansible-playbook -i inventory.yml play.yml -v
ansible-playbook -i inventory.yml play.yml -vv
ansible-playbook -i inventory.yml play.yml -vvv      # SSH-level debugging
ansible-playbook -i inventory.yml play.yml -vvvv     # connection plugin internals

# Limit to a subset of hosts
ansible-playbook -i inventory.yml play.yml -l 'lab:!ms-s1-max-old'

# Pass extra variables
ansible-playbook -i inventory.yml play.yml -e environment=staging -e topology=mirror

# Start from a specific task (by name)
ansible-playbook -i inventory.yml play.yml --start-at-task='install nginx'

# Step through interactively
ansible-playbook -i inventory.yml play.yml --step

# Use vault password
ansible-playbook -i inventory.yml play.yml --ask-vault-pass
ansible-playbook -i inventory.yml play.yml --vault-password-file ~/.vault_pass
```

## Reading the output

```
PLAY [Install baseline] ********************************************************

TASK [Gathering Facts] *********************************************************
ok: [ms-s1-max-lab]

TASK [install nginx] ***********************************************************
changed: [ms-s1-max-lab]

TASK [copy nginx config] *******************************************************
changed: [ms-s1-max-lab]

RUNNING HANDLER [reload nginx] **************************************************
changed: [ms-s1-max-lab]

PLAY RECAP *********************************************************************
ms-s1-max-lab : ok=4    changed=3    unreachable=0    failed=0    skipped=0    rescued=0    ignored=0
```

- The `PLAY RECAP` line is what to look at for a quick overall result.
- `changed=N` is your guide to drift detection. Healthy steady-state runs report `changed=0`.

## Examples from this build

The lab playbooks in `src/msai_setup/lab/ansible/playbooks/` demonstrate every pattern above. All six are real and shipped:

| Playbook | Patterns it demonstrates |
|---|---|
| `bootstrap.yml` | `apt` with a list, `community.general.timezone`, handlers, passwordless sudoers drop-in, `lineinfile` |
| `ssh-hardening.yml` | `copy` with content from a Jinja2-rendered string, `command` for validation, handlers |
| `ufw.yml` | `loop:` with dict items, `community.general.ufw` |
| `zfs.yml` | `shell` with `changed_when`, `set_fact`, `assert`, `block`/`when`, complex `command`, `community.general.zfs` |
| `docker.yml` | `get_url` GPG keyring, `uri` HEAD probe with codename fallback, `set_fact`, `user` group membership, `daemon.json` via `copy`, restart handler, smoke-test `command` |
| `services.yml` | `community.docker.docker_network` + `docker_compose_v2`, per-service `file`/`copy`, `uri` retry-until smoke test — deploys a Traefik + whoami stack |

Read them open in one tab while you read this page in another — the docs make a lot more sense paired with worked examples. The [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) walkthrough runs all of them against a throwaway VM via `msai lab apply`.

## Where to go next

- [Modules](modules.md) — the modules used in this build.
- [Variables](variables.md) — variable precedence and friends.
- [Templates](templates.md) — Jinja2 for config files.
- [Roles](roles.md) — when to graduate flat playbooks to roles.
- [Handlers](handlers.md) — the notify/listen mechanism.
