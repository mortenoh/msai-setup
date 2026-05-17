# VMs — lifecycle

A VirtualBox VM is a record in VBox's registry plus the disk files it references. This page covers the lifecycle: create, configure, run, control, destroy.

## Create

```bash
VBoxManage createvm \
    --name test \
    --ostype Ubuntu_64 \
    --platform-architecture x86 \
    --register
```

`--platform-architecture` is `x86` (default) or `arm`. **Set at create time only** — can't be changed by `modifyvm` later. On Apple Silicon, `arm` is mandatory.

`--ostype` is a hint VBox uses for hardware defaults (recommended graphics controller, USB controllers, etc.). Pick the closest match:

```bash
VBoxManage list ostypes | grep -A1 -i ubuntu
VBoxManage list --platform-arch=arm ostypes | grep -A1 -i ubuntu
```

Without `--register`, the VM exists but isn't in the VM list. Almost always you want `--register`.

The result of `createvm` is an empty VM:
- No memory configured
- No CPUs configured
- No disks
- No storage controllers
- Default NAT NIC (usually fine)

You can't `startvm` until you've at least added some disks and possibly some storage controllers.

## Configure

`modifyvm` is the workhorse. Most invocations look like:

```bash
VBoxManage modifyvm test \
    --memory 8192 \                   # MiB of RAM
    --cpus 4 \                        # number of vCPUs
    --vram 32 \                       # video RAM in MiB
    --firmware efi64 \                # x86 only: bios | efi | efi32 | efi64
    --nic1 nat \                      # primary NIC
    --rtcuseutc on \                  # RTC stored as UTC (Linux convention)
    --audio-driver none \             # no audio
    --boot1 disk --boot2 dvd \        # boot priority
    --boot3 none --boot4 none \
    --usbohci off --usbehci off --usbxhci off    # x86 only
```

It's **idempotent** — re-running with the same args is a no-op. Use this property in scripts: "make sure the VM has these settings" rather than "create only if absent".

### What each flag does

| Flag | What it does | Defaults / notes |
|---|---|---|
| `--memory N` | Sets RAM in MiB | Required before first start. Subtract from host RAM at start. |
| `--cpus N` | vCPU count | More than physical cores → degraded perf, not impossible. |
| `--vram N` | Video RAM in MiB | 32 is plenty for headless. |
| `--firmware bios/efi/efi32/efi64` | x86 only. EFI required for some modern guest installers. | `efi64` is right for Ubuntu 22+. |
| `--graphicscontroller` | `none`, `vboxvga`, `vmsvga`, `vmsvga`, `qemuramfb` | ARM **must** use `qemuramfb`. x86 default `vmsvga`. |
| `--chipset` | `piix3`, `ich9`, `armv8virtual` | ARM forced to `armv8virtual`. Use `ich9` for modern x86. |
| `--nic1` ... `--nic8` | Per-NIC type: `nat`, `bridged`, `hostonly`, `intnet`, `natnetwork`, `null`, `none` | Up to 8 NICs. |
| `--natpf1` | Add a NAT port-forward to nic1 | `"name,proto,host-ip,host-port,guest-ip,guest-port"` |
| `--rtcuseutc on` | Stores guest RTC as UTC, not local time | Linux convention; default on Linux ostypes anyway. |
| `--audio-driver none` | Disable audio | Defaults to `coreaudio`/`pulse`/`alsa`; not needed for headless servers. |
| `--usbohci/--usbehci/--usbxhci on/off` | x86 USB controllers | Turn off on headless lab VMs to reduce attack surface and noise. |
| `--boot1`..`--boot4 disk/dvd/net/none` | Boot priority order | First-found wins. |
| `--cpuid-set/--cpuid-remove` | Hide CPU features from the guest | Rarely needed. |
| `--paravirt-provider` | `default`, `kvm`, `hyperv`, `legacy`, `minimal`, `none` | Auto-picks. |
| `--hwvirtex on/off` | Hardware virt | Default on; off forces software emulation (very slow). |
| `--vrde on/off` | Enable VRDE remote console | See [Headless operation](headless.md). |

For Apple Silicon ARM VMs, several flags don't apply and others change meaning — see [Apple Silicon](apple-silicon.md).

### Network NIC types

`--nic1 nat` is the default and is what we use in the lab. Other modes:

```bash
# Bridged — joins the host's LAN as if it were a physical machine
VBoxManage modifyvm test \
    --nic1 bridged \
    --bridgeadapter1 "en0: Wi-Fi (AirPort)"           # macOS interface name

# Host-only — isolated network on a virtual subnet, host can reach it
VBoxManage hostonlyif create                          # creates vboxnet0
VBoxManage modifyvm test --nic1 hostonly --hostonlyadapter1 vboxnet0

# Internal — multiple VMs talk to each other on a named virtual network
VBoxManage modifyvm test --nic1 intnet --intnet1 my-private-net

# NAT Network — like NAT but shared across multiple VMs (uncommon)
VBoxManage natnetwork add --netname my-natnet --network 10.10.0.0/24 --enable
VBoxManage modifyvm test --nic1 natnetwork --nat-network1 my-natnet
```

For the lab: stay with NAT + host port-forwarding. Bridged adds LAN router complications you don't need.

### Storage doesn't go through `modifyvm`

