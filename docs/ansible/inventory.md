# Inventory

The inventory is the list of hosts Ansible knows about, organised into groups. Plays target groups (`hosts: lab`); the inventory says which actual hosts are in the `lab` group.

## Formats

Ansible accepts inventories in several formats. Use **YAML** unless you have a reason not to — it scales better than INI, integrates cleanly with variables, and you already know YAML from playbooks.

### YAML inventory (recommended)

```yaml
# inventory.yml
all:
  children:
    lab:
      hosts:
        ms-s1-max-lab:
          ansible_host: 127.0.0.1
          ansible_port: 2222
          ansible_user: morten

    production:
      hosts:
        ms-s1-max:
          ansible_host: 192.168.1.10
          ansible_user: morten

    homelab:
      children:
        - lab
        - production
```

Hosts can sit in multiple groups. Groups can contain other groups (`children:`). The `all` group implicitly contains every host.

### INI inventory (legacy)

```ini
# inventory.ini
[lab]
ms-s1-max-lab ansible_host=127.0.0.1 ansible_port=2222 ansible_user=morten

[production]
ms-s1-max ansible_host=192.168.1.10 ansible_user=morten

[homelab:children]
lab
production
```

Works but harder to manage as it grows.

## What's in a host entry

| Key | Meaning |
|---|---|
| `ansible_host` | DNS name or IP. Required if it differs from the inventory hostname. |
| `ansible_port` | SSH port (default 22). |
| `ansible_user` | SSH user (default: current user). |
| `ansible_password` | SSH password — avoid in plain files; use vault. |
| `ansible_become` | Use sudo? Boolean. |
| `ansible_become_user` | Sudo as which user (default: root). |
| `ansible_become_password` | Sudo password — vault it. |
| `ansible_ssh_private_key_file` | Path to private key. |
| `ansible_python_interpreter` | Path to remote python. Set when auto-detection misses. |
| `ansible_ssh_extra_args` | Extra args to pass to ssh. |

You can put any other key on a host or group — they become regular variables.

## Groups

Group on whatever makes sense for **how you target tasks**:

- Environment (`production`, `staging`, `lab`)
- Role (`db`, `web`, `proxy`)
- Provider (`aws`, `bare-metal`)
- Location (`home`, `office`, `colo`)

A host can belong to many groups; plays target whichever group makes the play applicable.

### Group hierarchies

```yaml
all:
  children:
    europe:
      children:
        norway:
          hosts:
            ms-s1-max:
              ansible_host: 192.168.1.10
        sweden:
          hosts:
            stockholm-box:
              ansible_host: 192.168.5.10
    backup:
      hosts:
        ms-s1-max:        # same host can appear in multiple groups
        backup-vps:
          ansible_host: backup.example.com
```

