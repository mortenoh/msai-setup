# Troubleshooting

Symptom-first. When something goes wrong, the workflow:

1. Re-run with `-vv` (or `-vvv` for SSH-level detail).
2. Read the actual error message — Ansible's errors are usually accurate, just verbose.
3. Try the operation manually via SSH to confirm it's not Ansible-specific.

## `-v` levels

```bash
ansible-playbook play.yml         # default: ok/changed/failed per task
ansible-playbook play.yml -v      # show registered values, task results
ansible-playbook play.yml -vv     # also: gather_facts details, module debug
ansible-playbook play.yml -vvv    # SSH command + exit code per task — the big one
ansible-playbook play.yml -vvvv   # connection plugin internals
```

`-vvv` is the workhorse. It shows the actual `ssh -i KEY -o ... user@host /usr/bin/python3 ...` invocation Ansible runs, which is what to compare against running by hand.

## "Host unreachable"

```
fatal: [ms-s1-max-lab]: UNREACHABLE! => {
    "changed": false,
    "msg": "Failed to connect to the host via ssh: ssh: connect to host 127.0.0.1 port 2222: Connection refused",
    "unreachable": true
}
```

Try SSH directly:

```bash
ssh -p 2222 -vvv morten@127.0.0.1
```

Common causes:

- VM not running / not booted yet.
- Wrong port (NAT forward not configured).
- Wrong user.
- SSH key not yet authorised (use password fallback or push the key first).
- Host key changed (delete the entry from known_hosts, or set `host_key_checking = False` in the lab).

## "Failed to connect — Permission denied (publickey)"

The user exists, SSH is up, but key auth failed. Either:

- Key not in `~/.ssh/authorized_keys` on the host.
- Wrong key offered (run `ssh -vvv` and check which keys it tries).
- Permissions on `~/.ssh/` are wrong (must be 700 / 600).
- `PubkeyAuthentication no` in sshd_config (the hardening playbook turns this on, but if something else turned it off...).

The bootstrap flow: `msai lab apply` (via `src/msai_setup/lab/ssh.py:push_authorized_key()`) first pushes the key using the install-time password (sshpass + ssh-copy-id). After that, every other run is key-auth.

## "Missing sudo password"

```
fatal: [...]: FAILED! => {
    "msg": "Missing sudo password"
}
```

Either:

- The remote user doesn't have passwordless sudo for this command — fix the sudoers (bootstrap.yml does this once).
- You forgot to provide one. `-K` / `--ask-become-pass`, or vault `ansible_become_password`.

## "Module not found"

```
ERROR! couldn't resolve module/action 'community.general.ufw'
```

The collection isn't installed:

```bash
ansible-galaxy collection install community.general
# Or via requirements.yml
ansible-galaxy collection install -r src/msai_setup/lab/ansible/requirements.yml
```

Confirm:

```bash
ansible-galaxy collection list | grep community.general
```

## "An exception occurred during task execution"

The module itself failed. Read the error carefully — it's usually a real condition on the host:

```
fatal: [...]: FAILED! => changed=false
  cmd:
  - zpool
  - create
  - tank
  - /dev/sdb
  msg: non-zero return code
  stderr: |-
    invalid vdev specification
    use '-f' to override the following errors:
    /dev/sdb is part of active pool 'oldpool'
  rc: 1
```

Here ZFS refuses to create a pool because the disk is already in use. Fix the actual state on the host (wipe the disk, destroy the old pool, whatever), then re-run.

## "FAILED! => Could not import module"

The remote host is missing a Python dependency the module needs. Install on the host:

```yaml
- name: install python deps the postgres module needs
  ansible.builtin.apt:
    name: python3-psycopg2
```

`community.docker` for example needs `python3-docker` on the target. Add it before any task that uses the module.

## "set_fact: undefined variable in template"

```
fatal: [...]: FAILED! => {
    "msg": "An unhandled exception occurred while templating '{{ foo.bar }}'.
            Error: 'dict object' has no attribute 'bar'"
}
```

The thing you tried to dereference isn't there. Debug with:

```yaml
- name: debug what foo actually is
  ansible.builtin.debug:
    var: foo
```

Common culprit: the registered variable is from a `failed_when: false` task that didn't actually run successfully, so the expected output fields aren't populated.

