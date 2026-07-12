"""VBoxManage wrapper.

Wraps the VBoxManage CLI in a small, testable Python surface. We use
subprocess rather than the vboxapi SDK because the SDK requires a fragile
COM/XPCOM install that varies by platform; subprocess is portable to any host
with a working VirtualBox installation.

All functions are idempotent: creating a VM that exists is a no-op, attaching
a disk that's already attached is a no-op, etc. Phases can re-run safely.
"""

from __future__ import annotations

import logging
import re
import subprocess
import time
from pathlib import Path

log = logging.getLogger(__name__)


class VBoxError(RuntimeError):
    """Raised when VBoxManage exits non-zero in a way we don't expect."""


def _run(args: list[str], *, check: bool = True, capture: bool = True) -> str:
    """Run a VBoxManage invocation and return stdout (stripped)."""
    cmd = ["VBoxManage", *args]
    log.debug("running: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise VBoxError(
            f"VBoxManage failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}\n"
            f"stdout: {result.stdout.strip()}"
        )
    return (result.stdout or "").strip()


def require_vboxmanage() -> None:
    """Verify VBoxManage is on PATH and runnable. Raise if not."""
    try:
        version = _run(["--version"])
    except FileNotFoundError as e:
        raise VBoxError("VBoxManage not found on PATH; install VirtualBox first") from e
    log.info("VBoxManage version %s", version)


# --- VM lookup ---------------------------------------------------------------


def list_vms() -> list[str]:
    """Return the names of all registered VMs."""
    out = _run(["list", "vms"])
    return re.findall(r'"([^"]+)"', out)


def list_running_vms() -> list[str]:
    """Return the names of currently running VMs."""
    out = _run(["list", "runningvms"])
    return re.findall(r'"([^"]+)"', out)


def vm_exists(name: str) -> bool:
    """Return True if a VM named `name` is registered."""
    return name in list_vms()


def vm_running(name: str) -> bool:
    """Return True if a VM named `name` is currently running."""
    return name in list_running_vms()


def showvminfo(name: str) -> dict[str, str]:
    """Return the machine-readable showvminfo as a dict.

    Keys are stripped of surrounding quotes. Missing values are empty strings.
    """
    out = _run(["showvminfo", name, "--machinereadable"])
    info: dict[str, str] = {}
    for line in out.splitlines():
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        info[key.strip()] = value.strip().strip('"')
    return info


# --- VM lifecycle ------------------------------------------------------------


def create_vm(name: str, *, ostype: str = "Ubuntu_64", platform: str = "x86") -> None:
    """Create + register a VM. No-op if it already exists.

    `platform` is 'x86' (default) or 'arm'. On Apple Silicon you want 'arm'
    AND a matching ostype (e.g. Ubuntu_arm64 for current 26.04 ARM media). This is set at createvm
    time only — `modifyvm` can't change it later.
    """
    if vm_exists(name):
        log.info("vm %s already exists", name)
        return
    _run([
        "createvm",
        "--name", name,
        "--ostype", ostype,
        "--platform-architecture", platform,
        "--register",
    ])
    log.info("created vm %s (platform=%s, ostype=%s)", name, platform, ostype)


def configure_vm(
    name: str,
    *,
    memory_mb: int,
    cpus: int,
    vram_mb: int,
    platform: str = "x86",
) -> None:
    """Apply baseline hardware config. Re-runnable to update settings.

    Firmware and USB controller flags differ between x86 and ARM:
      - x86: --firmware efi64; explicit USB OHCI/EHCI/XHCI toggles
      - ARM: VBox picks ARM-appropriate firmware from createvm's platform
        flag; classic USB toggles aren't applicable.
    """
    common = [
        "modifyvm", name,
        "--memory", str(memory_mb),
        "--cpus", str(cpus),
        "--vram", str(vram_mb),
        "--nic1", "nat",
        "--rtcuseutc", "on",
        "--audio-driver", "none",
        "--boot1", "disk",
        "--boot2", "dvd",
        "--boot3", "none",
        "--boot4", "none",
    ]
    if platform == "x86":
        common.extend([
            "--firmware", "efi64",
            "--usbohci", "off",
            "--usbehci", "off",
            "--usbxhci", "off",
        ])
    else:
        # ARM: the default `vboxvga` graphics controller conflicts with RAM
        # allocation on ARM (VERR_PGM_RAM_CONFLICT on startvm). `qemuramfb`
        # is the ARM-appropriate alternative.
        common.extend(["--graphicscontroller", "qemuramfb"])
    _run(common)


