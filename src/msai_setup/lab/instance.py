"""Named lab instances + current-instance pointer.

Multiple lab VMs can coexist under `target/`; one is the "current" one,
and most commands target it implicitly. The current-instance pointer lives
at `target/.current`.

Each instance owns these files in `target/`:
  <name>-primary.vdi
  <name>-lab-NN.vdi
  <name>-cidata.iso
  <name>-state.json

Shared across all instances:
  lab_id_ed25519, lab_id_ed25519.pub  (SSH keypair)
  ubuntu-<release>-*.iso              (cached install media)
  ubuntu-<release>-*-autoinstall.iso  (remastered install media)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path


def _target_dir() -> Path:
    return Path(os.environ.get("TARGET_DIR", "target")).resolve()


def _pointer_path() -> Path:
    return _target_dir() / ".current"


_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,30}$")


def validate_name(name: str) -> None:
    """Reject names that aren't safe as VBox VM names / filename prefixes."""
    if not _NAME_RE.match(name):
        raise ValueError(
            f"invalid instance name {name!r}: must match {_NAME_RE.pattern} "
            "(lowercase letters, digits, hyphens; 1-31 chars)"
        )


def get_current() -> str | None:
    """Return the currently-selected instance name, or None if unset."""
    p = _pointer_path()
    if not p.exists():
        return None
    val = p.read_text().strip()
    return val or None


def set_current(name: str) -> None:
    """Make `name` the current instance."""
    validate_name(name)
    target = _target_dir()
    target.mkdir(parents=True, exist_ok=True)
    _pointer_path().write_text(name + "\n")


def clear_current() -> None:
    """Forget which instance is current."""
    p = _pointer_path()
    if p.exists():
        p.unlink()


@dataclass(frozen=True)
class InstanceInfo:
    """Summary of one lab instance."""

    name: str
    state_file: Path
    has_state: bool
    has_disks: bool
    is_current: bool


def list_instances() -> list[InstanceInfo]:
    """Enumerate lab instances visible on disk."""
    target = _target_dir()
    current = get_current()
    if not target.exists():
        return []

    names: set[str] = set()
    # state files: <name>-state.json
    for p in target.glob("*-state.json"):
        names.add(p.name.removesuffix("-state.json"))
    # disk-only instances (no state yet): <name>-primary.vdi
    for p in target.glob("*-primary.vdi"):
        names.add(p.name.removesuffix("-primary.vdi"))

    out: list[InstanceInfo] = []
    for name in sorted(names):
        state_file = target / f"{name}-state.json"
        primary = target / f"{name}-primary.vdi"
        out.append(
            InstanceInfo(
                name=name,
                state_file=state_file,
                has_state=state_file.exists(),
                has_disks=primary.exists(),
                is_current=(name == current),
            )
        )
    return out


def require_current() -> str:
    """Return the current instance name or raise SystemExit with a helpful hint."""
    name = get_current()
    if name is None:
        raise SystemExit(
            "no current instance selected.\n"
            "Create one:           msai create <name>\n"
            "Or switch to an existing one:   msai use <name>\n"
            "List what exists:     msai list"
        )
    return name
