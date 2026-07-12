"""Incus CLI wrapper (the real Linux box / MS-S1 MAX provider).

Mirrors vbox.py: a small, testable subprocess surface over the `incus` CLI,
with a private `_run`, a `require_incus` preflight, and machine-readable
(`--format json`) parsing. subprocess (not a Python binding) keeps it portable.

All functions aim to be idempotent: creating an instance that exists is a no-op,
adding a device/volume that exists is a no-op, etc.

Conventions follow docs/incus/*.md. In particular the restricted **user-1000
project** forbids raw host-path disk devices, so install ISOs are imported as
managed storage volumes (`incus storage volume import <pool> <iso> <name>
--type=iso`) on the `lab` pool. Pool/project are configurable (see config.py).

HONESTY: this module is UNVALIDATED on the macOS dev host (no Incus here). It is
written to the documented CLI + unit-tested against a mocked `incus` subprocess;
real validation happens on the MS-S1 MAX. Treat argv as the tested contract.
"""

from __future__ import annotations

import json
import logging
import subprocess
from pathlib import Path
from typing import Any, cast

log = logging.getLogger(__name__)


class IncusError(RuntimeError):
    """Raised when `incus` exits non-zero in a way we don't expect."""


def _run(args: list[str], *, check: bool = True, capture: bool = True) -> str:
    """Run an `incus` invocation and return stdout (stripped)."""
    cmd = ["incus", *args]
    log.debug("running: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=capture,
        text=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise IncusError(
            f"incus failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}\n"
            f"stdout: {result.stdout.strip()}"
        )
    return (result.stdout or "").strip()


def _project_args(project: str) -> list[str]:
    """Return the global `--project` flag args, or empty for the current project."""
    return ["--project", project] if project else []


def require_incus() -> None:
    """Verify the `incus` CLI is on PATH and runnable. Raise if not."""
    try:
        version = _run(["version"])
    except FileNotFoundError as e:
        raise IncusError("incus not found on PATH; install Incus on the host first") from e
    log.info("incus version:\n%s", version)


# --- Instance lookup ---------------------------------------------------------


def _list_json(project: str) -> list[dict[str, Any]]:
    """Return `incus list --format json` parsed (list of instance dicts)."""
    out = _run(["list", *_project_args(project), "--format", "json"])
    if not out:
        return []
    data: Any = json.loads(out)
    if not isinstance(data, list):
        return []
    return cast("list[dict[str, Any]]", data)


def list_instances(*, project: str = "") -> list[str]:
    """Return the names of all instances in the project."""
    return [str(inst.get("name", "")) for inst in _list_json(project)]


def instance_exists(name: str, *, project: str = "") -> bool:
    """Return True if an instance named `name` exists in the project."""
    return name in list_instances(project=project)


def instance_running(name: str, *, project: str = "") -> bool:
    """Return True if `name` is currently running."""
    for inst in _list_json(project):
        if inst.get("name") == name:
            return str(inst.get("status", "")).lower() == "running"
    return False


def get_ipv4(name: str, *, project: str = "") -> str | None:
    """Return the instance's first global IPv4 address, or None if none yet.

    Parses `incus list --format json`: each instance has
    `state.network.<iface>.addresses[]` with `family`/`scope`/`address`. We skip
    loopback and return the first `inet` global address (usually on `eth0`).
    """
    for inst in _list_json(project):
        if inst.get("name") != name:
            continue
        state_obj: dict[str, Any] = inst.get("state") or {}
        network: dict[str, Any] = state_obj.get("network") or {}
        for iface, info_raw in network.items():
            if iface == "lo" or not isinstance(info_raw, dict):
                continue
            info = cast("dict[str, Any]", info_raw)
            addresses: list[Any] = info.get("addresses", []) or []
            for addr_raw in addresses:
                if not isinstance(addr_raw, dict):
                    continue
                addr = cast("dict[str, Any]", addr_raw)
                if addr.get("family") == "inet" and addr.get("scope") == "global":
                    return str(addr.get("address"))
    return None


# --- Instance lifecycle ------------------------------------------------------


def _resource_args(*, cpu: int, memory_mb: int, disk_size_mb: int) -> list[str]:
    """Build the common -c limits.* / -d root,size resource flags."""
    return [
        "-c", f"limits.cpu={cpu}",
        "-c", f"limits.memory={memory_mb}MiB",
        "-d", f"root,size={disk_size_mb}MiB",
    ]


def _config_args(config: dict[str, str] | None) -> list[str]:
    """Expand a config dict into repeated `-c key=value` flags."""
    args: list[str] = []
    for key, value in (config or {}).items():
        args.extend(["-c", f"{key}={value}"])
    return args


def init_vm(
    name: str,
    *,
    image: str | None = None,
    empty: bool = False,
    cpu: int,
    memory_mb: int,
    disk_size_mb: int,
    project: str = "",
    config: dict[str, str] | None = None,
) -> None:
    """`incus init` a VM. No-op if the instance already exists.

    Either boot from an `images:` remote image (`image=...`) or create a blank
    VM for an ISO install (`empty=True`). `config` is applied as `-c key=value`
    (e.g. cloud-init `user.user-data`).
    """
    if instance_exists(name, project=project):
        log.info("incus instance %s already exists", name)
        return
    args = ["init", *_project_args(project)]
    if image:
        args.append(image)
    args.append(name)
    args.append("--vm")
    if empty:
        args.append("--empty")
    args.extend(_resource_args(cpu=cpu, memory_mb=memory_mb, disk_size_mb=disk_size_mb))
    args.extend(_config_args(config))
    _run(args)
    log.info("incus init %s (--vm%s)", name, " --empty" if empty else f" {image}")


def launch_vm(
    name: str,
    *,
    image: str,
    cpu: int,
    memory_mb: int,
    disk_size_mb: int,
    project: str = "",
    config: dict[str, str] | None = None,
) -> None:
    """`incus launch` a VM from an image (init + start in one). No-op if it exists.

    Preferred for the Ubuntu path: a ready `images:` VM image plus cloud-init via
    `-c user.user-data=...` boots straight to a configured guest.
    """
    if instance_exists(name, project=project):
        log.info("incus instance %s already exists", name)
        return
    args = ["launch", *_project_args(project), image, name, "--vm"]
    args.extend(_resource_args(cpu=cpu, memory_mb=memory_mb, disk_size_mb=disk_size_mb))
    args.extend(_config_args(config))
    _run(args)
    log.info("incus launch %s from %s", name, image)


def config_set(name: str, key: str, value: str, *, project: str = "") -> None:
    """`incus config set <name> <key> <value>` (e.g. security.secureboot true)."""
    _run(["config", "set", *_project_args(project), name, key, value])
    log.info("incus config set %s %s=%s", name, key, value)


def device_names(name: str, *, project: str = "") -> list[str]:
    """Return the instance's device names (`incus config device list`)."""
    out = _run(["config", "device", "list", *_project_args(project), name], check=False)
    return [line.strip() for line in out.splitlines() if line.strip()]


def config_device_add(
    name: str,
    dev_name: str,
    dev_type: str,
    *,
    project: str = "",
    **props: str,
) -> None:
    """`incus config device add <name> <dev> <type> k=v ...`. No-op if present.

    Handles disk / tpm / gpu / unix-char / proxy devices via **props.
    """
    if dev_name in device_names(name, project=project):
        log.info("incus device %s already on %s", dev_name, name)
        return
    args = ["config", "device", "add", *_project_args(project), name, dev_name, dev_type]
    for key, value in props.items():
        args.append(f"{key.replace('_', '.')}={value}")
    _run(args)
    log.info("incus device add %s %s %s", name, dev_name, dev_type)


def config_device_remove(name: str, dev_name: str, *, project: str = "") -> None:
    """Remove a device. No-op if it isn't present."""
    if dev_name not in device_names(name, project=project):
        return
    _run(["config", "device", "remove", *_project_args(project), name, dev_name])
    log.info("incus device remove %s %s", name, dev_name)


# --- Storage volumes (managed-ISO route for the restricted project) ----------


def storage_volume_exists(pool: str, vol_name: str, *, project: str = "") -> bool:
    """Return True if a storage volume `vol_name` exists in `pool`."""
    out = _run(
        ["storage", "volume", "list", *_project_args(project), pool, "--format", "json"],
        check=False,
    )
    if not out:
        return False
    try:
        data: Any = json.loads(out)
    except json.JSONDecodeError:
        return False
    if not isinstance(data, list):
        return False
    volumes = cast("list[Any]", data)
    for v in volumes:
        if isinstance(v, dict) and cast("dict[str, Any]", v).get("name") == vol_name:
            return True
    return False


def storage_volume_import(
    pool: str, iso_path: Path, vol_name: str, *, project: str = ""
) -> None:
    """Import an ISO as a managed `iso`-type volume. No-op if it already exists.

    The restricted user-1000 project forbids raw host-path disk sources, so an
    install ISO must be imported as a managed volume then attached as a disk
    device (see docs/incus/vms.md).
    """
    if storage_volume_exists(pool, vol_name, project=project):
        log.info("incus storage volume %s/%s already exists", pool, vol_name)
        return
    _run([
        "storage", "volume", "import", *_project_args(project),
        pool, str(iso_path), vol_name, "--type=iso",
    ])
    log.info("incus storage volume import %s -> %s/%s", iso_path, pool, vol_name)


def storage_volume_delete(pool: str, vol_name: str, *, project: str = "") -> None:
    """Delete a managed storage volume. No-op if it isn't there."""
    if not storage_volume_exists(pool, vol_name, project=project):
        return
    _run(["storage", "volume", "delete", *_project_args(project), pool, vol_name])
    log.info("incus storage volume delete %s/%s", pool, vol_name)


def attach_iso_volume(
    name: str,
    dev_name: str,
    *,
    pool: str,
    vol_name: str,
    boot_priority: int | None = None,
    project: str = "",
) -> None:
    """Attach an imported ISO volume as a boot disk device.

    `boot_priority` (higher boots first) makes firmware boot the installer ISO
    before the empty root disk.
    """
    props: dict[str, str] = {"pool": pool, "source": vol_name}
    if boot_priority is not None:
        props["boot.priority"] = str(boot_priority)
    # boot.priority contains a dot, so build the args directly (not via **props,
    # which underscore-maps keys). Mirrors config_device_add's idempotency.
    if dev_name in device_names(name, project=project):
        log.info("incus device %s already on %s", dev_name, name)
        return
    args = ["config", "device", "add", *_project_args(project), name, dev_name, "disk"]
    args.extend(f"{k}={v}" for k, v in props.items())
    _run(args)
    log.info("incus attach iso volume %s/%s -> %s:%s", pool, vol_name, name, dev_name)


# --- Firmware / TPM (Windows) ------------------------------------------------


def add_vtpm(name: str, *, dev_name: str = "vtpm", project: str = "") -> None:
    """Add an emulated TPM 2.0 device (Windows 11). VM must be stopped."""
    config_device_add(name, dev_name, "tpm", project=project)


def set_secure_boot(name: str, *, enabled: bool, project: str = "") -> None:
    """Set `security.secureboot` (VM-only bool, defaults true in Incus)."""
    config_set(name, "security.secureboot", "true" if enabled else "false", project=project)


# --- GPU passthrough (CONTAINERS only — see gpu-passthrough.md) ---------------


def add_gpu_device(
    name: str,
    *,
    gid: int,
    dev_name: str = "gpu0",
    gpu_id: int = 0,
    project: str = "",
) -> None:
    """Add the `gpu` device (/dev/dri render nodes) to a CONTAINER.

    NOTE: this build never passes the single iGPU to a VM (host ROCm and VM
    passthrough are mutually exclusive — see gpu-passthrough.md / vms.md). GPU
    passthrough is a CONTAINER path only; the lab provisions VMs, so these
    helpers exist for completeness/parity with the docs and aren't used by the
    VM provisioning flow.
    """
    config_device_add(
        name, dev_name, "gpu",
        project=project, gputype="physical", id=str(gpu_id), gid=str(gid),
    )


def add_kfd_device(
    name: str,
    *,
    gid: int,
    dev_name: str = "dev_kfd",
    project: str = "",
) -> None:
    """Add the `/dev/kfd` unix-char device (ROCm compute) to a CONTAINER.

    The `gpu` device gives /dev/dri but NOT /dev/kfd — the single most common
    ROCm-in-container mistake (gpu-passthrough.md). Both are required for ROCm.
    Containers only; not applicable to the VM flows this lab drives.
    """
    config_device_add(
        name, dev_name, "unix-char",
        project=project, source="/dev/kfd", path="/dev/kfd", gid=str(gid),
    )


def add_proxy_device(
    name: str,
    dev_name: str,
    *,
    listen: str,
    connect: str,
    bind: str = "host",
    project: str = "",
) -> None:
    """Add a proxy device to expose a guest port on the host (e.g. RDP 3389)."""
    config_device_add(
        name, dev_name, "proxy",
        project=project, listen=listen, connect=connect, bind=bind,
    )


# --- Power & control ---------------------------------------------------------


def start(name: str, *, project: str = "") -> None:
    """Start the instance. No-op if already running."""
    if instance_running(name, project=project):
        log.info("incus instance %s already running", name)
        return
    _run(["start", *_project_args(project), name])
    log.info("incus start %s", name)


def stop(name: str, *, force: bool = False, project: str = "") -> None:
    """Stop the instance (graceful, or --force power-off). No-op if not running."""
    if not instance_running(name, project=project):
        log.info("incus instance %s is not running", name)
        return
    args = ["stop", *_project_args(project), name]
    if force:
        args.append("--force")
    _run(args)
    log.info("incus stop %s%s", name, " --force" if force else "")


def restart(name: str, *, project: str = "") -> None:
    """Restart the instance."""
    _run(["restart", *_project_args(project), name])
    log.info("incus restart %s", name)


def delete(name: str, *, force: bool = True, project: str = "") -> None:
    """Delete the instance (and its zvol). No-op if it doesn't exist."""
    if not instance_exists(name, project=project):
        return
    args = ["delete", *_project_args(project), name]
    if force:
        args.append("--force")
    _run(args)
    log.info("incus delete %s", name)


def exec_(name: str, argv: list[str], *, project: str = "", check: bool = True) -> str:
    """Run a command inside the instance via `incus exec <name> -- <argv>`.

    (Named `exec_` since `exec` is a builtin.) Requires the incus-agent in the
    guest (Linux images ship it; Windows/custom images may not).
    """
    return _run(["exec", *_project_args(project), name, "--", *argv], check=check)


# --- Snapshots ---------------------------------------------------------------


def snapshot(name: str, snap_name: str, *, project: str = "") -> None:
    """Create a snapshot of the instance."""
    _run(["snapshot", "create", *_project_args(project), name, snap_name])
    log.info("incus snapshot create %s/%s", name, snap_name)


def restore(name: str, snap_name: str, *, project: str = "") -> None:
    """Restore the instance to a snapshot."""
    _run(["snapshot", "restore", *_project_args(project), name, snap_name])
    log.info("incus snapshot restore %s/%s", name, snap_name)
