# Secrets Management

How secrets are (and aren't) handled on this single-host homelab. This is a headless Ubuntu box running plain Docker Compose, KVM VMs, and local LLM inference — managed over SSH and Tailscale. There is no CI/CD pipeline, no Kubernetes, and no Docker Swarm here, so the enterprise patterns (GitHub Actions secrets, cloud KMS, Swarm secrets, OIDC federation) don't apply. Keep the tooling proportional to a one-box setup.

## What counts as a secret here

| Secret | Examples | Where it lives |
|--------|----------|----------------|
| Service passwords | Postgres/MariaDB passwords, Authentik admin, Nextcloud admin | Compose `.env` files + ansible-vault |
| API tokens | Tailscale auth key, restic/B2 keys, ntfy/Discord webhook URLs | ansible-vault, password manager |
| SSH keys | Host access, syncoid-to-backup-host key | 1Password SSH agent |
| TLS | ACME account/email for Traefik | ansible-vault (email), auto-managed certs on disk |
| ZFS encryption | Passphrase for any encrypted dataset | Password manager, multiple offline copies |

## The intended pattern: ansible-vault

Anything that needs to be a secret in this project belongs in **ansible-vault**, not scattered in plaintext files. The full reference — how to create/edit vaulted files, the `group_vars/<group>/vault.yml` split, and unlocking the vault master from 1Password — is documented in [Ansible -> Vault](../ansible/vault.md). The short version:

- Keep secret **values** in a dedicated encrypted `vault.yml`, referenced from a plaintext `main.yml` so variable *names* stay reviewable in git.
- Encrypt the whole vault file (`ansible-vault create`/`edit`), never hand-edit it in a normal editor.
- Store the vault master password in 1Password and unlock it via a `--vault-password-file` script (`op read ...`), so no plaintext master ever lands on disk. This is the recommended pattern for this build — see [Vault -> Integration with 1Password](../ansible/vault.md#integration-with-1password--sops--bitwarden).

```yaml
# group_vars/production/main.yml (plain, committed)
postgres_user: authentik
postgres_password: "{{ vault_postgres_password }}"   # reference into vault.yml

# group_vars/production/vault.yml (ansible-vault encrypted)
vault_postgres_password: 'super-secret-passphrase'
vault_traefik_acme_email: 'me@example.com'
```

!!! warning "Current state: no vaulted secrets are actually in place yet"
    Be honest about where the shipped automation stands today. The playbooks in `src/msai_setup/lab/ansible/` **do not** use ansible-vault — there are no `group_vars/` or `vault.yml` files in the repo, and `bootstrap.yml` configures the managed user with **passwordless sudo** (`/etc/sudoers.d/90-<user>` containing `<user> ALL=(ALL) NOPASSWD:ALL`). That's a deliberate convenience for a throwaway lab and a private, Tailscale-only box, but it means:

    - Ansible needs no `ansible_become_password`, so there's nothing vaulted for privilege escalation.
    - Any real service secret you add (DB passwords, ACME email, restic keys) is currently expected to live in Compose `.env` files, which are **not** committed. Moving those into a vaulted `group_vars/production/vault.yml` (per [Vault](../ansible/vault.md)) is the recommended hardening step before this box holds anything sensitive beyond a private LAN.

## Docker Compose secrets (plain Compose, not Swarm)

Services here run under `docker compose`, which reads secrets from environment variables and `.env` files — there are no Swarm `secrets:` objects or `/run/secrets/` mounts in this build.

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: authentik
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}   # from .env, never inline
```

```bash
# .env — sits next to the compose file, chmod 600, NEVER committed
POSTGRES_PASSWORD=super-secret-passphrase
```

Rules for `.env` files on this box:

- Keep them out of git (see [Git safety](#git-safety) below). They live under `~/docker/<service>/.env` on the host.
- `chmod 600` them; they're readable by your user and root only.
- Back them up as part of the rebuild capture — they're explicitly copied into the ZFS `rebuild-<date>` snapshot in the [Rebuild Checklist](rebuild-checklist.md) Phase 0, and noted in [Backup &amp; Recovery](backup.md) as credentials to keep in a password manager too.
- When you adopt ansible-vault, generate these `.env` values from vaulted variables at deploy time instead of hand-editing them.

## SSH keys

SSH is the management plane, and the syncoid replication jobs authenticate to the backup host over SSH. Store the keys in the 1Password SSH agent rather than as bare files on disk.

```bash
# Generate (Ed25519)
ssh-keygen -t ed25519 -C "morten@ms-s1-max"
```

| Key | Path | Permission |
|-----|------|------------|
| Private | `~/.ssh/id_ed25519` | 600 |
| Public | `~/.ssh/id_ed25519.pub` | 644 |
| Config | `~/.ssh/config` | 600 |

Preferred: keep the private key in **1Password** and let its SSH agent serve it, so the key material never sits unencrypted on the laptop:

```
# ~/.ssh/config
Host *
    IdentityAgent "~/Library/Group Containers/2BUA8C4S2C.com.1password/t/agent.sock"
```

The same 1Password account then protects both your SSH keys and the ansible-vault master password. See [1Password CLI](../bash/tools/1password-cli.md).

## Git safety

Nothing sensitive should reach the repo — not even a private one. Belt-and-suspenders:

```gitignore
# Environment / secrets
.env
.env.local
*.pem
*.key
# Ansible vault password files (the vault files themselves are safe to commit;
# the password that unlocks them is not)
.ansible_vault_pass
.vault_pass*
```

Run a scanner before committing so a stray token never lands:

```bash
brew install gitleaks
gitleaks detect --source .     # scan history
gitleaks protect --staged      # pre-commit check
```

Note that ansible-vault files (`vault.yml`) are **designed** to be committed — they're encrypted at rest. It's the vault *password* that must never be committed.

## ZFS dataset encryption passphrases

If you enable native ZFS encryption on any dataset (see [ZFS Encryption](../zfs/encryption.md)), the passphrase is unrecoverable if lost — there is no reset. Store it in the password manager **and** keep an offline copy in a second secure location, exactly as the [Rebuild Checklist](rebuild-checklist.md) credential table requires.

## Rotation and exposure

Small setup, so keep it simple:

- **Service password rotation**: update the vaulted value (or `.env`), redeploy the service, verify, done. No zero-downtime dance needed on a homelab.
- **SSH key rotation**: generate a new key, add it to the target's `authorized_keys` and to the backup host, test, then remove the old one.
- **If a secret leaks**: rotate the underlying secret first (change the DB password, re-issue the token), *then* rekey the vault if the vault password was what leaked. A `git filter-repo` to scrub history is secondary — anyone with a clone already has it, so rotation is what actually protects you.

## See Also

- [Ansible -> Vault](../ansible/vault.md) — the canonical how-to for this project's secret storage
- [1Password CLI](../bash/tools/1password-cli.md) — password manager + SSH agent
- [Rebuild Checklist](rebuild-checklist.md) — how secrets are captured and restored on a rebuild
- [Backup &amp; Recovery](backup.md) — credential storage as part of disaster recovery