def set_boot_order(name: str, devices: list[str]) -> None:
    """Set the VM boot order (up to four slots).

    e.g. ``set_boot_order(name, ["dvd", "disk"])`` boots the optical drive
    first. The root-on-ZFS live-install flow uses this so the VM always
    re-enters the live installer ISO on reboot — on the aarch64 lab the
    firmware cannot execute the ZFSBootMenu EFI binary on the installed disk, so
    a deterministic DVD-first order is what makes reboots land back in the live
    environment for offline verification.
    """
    slots = (devices + ["none", "none", "none", "none"])[:4]
    args = ["modifyvm", name]
    for i, dev in enumerate(slots, start=1):
        args.extend([f"--boot{i}", dev])
    _run(args)
    log.info("set boot order on %s: %s", name, ", ".join(slots))


def add_tpm(name: str, *, version: str = "2.0") -> None:
    """Attach an emulated TPM to the VM (Windows 11 requires TPM 2.0).

    Uses `VBoxManage modifyvm <name> --tpm-type <version>` (verified against
    VBox 7.2: `--tpm-type= none | 1.2 | 2.0 | host | swtpm`). `modifyvm` is
    declarative, so re-running just re-sets the same value (idempotent-ish). The
    VM must be stopped (TPM can't be hot-added).
    """
    _run(["modifyvm", name, "--tpm-type", version])
    log.info("set TPM type %s on %s", version, name)


def set_secure_boot(name: str, *, enabled: bool) -> None:
    """Enable/disable UEFI Secure Boot on the VM (VBox 7.2 `modifynvram`).

    VBox 7.2 controls Secure Boot via the NVRAM, not `modifyvm`:
    `VBoxManage modifynvram <name> secureboot <--enable | --disable>`.

    For Windows to actually BOOT under Secure Boot the NVRAM also needs the
    platform key + Microsoft signature databases enrolled, so on enable we
    best-effort `enrollorclpk` (Oracle PK) then `enrollmssignatures` (MS KEK/db)
    before flipping it on. Those require the VM's EFI NVRAM to already exist and
    may be no-ops/failures on some setups — hence check=False with a warning.

    LIMITATION (honest): if enrollment fails (e.g. NVRAM not yet initialised on
    this host, or a VBox build quirk), Secure Boot may need to be completed by
    hand — enroll the keys in the VirtualBox GUI, or re-run these `modifynvram`
    commands once the VM's firmware NVRAM has been created. This path is NOT
    verifiable on the Apple-Silicon dev host (no amd64 Windows guest to boot).
    """
    if enabled:
        # Enroll keys first so `secureboot --enable` has a trusted chain.
        for sub in ("enrollorclpk", "enrollmssignatures"):
            result = _run(["modifynvram", name, sub], check=False)
            log.debug("modifynvram %s %s -> %s", name, sub, result or "(ok)")
        _run(["modifynvram", name, "secureboot", "--enable"])
        log.info("enabled Secure Boot on %s (keys enrolled best-effort)", name)
    else:
        _run(["modifynvram", name, "secureboot", "--disable"])
        log.info("disabled Secure Boot on %s", name)


