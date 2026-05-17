# Modules

A module is a unit of work Ansible can perform on a remote host. There are thousands; this page covers the ones used in this build, the conventions that apply across all of them, and how to find others.

## How modules are addressed

Modules live in collections. The fully-qualified name is `<namespace>.<collection>.<module>`:

| FQCN | What |
|---|---|
| `ansible.builtin.apt` | apt package manager — built into ansible-core |
| `ansible.builtin.copy` | copy a file — built in |
| `ansible.builtin.systemd` | systemd units — built in |
| `community.general.ufw` | UFW firewall — needs `community.general` collection |
| `community.general.zfs` | ZFS datasets — needs `community.general` |
| `community.general.timezone` | system timezone — needs `community.general` |
| `ansible.posix.firewalld` | firewalld (RHEL/Fedora) — needs `ansible.posix` |
| `community.docker.docker_compose_v2` | Docker Compose — needs `community.docker` |

The collections used in this build are in `scripts/lab/ansible/requirements.yml`. Install them with `ansible-galaxy collection install -r ...`.

You can also write modules with just the bare name (e.g. `apt:` instead of `ansible.builtin.apt:`) — Ansible resolves them via the implicit `collections:` path. Prefer FQCN: it's unambiguous and survives renames.

## Modules used in this build

### `ansible.builtin.apt`

```yaml
- name: install one package
  ansible.builtin.apt:
    name: htop
    state: present

- name: install many packages
  ansible.builtin.apt:
    name:
      - htop
      - tmux
      - jq
    state: present
    update_cache: true
    cache_valid_time: 3600       # use cached apt metadata if fresh enough

- name: upgrade everything
  ansible.builtin.apt:
    upgrade: dist
    update_cache: true

- name: remove a package
  ansible.builtin.apt:
    name: telnet
    state: absent
    purge: true
```

States: `present`, `absent`, `latest` (installs/upgrades to newest), `build-dep`, `fixed`.

### `ansible.builtin.copy`

```yaml
- name: copy from local file
  ansible.builtin.copy:
    src: nginx.conf                            # path relative to playbook / role / "files/"
    dest: /etc/nginx/nginx.conf
    owner: root
    group: root
    mode: "0644"
    backup: true                                # write a timestamped backup
  notify: reload nginx

- name: copy from inline content
  ansible.builtin.copy:
    dest: /etc/sysctl.d/99-tcp.conf
    owner: root
    group: root
    mode: "0644"
    content: |
      net.core.somaxconn = 4096
      net.ipv4.tcp_max_syn_backlog = 4096
```

`mode:` must be quoted (`"0644"`) or YAML interprets it as octal anyway, which sometimes bites you.

### `ansible.builtin.template`

Like `copy:` but renders the source file as a Jinja2 template first. See [Templates](templates.md):

```yaml
- name: render sshd_config from a template
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config.d/00-hardening.conf
    owner: root
    group: root
    mode: "0644"
    validate: '/usr/sbin/sshd -t -f %s'        # validate before installing
  notify: reload sshd
```

`validate:` runs the command (with `%s` substituted for a temp file) before the final move. If validation fails, the file isn't installed and the task fails — great for sshd / nginx / sudoers where a bad config locks you out.

### `ansible.builtin.file`

Manage paths — directories, ownership, modes, symlinks:

```yaml
- name: create a directory
  ansible.builtin.file:
    path: /opt/foo
    state: directory
    owner: root
    group: root
    mode: "0755"

- name: remove a file
  ansible.builtin.file:
    path: /etc/foo.conf.old
    state: absent

- name: create a symlink
  ansible.builtin.file:
    src: /opt/foo/current
    dest: /opt/foo/latest
    state: link

- name: chown a tree
  ansible.builtin.file:
    path: /mnt/tank/nextcloud-data
    owner: "33"
    group: "33"
    recurse: true
```

### `ansible.builtin.lineinfile`

Targeted single-line edits in existing files. Use sparingly — prefer `template:` for whole files:

