"""Multipass wrapper — alternative provisioner for Apple Silicon Macs.

Multipass is Canonical's native Ubuntu-VM-on-your-laptop tool. It works very
well on Apple Silicon (where VirtualBox 7.2 is still tech-preview-quality for
ARM Linux guests), and it's simpler than VBoxManage for the common case:

  multipass launch                          # create + boot
  multipass exec <name> -- <command>        # run something inside
  multipass mount / multipass info / etc

The Ansible playbooks in this repo run against any SSH-reachable Ubuntu VM,
so swapping the provisioner is a one-line change in `02_apply.py`.

Install on macOS:
    brew install --cask multipass
"""

from __future__ import annotations

import json
import logging
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger(__name__)


class MultipassError(RuntimeError):
    pass


def _run(args: list[str], *, check: bool = True, capture: bool = True) -> str:
    cmd = ["multipass", *args]
    log.debug("running: %s", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=capture, text=True, check=False)
    if check and result.returncode != 0:
        raise MultipassError(
            f"multipass failed (exit {result.returncode}): {' '.join(cmd)}\n"
            f"stderr: {result.stderr.strip()}"
        )
    return (result.stdout or "").strip()


def require_multipass() -> None:
    if shutil.which("multipass") is None:
        raise MultipassError(
            "multipass not on PATH. Install:\n"
            "    brew install --cask multipass    # macOS\n"
            "    sudo snap install multipass      # Linux"
        )
    version = _run(["version"], capture=True)
    log.info("multipass: %s", version.splitlines()[0] if version else "(version unknown)")


def list_vms() -> list[dict]:
    raw = _run(["list", "--format", "json"])
    return json.loads(raw)["list"]


def vm_exists(name: str) -> bool:
    return any(vm["name"] == name for vm in list_vms())


def info(name: str) -> dict:
    raw = _run(["info", name, "--format", "json"])
    return json.loads(raw)["info"][name]


def launch(
    name: str,
    *,
    release: str = "24.04",
    cpus: int = 4,
    memory_gb: int = 8,
    primary_disk_gb: int = 80,
    cloud_init: Path | None = None,
) -> None:
    """Create + boot an Ubuntu VM. No-op if it already exists."""
    if vm_exists(name):
        log.info("multipass VM %s already exists", name)
        return
    args = [
        "launch",
        release,
        "--name", name,
        "--cpus", str(cpus),
        "--memory", f"{memory_gb}G",
        "--disk", f"{primary_disk_gb}G",
    ]
    if cloud_init is not None:
        args.extend(["--cloud-init", str(cloud_init)])
    _run(args, capture=False)


def exec_remote(name: str, command: str, *, check: bool = True) -> subprocess.CompletedProcess[str]:
    """Run a command inside the VM via `multipass exec`."""
    return subprocess.run(
        ["multipass", "exec", name, "--", "sh", "-c", command],
        capture_output=True,
        text=True,
        check=check,
    )


def get_ipv4(name: str) -> str:
    """Return the VM's primary IPv4 address."""
    data = info(name)
    addrs = data.get("ipv4", [])
    if not addrs:
        raise MultipassError(f"no IPv4 address yet for {name}")
    return addrs[0]


def stop(name: str) -> None:
    _run(["stop", name])


def start(name: str) -> None:
    _run(["start", name])


def delete(name: str, *, purge: bool = True) -> None:
    if not vm_exists(name):
        log.info("multipass VM %s already absent", name)
        return
    _run(["delete", name])
    if purge:
        _run(["purge"])
    log.info("multipass VM %s deleted%s", name, " and purged" if purge else "")


def snapshot_take(name: str, snapshot_name: str, *, comment: str = "") -> None:
    """Snapshot a stopped VM. Multipass requires the VM to be stopped."""
    _run(["stop", name], check=False)
    args = ["snapshot", name, "--name", snapshot_name]
    if comment:
        args.extend(["--comment", comment])
    _run(args)
    _run(["start", name])


def snapshot_restore(name: str, snapshot_name: str) -> None:
    _run(["stop", name], check=False)
    _run(["restore", "--destructive", f"{name}.{snapshot_name}"])
    _run(["start", name])
