# Unattended install

VirtualBox 7.0+ ships an `unattended install` subcommand that wraps "install Ubuntu/Debian/Fedora/etc. without clicking through the installer". It works well — when the bundled templates know about your specific OS version. When they don't (and they don't for Ubuntu 26.04 as of VBox 7.2.8), you do it yourself via cloud-init.

This page covers both: VBoxManage's built-in path, why it falls behind, and the approach the lab uses (self-built cloud-init `CIDATA` ISO + remastered install ISO with `autoinstall` in GRUB).

## The VBoxManage built-in path

```bash
VBoxManage unattended detect --iso /path/to/ubuntu-24.04.4-live-server-amd64.iso
# Detected '...' to be:
#   OS TypeId     = Ubuntu24_LTS_64
#   OS Version    = 24.04
#   OS Flavor     = Server
#   OS Languages  = ...
#   OS Hints      = ...
#   Unattended installation supported = yes

VBoxManage unattended install <vm> \
    --iso /path/to/iso \
    --user morten \
    --password 'changeme' \
    --full-user-name "Morten Hansen" \
    --hostname testvm.local \
    --time-zone Europe/Oslo \
    --locale en_US \                       # ll_CC ONLY, no .UTF-8
    --install-additions
```

What VBoxManage actually does:

1. Detects the ISO's flavour from its metadata.
2. Renders a `preseed.cfg` (Debian) or `autoinstall` (Ubuntu Subiquity) or kickstart (RHEL) from a built-in template, filling in your `--user`, `--hostname`, etc.
3. Builds a small ISO containing that config plus an init script.
4. Attaches the install ISO + the config ISO to the VM.
5. Modifies the install ISO's bootloader to add the kernel cmdline that tells the installer to use the config.
6. Boots the VM. Installer runs fully unattended.

Pros: one command. Works.

Cons:

- **Only works for ISOs the bundled templates know.** Each VirtualBox release ships templates for a snapshot of Ubuntu/RHEL/etc. Newer releases (Ubuntu 26.04 as of VBox 7.2.8) return `Unattended installation supported = no` and `Prepare()` fails.
- Custom autoinstall (extra packages, fancy partitioning, late-commands) requires templating that VBoxManage doesn't expose — you'd have to extract its templates and patch them.

For lab use against current Ubuntu, **the lab does it manually** instead.

## The lab's approach — cloud-init + remastered ISO

Modern Ubuntu (24.04+) uses **Subiquity** as the installer. Subiquity supports a "fully unattended" mode that reads a cloud-init `autoinstall:` block from:

1. The Ubuntu ISO itself (`/cdrom/autoinstall.yaml`), if it's there, OR
2. Any cloud-init `NoCloud` datasource — most easily, a CD-ROM labelled `CIDATA` containing `user-data` and `meta-data` files

You also need to tell the kernel at boot time to look for autoinstall. That's done by adding `autoinstall` to the kernel cmdline. The simplest way: edit the install ISO's GRUB config.

So the lab does three things:

1. **Build a CIDATA ISO** with cloud-init `user-data` (the autoinstall config) and `meta-data` (instance-id + hostname).
2. **Remaster the Ubuntu install ISO** to add `autoinstall` to GRUB's kernel cmdline.
3. **Boot the VM** with both ISOs attached. Subiquity sees the cmdline, finds the CIDATA volume, applies the autoinstall config, installs Ubuntu unattended, reboots.

### Step 1: build the CIDATA ISO

```bash
# Render user-data
cat > /tmp/user-data <<'EOF'
#cloud-config
autoinstall:
  version: 1
  interactive-sections: []
  refresh-installer:
    update: false
  locale: en_US.UTF-8
  keyboard: {layout: us}
  network:
    version: 2
    ethernets:
      enp0s3: {dhcp4: true}
      eth0:   {dhcp4: true}
  identity:
    realname: "Lab User"
    username: morten
    hostname: testvm
    password: "$6$rounds=4096$..."     # SHA-512 crypt, generated with `openssl passwd -6`
  ssh:
    install-server: true
    allow-pw: false
    authorized-keys:
      - "ssh-ed25519 AAAA... my-key"
  storage:
    layout: {name: direct}
  packages:
    - openssh-server
    - python3
  late-commands:
    - echo 'morten ALL=(ALL) NOPASSWD:ALL' > /target/etc/sudoers.d/90-morten
    - chmod 0440 /target/etc/sudoers.d/90-morten
  shutdown: reboot
EOF

# Render meta-data (instance-id is opaque; hostname is shown to cloud-init)
cat > /tmp/meta-data <<'EOF'
instance-id: iid-local-testvm
local-hostname: testvm
EOF

# Empty vendor-data (some Subiquity versions look for it)
touch /tmp/vendor-data

# Build the ISO — volume label MUST be CIDATA (case-insensitive)
xorriso -as mkisofs \
    -output /tmp/cidata.iso \
    -volid CIDATA \
    -joliet -rock \
    /tmp/user-data /tmp/meta-data /tmp/vendor-data
```

