"""OS profiles for the lab — what to install, independent of host arch.

An :class:`OSProfile` describes *which* operating system a lab VM should run
and *how* it is installed, without hardcoding the host architecture. The same
profile yields arm64 media on an Apple-Silicon Mac and amd64 media on an x86
host; the arch-aware bits live in the profile's `*(arch)` methods, which the
config layer calls after autodetecting the host arch.

This is the seam future OSes plug into (Windows via autounattend, ...). Today
the Ubuntu family (Subiquity autoinstall) and the Fedora family (kickstart via
an OEMDRV-labelled seed ISO) are registered; their media methods branch on
`family` since the two distros lay out ISOs, checksums, and installers very
differently.

The Ubuntu media values here MUST match what config.py historically computed so
that the default `ubuntu-server` profile produces a byte-for-byte identical VM
to before profiles existed.

Fedora media are pinned to a specific release/build (see the fedora profile);
config.py layers FEDORA_* env overrides on top for a different release.
"""

from __future__ import annotations

from dataclasses import dataclass

# Fedora Server netinst media, pinned to the current stable release. Verified
# 2026-07 against the Fedora mirror directory index
# (download.fedoraproject.org/pub/fedora/linux/releases/44/Server/<arch>/iso/).
# Bump these (and re-verify the exact build suffix) when Fedora N+1 ships; every
# value is env-overridable via FEDORA_* in config.py.
_FEDORA_RELEASE = "44"
_FEDORA_BUILD = "1.7"


@dataclass(frozen=True)
class OSProfile:
    """An installable OS, described independently of the host architecture.

    Arch-specific media (ISO name, download base, VBox ostype/platform) are
    NOT stored as fields — they are derived per-arch by the `*(arch)` methods,
    since one profile serves both arm64 and amd64 hosts.
    """

    # Stable registry key, e.g. "ubuntu-server". Used on the CLI (`--os`) and
    # in $LAB_OS, and recorded in the VM state file.
    key: str

    # Human-facing label for logs / help text.
    display_name: str

    # OS family, e.g. "ubuntu". Future families: "fedora", "windows". Lets code
    # branch on the family without matching individual keys.
    family: str

    # Install mechanism. Only "subiquity" (Ubuntu autoinstall) is wired up
    # today; "kickstart" (Fedora) and "autounattend" (Windows) are reserved for
    # later and intentionally NOT implemented yet.
    unattended: str

    # Extra apt packages folded into the autoinstall `packages:` list on top of
    # the always-present baseline (openssh-server, python3). Empty for a plain
    # server; the desktop profile pulls in the GUI + an RDP server here.
    extra_packages: tuple[str, ...]

    # Ansible playbooks this profile wants applied after provisioning. Declared
    # here so callers know the profile's intent; the playbooks themselves live
    # under the Ansible tree and are authored separately.
    default_playbooks: tuple[str, ...]

    # True for a desktop/graphical install, False for a headless server. Drives
    # nothing in the media methods (Ubuntu desktop uses the same ISO) — it's a
    # hint for callers deciding whether a visible console is worthwhile.
    is_graphical: bool

    def iso_filename(self, arch: str) -> str:
        """Installer ISO filename for the given arch ('arm64' | 'amd64').

        Both Ubuntu server and desktop use the SAME live-server ISO: the
        desktop is achieved by installing desktop packages via autoinstall
        (see `extra_packages`), NOT by fetching a different (desktop) image.
        Fedora uses the small Server **netinst** ISO (fast to download/test).
        """
        if self.family == "fedora":
            cpu = "aarch64" if arch == "arm64" else "x86_64"
            return f"Fedora-Server-netinst-{cpu}-{_FEDORA_RELEASE}-{_FEDORA_BUILD}.iso"
        suffix = "arm64" if arch == "arm64" else "amd64"
        return f"ubuntu-26.04-live-server-{suffix}.iso"

    def iso_base_url(self, arch: str) -> str:
        """Base URL the installer ISO + checksum are fetched from.

        Ubuntu splits its media hosting by arch: amd64 lives on
        releases.ubuntu.com, arm64 on cdimage.ubuntu.com/releases/.../release.
        Fedora serves both arches from download.fedoraproject.org, which
        302-redirects to a mirror (urllib follows it fine).
        """
        if self.family == "fedora":
            cpu = "aarch64" if arch == "arm64" else "x86_64"
            return (
                "https://download.fedoraproject.org/pub/fedora/linux/releases/"
                f"{_FEDORA_RELEASE}/Server/{cpu}/iso"
            )
        if arch == "arm64":
            return "https://cdimage.ubuntu.com/releases/26.04/release"
        return "https://releases.ubuntu.com/26.04"

    def checksum_filename(self, arch: str) -> str:
        """Filename of the checksum manifest within `iso_base_url(arch)`.

        Ubuntu ships a single `SHA256SUMS` covering every image; Fedora ships a
        per-release/per-arch `Fedora-Server-<rel>-<build>-<cpu>-CHECKSUM`.
        """
        if self.family == "fedora":
            cpu = "aarch64" if arch == "arm64" else "x86_64"
            return f"Fedora-Server-{_FEDORA_RELEASE}-{_FEDORA_BUILD}-{cpu}-CHECKSUM"
        return "SHA256SUMS"

    def checksum_url(self, arch: str) -> str:
        """Absolute URL of the checksum manifest for the given arch."""
        return f"{self.iso_base_url(arch)}/{self.checksum_filename(arch)}"

    def ostype(self, arch: str) -> str:
        """VBox `--ostype` for the given arch (verified via `VBoxManage list ostypes`).

        VBox 7.2 doesn't ship an Ubuntu26_LTS_arm64 ostype yet; the generic
        Ubuntu_arm64 type is fine — it only affects hardware hints, not boot.
        Fedora has first-class Fedora_64 / Fedora_arm64 types.
        """
        if self.family == "fedora":
            return "Fedora_arm64" if arch == "arm64" else "Fedora_64"
        return "Ubuntu_arm64" if arch == "arm64" else "Ubuntu_64"

    def platform(self, arch: str) -> str:
        """VBox `--platform-architecture` for the given arch ('arm' | 'x86')."""
        return "arm" if arch == "arm64" else "x86"


