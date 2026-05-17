# Automation

Everything VirtualBox can do is in `VBoxManage`. That makes it trivial to script — bash, Python, Ansible, whatever. This page covers the patterns the lab uses and a few that didn't make the cut but are useful in adjacent setups.

## Patterns

### Idempotency first

Every operation should be safe to re-run. The skeleton:

```bash
# Stop and remove if exists
if VBoxManage list vms | grep -q "\"$NAME\""; then
    VBoxManage controlvm "$NAME" poweroff 2>/dev/null || true
    sleep 1
    VBoxManage unregistervm "$NAME" --delete
fi
# (Re)create
VBoxManage createvm --name "$NAME" --ostype Ubuntu_64 --register
# ...
```

In Python, `vm_exists(name)` and `vm_running(name)` helpers in the lab's `_vbox.py` express this directly. Each setup function checks state before acting.

### Wait for SSH, not just port-open

VirtualBox's NAT forwards accept the TCP handshake on the host port even before the guest's sshd is listening. Don't trust a port-open probe — actually try to authenticate:

```bash
# WRONG — false positive on NAT
nc -z 127.0.0.1 2222

# BETTER — at least read the SSH banner
(echo "" | nc -w 2 127.0.0.1 2222) 2>&1 | grep -q '^SSH-'

# BEST — actually authenticate
ssh -p 2222 -i key -o BatchMode=yes -o ConnectTimeout=5 user@127.0.0.1 true
```

The lab's `_ssh.wait_for_ssh` polls the third form. Also: the Ubuntu live installer runs sshd on the same port during install (same banner!), so the only way to know the guest's installed system is up is to authenticate as your lab user (which the installer's sshd doesn't accept).

### Parse `--machinereadable`, never the human form

```bash
# BAD — `head -1` could fail if VirtualBox changes the format
VBoxManage showvminfo test | grep "VRAM size" | awk '{print $3}'

# GOOD — stable key=value format
VBoxManage showvminfo test --machinereadable | awk -F= '/^VRAM=/{print $2}'
```

For complex queries, `--machinereadable` is essentially a flat ini file (quotes around values that need them). Easy to parse in any language.

In Python:

```python
def showvminfo(name: str) -> dict[str, str]:
    out = subprocess.run(
        ["VBoxManage", "showvminfo", name, "--machinereadable"],
        capture_output=True, text=True, check=True,
    ).stdout
    info = {}
    for line in out.splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            info[key.strip()] = value.strip().strip('"')
    return info
```

The lab's `_vbox.showvminfo()` is exactly this.

### Errors are valuable; capture and inspect

`VBoxManage` exits non-zero with a useful stderr on every error. Wrap subprocess calls to surface it:

```python
result = subprocess.run(
    cmd, capture_output=True, text=True, check=False,
)
if result.returncode != 0:
    raise RuntimeError(
        f"VBoxManage failed (exit {result.returncode}): {' '.join(cmd)}\n"
        f"stderr: {result.stderr.strip()}\n"
        f"stdout: {result.stdout.strip()}"
    )
```

The lab's `_vbox._run` does this. Saves an enormous amount of debugging time when a flag is wrong.

### Provision once, snapshot, iterate

The expensive thing in a lab is the Ubuntu install (3-5 minutes). Snapshot it:

```bash
VBoxManage snapshot test take "fresh-install" --pause
```

Now subsequent experiments restore back to "fresh Ubuntu" in seconds. Build snapshots in a tree:

```
fresh-install
├── zfs-stripe       (after `msai lab apply zfs`)
├── zfs-mirror       (after `msai lab apply zfs -e topology=mirror`)
└── full-stack       (after `msai lab apply` with everything)
```

`msai lab snapshot <name>` + `msai lab restore <name>` wrap this.

### Background long operations

`startvm` returns immediately; the actual install takes minutes. Don't block waiting — let the operation run in background while you do other work, and signal when it's ready.

```bash
VBoxManage startvm test --type headless &     # backgrounded shell job
SSH_WAIT_PID=$(
    nohup bash -c 'while ! ssh -i key -o BatchMode=yes -o ConnectTimeout=3 \
        -p 2222 user@127.0.0.1 true 2>/dev/null; do sleep 30; done; \
        echo SSH up' > /tmp/ssh-wait.log 2>&1 < /dev/null & echo $!
)
```

The lab's Python pipeline uses subprocess.Popen + polling for the same shape.

## VBoxManage from Python

Three integration patterns, from least to most invasive:

### subprocess wrapper

```python
import subprocess

def vbm(*args: str, check: bool = True) -> str:
    result = subprocess.run(
        ["VBoxManage", *args],
        capture_output=True, text=True, check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(f"VBoxManage failed: {result.stderr}")
    return result.stdout
```

The lab uses this. Pros: portable, no extra deps, works everywhere VBoxManage works. Cons: shells out for each call (small overhead, but it adds up if you make thousands).

### vboxapi (Python bindings)

VirtualBox ships Python bindings as part of the SDK:

```python
from vboxapi import VirtualBoxManager
vbox = VirtualBoxManager(None, None).getVirtualBox()
for m in vbox.machines:
    print(m.name, m.OSTypeId)
```

