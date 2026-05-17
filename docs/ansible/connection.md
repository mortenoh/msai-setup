# Connection &amp; Privilege Escalation

How Ansible reaches managed hosts and gains root once it's in. Mostly about SSH, with `become:` (sudo) on top.

## Connection plugin

The default plugin is `ssh`. It uses your system `ssh` binary. Almost never needs changing.

Other plugins:

| Plugin | Use case |
|---|---|
| `ssh` | The default. Real machines, VMs, anything with sshd. |
| `local` | The control node itself. `hosts: localhost` automatically gets this. |
| `paramiko_ssh` | Pure-Python SSH; useful if your system ssh has quirks. |
| `docker` | Run tasks inside a docker container without SSH. |
| `community.general.lxd` | LXD containers. |
| `community.general.vagrant` | Vagrant VMs. |
| `community.docker.docker` | Same as `docker`. |

To override per-host:

```yaml
all:
  hosts:
    my-container:
      ansible_connection: docker
      ansible_host: my-running-container-name
```

## SSH configuration

### Identity (which key)

If your `~/.ssh/config` already has a `Host` block that picks the right key for the target, Ansible uses it. Otherwise, set explicitly:

```yaml
ansible_ssh_private_key_file: ~/.ssh/id_ed25519_lab
```

Or globally in `ansible.cfg`:

```ini
[defaults]
private_key_file = ~/.ssh/id_ed25519_lab
```

### Host key checking

Ansible verifies SSH host keys by default. For the lab where VMs come and go, you usually want this off:

```ini
# ansible.cfg
[defaults]
host_key_checking = False
```

Equivalent at the SSH level (per-host extra args):

```yaml
ansible_ssh_extra_args: >-
  -o StrictHostKeyChecking=accept-new
  -o UserKnownHostsFile=/dev/null
```

`accept-new` is a middle ground — accepts new keys automatically but still warns on changes. `UserKnownHostsFile=/dev/null` discards the known-hosts entirely (lab pattern).

For production: `host_key_checking = True` and keep a clean `known_hosts`.

### Control persistence

Ansible relies on OpenSSH's ControlMaster to multiplex many tasks over a single SSH connection. This is what makes a 50-task playbook complete in seconds rather than minutes.

Defaults are fine. To tune:

```ini
# ansible.cfg
[ssh_connection]
pipelining = True
control_path = ~/.ansible/cp/%%h-%%p-%%r
ssh_args = -o ControlMaster=auto -o ControlPersist=60s
```

`pipelining = True` is the biggest win: skips writing modules to a temp file on the target, instead pipes them over the existing SSH channel. Requires `requiretty` to be off in sudoers (default on most distros).

### Custom SSH options per host

```yaml
ms-s1-max-lab:
  ansible_host: 127.0.0.1
  ansible_port: 2222
  ansible_ssh_extra_args: '-o ConnectTimeout=30 -o PreferredAuthentications=publickey'
```

`ansible_ssh_extra_args` is the catch-all for "anything I'd normally put in `~/.ssh/config`".

## Become — privilege escalation

`become: true` means "use sudo (by default) to run the task as root":

```yaml
- hosts: lab
  become: true                      # whole play runs as root
  tasks:
    - apt: ...
```

Per-task override:

```yaml
- hosts: lab
  tasks:
    - name: read something
      ansible.builtin.command: cat /etc/hostname
      # no become — runs as ansible_user

    - name: write something
      ansible.builtin.copy:
        dest: /etc/foo
        content: bar
      become: true                  # only this task elevates

    - name: write as different user
      ansible.builtin.shell: psql ...
      become: true
      become_user: postgres
```

### Sudo password

