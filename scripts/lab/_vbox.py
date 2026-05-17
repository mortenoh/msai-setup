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
from collections.abc import Iterable
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
    return name in list_vms()


def vm_running(name: str) -> bool:
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


def create_vm(name: str, *, ostype: str = "Ubuntu_64") -> None:
    """Create + register a VM. No-op if it already exists."""
    if vm_exists(name):
        log.info("vm %s already exists", name)
        return
    _run(["createvm", "--name", name, "--ostype", ostype, "--register"])
    log.info("created vm %s", name)


def configure_vm(
    name: str,
    *,
    memory_mb: int,
    cpus: int,
    vram_mb: int,
    firmware: str = "efi64",
) -> None:
    """Apply baseline hardware config. Re-runnable to update settings."""
    _run([
        "modifyvm", name,
        "--memory", str(memory_mb),
        "--cpus", str(cpus),
        "--vram", str(vram_mb),
        "--firmware", firmware,
        "--nic1", "nat",
        "--rtcuseutc", "on",
        "--audio-driver", "none",
        "--usbohci", "off",
        "--usbehci", "off",
        "--usbxhci", "off",
        "--boot1", "disk",
        "--boot2", "dvd",
        "--boot3", "none",
        "--boot4", "none",
    ])


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


# --- Unattended install ------------------------------------------------------


def unattended_install(
    name: str,
    *,
    iso: Path,
    user: str,
    password: str,
    full_user_name: str,
    hostname: str,
    time_zone: str = "Europe/Oslo",
    locale: str = "en_US.UTF-8",
    install_guest_additions: bool = True,
) -> None:
    """Configure (but don't start) an unattended install on the VM."""
    args = [
        "unattended", "install", name,
        "--iso", str(iso),
        "--user", user,
        "--password", password,
        "--full-user-name", full_user_name,
        "--hostname", hostname,
        "--time-zone", time_zone,
        "--locale", locale,
    ]
    if install_guest_additions:
        args.append("--install-additions")
    _run(args)
    log.info("configured unattended install for %s (user=%s)", name, user)


# --- Power & control ---------------------------------------------------------


def start_headless(name: str) -> None:
    if vm_running(name):
        log.info("vm %s is already running", name)
        return
    _run(["startvm", name, "--type", "headless"])
    log.info("started %s headless", name)


def power_off(name: str) -> None:
    if not vm_running(name):
        log.info("vm %s is not running", name)
        return
    _run(["controlvm", name, "poweroff"], check=False)
    log.info("powered off %s", name)


def acpi_power_button(name: str) -> None:
    if not vm_running(name):
        log.info("vm %s is not running", name)
        return
    _run(["controlvm", name, "acpipowerbutton"])


# --- Snapshots ---------------------------------------------------------------


def snapshot_take(name: str, snapshot_name: str, *, pause: bool = True) -> None:
    args = ["snapshot", name, "take", snapshot_name]
    if pause:
        args.append("--pause")
    _run(args)
    log.info("snapshot taken: %s/%s", name, snapshot_name)


def snapshot_restore_current(name: str) -> None:
    _run(["snapshot", name, "restorecurrent"])
    log.info("restored most recent snapshot of %s", name)


def snapshot_list(name: str) -> list[str]:
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