Disks and ISOs are attached via `storageattach` (after a `storagectl` adds a controller). See [Storage](storage.md).

## Start

```bash
VBoxManage startvm test                       # open a window (GUI default)
VBoxManage startvm test --type gui            # explicit GUI
VBoxManage startvm test --type separate       # window + the VM process is detached
VBoxManage startvm test --type headless       # no window, runs in background
VBoxManage startvm test --type sdl            # SDL frontend (lightweight, no Qt)
```

`headless` is what you want for scripts and servers. The VM still has a framebuffer (you can `screenshotpng` it) but no window opens and no input device is attached.

`startvm` returns as soon as the VM begins booting — it doesn't wait for the OS to be up. To know when the guest is reachable, poll the SSH port (see `src/msai_setup/lab/ssh.py:wait_for_ssh` for the pattern).

## Control (while running)

```bash
VBoxManage controlvm test pause                       # freeze
VBoxManage controlvm test resume

VBoxManage controlvm test acpipowerbutton             # graceful shutdown
VBoxManage controlvm test acpisleepbutton             # suspend
VBoxManage controlvm test reset                       # hard reset (Ctrl+Alt+Del)
VBoxManage controlvm test poweroff                    # pull the plug
VBoxManage controlvm test savestate                   # suspend to disk

VBoxManage controlvm test screenshotpng /tmp/test.png # capture framebuffer
VBoxManage controlvm test keyboardputstring "ls\n"   # type into the guest
VBoxManage controlvm test keyboardputscancode 1c     # raw scancode (Enter)
VBoxManage controlvm test mouse moveabs 100 100 0 0 0 # move mouse pointer
```

`acpipowerbutton` vs `poweroff`:

- `acpipowerbutton` sends the ACPI signal that pressing the power button on a physical PC would send. Modern guests (systemd-logind) handle this and do a clean shutdown.
- `poweroff` is "yank the cord". Use only if the guest is unresponsive — risk of filesystem corruption.

`savestate` is interesting: it suspends the VM state to a file, frees the host RAM, and `startvm` resumes from exactly where you left off (full state, not a snapshot). Different from snapshots in that it's just a single suspend point with no branching.

## Inspect

```bash
VBoxManage showvminfo test                            # human dump
VBoxManage showvminfo test --machinereadable         # parseable
```

Useful queries:

```bash
# What's the VM's state?
VBoxManage showvminfo test --machinereadable | awk -F= '/^VMState=/{print $2}'
# "running", "poweroff", "paused", "saved", etc.

# How many CPUs?
VBoxManage showvminfo test --machinereadable | awk -F= '/^cpus=/{print $2}'

# Which storage controllers?
VBoxManage showvminfo test --machinereadable | grep '^storagecontrollername'

# Forwarding rules?
VBoxManage showvminfo test --machinereadable | grep '^Forwarding'
```

For programmatic use, parse `--machinereadable` — it's stable and quoted-where-needed.

## Modify a running VM

Some properties can change while running, others can't:

| Change | Requires VM stopped? |
|---|---|
| Add a NAT port forward (`--natpf1`) | No |
| Change RAM | Yes |
| Change CPU count | Yes |
| Hot-plug a disk (`storageattach --hotpluggable on`) | No |
| Change firmware | Yes |
| Change graphics controller | Yes |
| Add a snapshot | No |

If you try a stop-required change on a running VM, VBoxManage errors with `VBOX_E_INVALID_VM_STATE`. Stop the VM first, retry.

## Destroy

```bash
# Stop if running
VBoxManage controlvm test poweroff 2>/dev/null || true
sleep 1

# Unregister + delete files
VBoxManage unregistervm test --delete

# Or unregister without deleting (useful for moving VMs)
VBoxManage unregistervm test
```

`--delete` removes the `.vbox` config, snapshots, and any disks the VM considers owned. Disks created independently and attached via path may not be considered owned — they stay on disk after `--delete`. To be sure they're gone, `closemedium disk /path --delete` per disk first.

## Lifecycle in scripts

Idempotent pattern:

```bash
NAME=test

# Stop + delete if exists
if VBoxManage list vms | grep -q "\"$NAME\""; then
    VBoxManage controlvm "$NAME" poweroff 2>/dev/null || true
    sleep 1
    VBoxManage unregistervm "$NAME" --delete
fi

# Recreate
VBoxManage createvm --name "$NAME" --ostype Ubuntu_64 --register
VBoxManage modifyvm "$NAME" --memory 4096 --cpus 2 --firmware efi64 --nic1 nat
VBoxManage createmedium disk --filename "$NAME.vdi" --size 20000
VBoxManage storagectl "$NAME" --name SATA --add sata
VBoxManage storageattach "$NAME" --storagectl SATA --port 0 --device 0 \
    --type hdd --medium "$NAME.vdi"
VBoxManage startvm "$NAME" --type headless
```

For real automation use the Python wrapper in `src/msai_setup/lab/vbox.py` — same idea, with proper error handling and idempotency at the function level.

## Where to go next

- [Storage](storage.md) — disks, controllers, ISO attachment
- [Networking](networking.md) — NAT, bridge, port forwarding in depth
- [Snapshots](snapshots.md) — branching state safely
- [Headless](headless.md) — startvm headless + remote console
