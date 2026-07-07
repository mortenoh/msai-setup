"""Host profile: server vs desktop.

The doctor runs the same checks everywhere, but what counts as a *problem*
depends on the role of the box. On the provisioned MS-S1 MAX server, missing
ZFS pools or KVM are real failures. On an experimental Ubuntu desktop install
of the same hardware, they are simply not set up yet and should not read as
red failures. The active profile decides which categories are expected.
"""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path

from msai_setup.doctor.checks import Category
from msai_setup.utils.shell import run_command


class Profile(Enum):
    """Role of the machine the doctor is running on."""

    SERVER = "server"
    DESKTOP = "desktop"


# Categories whose absence/failure genuinely matters, per profile. A category
# not listed here is downgraded from FAIL/WARN to SKIP with an explanatory note
# (it is "not expected on this profile"), so the report stays honest instead of
# flooding red on a box where that component was never meant to be installed.
_EXPECTED: dict[Profile, set[Category]] = {
    Profile.SERVER: set(Category),  # everything is expected on the real server
    Profile.DESKTOP: {
        Category.SYSTEM,
        Category.DOCKER,
        Category.INCUS,
        Category.GPU,
        Category.INFERENCE,
        Category.TAILSCALE,
    },
}


CONFIG_PATH = Path(os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))) / "msai" / "profile"


def category_expected(profile: Profile, category: Category) -> bool:
    """Whether a category's failures should be treated as real on this profile."""
    return category in _EXPECTED[profile]


def _auto_detect() -> Profile:
    """Guess the profile from the systemd default target (headless => server)."""
    result = run_command("systemctl get-default")
    if result.success and "graphical" in result.output:
        return Profile.DESKTOP
    return Profile.SERVER


def resolve_profile() -> tuple[Profile, str]:
    """Determine the active profile and how it was resolved.

    Resolution order: MSAI_PROFILE env var, then the config file, then
    autodetection from the systemd default target.

    Returns:
        (profile, source) where source is a short human-readable origin.
    """
    env = os.environ.get("MSAI_PROFILE")
    if env:
        try:
            return Profile(env.strip().lower()), "MSAI_PROFILE"
        except ValueError:
            pass  # fall through to other sources on a bad value

    if CONFIG_PATH.exists():
        raw = CONFIG_PATH.read_text().strip().lower()
        try:
            return Profile(raw), str(CONFIG_PATH)
        except ValueError:
            pass

    return _auto_detect(), "autodetected"


def set_profile(profile: Profile) -> Path:
    """Persist the profile to the config file and return its path."""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(profile.value + "\n")
    return CONFIG_PATH