def enable_vrde(name: str, *, port: int = 3389) -> None:
    """Enable VRDE (VirtualBox Remote Desktop) so a headless VM has a console.

    Useful for the rare path where unattended install isn't supported and the
    user needs to drive Subiquity interactively. Connect with any RDP client.
    """
    _run([
        "modifyvm", name,
        "--vrde", "on",
        "--vrdeport", str(port),
        "--vrdeaddress", "127.0.0.1",
        "--vrdeauthtype", "null",
    ])
    log.info("enabled VRDE on 127.0.0.1:%d (no auth)", port)


def add_ssh_port_forward(name: str, *, host_port: int, guest_port: int = 22) -> None:
    """Add an SSH port forward (host_port -> guest 22). No-op if already set."""
    info = showvminfo(name)
    # NAT port-forward keys look like: Forwarding(0)="ssh,tcp,127.0.0.1,2222,,22"
    for key, value in info.items():
        if key.startswith("Forwarding(") and value.startswith("ssh,"):
            log.info("ssh port forward already configured: %s", value)
            return
    _run([
        "modifyvm", name,
        "--natpf1", f"ssh,tcp,127.0.0.1,{host_port},,{guest_port}",
    ])
    log.info("added ssh port forward: 127.0.0.1:%d -> guest:%d", host_port, guest_port)


def add_rdp_port_forward(name: str, *, host_port: int, guest_port: int = 3389) -> None:
    """Add an RDP port forward (host_port -> guest 3389). No-op if already set."""
    info = showvminfo(name)
    # NAT port-forward keys look like: Forwarding(1)="rdp,tcp,127.0.0.1,3390,,3389"
    for key, value in info.items():
        if key.startswith("Forwarding(") and value.startswith("rdp,"):
            log.info("rdp port forward already configured: %s", value)
            return
    _run([
        "modifyvm", name,
        "--natpf1", f"rdp,tcp,127.0.0.1,{host_port},,{guest_port}",
    ])
    log.info("added rdp port forward: 127.0.0.1:%d -> guest:%d", host_port, guest_port)


# --- Storage -----------------------------------------------------------------


def create_disk(path: Path, *, size_mb: int) -> None:
    """Create a fresh VDI disk image. No-op if the file already exists."""
    if path.exists():
        log.info("disk already exists: %s", path)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    _run([
        "createmedium", "disk",
        "--filename", str(path),
        "--size", str(size_mb),
        "--format", "VDI",
    ])
    log.info("created disk %s (%d MiB)", path, size_mb)


def ensure_storage_controller(name: str, *, ctrl_name: str, kind: str, **kwargs: object) -> None:
    """Add a storage controller if missing.

    kind: 'sata' | 'ide' | 'nvme' (whatever VBoxManage supports)
    kwargs: forwarded as additional --key value pairs (e.g. controller='IntelAhci')
    """
    info = showvminfo(name)
    if any(v == ctrl_name for k, v in info.items() if k.startswith("storagecontrollername")):
        log.info("controller %s already present", ctrl_name)
        return

    args = ["storagectl", name, "--name", ctrl_name, "--add", kind]
    for k, v in kwargs.items():
        args.extend([f"--{k.replace('_', '-')}", str(v)])
    _run(args)
    log.info("added %s controller %s", kind, ctrl_name)


def attach_disk(
    name: str,
    *,
    controller: str,
    port: int,
    device: int = 0,
    medium: Path | None,
    type_: str = "hdd",
    nonrotational: bool = True,
    discard: bool = True,
) -> None:
    """Attach a disk (or detach with medium=None)."""
    args = [
        "storageattach", name,
        "--storagectl", controller,
        "--port", str(port),
        "--device", str(device),
        "--type", type_,
        "--medium", "none" if medium is None else str(medium),
    ]
    if medium is not None and type_ == "hdd":
        if nonrotational:
            args.extend(["--nonrotational", "on"])
        if discard:
            args.extend(["--discard", "on"])
    _run(args)
    if medium is None:
        log.info("detached %s port %d device %d on %s", controller, port, device, name)
    else:
        log.info("attached %s on %s port %d device %d (%s)", medium, controller, port, device, name)