This is what `src/msai_setup/lab/cloudinit.py` does, parameterised by the lab config. The CIDATA ISO ends up ~400 KB.

### Step 2: remaster the Ubuntu ISO

Add `autoinstall` to GRUB:

```bash
# Extract grub.cfg from the Ubuntu ISO
mkdir -p /tmp/iso-mod
xorriso -osirrox on \
    -indev ubuntu-26.04-live-server-arm64.iso \
    -extract /boot/grub/grub.cfg /tmp/iso-mod/grub.cfg

# Original lines look like:
#   linux  /casper/vmlinuz  --- console=tty0
# We want:
#   linux  /casper/vmlinuz  autoinstall  --- console=tty0

chmod 0644 /tmp/iso-mod/grub.cfg     # extracted file is read-only
sed -i 's|\(linux\s\+/casper/vmlinuz\)\s\+\(.*---\)|\1 autoinstall \2|g' /tmp/iso-mod/grub.cfg
# Also handle hwe-vmlinuz
sed -i 's|\(linux\s\+/casper/hwe-vmlinuz\)\s\+\(.*---\)|\1 autoinstall \2|g' /tmp/iso-mod/grub.cfg

# Write a new ISO with the patched grub.cfg, preserving the boot record
xorriso -indev ubuntu-26.04-live-server-arm64.iso \
    -outdev ubuntu-26.04-live-server-arm64-autoinstall.iso \
    -boot_image any keep \
    -map /tmp/iso-mod/grub.cfg /boot/grub/grub.cfg \
    -commit
```

This is what `src/msai_setup/lab/iso.py:remaster_iso_for_autoinstall` does. Result: a new ISO that boots straight into autoinstall mode.

`-boot_image any keep` is the key flag — it preserves the original boot record so the remastered ISO is still bootable. Without it, the new ISO has no bootloader and the VM refuses to boot from it.

### Step 3: attach both ISOs and boot

```bash
VBoxManage storageattach test \
    --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium ubuntu-26.04-live-server-arm64-autoinstall.iso

VBoxManage storageattach test \
    --storagectl SATA --port 8 --device 0 \
    --type dvddrive --medium /tmp/cidata.iso

VBoxManage startvm test --type headless
```

Subiquity boots, sees `autoinstall` cmdline, looks for a NoCloud datasource, finds the CIDATA-labelled CD, applies the user-data, installs, and reboots.

