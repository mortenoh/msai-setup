# Templates

Ansible's `template:` module renders a Jinja2 template on the control node and writes the result to the managed host. It's the canonical way to deploy any config file that needs dynamic content.

## When to use `template:` vs `copy:`

- **`copy:`** — the file is static. Same bytes on every host. Maybe inline content. No substitution.
- **`template:`** — the file needs variables (`{{ }}`), conditionals (`{% if %}`), or loops (`{% for %}`).

If you're unsure, start with `copy:`. Promote to `template:` only when you actually need substitution.

## A first template

```yaml
# playbook.yml
- name: render sshd config
  ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config.d/00-managed.conf
    owner: root
    group: root
    mode: "0644"
    backup: true
    validate: '/usr/sbin/sshd -t -f %s'
  notify: reload sshd
```

```jinja2
# templates/sshd_config.j2
# {{ ansible_managed }}
# Managed by Ansible. Do not edit by hand.

Port {{ ssh_port | default(22) }}
PermitRootLogin {{ permit_root_login | default('no') }}

{% if allow_agent_forwarding | default(false) %}
AllowAgentForwarding yes
{% else %}
AllowAgentForwarding no
{% endif %}

# Allowed users
{% for user in allowed_users | default(['morten']) %}
AllowUsers {{ user }}
{% endfor %}
```

Notes:

- `templates/` next to the playbook is the conventional location; Ansible finds files relative to the playbook/role.
- `{{ ansible_managed }}` is a magic variable yielding a "this file is managed by Ansible, edit the template instead" string.
- `validate: '... %s'` runs the validator with `%s` as the temp-rendered file before installing. Saves you from broken sshd configs.

## Jinja2 syntax cheat-sheet

### Substitution

```jinja
{{ variable }}                  # plain
{{ variable | filter }}         # apply a filter
{{ variable.attribute }}        # access dict/object attribute
{{ variable['key'] }}           # equivalent
{{ list[0] }}                   # index
{{ dict['key'] | default('') }} # missing key -> empty
```

### Conditionals

```jinja
{% if foo == 'bar' %}
  ...
{% elif foo == 'baz' %}
  ...
{% else %}
  ...
{% endif %}
```

Truthiness: empty strings, empty lists, empty dicts, `false`, `none`, and `0` are all falsy.

### Loops

```jinja
{% for item in items %}
  - {{ item }}
{% endfor %}

{% for key, value in dict.items() %}
  {{ key }}: {{ value }}
{% endfor %}

{% for item in items if item.enabled %}
  - {{ item.name }}
{% endfor %}
```

Inside a loop, `loop.index` (1-based), `loop.index0` (0-based), `loop.first`, `loop.last` are available.

### Whitespace control

Jinja preserves whitespace by default. Trim with `-`:

```jinja
{%- for item in items %}
{{ item }}
{%- endfor %}
```

`{%- ... %}` strips whitespace before; `{% ... -%}` strips after. Useful when the resulting file's blank lines matter.

### Comments

```jinja
{# this is a Jinja comment — not in output #}
```

## Common filters

Ansible adds many filters on top of Jinja2's built-ins. The ones you'll use most:

### Defaults and existence

```jinja
{{ foo | default('fallback') }}
{{ foo | default('fallback', true) }}   # also use fallback if foo is empty/false

{% if foo is defined %}...{% endif %}
{% if foo is not none %}...{% endif %}
{% if foo is truthy %}...{% endif %}
```

### Strings

```jinja
{{ "hello" | upper }}                   # HELLO
{{ "HELLO" | lower }}                   # hello
{{ "hello world" | title }}             # Hello World
{{ "  trim me  " | trim }}              # "trim me"
{{ "abc-def" | replace('-', '_') }}     # abc_def
{{ "abc" | length }}                    # 3
```

### Lists

```jinja
{{ [1, 2, 3] | length }}                # 3
{{ [1, 2, 3] | join(',') }}             # 1,2,3
{{ [3, 1, 2] | sort }}                  # [1, 2, 3]
{{ list1 | union(list2) }}              # set union
{{ list1 | intersect(list2) }}
{{ list1 | difference(list2) }}
{{ list | unique }}
{{ list | min }} / {{ list | max }}
```

### Dicts

```jinja
{{ {'a': 1, 'b': 2} | items }}          # [['a', 1], ['b', 2]]
{{ dict | dict2items }}                 # [{key: a, value: 1}, ...]
{{ list_of_dicts | items2dict }}        # inverse
```

### Selection

```jinja
{{ users | selectattr('admin', 'equalto', true) | list }}
{{ users | rejectattr('disabled') | list }}
{{ users | map(attribute='email') | list }}
{{ services | selectattr('enabled') | map(attribute='name') | join(', ') }}
```

These chain naturally. Read left-to-right: "from `users`, take items where `.admin == true`, return as a list".

### Path / URL

```jinja
{{ '/etc/ssh/sshd_config' | basename }}    # sshd_config
{{ '/etc/ssh/sshd_config' | dirname }}     # /etc/ssh
{{ 'foo.conf' | splitext }}                # ('foo', '.conf')
```

### Hashing / encoding

```jinja
{{ "password" | hash('sha256') }}
{{ "data" | b64encode }}
{{ "ZGF0YQ==" | b64decode }}
```

### Network

Ansible's `ansible.utils` collection adds network filters:

```jinja
{{ '192.168.1.0/24' | ansible.utils.ipaddr('hostmin') }}
{{ ip | ansible.utils.ipaddr('network') }}
```