```yaml
- name: set a sysctl
  ansible.builtin.lineinfile:
    path: /etc/sysctl.conf
    regexp: '^net\.ipv4\.ip_forward\s*='
    line: 'net.ipv4.ip_forward=1'
    state: present

- name: comment out a line
  ansible.builtin.lineinfile:
    path: /etc/ssh/sshd_config
    regexp: '^PermitRootLogin'
    line: '# PermitRootLogin no  (managed by playbook ssh-hardening.yml)'
```

For complex multi-line edits, `blockinfile:` (also in `ansible.builtin`) adds a managed block bracketed by markers it tracks.

### `ansible.builtin.systemd`

```yaml
- name: ensure a service is running
  ansible.builtin.systemd:
    name: nginx
    state: started
    enabled: true

- name: reload after a config change
  ansible.builtin.systemd:
    name: nginx
    state: reloaded

- name: daemon-reload after dropping a new unit file
  ansible.builtin.systemd:
    daemon_reload: true

- name: disable + stop
  ansible.builtin.systemd:
    name: snapd
    state: stopped
    enabled: false
    masked: true
```

States: `started`, `stopped`, `restarted`, `reloaded`. Booleans: `enabled:`, `masked:`, `daemon_reload:`.

### `ansible.builtin.command` / `shell`

When no module fits:

```yaml
- name: run something
  ansible.builtin.command:
    cmd: zpool create -o ashift=12 tank /dev/sdb
  args:
    creates: /etc/zfs/zpool.cache               # only run if this path doesn't exist
  # OR equivalently:
  ansible.builtin.command: zpool create -o ashift=12 tank /dev/sdb

- name: piped stuff (shell only)
  ansible.builtin.shell: 'curl -sf example.com | sha256sum'
  register: hash_result
  changed_when: false                            # this is a read, not a change
```

`command` doesn't run through a shell — no pipes, redirects, globs, environment expansion. `shell` does.

**Always set one of these:**

- `creates:` — skip if file exists. Best for idempotent "make this thing".
- `removes:` — skip if file doesn't exist. For "delete this thing".
- `changed_when:` — explicit "is this changed". Necessary for anything that's a read (`changed_when: false`) or has its own change detection.

Without one, Ansible reports `changed: true` on every run, defeating idempotency.

### `community.general.ufw`

```yaml
- name: deny by default
  community.general.ufw:
    direction: incoming
    policy: deny

- name: allow SSH
  community.general.ufw:
    rule: allow
    name: OpenSSH

- name: allow specific port from specific source
  community.general.ufw:
    rule: allow
    proto: tcp
    port: 8080
    src: 192.168.1.0/24

- name: enable UFW
  community.general.ufw:
    state: enabled
```

### `community.general.timezone`

```yaml
- name: set timezone
  community.general.timezone:
    name: Europe/Oslo
```

Idempotent; checks current value before changing.

### `community.general.zfs`

```yaml
- name: create a dataset
  community.general.zfs:
    name: tank/foo
    state: present
    extra_zfs_properties:
      recordsize: 1M
      compression: lz4
      atime: 'off'

- name: destroy a dataset
  community.general.zfs:
    name: tank/foo
    state: absent
```

For pool-level operations (`zpool create`, `zpool import`, etc.) the module doesn't help — use `command:` with `creates:` for idempotency.

### `community.docker.docker_compose_v2`

```yaml
- name: bring up a compose stack
  community.docker.docker_compose_v2:
    project_src: /mnt/tank/containers/nextcloud
    state: present
    pull: always

- name: tear down
  community.docker.docker_compose_v2:
    project_src: /mnt/tank/containers/nextcloud
    state: absent
```

Wraps `docker compose up`/`down`. Detects whether containers are running/stopped/missing and converges.

### `ansible.posix.mount`

```yaml
- name: mount a filesystem on boot
  ansible.posix.mount:
    path: /srv/data
    src: /dev/disk/by-uuid/abcd-1234
    fstype: ext4
    opts: defaults,nodev,nosuid
    state: mounted          # mount now AND write fstab entry
```

States: `mounted`, `present` (fstab only), `unmounted`, `absent`, `remounted`.

### `ansible.builtin.user` / `ansible.builtin.group`

