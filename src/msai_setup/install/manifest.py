"""Parse the declarative stack manifest (`components.toml`).

Mirrors the dotfiles `dt` installer model: each component names an idempotency
probe (`detect`), an install `method`, and optional `post` commands. Two
methods are supported today:

* ``apt``     -- install packages from the Ubuntu archive.
* ``curl_sh`` -- run an upstream ``curl | sh`` installer.

Pool creation and other destructive disk work are deliberately out of scope --
this installer brings up packages and daemons only.

Validation is intentionally strict: unknown keys, unknown methods, or a method
missing its required fields raise ``ManifestError`` so a typo in the TOML fails
loudly instead of silently skipping a component.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST_PATH = Path(__file__).with_name("components.toml")

_METHODS = {"apt", "curl_sh"}
_COMMON_KEYS = {"description", "detect", "post", "category", "needs_root", "method"}
_METHOD_KEYS = {
    "apt": {"packages"},
    "curl_sh": {"url", "extra_args", "shell"},
}


class ManifestError(ValueError):
    """Raised when the manifest is malformed."""


def _str_list() -> list[str]:
    return []


@dataclass(frozen=True)
class Component:
    """One installable stack component."""

    method: str
    description: str = ""
    detect: str = ""
    post: list[str] = field(default_factory=_str_list)
    category: str | None = None
    needs_root: bool = True
    # apt
    packages: list[str] = field(default_factory=_str_list)
    # curl_sh
    url: str = ""
    extra_args: list[str] = field(default_factory=_str_list)
    shell: str = "sh"


def _parse_component(name: str, spec: dict[str, object]) -> Component:
    method = spec.get("method")
    if not isinstance(method, str) or method not in _METHODS:
        raise ManifestError(f"{name}: method must be one of {sorted(_METHODS)}, got {method!r}")

    allowed = _COMMON_KEYS | _METHOD_KEYS[method]
    unknown = set(spec) - allowed
    if unknown:
        raise ManifestError(f"{name}: unknown key(s) {sorted(unknown)} for method '{method}'")

    if method == "apt" and not spec.get("packages"):
        raise ManifestError(f"{name}: apt method requires a non-empty 'packages' list")
    if method == "curl_sh" and not spec.get("url"):
        raise ManifestError(f"{name}: curl_sh method requires 'url'")

    return Component(**spec)  # type: ignore[arg-type]


def load_manifest(path: Path | None = None) -> dict[str, Component]:
    """Load and validate the manifest, preserving file (install) order."""
    raw = tomllib.loads((path or MANIFEST_PATH).read_text())
    return {name: _parse_component(name, spec) for name, spec in raw.items()}