### JSON / YAML

```jinja
{{ {'a': 1} | to_json }}
{{ {'a': 1} | to_nice_json }}
{{ {'a': 1} | to_yaml }}
{{ {'a': 1} | to_nice_yaml }}
{{ json_string | from_json }}
{{ yaml_string | from_yaml }}
```

`to_nice_*` adds indentation and is what you want for human-readable output.

## Real examples from this build

### Generating a dynamic ufw rules file

```yaml
- name: generate ufw rules
  ansible.builtin.template:
    src: ufw-rules.j2
    dest: /etc/ufw/user.rules
  vars:
    allowed_ports:
      - { port: 22,   proto: tcp, comment: "ssh" }
      - { port: 80,   proto: tcp, comment: "http" }
      - { port: 443,  proto: tcp, comment: "https" }
      - { port: 41641, proto: udp, comment: "tailscale" }
```

```jinja
# {{ ansible_managed }}
*filter
:ufw-user-input - [0:0]

{% for rule in allowed_ports %}
-A ufw-user-input -p {{ rule.proto }} --dport {{ rule.port }} -j ACCEPT  -m comment --comment "{{ rule.comment }}"
{% endfor %}

COMMIT
```

### sanoid.conf from a list of datasets

```yaml
- name: configure sanoid retention
  ansible.builtin.template:
    src: sanoid.conf.j2
    dest: /etc/sanoid/sanoid.conf
  vars:
    sanoid_templates:
      data: { hourly: 24, daily: 30, weekly: 4, monthly: 6 }
      db:   { frequently: 6, hourly: 48, daily: 30 }
    sanoid_datasets:
      - { name: tank/nextcloud-data, template: data }
      - { name: tank/db,             template: db, recursive: true }
```

```jinja
# {{ ansible_managed }}
{% for name, settings in sanoid_templates.items() %}
[template_{{ name }}]
{%- for key, value in settings.items() %}
    {{ key }} = {{ value }}
{%- endfor %}
    autosnap = yes
    autoprune = yes
{% endfor %}

{% for ds in sanoid_datasets %}
[{{ ds.name }}]
    use_template = {{ ds.template }}
{%- if ds.recursive | default(false) %}
    recursive = yes
{%- endif %}
{% endfor %}
```

### `/etc/hosts` from inventory

```yaml
- name: generate /etc/hosts with all lab hosts
  ansible.builtin.template:
    src: hosts.j2
    dest: /etc/hosts
```

```jinja
# {{ ansible_managed }}
127.0.0.1 localhost
{{ ansible_default_ipv4.address }} {{ inventory_hostname }}

{% for host in groups['lab'] %}
{% if hostvars[host].ansible_default_ipv4 is defined and host != inventory_hostname %}
{{ hostvars[host].ansible_default_ipv4.address }} {{ host }}
{% endif %}
{% endfor %}
```

## Lookups — read content from the control node

Inside templates (and YAML), `lookup()` returns content from the control node:

```jinja
# embed a file's contents
ssh_authorized_keys = "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"

# embed an environment variable
api_key = "{{ lookup('env', 'API_KEY') }}"

# embed output of a command
build_id = "{{ lookup('pipe', 'git rev-parse HEAD') }}"
```

For secrets, prefer `ansible-vault` over `lookup('env', ...)` — env vars leak to logs.

## Validation — never deploy a broken file

Almost every config-file module supports `validate:`:

```yaml
- ansible.builtin.template:
    src: sshd_config.j2
    dest: /etc/ssh/sshd_config
    validate: '/usr/sbin/sshd -t -f %s'

- ansible.builtin.template:
    src: nginx.conf.j2
    dest: /etc/nginx/nginx.conf
    validate: '/usr/sbin/nginx -t -c %s'

- ansible.builtin.template:
    src: sudoers-extra.j2
    dest: /etc/sudoers.d/90-managed
    validate: '/usr/sbin/visudo -cf %s'
```

The `%s` is substituted with the rendered file's path in a temp dir. If validation fails, the temp file is discarded and the task fails — your existing config is untouched.

**Use this for any config a syntax error in which would lock you out.** sshd, sudoers, nginx, etc.

## Debugging templates

```bash
# Render a template against a host without copying it
ansible -i inventory.yml ms-s1-max -m ansible.builtin.template -a 'src=foo.j2 dest=/tmp/foo' --check --diff
```

For richer debugging, add `-vv` to see the rendered content in the diff:

```bash
ansible-playbook -i inventory.yml play.yml --check --diff -vv
```

## Common mistakes

### Forgetting to quote `{{ }}` in YAML

```yaml
# WRONG — YAML reads as a dict
foo: {{ bar }}

# RIGHT
foo: "{{ bar }}"
```

### Mixing Jinja and shell quoting

```jinja
# inside a template, no extra quoting
ssh_user = {{ ssh_user }}

# But to put it inside a shell command in a playbook task:
ansible.builtin.shell: 'echo "{{ msg }}"'   # single-quote the outer, double-quote the inner
```

### Empty values vs undefined

```jinja
# fails if `foo` is undefined
{% if foo %}...{% endif %}

# safe
{% if foo is defined and foo %}...{% endif %}

# or use default
{% if foo | default('') %}...{% endif %}
```

## Where to go next

- [Variables](variables.md) — what's available inside `{{ }}`.
- [Modules -> `template:`](modules.md) — the module parameters.
- [Vault](vault.md) — how to use encrypted values inside templates.
