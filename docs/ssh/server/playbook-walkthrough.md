# SSH hardening playbook walkthrough

This is the practical "what does the `ssh-hardening` Ansible playbook
actually do, line by line" companion to [SSH Server Hardening](hardening.md).
It walks through the directives the playbook drops into
`/etc/ssh/sshd_config.d/00-hardening.conf`, explains why each one
matters, and shows how to verify on a running host.

The playbook itself is at
`src/msai_setup/lab/ansible/playbooks/ssh-hardening.yml` and is
idempotent — running it twice is a no-op.

## What the playbook produces

A single drop-in at `/etc/ssh/sshd_config.d/00-hardening.conf`. The
handler reloads `sshd` only if the file changed, and a pre-reload
`sshd -t` check refuses to apply a config that wouldn't parse.

!!! note "Why the drop-in wins: parsed first, not loaded last"
    It is tempting to think the drop-in overrides the distro defaults because
    it is "loaded last." That is backwards. Ubuntu's `/etc/ssh/sshd_config`
    puts its `Include /etc/ssh/sshd_config.d/*.conf` line **near the top** of
    the file, so the contents of `00-hardening.conf` are parsed **before**
    most of the directives in the base file. And sshd is **first-match-wins**:
    for most directives, the *first* value seen for a directive is the one
    that takes effect and later occurrences are ignored. So the drop-in wins
    precisely because it is parsed **first** (via that early `Include`), not
    because it loads later. This is also why the `00-` prefix matters — among
    the drop-ins, lexical order decides who is parsed first, and the earliest
    file wins each directive.

> **Order matters**: the playbook depends on your public key already
> being authorised (`bootstrap.yml` puts it there during provisioning).
> Disabling password auth before keys are in place is how you lock
> yourself out.

## The directives

### Connectivity baseline

```ini
Port 22
AddressFamily any
```

`Port 22` is intentional — moving SSH to a non-standard port is
security theatre on a private network. If you must hide from internet
scanners, front sshd with WireGuard / Tailscale instead. `AddressFamily
any` lets the server listen on both IPv4 and IPv6; restrict only if
you have a specific reason.

### Authentication policy

```ini
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
ChallengeResponseAuthentication no
KbdInteractiveAuthentication no
PermitEmptyPasswords no
UsePAM yes
MaxAuthTries 3
LoginGraceTime 60
```

The four loud-and-clear rules:

- **No root over SSH.** Use `sudo` from an unprivileged account.
- **No password auth.** Keys only. Eliminates the entire "brute force
  weak password" attack class.
- **No keyboard-interactive / PAM password prompts** sneaking back in.
  `KbdInteractiveAuthentication` and `ChallengeResponseAuthentication`
  are both off because PAM can offer password-style prompts via either
  unless you nail them down.
- **`MaxAuthTries 3`** caps per-connection auth attempts. Combined with
  `LoginGraceTime 60` (drop the connection if it doesn't authenticate
  in 60 s), this makes scripted attempts expensive.

`UsePAM yes` is left enabled because account/session PAM hooks
(e.g. `pam_limits`, audit logging, `pam_motd`) still need to run.

### Reduce what sshd offers

```ini
X11Forwarding no
AllowTcpForwarding no
AllowAgentForwarding no
AllowStreamLocalForwarding no
PermitTunnel no
```

If you don't use a feature, it shouldn't be available — there are
known exploits (CVE-2023-38408 was an agent-forwarding RCE) that only
work if the corresponding switch is on.

Turn one back on per-user via `Match` if you actually need it:

```ini
Match User morten
    AllowAgentForwarding yes
```

### Session limits

```ini
ClientAliveInterval 300
ClientAliveCountMax 2
MaxSessions 2
MaxStartups 10:30:60
LogLevel VERBOSE
```

- **`ClientAliveInterval 300` + `ClientAliveCountMax 2`** drops dead
  connections after ~10 minutes of silence. Without this, an
  abandoned laptop keeps your session pinned forever.
- **`MaxSessions 2`** caps multiplexed sessions per connection — limits
  blast radius from a compromised client.
- **`MaxStartups 10:30:60`**: at 10 pre-auth connections, start dropping
  30% of new ones; reject all once we hit 60. This is the cheap defence
  against connection-flood DoS.
- **`LogLevel VERBOSE`** writes the *fingerprint* of the key used on
  every successful login. Indispensable for "which key actually let
  this in?" forensics.

