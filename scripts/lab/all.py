#!/usr/bin/env python3
"""Run the whole lab pipeline end-to-end.

Idempotent: phases that finished previously (per state.json) are skipped
unless --force is passed. Each phase is callable on its own; this orchestrator
just chains them.

Usage:

    python3 scripts/lab/all.py                      # full pipeline
    python3 scripts/lab/all.py --provisioner multipass  # default on Apple Silicon
    python3 scripts/lab/all.py --provisioner vbox       # x86_64 Macs / Linux / Windows
    python3 scripts/lab/all.py --force                  # re-run everything
    python3 scripts/lab/all.py --stop-after apply       # stop after Ansible

Phases:

    provision    — VBox or Multipass: create VM, install Ubuntu, wait for SSH
    apply        — Ansible: bootstrap, ssh-hardening, ufw, zfs, docker, services
"""

from __future__ import annotations

import argparse
import logging
import platform
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lab import _state  # noqa: E402
from lab._config import load_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("lab.all")

LAB_DIR = Path(__file__).resolve().parent


def _default_provisioner() -> str:
    """Apple Silicon -> multipass; everything else -> vbox."""
    return "multipass" if platform.machine().lower() in ("arm64", "aarch64") else "vbox"


def run_python_phase(script_name: str, *, force: bool, cfg) -> None:
    """Spawn another Python file in scripts/lab/ as a phase."""
    if force:
        _state.reset_phase(cfg.state_path, script_name.removeprefix("01_").removeprefix("02_").removesuffix(".py").removesuffix("_multipass"))
    log.info("running phase: %s", script_name)
    subprocess.run(
        [sys.executable, str(LAB_DIR / script_name)],
        check=True,
    )


def run_ansible_phase(*playbooks: str) -> None:
    cmd = [sys.executable, str(LAB_DIR / "02_apply.py"), *playbooks]
    log.info("running phase: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--provisioner",
        choices=("vbox", "multipass"),
        default=_default_provisioner(),
        help="VM provisioner (default: auto-detected from host arch)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Re-run phases even if state.json says they already finished",
    )
    parser.add_argument(
        "--stop-after",
        choices=("provision", "apply"),
        help="Stop after the named phase",
    )
    parser.add_argument(
        "--playbooks",
        default="bootstrap,ssh-hardening,ufw,zfs,docker,services",
        help="Comma-separated playbooks for the apply phase",
    )
    args = parser.parse_args(argv)

    cfg = load_config()
    log.info("lab pipeline starting: provisioner=%s vm=%s", args.provisioner, cfg.vm_name)
    log.info("state file: %s", cfg.state_path)

    # 1. provision
    provision_script = (
        "01_provision_multipass.py" if args.provisioner == "multipass" else "01_provision.py"
    )
    run_python_phase(provision_script, force=args.force, cfg=cfg)
    if args.stop_after == "provision":
        log.info("stopping after provision (--stop-after provision)")
        return

    # 2. apply
    playbooks = [p.strip() for p in args.playbooks.split(",") if p.strip()]
    run_ansible_phase(*playbooks)
    if args.stop_after == "apply":
        log.info("stopping after apply (--stop-after apply)")
        return

    log.info("lab pipeline complete")
    _show_summary(cfg)


def _show_summary(cfg) -> None:
    state = _state.load(cfg.state_path)
    log.info("=" * 60)
    log.info("Lab summary")
    log.info("=" * 60)
    for phase, info in state.get("phases", {}).items():
        log.info("  %s: %s", phase, info.get("finished_at"))
    log.info("")
    log.info("Connect:")
    log.info("  ssh %s@127.0.0.1 -p %d   # if provisioned via VBox", cfg.vm_user, cfg.ssh_forward_port)
    log.info("  multipass shell %s        # if provisioned via Multipass", cfg.vm_name)


if __name__ == "__main__":
    main(sys.argv[1:])
