# Vault

`ansible-vault` is Ansible's built-in encryption layer. Use it for any value that shouldn't be in plain text in git: passwords, API tokens, TLS keys, the SSH host key Ansible pushes onto a target.

!!! note "The shipped playbooks do not use ansible-vault (yet)"
    None of the six playbooks in this repo (`bootstrap`, `ssh-hardening`, `ufw`, `zfs`, `docker`, `services`) needs a secret, so **nothing is vaulted today**. Sudo is passwordless (bootstrap.yml writes a NOPASSWD sudoers drop-in, so there is no `ansible_become_password`), and SSH is key-only. There is no `group_vars/vault.yml` and no 1Password lookup wired into the real playbooks.

    This page is kept as generic, accurate reference material for the day you add a playbook that *does* need a secret — an API token, a TLS key, a service password. At that point `ansible-vault` is the right built-in tool. Read it as "here's how you would" rather than "here's what this build does".

## When to use vault

- **Always for production secrets.** Database passwords, API tokens, TLS keys — *if you add a playbook that needs them*. The current playbooks don't.
- **Not needed for the shipped build.** Sudo is passwordless and SSH is key-only, so there's nothing to encrypt right now.
- **Not for non-secret config.** Hostnames, ports, retention policies — those live in regular `group_vars/`.

There's no "tier" between vault and plain — encrypt the whole file or don't. Pattern: keep your secret values in dedicated `vault.yml` files and reference them from regular vars files. That way diffs in the regular files stay reviewable.

## Setting a vault password

Vault uses a passphrase. You can store it in a few places:

```bash
# Interactive: prompt for the password every time
ansible-playbook play.yml --ask-vault-pass

# From a file (most common for CI / convenience)
echo 'my-vault-password' > ~/.ansible_vault_pass
chmod 600 ~/.ansible_vault_pass
ansible-playbook play.yml --vault-password-file ~/.ansible_vault_pass

# Or in ansible.cfg:
[defaults]
vault_password_file = ~/.ansible_vault_pass

# Or from a script that prints the password (e.g. fetch from 1Password):
chmod +x ~/.bin/vault-pass-from-1p
ansible-playbook play.yml --vault-password-file ~/.bin/vault-pass-from-1p
```

A script-based password file is the pattern that scales — see "Integration with 1Password / sops" below.

## Encrypting a whole file

```bash
# Create a new encrypted file (path is illustrative — this build ships no such file)
ansible-vault create src/msai_setup/lab/ansible/group_vars/lab/vault.yml

# Edit an existing one
ansible-vault edit src/msai_setup/lab/ansible/group_vars/lab/vault.yml

# Decrypt to stdout (just to view)
ansible-vault view src/msai_setup/lab/ansible/group_vars/lab/vault.yml

# Encrypt an existing plain file in place
ansible-vault encrypt some-secret-file.yml

# Decrypt in place (turns it back into plain)
ansible-vault decrypt some-secret-file.yml

# Re-key (change the vault password)
ansible-vault rekey some-secret-file.yml
```

An encrypted file's contents look like:

```
$ANSIBLE_VAULT;1.1;AES256
3565363762363266633165613961383139666264663366393234653236616533613961323239
3863306561336536353262656566303930313637393461630a626537353438303236623238...
```

Ansible decrypts in memory at play time. The on-disk form stays encrypted.

## Encrypted variables (inline)

Sometimes you want just one value encrypted, not the whole file:

```bash
ansible-vault encrypt_string 'super-secret-password' --name 'database_password'
```

Output:

```yaml
database_password: !vault |
  $ANSIBLE_VAULT;1.1;AES256
  39613363633838656532643536656334373064323539353337376533633763383035313764...
```

Paste that into any regular YAML file. Ansible recognises `!vault |` and decrypts at use time.

## Group-vars layout for secrets

The standard pattern: split each `group_vars/<group>.yml` into two files:

```
ansible/
  group_vars/
    lab/
      main.yml          # plain config — committed in clear
      vault.yml         # encrypted secrets
    production/
      main.yml
      vault.yml
```

Ansible auto-loads everything in `group_vars/<group>/`, regardless of file count or name.

```yaml
# group_vars/lab/main.yml (plain)
postgres_database: lab_db
postgres_user: lab_user
postgres_password: "{{ vault_postgres_password }}"     # reference into vault.yml
```

```yaml
# group_vars/lab/vault.yml (ansible-vault encrypted)
vault_postgres_password: 'super-secret-passphrase'
vault_traefik_acme_email: 'me@example.com'
```