def attach_iso(name: str, *, controller: str, port: int, device: int, iso: Path) -> None:
    """Attach an ISO as a dvddrive."""
    attach_disk(
        name,
        controller=controller, port=port, device=device,
        medium=iso, type_="dvddrive",
        nonrotational=False, discard=False,
    )


# --- Power & control ---------------------------------------------------------


def start_headless(name: str) -> None:
    """Start the VM headless. No-op if it's already running."""
    if vm_running(name):
        log.info("vm %s is already running", name)
        return
    _run(["startvm", name, "--type", "headless"])
    log.info("started %s headless", name)


def start_gui(name: str) -> None:
    """Start the VM with a visible GUI window. No-op if it's already running.

    Mirrors :func:`start_headless` but uses `--type gui`, so the user can watch
    the install and take over a stuck installer by hand.
    """
    if vm_running(name):
        log.info("vm %s is already running", name)
        return
    _run(["startvm", name, "--type", "gui"])
    log.info("started %s with GUI console", name)


def start(name: str, *, headless: bool) -> None:
    """Start the VM, dispatching to headless or GUI boot based on `headless`."""
    if headless:
        start_headless(name)
    else:
        start_gui(name)


def power_off(name: str) -> None:
    """Hard power-off the VM. No-op if it's not running."""
    if not vm_running(name):
        log.info("vm %s is not running", name)
        return
    _run(["controlvm", name, "poweroff"], check=False)
    log.info("powered off %s", name)


def acpi_power_button(name: str) -> None:
    """Send an ACPI power-button event so the guest shuts down gracefully."""
    if not vm_running(name):
        log.info("vm %s is not running", name)
        return
    _run(["controlvm", name, "acpipowerbutton"])


def wait_until_stopped(name: str, *, timeout: int = 180, interval: int = 3) -> None:
    """Poll until the VM is no longer running, or raise on timeout.

    Used after asking a guest to power off (e.g. `poweroff` over SSH) before
    reconfiguring storage host-side, since VBoxManage storageattach requires the
    VM to be fully stopped.
    """
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not vm_running(name):
            log.info("vm %s has stopped", name)
            return
        time.sleep(interval)
    raise VBoxError(f"vm {name} did not stop within {timeout}s")


# --- Snapshots ---------------------------------------------------------------


def snapshot_take(name: str, snapshot_name: str, *, pause: bool = True) -> None:
    """Take a snapshot of `name`, optionally pausing the VM during capture."""
    args = ["snapshot", name, "take", snapshot_name]
    if pause:
        args.append("--pause")
    _run(args)
    log.info("snapshot taken: %s/%s", name, snapshot_name)


def snapshot_restore(name: str, snapshot_name: str) -> None:
    """Restore `name` to the named snapshot."""
    _run(["snapshot", name, "restore", snapshot_name])
    log.info("restored snapshot %s/%s", name, snapshot_name)


def snapshot_restore_current(name: str) -> None:
    """Restore `name` to its most recent snapshot."""
    _run(["snapshot", name, "restorecurrent"])
    log.info("restored most recent snapshot of %s", name)


def snapshot_list(name: str) -> list[str]:
    """Return the snapshot names of `name`, or an empty list if it has none."""
    try:
        out = _run(["snapshot", name, "list", "--machinereadable"])
    except VBoxError:
        return []
    return [
        line.split("=", 1)[1].strip('"')
        for line in out.splitlines()
        if line.startswith("SnapshotName")
    ]


# --- Destroy -----------------------------------------------------------------


def unregister_and_delete(name: str) -> None:
    """Power off, unregister, and delete all VM files."""
    if vm_running(name):
        power_off(name)
    if vm_exists(name):
        _run(["unregistervm", name, "--delete"])
        log.info("unregistered and deleted %s", name)