```yaml
- name: ensure user exists
  ansible.builtin.user:
    name: morten
    groups: [sudo, docker]
    shell: /bin/bash
    create_home: true

- name: lock a user
  ansible.builtin.user:
    name: oldadmin
    state: absent
    remove: true
    force: true
```

### `ansible.builtin.authorized_key`

```yaml
- name: install SSH key
  ansible.builtin.authorized_key:
    user: morten
    key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"
    state: present
```

Idempotent: doesn't duplicate the key if it's already there.

### `ansible.builtin.cron`

```yaml
- name: daily ZFS snapshot
  ansible.builtin.cron:
    name: daily-snapshot
    user: root
    minute: "0"
    hour: "3"
    job: "/usr/sbin/sanoid --cron"

- name: remove an old cron job
  ansible.builtin.cron:
    name: legacy-task
    state: absent
```

The `name:` field is how Ansible identifies the line in crontab. Required if you ever want to update or remove it.

### `ansible.builtin.git`

```yaml
- name: clone a repo
  ansible.builtin.git:
    repo: 'https://github.com/example/foo.git'
    dest: /opt/foo
    version: main
    depth: 1
    force: false        # don't blow away local changes
```

### `ansible.builtin.uri`

HTTP requests — health checks, API calls:

```yaml
- name: health-check after deploy
  ansible.builtin.uri:
    url: http://localhost:8080/health
    method: GET
    status_code: 200
  retries: 6
  delay: 5
  register: health
  until: health.status == 200
```

### `ansible.builtin.set_fact`

Create a variable at runtime, scoped to the current host:

```yaml
- name: build a derived value
  ansible.builtin.set_fact:
    pool_name: "tank-{{ environment }}"

- name: use it
  ansible.builtin.debug:
    msg: "Pool name is {{ pool_name }}"
```

### `ansible.builtin.assert`

Halt the play with a useful message if a condition isn't met:

```yaml
- name: confirm we found at least one disk
  ansible.builtin.assert:
    that: disks | length > 0
    fail_msg: "No disks found — did you set up the lab correctly?"
    success_msg: "Found {{ disks | length }} disks: OK"
```

### `ansible.builtin.debug`

```yaml
- name: show a value
  ansible.builtin.debug:
    msg: "Pool topology is {{ topology }}"

- name: show an entire registered variable
  ansible.builtin.debug:
    var: zpool_status

- name: increase verbosity gate
  ansible.builtin.debug:
    msg: "I only show with -vv"
    verbosity: 2
```

## Finding more modules

```bash
# Show all available modules
ansible-doc -l

# Search by keyword
ansible-doc -l | grep -i nginx

# Read the docs for a specific module
ansible-doc ansible.builtin.apt
ansible-doc community.general.ufw
ansible-doc community.general.zfs

# Just show example invocations
ansible-doc -s ansible.builtin.copy
```

The `ansible-doc` output for a module is the canonical reference — it lists every parameter, type, default, required-or-not, and includes examples. Faster than Google.

## Idempotency expectations

A well-written module reports `changed: true` only when it actually changed something. When you're writing your own `command:`/`shell:` tasks, you're responsible for matching that contract:

```yaml
# WRONG — always reports changed=true, hurts drift detection
- name: install go
  ansible.builtin.shell: |
    curl -L https://go.dev/dl/go1.22.linux-amd64.tar.gz | tar -C /usr/local -xz

# RIGHT — only runs when the binary is missing
- name: install go
  ansible.builtin.shell: |
    curl -L https://go.dev/dl/go1.22.linux-amd64.tar.gz | tar -C /usr/local -xz
  args:
    creates: /usr/local/go/bin/go

# ALSO RIGHT — explicit changed_when
- name: check something
  ansible.builtin.shell: 'rocm-smi --showdriverversion'
  register: rocm
  changed_when: false             # this is a read; never changes anything
```

## Where to go next

- [Templates](templates.md) — for the `template:` module's source files.
- [Variables](variables.md) — how to feed parameters into modules.
- [Handlers](handlers.md) — what `notify:` triggers.
- [Vault](vault.md) — when a module parameter is a secret.