### Modern crypto

```ini
KexAlgorithms sntrup761x25519-sha512@openssh.com,curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
HostKeyAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256
PubkeyAcceptedAlgorithms ssh-ed25519,ssh-ed25519-cert-v01@openssh.com,rsa-sha2-512,rsa-sha2-256
```

Three things going on:

- **Post-quantum-hybrid KEX**: `sntrup761x25519-sha512@openssh.com`
  combines classical X25519 with a lattice-based KEM so traffic that's
  recorded today can't be decrypted by a future quantum attacker. Both
  endpoints must support it; modern OpenSSH does.
- **AEAD ciphers only**: chacha20-poly1305 and AES-GCM. No CBC-mode,
  no plain CTR — those are vulnerable to padding-oracle / MAC-tag
  forgery in adversarial conditions.
- **ETM MACs**: encrypt-then-MAC is the correct order. The `-etm@`
  suffix isn't decorative; without it sshd would default to
  encrypt-and-MAC for some algorithms.

The `*Algorithms` lines drop ssh-rsa with SHA1, DSA, ssh-rsa-cert-v01
(SHA1 cert chain), and anything else CIS-style scanners flag.

## Verify the result

After running the playbook, query the *effective* sshd config (not
just the drop-in file — `sshd -T` shows the merged final state):

```bash
sudo sshd -T 2>/dev/null | grep -iE \
  '^(permitroot|password|pubkey|kbd|maxauth|clientalive|allow(tcp|agent)forwarding|x11|ciphers|macs|kexalgorithms)' \
  | sort
```

Expected output on a lab VM after `msai lab apply ssh-hardening`:

```
allowagentforwarding no
allowtcpforwarding no
ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com,aes128-gcm@openssh.com
clientalivecountmax 2
clientaliveinterval 300
kbdinteractiveauthentication no
kexalgorithms sntrup761x25519-sha512@openssh.com,...
macs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
maxauthtries 3
passwordauthentication no
permitrootlogin no
pubkeyacceptedalgorithms ssh-ed25519,...,rsa-sha2-512,rsa-sha2-256
pubkeyauthentication yes
x11forwarding no
```

### Sanity checks from the client

Try a password auth attempt — it should fail before sshd asks you:

```bash
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no morten@<host>
# expected: "Permission denied (publickey)."
```

Confirm root login is blocked even with the right key:

```bash
ssh -i ~/.ssh/lab_id_ed25519 root@<host>
# expected: "Permission denied (publickey)."
```

Confirm forwarding is disabled:

```bash
ssh -L 9999:localhost:11434 morten@<host>
# expected: "channel 0: open failed: administratively prohibited: open failed"
```

### Run the audit tool

[ssh-audit](https://github.com/jtesta/ssh-audit) cross-checks against a
known-good policy and flags anything you missed:

```bash
pip install ssh-audit
ssh-audit -p 22 <host>
```

You should see all green; if you don't, treat the warnings as a TODO.

## Applying the same playbook to the real box

The playbook is hardware-agnostic — same file runs against the lab VM
and against the MS-S1 MAX itself. Two prerequisites:

1. Your public key is already in
   `/home/morten/.ssh/authorized_keys` on the target. The provisioner
   handles this for the lab; on a fresh MS-S1 MAX install, copy it in
   manually first via `ssh-copy-id` while password auth is still
   enabled.
2. You can reach the box from your laptop on port 22 (no firewall
   between you).

Then:

```bash
ansible-playbook -i prod-inventory.yml playbooks/ssh-hardening.yml
```

Where `prod-inventory.yml` points `lab` (or whatever group your real
host is in) at the production IP/hostname.

## Re-running and updating

The playbook is idempotent — running it a second time produces no
diff. If you edit the directive list in the playbook, the next run
produces a precise diff (what changed, what stayed), and `sshd -T` /
the audit tool confirm the new effective state.

If you ever need to roll a change back: delete
`/etc/ssh/sshd_config.d/00-hardening.conf` and reload sshd. The distro
defaults take over.

## See also

- [SSH Server Hardening](hardening.md) — the full reference, including
  fail2ban / 2FA / chroot-SFTP options the lab playbook intentionally
  does not enable
- [SSH Configuration](configuration.md) — every sshd_config directive
- `src/msai_setup/lab/ansible/playbooks/ssh-hardening.yml` — the
  authoritative source
