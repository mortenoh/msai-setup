# Installing Ansible

Ansible is installed only on your **control node** — the machine you run `ansible-playbook` from. There's nothing to install on the managed hosts beyond `openssh-server` and `python3`, both of which Ubuntu Server 26.04 ships by default.

## On macOS (control node = your Mac)

The cleanest install is via [Homebrew](https://brew.sh):

```bash
brew install ansible
```

This pulls in `ansible-core`, `ansible-lint`, and the most-used collections. Verify:

```bash
ansible --version
# ansible [core 2.18.x]
#   config file = /Users/.../ansible.cfg
#   python version = 3.13.x

ansible-playbook --version
ansible-galaxy --version
ansible-vault --version
```

Alternative: install via `pipx` for a single-user, isolated install:

```bash
pipx install --include-deps ansible
```

`--include-deps` pulls in the related CLI scripts (`ansible-playbook`, `ansible-galaxy`, etc.).

## On Linux (control node)

Most distros ship Ansible in their repositories, but the packaged version is often a major release or two behind upstream. Prefer a `pipx` install:

```bash
sudo apt install pipx
pipx ensurepath
pipx install --include-deps ansible
```

For the **system-wide** install (Ubuntu's `ppa:ansible/ansible`):

```bash
sudo apt install software-properties-common
sudo add-apt-repository --yes --update ppa:ansible/ansible
sudo apt install ansible
```

The PPA stays current with upstream releases.

## On the managed host (Ubuntu 26.04)

Nothing to install. SSH and Python 3 are present. If you've shrunk to "minimised" Ubuntu Server and Python 3 is absent, install it:

```bash
sudo apt install python3
```

Ansible's `setup` module needs Python 3 ≥ 3.6 on the target. Ubuntu 26.04 ships 3.12+; you're fine.

## Optional control-node tools

These aren't strictly necessary but make life better:

```bash
# Linter for playbook style
brew install ansible-lint              # macOS
pipx install ansible-lint              # any host

# Encrypted YAML editing helper
brew install gnupg                      # if you encrypt with GPG-backed vault passwords

# Pretty `ansible-playbook -vvv` output
pipx install rich

# Pre-commit hooks (run ansible-lint on commit)
brew install pre-commit
```

## sshpass — for the bootstrap-with-password phase

Until you've pushed an SSH key, Ansible falls back to password auth, which needs `sshpass` on the control node:

```bash
brew install hudochenkov/sshpass/sshpass        # macOS — not in main repo because of upstream license
sudo apt install sshpass                         # Linux
```

After bootstrap pushes your public key, you can uninstall `sshpass` if you like — every subsequent run uses key auth.

## Collections

Ansible's modules are bundled into "collections". Some are built-in (`ansible.builtin.*`) and ship with `ansible-core`. Others are installed via Galaxy.

This build uses:

```yaml
# scripts/lab/ansible/requirements.yml
collections:
  - name: community.general
  - name: ansible.posix
  - name: devsec.hardening
```

Install:

```bash
ansible-galaxy collection install -r scripts/lab/ansible/requirements.yml
```

Collections are stored in `~/.ansible/collections/` by default. To pin them inside the project tree (recommended for reproducibility):

```bash
ansible-galaxy collection install \
    -r scripts/lab/ansible/requirements.yml \
    -p scripts/lab/ansible/collections
```

Then the `ansible.cfg` in `scripts/lab/ansible/` points at that path so plays find them automatically.

## Verifying the install

The fastest sanity check is a `ping` against localhost over SSH:

```bash
# Make sure SSH to localhost works
ssh localhost echo ok

# Then ping via Ansible
ansible localhost -m ansible.builtin.ping
# localhost | SUCCESS => { "changed": false, "ping": "pong" }
```

If `ping` works, the install is fine. Move on to [Inventory](inventory.md).

## Updating Ansible

- Homebrew: `brew upgrade ansible`
- pipx: `pipx upgrade ansible`
- apt: `sudo apt update && sudo apt upgrade ansible`

Major releases of `ansible-core` ship every 6 months. Read the porting guide before crossing a major version on production playbooks.

## Uninstalling

- Homebrew: `brew uninstall ansible`
- pipx: `pipx uninstall ansible`
- apt: `sudo apt remove --purge ansible`

Removing Ansible doesn't touch managed hosts (since there's no agent). Your playbooks and inventories stay where they were.