Why the indirection? Because in `main.yml` you can see the variable names (audit-able), and the actual secret never appears in plain text anywhere. If you want to share `main.yml` with someone or reference it in docs, you can — the secret stays in vault.

## Multiple vault passwords (`--vault-id`)

For a project that has lab + production with different vault passwords:

```bash
# Create with a labelled vault-id
ansible-vault create --vault-id lab@~/.lab_vault_pass \
    group_vars/lab/vault.yml

ansible-vault create --vault-id prod@~/.prod_vault_pass \
    group_vars/production/vault.yml

# Use both at runtime
ansible-playbook play.yml \
    --vault-id lab@~/.lab_vault_pass \
    --vault-id prod@~/.prod_vault_pass
```

The vault-id syntax is `label@source`. `source` can be a path to a file or an executable script.

## Integration with 1Password / sops / Bitwarden

Hard-coding `vault_password_file = ~/.ansible_vault_pass` puts the master in plain on the laptop. Better: have the password-file be a **script** that fetches it from a real password manager:

```bash
#!/usr/bin/env bash
# ~/.bin/ansible-vault-pass-1p
op read 'op://Personal/ansible-vault/password'
```

```bash
chmod +x ~/.bin/ansible-vault-pass-1p

# Use it
ansible-playbook play.yml --vault-password-file ~/.bin/ansible-vault-pass-1p
```

Now the master never lives in plain on disk — it's in 1Password (which is in turn protected by your account passphrase + biometric). The script unlocks via `op` (1Password CLI) which is itself authenticated separately.

If you do add vaulted secrets to this build later, this is the recommended pattern: master password in 1Password, vault files in git, no plaintext secrets anywhere. (Nothing wires this up today — the shipped playbooks need no secrets.)

## Sops as an alternative

[sops](https://github.com/getsops/sops) is a more flexible secret-encryption tool that integrates with KMS / GPG / age. Some teams prefer it over ansible-vault because:

- It encrypts only **values** (the file stays YAML-shaped and diff-able).
- It supports multiple recipients (your laptop + a CI service account, both able to decrypt without sharing a single password).

If you're starting fresh and not committed to ansible-vault: consider sops + age, with `community.sops.load_vars` for Ansible integration. For this lab, ansible-vault is simpler and built-in; I'd only move to sops once you have multiple decrypters who shouldn't share a single passphrase.

## What to vault, what not to

| Type | Vault? |
|---|---|
| Plaintext password (sudo, db, ACME email) | Yes |
| API token | Yes |
| Private TLS key | Yes |
| Hostnames / IPs / ports | No — boring config |
| Username (not the password) | No — usually fine |
| `ansible_become_password` | Yes |
| Public SSH keys | No (they're public) |
| Private SSH keys (when storing them in repo to push to hosts) | Yes, encrypted with vault |

## Reviewing diffs of encrypted files

By default, a `git diff` of an encrypted vault file is useless (the AES blob changes on every edit). Configure a Git diff filter:

```bash
# In your repo's .gitattributes
group_vars/*/vault.yml diff=ansible-vault

# In ~/.gitconfig
git config --global diff.ansible-vault.textconv 'ansible-vault view'
```

Now `git diff` shows the decrypted contents. Don't commit `~/.gitconfig` with that filter on a shared machine — it bypasses encryption visually for anyone with the vault password.

## Common mistakes

### Committing the vault password file

If `.ansible_vault_pass` is in the repo, the encryption does nothing. Always:

```
# .gitignore
.ansible_vault_pass
.vault_pass*
```

### Editing vault.yml in your normal editor

If you `vim group_vars/lab/vault.yml` directly, you'll get the encrypted blob and likely corrupt it. Use `ansible-vault edit`.

### Forgetting to rekey after a leak

If a vault password is exposed, every encrypted file with that password is now compromised. `ansible-vault rekey` changes the wrapping passphrase, but **doesn't re-encrypt the underlying secrets**. Old git history still has the original blob, which the old password decrypts.

If a secret really leaks: rotate the underlying secret (change the DB password, re-issue the API token), THEN rekey the vault. Both steps.

## Where to go next

- [Variables](variables.md) — where vault values fit in the precedence picture.
- [Inventory](inventory.md) — `group_vars/<group>/vault.yml` placement.
- [Integration](integration.md) — why the shipped playbooks need no vaulted secrets today.
- The hands-on walkthrough: [`src/msai_setup/lab/README.md`](https://github.com/mortenoh/msai-setup/blob/main/src/msai_setup/lab/README.md) — the real, secret-free `msai` CLI + playbook workflow.