Most setups have password-less sudo for the ansible user (it's how the bootstrap playbook configures it). For password-required sudo:

```bash
ansible-playbook play.yml --ask-become-pass
# or:
ansible-playbook play.yml -K
```

Or set in inventory (vault this):

```yaml
ansible_become_password: '{{ vault_become_password }}'
```

### Become methods (alternatives to sudo)

`become_method:` switches the elevation tool:

- `sudo` (default)
- `su`
- `doas` (BSDs)
- `pbrun`, `pfexec`, `runas` (Solaris/Windows)

For Linux you almost always want `sudo`. Make sure passwordless sudo is configured for the ansible user (bootstrap.yml in this build does that with a sudoers.d drop-in).

## SSH keys

### Pushing a new key to a host

Use the `authorized_key` module:

```yaml
- name: install my key
  ansible.builtin.authorized_key:
    user: "{{ ansible_user }}"
    key: "{{ lookup('file', '~/.ssh/id_ed25519.pub') }}"
    state: present
```

Idempotent — won't duplicate. For initial bootstrap (when the only way in is a password), see `scripts/lab/_ssh.py:push_authorized_key()` which wraps `ssh-copy-id`.

### Rotating keys

Add the new key first, verify it works, then remove the old one:

```yaml
- name: add new key
  ansible.builtin.authorized_key:
    user: morten
    key: "{{ lookup('file', '~/.ssh/id_ed25519_new.pub') }}"
    state: present

# Test with a new SSH session at this point — make sure new key works.

- name: remove old key
  ansible.builtin.authorized_key:
    user: morten
    key: "{{ lookup('file', '~/.ssh/id_ed25519_old.pub') }}"
    state: absent
```

Doing it in this order means you can't lock yourself out — if the new key fails, the old one still works.

## Jump hosts (ProxyJump)

When the target isn't directly reachable but a jump host is:

```yaml
backstage:
  ansible_host: 10.0.0.10
  ansible_user: morten
  ansible_ssh_extra_args: '-o ProxyJump=jump.example.com'
```

Or in `~/.ssh/config`:

```
Host backstage
  HostName 10.0.0.10
  User morten
  ProxyJump jump.example.com
```

Ansible inherits ssh-config.

## Tailscale-only targets

For the real MS-S1 MAX, you can SSH via its Tailscale MagicDNS name:

```yaml
ms-s1-max:
  ansible_host: ms-s1-max.tail-network.ts.net
  ansible_user: morten
```

Tailscale handles the routing. No special Ansible config needed — it's just SSH.

You can also use Tailscale SSH (`tailscale up --ssh`) which replaces sshd's authentication with Tailscale identity. Works with Ansible — the connection plugin doesn't know or care.

## Connection-related env vars

| Env var | Effect |
|---|---|
| `ANSIBLE_HOST_KEY_CHECKING` | Skip strict host-key check (`false`) |
| `ANSIBLE_SSH_RETRIES` | Retry count on ssh failure |
| `ANSIBLE_PIPELINING` | Set to `True` for the pipelining speedup |
| `ANSIBLE_NOCOWS` | Disable cowsay output (yes, really) |

## When things go wrong

### "UNREACHABLE — Failed to connect to the host via ssh"

```bash
# Try the raw SSH command first
ssh -vvv -p 2222 morten@127.0.0.1

# Confirm Ansible's view
ansible -i inventory.yml lab -m ping -vvv
```

`-vvv` on `ansible-playbook` shows the full SSH command being run. Usually the issue is wrong port, wrong user, missing key, host-key change.

### "sudo: a password is required"

The remote user doesn't have passwordless sudo for this command. Either:

- Fix the sudoers config (bootstrap.yml does this).
- Use `--ask-become-pass` or `ansible_become_password`.

### "pipelining requires requiretty to be disabled"

In `/etc/sudoers` (or via a drop-in), ensure `Defaults requiretty` is NOT set, or set `Defaults !requiretty`. Ubuntu doesn't enable it by default.

### Timeouts on slow hosts

```yaml
ansible_ssh_extra_args: '-o ConnectTimeout=30'
```

Or in `ansible.cfg`:

```ini
[defaults]
timeout = 30
```

## Where to go next

- [Inventory](inventory.md) — where these connection variables go.
- [Vault](vault.md) — for `ansible_become_password`.
- [Troubleshooting](troubleshooting.md) — connection-error diagnosis.