# Registry of known profiles, keyed by `OSProfile.key`.
PROFILES: dict[str, OSProfile] = {
    "ubuntu-server": OSProfile(
        key="ubuntu-server",
        display_name="Ubuntu Server 26.04",
        family="ubuntu",
        unattended="subiquity",
        extra_packages=(),
        default_playbooks=(),
        is_graphical=False,
    ),
    "ubuntu-desktop": OSProfile(
        key="ubuntu-desktop",
        display_name="Ubuntu Desktop 26.04 (GNOME + RDP)",
        family="ubuntu",
        unattended="subiquity",
        # Same live-server ISO as the server profile; the GUI comes from these
        # packages. `xrdp` exposes the desktop over RDP for headless access.
        extra_packages=("ubuntu-desktop-minimal", "xrdp"),
        default_playbooks=("rdp",),
        is_graphical=True,
    ),
    "fedora": OSProfile(
        key="fedora",
        display_name=f"Fedora Server {_FEDORA_RELEASE}",
        family="fedora",
        # Kickstart delivered via an OEMDRV-labelled seed ISO (auto-detected by
        # anaconda); no GRUB remaster, unlike the Ubuntu subiquity path.
        unattended="kickstart",
        extra_packages=(),
        default_playbooks=(),
        is_graphical=False,
    ),
}


def get_profile(key: str) -> OSProfile:
    """Return the registered :class:`OSProfile` for `key`.

    Raises:
        ValueError: If `key` isn't a known profile; the message lists the valid
            keys so the user can correct a typo.
    """
    try:
        return PROFILES[key]
    except KeyError:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"unknown OS profile '{key}'. Valid: {valid}") from None