Use `default()` filter for optional fields:

```jinja
{{ foo.bar | default('fallback') }}
```

## "FAILED! => the resolved binary 'python3' is not on the path"

The remote host is too minimal — `python3` isn't installed (rare on Ubuntu, more likely on Alpine/minimal containers).

```bash
# Bootstrap python manually before Ansible
ssh user@host 'sudo apt update && sudo apt install -y python3'
```

Or use Ansible's `raw` module which doesn't need Python:

```yaml
- hosts: lab
  gather_facts: false
  tasks:
    - name: install python
      ansible.builtin.raw: |
        which python3 || apt-get update && apt-get install -y python3
      changed_when: false
```

## "Idempotent run reports changes"

You ran the play once, then again, and the second run shows `changed > 0`. Means some task isn't idempotent.

Find it:

```bash
ansible-playbook play.yml -v | grep -A2 'changed:'
```

Common culprits:

- `shell:` / `command:` without `creates:`, `removes:`, or `changed_when:`.
- `lineinfile:` matching slightly different content each run.
- `template:` where the template renders different output due to a time-dependent variable.

Add the right idempotency hook:

```yaml
- name: install thing
  ansible.builtin.shell: |
    curl ... | tar xz
  args:
    creates: /usr/local/bin/the-binary
```

## "Host key verification failed"

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!     @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
```

A VM you destroyed and recreated has a new host key. Either:

```bash
# Clean the offending entry
ssh-keygen -R '[127.0.0.1]:2222'

# Or for the lab, set host-key-checking off in ansible.cfg
[defaults]
host_key_checking = False
```

## Slow plays — too much SSH overhead

Common with many small tasks. Fixes:

- Enable pipelining: `pipelining = True` in `ansible.cfg`.
- Enable ControlPersist: should be on by default; check `ssh_args` in ansible.cfg.
- Use `forks = 10` (or higher) to parallelise across hosts.
- Profile: `ANSIBLE_CALLBACKS_ENABLED=profile_tasks ansible-playbook ...`.

If a single task is slow on a single host, profile inside the host — usually it's apt waiting on locks or network.

## "Task includes an option with an undefined variable"

You wrote `{{ foo }}` somewhere where `foo` isn't set. Debug:

```bash
ansible-playbook play.yml -vv
```

Look at the failed task. The template/expression that broke is in the error message. Either:

- Define the variable in `group_vars/`/`host_vars/`/`-e`.
- Use `default()`: `{{ foo | default('') }}`.
- Add `when: foo is defined` to the task.

## Connection times out repeatedly

Some VMs / cloud images need a moment after boot before SSH responds. Configure retry behaviour:

```yaml
ansible_ssh_retries: 6
ansible_ssh_extra_args: '-o ConnectTimeout=30'
```

Or in `ansible.cfg`:

```ini
[defaults]
timeout = 30

[ssh_connection]
retries = 6
```

## "Encryption error / vault password incorrect"

```
ERROR! Attempting to decrypt but no vault secrets found
```

Pass a vault password:

```bash
ansible-playbook play.yml --ask-vault-pass
# or:
ansible-playbook play.yml --vault-password-file ~/.ansible_vault_pass
```

For a script-based vault password (1Password etc.), make sure the script is executable and prints the password to stdout with no trailing junk.

## When Ansible itself is the bug

It's rare, but happens (especially with new collections / modules just out of beta). Try:

- Downgrade the collection: `ansible-galaxy collection install community.general:8.6.0`
- Run the equivalent command manually on the host; if it works, the module is the issue.
- Check the [collection's GitHub issues](https://github.com/ansible-collections/community.general/issues) for your symptom.

## Where to get more help

- `ansible-doc <module>` — canonical reference for any module.
- `ansible-config dump` — show every config setting and where it came from.
- [Ansible docs](https://docs.ansible.com/) — the official ones; spotty in places but authoritative.
- [Ansible community on Matrix / Discord / Reddit](https://docs.ansible.com/ansible/latest/community/communication.html).

## Where to go next

- [Connection](connection.md) — SSH/become layer specifically.
- [Testing](testing.md) — catch problems before they hit production.
- [Integration](integration.md) — how this all fits the lab.
- The hands-on walkthrough: [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) — reproduce and debug against a throwaway `msai` VM.
