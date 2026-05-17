"""Full-pipeline orchestration for the lab.

Chains `provision` -> `apply` in one call. Idempotent: phases that finished
previously (per state.json) are skipped unless force=True.
"""

from __future__ import annotations

import logging
from typing import Literal

from msai_setup.lab import apply, provision, state
from msai_setup.lab.config import LabConfig, load_config

log = logging.getLogger(__name__)

DEFAULT_PLAYBOOKS = ("bootstrap", "ssh-hardening", "ufw", "zfs", "docker", "services")

StopAfter = Literal["provision", "apply", None]


def run_pipeline(
    *,
    playbooks: list[str] | None = None,
    force: bool = False,
    stop_after: StopAfter = None,
) -> None:
    """Run the full lab pipeline."""
    cfg = load_config()
    log.info("lab pipeline starting: vm=%s platform=%s", cfg.vm_name, cfg.platform)
    log.info("state file: %s", cfg.state_path)

    playbooks = list(playbooks) if playbooks else list(DEFAULT_PLAYBOOKS)

    # 1. Provision
    if force:
        state.reset_phase(cfg.state_path, "provision")
    provision.main()
    if stop_after == "provision":
        log.info("stopping after provision (stop_after='provision')")
        return

    # 2. Apply
    if force:
        state.reset_phase(cfg.state_path, "apply")
    apply.run_apply(playbooks)
    if stop_after == "apply":
        log.info("stopping after apply (stop_after='apply')")
        return

    log.info("lab pipeline complete")
    _show_summary(cfg)


def _show_summary(cfg: LabConfig) -> None:
    s = state.load(cfg.state_path)
    log.info("=" * 60)
    log.info("Lab summary")
    log.info("=" * 60)
    for phase, info in s.get("phases", {}).items():
        log.info("  %s: %s", phase, info.get("finished_at"))
    log.info("")
    log.info("Connect:")
    log.info("  ssh %s@127.0.0.1 -p %d", cfg.vm_user, cfg.ssh_forward_port)
