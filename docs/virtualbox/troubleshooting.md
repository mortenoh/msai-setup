# Troubleshooting

Symptom-first. Each entry has the exact error string you'll see, the cause, and the fix. Most of these I hit during the lab build, so the fixes are battle-tested rather than guessed.

## "Firmware type: failed - VERR_NOT_SUPPORTED"

In `~/VirtualBox VMs/<vm>/Logs/VBox.log` after a failed `startvm`. Usually accompanied by `VERR_MAIN_CONFIG_CONSTRUCTOR_COM_ERROR` from `VBoxManage startvm` itself.

**Cause**: on Apple Silicon, the IDE storage controller crashes the ARM EFI firmware. The firmware constructor enumerates attached storage, sees IDE, and bails.

**Fix**: don't use IDE on ARM. Move everything (disks AND ISOs) to SATA:

```bash
# Detach anything on IDE
VBoxManage storageattach test --storagectl IDE --port 0 --device 0 --medium none
VBoxManage storagectl test --name IDE --remove

# Attach ISOs to SATA instead
VBoxManage storageattach test --storagectl SATA --port 7 --device 0 \
    --type dvddrive --medium /path/to/iso
```

See [Apple Silicon](apple-silicon.md) for the full set of ARM quirks.

## "Failed to construct device 'vga' instance #0 (VERR_PGM_RAM_CONFLICT)"

In VBox.log after `startvm` fails.

**Cause**: on Apple Silicon (ARM), the default `vboxvga` graphics controller doesn't work — it conflicts with the ARM memory layout.

**Fix**: switch to `qemuramfb`:

```bash
VBoxManage modifyvm test --graphicscontroller qemuramfb
```

This must be set before `startvm`.

## "Cannot run the machine because its platform architecture x86 is not supported on ARM"

`VBoxManage startvm` exits non-zero with this in stderr.

**Cause**: the VM was created without `--platform-architecture arm` (defaulted to x86) on an Apple Silicon host.

**Fix**: platform architecture is set at `createvm` time only — you can't `modifyvm` it. Destroy and recreate:

```bash
VBoxManage unregistervm test --delete
VBoxManage createvm \
    --name test \
    --ostype Ubuntu_arm64 \
    --platform-architecture arm \
    --register
# ... reconfigure modifyvm, recreate disks, etc.
```

## "Unattended installation supported = no"

`VBoxManage unattended detect --iso ...` reports this for newer Ubuntu releases. `VBoxManage unattended install ...` then fails with `NS_ERROR_FAILURE` from `Prepare()`.

**Cause**: VBoxManage's bundled unattended-install templates only know about Ubuntu releases that shipped before the VirtualBox release. VBox 7.2.8 knows up to 25.04; 26.04 ISOs return "supported = no".

**Fix**: don't use VBoxManage's unattended install. Build a cloud-init CIDATA ISO + remaster the install ISO with `autoinstall` in GRUB yourself. See [Unattended install](unattended.md) for the full procedure, or use `msai lab create` which does it for you.

## "Connection timed out during banner exchange"

`ssh -p 2222 user@127.0.0.1` returns this.

**Cause**: VBox's NAT accepted the host-side TCP handshake (so `nc -zv` shows the port "open") but the guest's sshd isn't actually running yet — could be still installing, mid-reboot, or sshd genuinely not configured.

**Fix**:

1. Check the VM is actually running: `VBoxManage list runningvms`
2. Take a screenshot to see what state it's in: `VBoxManage controlvm test screenshotpng /tmp/test.png; open /tmp/test.png`
3. If installing: wait for the install to finish (3-5 min for Ubuntu autoinstall).
4. If installed but sshd not running: SSH in from the framebuffer (VRDE), check `systemctl status ssh`.
5. If sshd wasn't installed at all: your autoinstall config didn't include `openssh-server` in `packages:` or `install-server: true` under `ssh:`.

## "Permission denied (publickey)"

SSH connects but rejects your key.

**Cause**: the lab's user has the key, but you're trying to authenticate as a different user, or your key isn't the one cloud-init authorised.

**Fix**:

