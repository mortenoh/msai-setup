# Handlers

Handlers are tasks that run **only when notified** by another task, and only **once per play** even if notified multiple times. The classic use case: "restart nginx if any of these configuration changes happen".

## The basic pattern

```yaml
- hosts: lab
  become: true

  tasks:
    - name: copy main nginx config
      ansible.builtin.template:
        src: nginx.conf.j2
        dest: /etc/nginx/nginx.conf
      notify: reload nginx

    - name: copy site config
      ansible.builtin.template:
        src: site.conf.j2
        dest: /etc/nginx/sites-available/site.conf
      notify: reload nginx

    - name: enable site
      ansible.builtin.file:
        src: /etc/nginx/sites-available/site.conf
        dest: /etc/nginx/sites-enabled/site.conf
        state: link
      notify: reload nginx

  handlers:
    - name: reload nginx
      ansible.builtin.systemd:
        name: nginx
        state: reloaded
```

If any one of the three tasks reports `changed`, `reload nginx` runs **once** at the end of the play.

## When handlers run

By default: **at the end of the play**, after all tasks complete. Notifications queue up; the handler section runs them in the order they appear in the `handlers:` block, regardless of which task triggered them.

You can force handlers earlier with `flush_handlers:`:

```yaml
tasks:
  - name: copy config
    ansible.builtin.template: ...
    notify: reload nginx

  - name: force the reload right now
    ansible.builtin.meta: flush_handlers

  - name: now check that the service responds
    ansible.builtin.uri:
      url: http://localhost
      status_code: 200
```

`flush_handlers` is rare in practice. It's mostly useful in roles where you need a service restarted before subsequent tasks in the **same** role.

## Multiple notifies, single run

```yaml
- name: a
  ansible.builtin.copy: ...
  notify:
    - reload nginx
    - restart varnish

- name: b
  ansible.builtin.copy: ...
  notify: reload nginx
```

If both `a` and `b` are `changed`, **`reload nginx` runs once**, then `restart varnish` runs once. The handler runs at most once per play even when notified by N tasks.

## Listen — many notifiers to one handler

When you have several tasks that each ought to trigger "restart everything", give them a shared `listen` topic:

```yaml
tasks:
  - name: a
    ansible.builtin.copy: ...
    notify: app reconfig

  - name: b
    ansible.builtin.copy: ...
    notify: app reconfig

handlers:
  - name: restart nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted
    listen: app reconfig

  - name: restart varnish
    ansible.builtin.systemd:
      name: varnish
      state: restarted
    listen: app reconfig
```

`notify: app reconfig` triggers both handlers (because both listen on that topic).

## When handlers DON'T run

- **The triggering task wasn't `changed`.** If `apt: name=nginx state=present` runs and nginx is already installed, no `changed`, no notification.
- **Earlier tasks failed.** A play that fails on a host typically skips the handlers for that host. Override with `force_handlers: true`:

  ```yaml
  - hosts: lab
    force_handlers: true
    tasks: [...]
    handlers: [...]
  ```

- **`--list-tasks` / `--check`.** Dry runs go through the motions but don't actually trigger handler runs in some cases. `--check --diff` runs handlers in check mode (which most handlers tolerate fine: `systemd: state: reloaded` reports "would reload" without doing it).

## Ordering guarantees

Handlers run **in the order they appear in `handlers:`**, NOT in the order they were notified. If A is defined before B in handlers, and B was notified first, A still runs first.

That's almost always what you want — it means you can put `daemon-reload` before `restart nginx` in handler definitions and trust it'll run in that order even if `restart nginx` got notified first.

```yaml
handlers:
  - name: reload systemd                # runs first if both notified
    ansible.builtin.systemd:
      daemon_reload: true

  - name: restart nginx
    ansible.builtin.systemd:
      name: nginx
      state: restarted
```

## Service-restart pattern for config files

The canonical pattern for any service whose config you manage:

```yaml
tasks:
  - name: install service
    ansible.builtin.apt:
      name: foo
      state: present
    notify: enable foo

  - name: configure service
    ansible.builtin.template:
      src: foo.conf.j2
      dest: /etc/foo/foo.conf
      validate: '/usr/bin/foo --check-config %s'
    notify: restart foo

handlers:
  - name: enable foo
    ansible.builtin.systemd:
      name: foo
      enabled: true
      state: started

  - name: restart foo
    ansible.builtin.systemd:
      name: foo
      state: restarted
```

The `enable foo` handler runs once after install. The `restart foo` runs once if config changed. If both fire in the same play, `enable foo` runs first (handler-order, not notify-order), which guarantees the service is enabled before we try to restart it.

## Reload vs restart

- `state: reloaded` — send SIGHUP (or service-specific reload); typically zero downtime. Use for config-file changes.
- `state: restarted` — full stop+start; brief downtime. Use when reloading isn't enough (binary upgrade, port change, kernel module reload).

For nginx, sshd, postgres, almost everything: `reloaded` is the right answer for config changes. Use `restarted` only when the docs say you have to (e.g. logrotate creating a new file that requires the service to re-open).

## Examples from this build

```yaml
# scripts/lab/ansible/playbooks/ssh-hardening.yml
- name: sshd_config — drop a hardened override
  ansible.builtin.copy:
    dest: /etc/ssh/sshd_config.d/00-hardening.conf
    ...
  notify: reload sshd

handlers:
  - name: reload sshd
    ansible.builtin.systemd:
      name: ssh
      state: reloaded
```

```yaml
# scripts/lab/ansible/playbooks/bootstrap.yml
- name: journald — keep logs persistent across reboots
  ansible.builtin.lineinfile:
    path: /etc/systemd/journald.conf
    regexp: '^#?\s*Storage='
    line: 'Storage=persistent'
  notify: restart journald

handlers:
  - name: restart journald
    ansible.builtin.systemd:
      name: systemd-journald
      state: restarted
```

## Tips

- **Always name your handlers descriptively.** `notify: reload nginx` is better than `notify: handler1`.
- **Define handlers in `handlers:`, never in `tasks:`.** A handler-style task in `tasks:` runs every time, defeating the point.
- **Test handlers in check mode.** `ansible-playbook play.yml --check --diff` walks through handler runs without actually restarting services. Good sanity check before applying.

## Where to go next

- [Modules → systemd](modules.md#ansiblebuiltinsystemd) — the module handlers typically invoke.
- [Playbooks](playbooks.md) — where `notify:` fits in task syntax.