When variables conflict, child group wins over parent group, and host wins over group. See [Variables -> Precedence](variables.md#variable-precedence-simplified).

## Inventory variables

Inventory files can carry variables at host or group level. Two patterns:

### Inline on the host/group

```yaml
all:
  children:
    lab:
      hosts:
        ms-s1-max-lab:
          ansible_host: 127.0.0.1
          ansible_port: 2222
          ansible_user: morten
          # custom vars used by your playbooks:
          datacenter: home
          role: storage
      vars:
        # vars for every host in 'lab':
        environment: lab
        ntp_server: 192.168.1.1
```

Inline is fine for small setups. Gets noisy fast.

### Separate `group_vars/` and `host_vars/`

Ansible automatically loads variables from `group_vars/<groupname>.yml` and `host_vars/<hostname>.yml` next to the inventory file:

```
ansible/
  inventory.yml
  group_vars/
    all.yml           # applies to every host
    lab.yml           # applies to hosts in group 'lab'
    production.yml
  host_vars/
    ms-s1-max.yml     # applies only to host 'ms-s1-max'
```

```yaml
# group_vars/lab.yml
environment: lab
datasets_path: /mnt/tank
http_listen_port: 8080
```

Loaded automatically; no need to reference them anywhere. The inventory file stays clean — it's just the host/group structure.

## Patterns to limit what gets targeted

`ansible-playbook -i inventory.yml play.yml -l <pattern>` runs the play against only the matched hosts. Patterns:

| Pattern | Matches |
|---|---|
| `lab` | hosts in group `lab` |
| `lab:production` | hosts in `lab` OR `production` (union) |
| `lab:&production` | hosts in BOTH `lab` AND `production` (intersection) |
| `lab:!ms-s1-max` | hosts in `lab` EXCEPT `ms-s1-max` |
| `*.example.com` | hosts matching the glob |
| `ms-s1-max[0:2]` | inventory hosts indexed 0-2 |

The default if you don't specify `-l` is whatever the play's `hosts:` line declared.

## Dynamic inventories

When hosts come and go (cloud, k8s, CI), a static YAML file gets stale. Dynamic inventories run a script or plugin that produces inventory JSON on demand:

- AWS EC2: `amazon.aws.aws_ec2` plugin
- Hetzner Cloud: `hetzner.hcloud.hcloud` plugin
- Tailscale: community plugins exist
- Custom: any executable script that outputs valid JSON to stdout

For the homelab in this build, **a static YAML inventory is fine and easier to reason about**. Move to dynamic when you have more than ~20 hosts that come and go.

## Inventory for this build

The lab automation (`msai lab apply`, implemented in `src/msai_setup/lab/apply.py`) **generates an inventory file at runtime** from the lab config. Note there is **no** `ansible_become_password` — sudo is passwordless via bootstrap.yml — and auth is the lab keypair via `ansible_ssh_private_key_file`:

```yaml
# src/msai_setup/lab/ansible/inventory.generated.yml (auto-generated — do not edit by hand)
all:
  children:
    lab:
      hosts:
        test:
          ansible_host: 127.0.0.1
          ansible_port: 2222
          ansible_user: morten
          ansible_become: true
          ansible_ssh_private_key_file: target/lab_id_ed25519
          ansible_python_interpreter: /usr/bin/python3
          ansible_ssh_extra_args: >-
            -o StrictHostKeyChecking=accept-new
            -o UserKnownHostsFile=/dev/null
            -o IdentitiesOnly=yes
            -o LogLevel=ERROR
```

For the real MS-S1 MAX, you'd hand-write an inventory once — matching the "From lab to real MS-S1 MAX" section of `src/msai_setup/lab/README.md`:

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
          # no become password; key-based auth + passwordless sudo (via bootstrap.yml)
```

## Verifying inventory

```bash
# Show what Ansible understands the inventory to be
ansible-inventory -i inventory.yml --list
ansible-inventory -i inventory.yml --graph

# List hosts matching a pattern
ansible -i inventory.yml lab --list-hosts

# Ping all hosts in a group
ansible -i inventory.yml lab -m ansible.builtin.ping
```

`--graph` is the most useful for sanity-checking group structure:

```
@all:
  |--@lab:
  |  |--ms-s1-max-lab
  |--@production:
  |  |--ms-s1-max
  |--@ungrouped:
```

If a host shows up in `ungrouped` that you expected to be in `lab`, your inventory file has a typo.

## Common mistakes

### Putting variables in the wrong file

`group_vars/production.yml` doesn't apply to hosts in `lab`. Easy mistake when copy-pasting.

### Forgetting to set `ansible_python_interpreter`

Auto-discovery usually works. When it doesn't (custom Python paths, container hosts), set it explicitly:

```yaml
ansible_python_interpreter: /usr/bin/python3
```

Setting it shouldn't break anything; not setting it can leave you debugging weird `python` vs `python3` errors.

### Multiple inventories without merging

You can pass `-i inventory1.yml -i inventory2.yml` to merge. Or set `inventory = inv1,inv2` in ansible.cfg. Easy to forget when restructuring.

## Where to go next

- [Variables](variables.md) — what `vars:` and `group_vars/*.yml` do precisely.
- [Playbooks](playbooks.md) — how `hosts: lab` actually selects.
- [Vault](vault.md) — how to keep `ansible_become_password` out of plain YAML.