These live in `/Applications/VirtualBox.app/Contents/MacOS/sdk/installer/vboxapisetup.py` on macOS. Install via `pip install -e .` from that directory. Pros: no subprocess overhead, full IVirtualBox COM-style API. Cons: more code, version-tied to VirtualBox, less portable. Worth it only if you're hammering VBox with hundreds of calls per minute.

### `pyvbox` wrapper

A community wrapper over `vboxapi`:

```python
import virtualbox
vbox = virtualbox.VirtualBox()
session = virtualbox.Session()
machine = vbox.find_machine("test")
progress = machine.launch_vm_process(session, "headless", [])
progress.wait_for_completion(-1)
```

Higher-level API, but you still need `vboxapi` installed underneath. For the lab's use case, subprocess is plenty.

## The lab's architecture (reference)

```
src/msai_setup/lab/
  vbox.py            # subprocess wrapper around VBoxManage. Functions:
                     # require_vboxmanage, list_vms, vm_exists, vm_running,
                     # showvminfo, create_vm, configure_vm, add_ssh_port_forward,
                     # create_disk, ensure_storage_controller, attach_disk,
                     # attach_iso, start_headless, power_off, acpi_power_button,
                     # snapshot_take, snapshot_restore_current, snapshot_list,
                     # enable_vrde, unregister_and_delete

  iso.py             # ISO download (with SHA256 verify) + remaster for
                     # autoinstall (extract grub.cfg, patch with `autoinstall`,
                     # repack with -boot_image any keep)

  cloudinit.py       # render Subiquity autoinstall user-data via yaml.safe_dump,
                     # build CIDATA ISO via xorriso

  ssh.py             # ensure_lab_keypair (auto-generate dedicated ed25519),
                     # wait_for_ssh (real authentication, not just banner),
                     # ssh_args (build the canonical ssh CLI invocation)

  state.py           # JSON-backed state file at target/<name>-state.json
                     # tracks phase completion

  instance.py        # current-instance pointer (target/.current);
                     # list_instances() enumerates from filesystem

  config.py          # env-driven LabConfig dataclass with architecture-aware
                     # defaults (arm64 vs amd64 -> different ISO URL, different
                     # ostype, different platform)

  provision.py       # main() - the whole "create a VM" flow
  apply.py           # run_apply() - ansible-playbook invocations
  pipeline.py        # run_pipeline() - chain provision + apply
  cli.py             # Typer commands under `msai lab`
```

Top-level `msai` CLI in `src/msai_setup/cli.py` exposes `create`, `list`, `ls`, `use`, `start`, `stop`, `ssh`/`login` — the lab is a subcommand group via `app.add_typer(lab_app, name="lab")`.

## Useful one-liners

Things that come up often, in working bash:

```bash
# Power off everything
VBoxManage list runningvms | grep -oE '"[^"]+"' | tr -d '"' | xargs -n1 -I{} VBoxManage controlvm {} poweroff

# Unregister + delete everything (DESTRUCTIVE)
VBoxManage list vms | grep -oE '"[^"]+"' | tr -d '"' | xargs -n1 -I{} VBoxManage unregistervm {} --delete

# Show RAM usage of all running VMs
VBoxManage list runningvms | grep -oE '"[^"]+"' | tr -d '"' | while read vm; do
    mem=$(VBoxManage showvminfo "$vm" --machinereadable | awk -F= '/^memory=/{print $2}')
    echo "$vm: ${mem} MB"
done

# Take a snapshot of every running VM
VBoxManage list runningvms | grep -oE '"[^"]+"' | tr -d '"' | while read vm; do
    VBoxManage snapshot "$vm" take "checkpoint-$(date +%Y%m%d-%H%M%S)" --pause
done

# Find disks that aren't attached to any VM
VBoxManage list hdds | grep "^Location:" | awk '{print $2}' > /tmp/all-disks
VBoxManage list vms | grep -oE '"[^"]+"' | tr -d '"' | while read vm; do
    VBoxManage showvminfo "$vm" --machinereadable | grep -oE '"[^"]+\.vdi"'
done | tr -d '"' | sort -u > /tmp/used-disks
comm -23 /tmp/all-disks /tmp/used-disks    # disks not in any VM
```

## Performance tips for scripted lab work

- **Run `startvm` headless, never GUI.** Avoids window-creation overhead and X11/Wayland round-trips.
- **Use `--hostiocache off` on storage controllers if you care about IO correctness.** Slightly slower but matches the real MS-S1 MAX semantics.
- **Detach the install ISO after install.** Saves the controller from probing it on every subsequent boot.
- **Compact disks periodically.** After a guest has rewritten data many times, the `.vdi` accumulates unused sectors. `VBoxManage modifymedium disk X.vdi --compact` reclaims them (after zeroing free space inside the guest).
- **Use snapshots aggressively.** Restoring is much faster than reinstalling.

## See also

- [VBoxManage CLI](vboxmanage.md) — full command reference
- [VMs](vms.md), [Storage](storage.md), [Networking](networking.md) — the bits being automated
- [Troubleshooting](troubleshooting.md) — common errors during scripted runs
- The lab's actual code: `src/msai_setup/lab/`