```bash
# Confirm the key cloud-init used was your lab key
xorriso -osirrox on -indev target/<vm>-cidata.iso \
    -extract /user-data /tmp/user-data
grep authorized-keys -A1 /tmp/user-data

# Confirm you're using the right user + identity file
ssh -v -p 2222 \
    -i target/lab_id_ed25519 \
    morten@127.0.0.1 'true'
# Look for: 'Offering public key: ED25519 SHA256:...'
# Then: 'Authenticated to 127.0.0.1 ([127.0.0.1]:2222) using "publickey"'
```

If you've destroyed and recreated the VM but kept your `~/.ssh/known_hosts`, you may also get host-key warnings — fix with `ssh-keygen -R '[127.0.0.1]:2222'` or set `StrictHostKeyChecking=accept-new` in your ssh args.

## "Extension pack '...' is incompatible with this VirtualBox version"

After upgrading VirtualBox.

**Cause**: VBox and the Extension Pack are version-locked. Upgrading VBox without re-installing the matching Extension Pack breaks the extpack.

**Fix**:

```bash
# macOS
brew upgrade --cask virtualbox-extension-pack

# Linux: download the matching version manually
VER=$(VBoxManage --version | sed 's/r.*//')
curl -L -o /tmp/extpack.vbox-extpack \
    "https://download.virtualbox.org/virtualbox/${VER}/Oracle_VM_VirtualBox_Extension_Pack-${VER}.vbox-extpack"
sudo VBoxManage extpack install --replace /tmp/extpack.vbox-extpack

# Confirm
VBoxManage list extpacks | grep -E '^Pack |^Version'
```

## "VBoxManage: error: Cannot open the medium..."

Trying to attach a disk that's not in VBox's media registry.

**Cause**: the `.vdi` file exists but VBox doesn't know about it (closed previously, or moved). Or the path is wrong.

**Fix**:

```bash
# Register the disk
VBoxManage closemedium disk /path/to/disk.vdi  # cleans up any stale registration
VBoxManage list hdds                            # see what VBox knows about
# Re-attach
VBoxManage storageattach test --storagectl SATA --port 0 --device 0 \
    --type hdd --medium /path/to/disk.vdi      # this implicitly registers it
```

## "VBoxManage: error: Failed to create the differencing image..."

Snapshot operations failing.

**Cause**: usually a disk attribute is preventing the snapshot. Common case: a disk attached `--mtype writethrough` (which excludes it from snapshots) is fine, but the VM may have multiple disks and you've explicitly excluded one of them.

**Fix**: check `mtype` on all attached disks:

```bash
VBoxManage showvminfo test --machinereadable | grep mtype
```

All disks must be in a snapshotable mode (`normal`, `immutable`, or have differencing already). For shareable/writethrough/readonly disks, exclude them from the snapshot or change their mode.

## "Snapshot 'X' is not deleted... merge failed"

Snapshot delete reports an error mid-merge.

**Cause**: the snapshot's delta file is huge and VBox ran out of memory or time. Or the destination (the parent disk) is read-only somehow.

**Fix**:

1. Ensure the VM is stopped: `VBoxManage controlvm test poweroff`
2. Try again: `VBoxManage snapshot test delete X`
3. If still fails, check the `.vbox` config for the snapshot tree state with `VBoxManage snapshot test list --details` and confirm parent/child relationships are sane.
4. As last resort: clone the VM (`VBoxManage clonevm`) which discards the snapshot history and produces a flattened standalone VM.

## "VBoxManage: error: Could not lock the media tree"

Multiple VBox operations running at once on the same media.

**Cause**: VBoxManage uses a global lock for media operations. Two `storageattach` or `closemedium` at the same time will conflict.

**Fix**: serialise them. In scripts, don't run multiple `VBoxManage` commands in parallel that touch storage.

## "VBoxManage: error: A session for the machine '...' is currently open"

Trying to modify a VM while another session has it open.

**Cause**: a stale `VBoxManage` process (or a crashed GUI) still holds the session.

**Fix**:

```bash
# See who has it
VBoxManage showvminfo test --machinereadable | grep ^Session
# If 'SessionType="GUI"' and you're not running the GUI, you have a stuck session.

# Try poweroff (which forces session close)
VBoxManage controlvm test poweroff

# If still stuck, the VBoxSVC process may need a kick:
pkill -f VBoxSVC
# Wait a few seconds; it restarts automatically. Try again.
```

