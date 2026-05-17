"""Tiny JSON-backed state store so phases can detect prior completion.

Each phase records that it finished by setting a key in the state file. The
orchestrator (`all.py`) checks these to skip phases that are already done.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any


def load(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text())


def save(state_path: Path, state: dict[str, Any]) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def mark_phase_done(state_path: Path, phase: str, **extra: Any) -> None:
    """Record that `phase` finished successfully.

    Extra kwargs are stored alongside the timestamp for debugging (e.g. the
    Ubuntu release that was installed, the VM name, etc.).
    """
    state = load(state_path)
    state.setdefault("phases", {})
    state["phases"][phase] = {
        "finished_at": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        **extra,
    }
    save(state_path, state)


def is_phase_done(state_path: Path, phase: str) -> bool:
    state = load(state_path)
    return phase in state.get("phases", {})


def reset_phase(state_path: Path, phase: str) -> None:
    """Forget that `phase` completed; the next run will redo it."""
    state = load(state_path)
    state.get("phases", {}).pop(phase, None)
    save(state_path, state)