After install, the ISOs auto-detach (the OS disk's GRUB takes over the boot chain).

## Why this approach is more robust

- **Any Ubuntu version works** — no dependency on VBox shipping a template for it
- **You control the autoinstall fully** — late-commands, custom packages, network config, storage layout
- **Reproducible** — the CIDATA ISO is deterministic from your user-data; commit it to a script
- **Forward-compatible** — when Ubuntu 28.04 ships, the same code works without VBox upgrades

The trade-off is more code to maintain. The lab's `cloudinit.py` (~120 lines) + `iso.py:remaster_iso_for_autoinstall` (~50 lines) is the price.

## Subiquity autoinstall — the full schema

The full schema lives at <https://ubuntu.com/server/docs/install/autoinstall-reference>. The minimum keys you actually need:

```yaml
#cloud-config
autoinstall:
  version: 1                            # always 1 for now
  interactive-sections: []              # empty = run everything unattended
  locale: en_US.UTF-8
  keyboard: {layout: us}
  network:                              # required, even if just DHCP
    version: 2
    ethernets:
      enp0s3: {dhcp4: true}
  identity:                             # required
    username: morten
    hostname: testvm
    password: "$6$..."                  # SHA-512 crypt
  ssh:                                  # optional but useful
    install-server: true
    authorized-keys: ["ssh-ed25519 ..."]
  storage:                              # required
    layout:
      name: direct                      # use the whole first disk
  packages:                             # optional
    - openssh-server
  late-commands:                        # optional, runs in the installer's chroot
    - echo "..." > /target/etc/foo
  shutdown: reboot                      # or 'poweroff'
```

The `storage:` block is where complexity hides. `layout: name: direct` is "use the first disk, default partition layout". For more control (LVM, encryption, multiple disks, specific partitions), the schema is documented but verbose. The lab keeps it simple.

`late-commands:` runs **inside the target system's chroot**, not the installer's live environment. Use `/target/...` paths (the installer mounts the target at `/target` during install) or `curtin in-target -- ...` to run commands in the actual target.

## Password generation

Subiquity wants a crypt-hashed password in `identity.password`, not plaintext:

```bash
openssl passwd -6 'changeme'
# $6$rounds=4096$<salt>$<hash>
```

Or in Python (3.13+ removed `crypt`; use `passlib` or shell out to openssl):

```python
import subprocess
result = subprocess.run(
    ["openssl", "passwd", "-6", "changeme"],
    capture_output=True, text=True, check=True,
)
crypted = result.stdout.strip()
```

The lab's `cloudinit.py:_crypt_password` does exactly this.

## Common autoinstall mistakes

### Whitespace + YAML

The lab learned this the hard way: building YAML with f-string + `textwrap.dedent` leaves subtle indentation bugs when interpolated values themselves contain lines. **Use `yaml.safe_dump(dict, default_flow_style=False)` instead** — it generates correct YAML by construction.

```python
# BAD — fragile
return textwrap.dedent(f"""\
    autoinstall:
      packages:
{package_lines}              # easy to misalign
      identity:
        password: "{crypted}"
""")

# GOOD — robust
import yaml
return "#cloud-config\n" + yaml.safe_dump(
    {"autoinstall": {
        "packages": packages,
        "identity": {"password": crypted, ...},
        ...
    }},
    default_flow_style=False, sort_keys=False,
)
```

### Wrong volume label

The NoCloud datasource specifically looks for `CIDATA` (case-insensitive). Other labels are ignored. `xorriso -volid CIDATA` is the right invocation.

### Missing `meta-data`

Even if it's just `instance-id: iid-something`, cloud-init wants it present.

### Network interface names

The default Subiquity expects `enp0s3` (the systemd-predictable name for the first VBox NIC). On other hypervisors it might be different (`enp1s0` etc.). The lab's user-data sets both `enp0s3` and `eth0` to DHCP so it works across naming schemes.

### `interactive-sections: []`

Without this (and with required keys missing), Subiquity falls back to interactive prompts. Always include `interactive-sections: []` for true unattended.

## Debugging an install that hangs at the menu

If Subiquity opens to the language menu instead of running unattended:

1. **Check the kernel cmdline.** Look at the GRUB menu (`screenshotpng`). Does `autoinstall` appear in the linux line? If not, the remaster didn't take. Check `xorriso -indev <iso> -extract /boot/grub/grub.cfg -` to see what's in the remastered ISO.
2. **Check the CIDATA ISO contents.** `xorriso -indev cidata.iso -ls` — should show `user-data`, `meta-data`, `vendor-data` at the root. Volume label should be `CIDATA`.
3. **Check the YAML.** `xorriso -osirrox on -indev cidata.iso -extract /user-data -` | python3 -c "import yaml, sys; yaml.safe_load(sys.stdin)"` — does it parse? Does it have the right top-level `autoinstall:` key?
4. **Check Subiquity's logs.** SSH in (the live installer's sshd runs even during install, on the same port; user is `installer`/no-key, so you need a way to read the framebuffer). Or boot interactively just to see what Subiquity says in `/var/log/installer/` on the target.

## See also

- [Storage](storage.md) — attaching the install ISO + CIDATA ISO
- [VMs](vms.md) — VM lifecycle
- [Apple Silicon](apple-silicon.md) — ARM-specific install quirks
- [Ubuntu autoinstall reference](https://ubuntu.com/server/docs/install/autoinstall-reference)