## "X is not a valid command. Use --help"

Most commonly: a flag exists in a newer/older version of VBoxManage than yours.

**Fix**:

```bash
# What version do I have?
VBoxManage --version

# What does this subcommand actually accept?
VBoxManage <subcommand> --help

# Look in the official docs for that version specifically
# https://docs.oracle.com/en/virtualization/virtualbox/7.2/user/...
```

The user manual is version-pinned in the URL; make sure you're looking at the right one.

## VM hangs at boot

Different from "fails to start". The VM is running but stuck at GRUB, the kernel never loads, or systemd is wedged.

**Steps**:

1. **Screenshot**: `VBoxManage controlvm test screenshotpng /tmp/test.png; open /tmp/test.png`. See where it's hung.
2. **Logs**: `tail -f "$HOME/VirtualBox VMs/test/Logs/VBox.log"` shows what VirtualBox is seeing.
3. **Console**: enable VRDE (`--vrde on --vrdeport 3389 --vrdeaddress 127.0.0.1 --vrdeauthtype null`) and connect with an RDP client. Watch the kernel/init output.
4. **Serial console**: configure the guest to log to ttyS0, configure the VM with `--uart1 0x3F8 4 --uartmode1 file /tmp/test-console.log`, watch that file from the host. Captures everything pre-network.

## Disk I/O is mysteriously slow

The guest reports slow disk performance vs what you expect from native.

**Causes + fixes**:

- **Host filesystem encryption**: VBox runs slower on FileVault/LUKS-backed `.vdi` paths. Move VMs to an unencrypted area.
- **Dynamic allocation, first writes**: dynamic VDIs grow on demand; first write to a region is slow. Re-run the benchmark — second pass should be faster.
- **`--hostiocache on/off`**: with `on`, the host kernel caches; bursty writes look fast but aren't actually durable. With `off`, you're seeing real device performance.
- **Disk on a spinning USB drive**: especially on macOS, USB-attached HDDs as VM storage are very slow. Use NVMe.
- **VBox shared mutex contention**: lots of small simultaneous IOs can serialize. Larger sequential IOs are fine.

For lab work where you're not benchmarking, these usually don't matter — the VM does its job in a few minutes either way.

## "AssertionError: Storage size mismatch"

Rare, but seen when restoring a snapshot whose disk file has been modified outside VBox.

**Cause**: you (or another process) edited the `.vdi` file directly between snapshot and restore. VBox's snapshot metadata thinks the base disk has size X; actual is Y.

**Fix**: usually not recoverable cleanly. You can try:

```bash
VBoxManage closemedium disk /path/to/disk.vdi --delete
# (lose the snapshot's changes)
```

Or restore from a backup.

Lesson: don't edit `.vdi` files outside VBox.

## "VERR_VD_GENERIC_IO_ERROR" or "Host I/O cache: error"

Underlying host-disk problem. The host filesystem is failing reads/writes to the `.vdi`.

**Cause**: host disk full, host disk failing, network filesystem hiccup (if `.vdi` is on NFS), permissions changed.

**Fix**:

```bash
df -h .                              # disk space
ls -la *.vdi                         # permissions
dmesg | tail -50                     # host kernel may have logged disk errors
```

## When you give up and start over

The nuclear reset:

```bash
# Power-off + unregister + delete every VM
VBoxManage list vms | grep -oE '"[^"]+"' | tr -d '"' | while read vm; do
    VBoxManage controlvm "$vm" poweroff 2>/dev/null
    VBoxManage unregistervm "$vm" --delete 2>/dev/null
done

# Clear the entire VBox config (DESTRUCTIVE — nukes all settings)
rm -rf ~/.config/VirtualBox/                     # Linux
rm -rf ~/Library/VirtualBox/                     # macOS

# Clear all VM data
rm -rf ~/VirtualBox\ VMs/

# Restart VBoxSVC
pkill -f VBoxSVC
```

Then `VBoxManage --version` confirms it still works (it will — the binaries don't care about user config), and you're back to a clean slate.

## See also

- [Apple Silicon](apple-silicon.md) — the ARM-specific quirks all together
- [Unattended install](unattended.md) — install-time failure modes
- [VBoxManage CLI](vboxmanage.md) — what each command takes
