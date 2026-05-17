# Testing &amp; Validation

How to know your playbooks work before they touch real hosts. From cheap (syntax check, `--check`) to thorough (molecule + a real test VM).

## Syntax check

```bash
ansible-playbook play.yml --syntax-check
```

Parses the YAML and verifies module names exist. Doesn't connect to hosts. Run this in CI; it catches typos in seconds.

## Dry-run with `--check`

```bash
ansible-playbook -i inventory.yml play.yml --check
```

Connects to hosts and goes through the motions, but modules report "would change" rather than changing anything. Most modules support this well; a few (`shell`, `command`) can't check meaningfully and run normally or skip.

Add `--diff` to see what would change in files:

```bash
ansible-playbook -i inventory.yml play.yml --check --diff
```

Output for a `template:` task:

```
TASK [render sshd config] ******************************************************
--- before: /etc/ssh/sshd_config.d/00-hardening.conf
+++ after:  generated rendered output

@@ -1,6 +1,7 @@
 Port 22
-PermitRootLogin yes
+PermitRootLogin no
 PubkeyAuthentication yes
```

Use `--check --diff` regularly on a configured host to detect drift: a clean diff means nothing has changed; non-empty diff means something on the host or in the playbook needs reconciling.

## `ansible-lint`

Lint your playbooks for style and common mistakes:

```bash
pipx install ansible-lint
ansible-lint scripts/lab/ansible/playbooks/

# Or via pre-commit
brew install pre-commit
cat > .pre-commit-config.yaml <<EOF
repos:
  - repo: https://github.com/ansible/ansible-lint
    rev: v25.x.x
    hooks:
      - id: ansible-lint
EOF
pre-commit install
```

ansible-lint catches:

- Missing `name:` on tasks
- Risky `shell`/`command` without `creates:`/`changed_when:`
- Hardcoded values that should be variables
- Deprecated module names
- Common YAML mistakes

Some rules are opinionated; tune via `.ansible-lint`:

```yaml
# .ansible-lint
skip_list:
  - yaml[line-length]              # we live with long lines
warn_list:
  - command-instead-of-shell       # warn but don't fail
```

## `molecule` — full integration testing

[molecule](https://ansible.readthedocs.io/projects/molecule/) is the heavy artillery: spin up a fresh container/VM, run your role/playbook against it, run verification tests, tear down. Per-driver: docker, podman, vagrant, etc.

```bash
pipx install --include-deps molecule molecule-docker

# Initialize a role with molecule config:
molecule init role my_role --driver-name docker

# Run the default scenario
cd my_role
molecule test
```

Molecule overkill for a homelab; **the VirtualBox/Multipass lab + the `--check --diff` workflow gets you 80% of the value at 10% of the complexity**. Save molecule for when you publish roles to Galaxy or maintain many playbooks across many environments.

## Testing locally with the lab VM

The pattern this build encourages:

```bash
# 1. provision a fresh VM
python3 scripts/lab/01_provision_multipass.py   # or 01_provision.py for VBox

# 2. apply a single playbook
python3 scripts/lab/02_apply.py bootstrap

# 3. check what changed
python3 scripts/lab/02_apply.py bootstrap --check --diff

# 4. snapshot before risky changes
multipass snapshot ms-s1-max-lab --name pre-experiment
# or:
VBoxManage snapshot ms-s1-max-lab take pre-experiment --pause

# 5. apply the risky thing
python3 scripts/lab/02_apply.py zfs -e topology=mirror

# 6. roll back if it goes wrong
multipass restore ms-s1-max-lab.pre-experiment
# or:
VBoxManage snapshot ms-s1-max-lab restorecurrent
```

This is the "real" test loop. Fast, real, and matches what you'll do for the actual MS-S1 MAX install.

## Idempotency testing

A well-written playbook should report `changed=0` on the second run:

```bash
ansible-playbook play.yml          # first run: maybe lots of changes
ansible-playbook play.yml          # second run: should be changed=0
```

If the second run reports changes, you have a non-idempotent task somewhere — typically a `shell:`/`command:` without `creates:`/`changed_when:`. Find and fix it.

## Variable validation

Use `ansible.builtin.assert` early in a playbook to check inputs:

```yaml
- hosts: lab
  pre_tasks:
    - name: validate required variables
      ansible.builtin.assert:
        that:
          - environment is defined
          - environment in ['lab', 'staging', 'production']
          - pool_name is defined
        fail_msg: |
          Missing or invalid required variables. Pass via -e or set in
          group_vars/. Required: environment in [lab, staging, production],
          pool_name (any string).
```

Better to fail early with a useful message than ten tasks in with a cryptic error.

## Smoke tests after deploy

After running a play, verify the result:

```yaml
- name: confirm sshd is reloadable
  ansible.builtin.command: sshd -t
  changed_when: false

- name: confirm service is listening
  ansible.builtin.wait_for:
    host: localhost
    port: 22
    timeout: 10

- name: hit the health endpoint
  ansible.builtin.uri:
    url: http://localhost:8080/health
    status_code: 200
  retries: 6
  delay: 5
```

These aren't separate test files — they're tasks at the end of your playbook that fail the play if the service doesn't come up correctly.

## CI hooking

The minimum for CI on an Ansible repo:

```yaml
# .github/workflows/ansible.yml
name: ansible
on: [push, pull_request]
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pipx install ansible-lint
      - run: ansible-lint scripts/lab/ansible/

  syntax-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pipx install ansible
      - run: |
          for play in scripts/lab/ansible/playbooks/*.yml; do
            ansible-playbook "$play" --syntax-check -i scripts/lab/ansible/inventory.example.yml
          done
```

For richer CI (run the playbook against a container), use molecule with the docker driver — but that's more setup than most homelabs need.

## Common mistakes

### Forgetting `--check` does NOT catch all issues

`--check` runs the modules but uses their check-mode behaviour. Some modules don't have great check-mode support; some custom `shell:` tasks lie about whether they changed something. `--check` is a sanity test, not a guarantee.

The real test is: run on a sacrificial host (the lab VM) before running on production. The lab is for exactly this.

### Comparing `--diff` of vault-encrypted files

Without the diff filter from [Vault](vault.md), `--diff` on a vault file shows the encrypted blob diff. Set up the `ansible-vault view` diff filter or you'll be guessing.

### Running ansible-lint with default rules and hating it

Cherry-pick. The default ruleset is opinionated; many rules don't fit homelab patterns. Use `skip_list:` aggressively at first, gradually adopt rules as they make sense.

## Where to go next

- [Troubleshooting](troubleshooting.md) — when tests reveal real bugs.
- [Integration](integration.md) — how this all fits with the lab automation.
