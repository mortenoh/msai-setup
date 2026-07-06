"""Tiny JSON-backed state store so phases can detect prior completion.

Each phase records that it finished by setting a key in the state file. The
orchestrator (`all.py`) checks these to skip phases that are already done.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, cast


def load(state_path: Path) -> dict[str, Any]:
    """Load the JSON state file, or return an empty dict if it doesn't exist."""
    if not state_path.exists():
        return {}
    data = json.loads(state_path.read_text())
    if not isinstance(data, dict):
        return {}
    return cast("dict[str, Any]", data)


def save(state_path: Path, state: dict[str, Any]) -> None:
    """Persist `state` to `state_path` atomically.

    Writes to a sibling `.partial` file and renames it into place (atomic on
    POSIX) so a crash mid-write can't leave a truncated/corrupt state file.
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = state_path.with_suffix(state_path.suffix + ".partial")
    tmp.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    tmp.rename(state_path)


def mark_phase_done(state_path: Path, phase: str, **extra: Any) -> None:
    """Record that `phase` finished successfully.

    Extra kwargs are stored alongside the timestamp for debugging (e.g. the
    Ubuntu release that was installed, the VM name, etc.).
    """
    state = load(state_path)
    state.setdefault("phases", {})
    finished_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    state["phases"][phase] = {
        "finished_at": finished_at,
        **extra,
    }
    save(state_path, state)


def is_phase_done(state_path: Path, phase: str) -> bool:
    """Return True if `phase` has been recorded as finished in the state file."""
    state = load(state_path)
    return phase in state.get("phases", {})


def reset_phase(state_path: Path, phase: str) -> None:
    """Forget that `phase` completed; the next run will redo it."""
    state = load(state_path)
    state.get("phases", {}).pop(phase, None)
    save(state_path, state)
