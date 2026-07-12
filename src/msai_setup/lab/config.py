"""Configuration for the MS-S1 MAX VirtualBox lab.

All defaults are tunable via environment variables, so phases can be re-run with
different settings without editing this file. Defaults aim for a usable lab on a
modern Mac with 16+ GB of host RAM.
"""

from __future__ import annotations

import os
import platform
import secrets
from dataclasses import dataclass, field
from pathlib import Path

from msai_setup.lab import instance as _instance
from msai_setup.lab.profiles import PROFILES, OSProfile, get_profile


def _default_vm_name() -> str:
    return os.environ.get("VM_NAME") or _instance.get_current() or "ms-s1-max-lab"


def _default_vm_password() -> str:
    """Return $VM_PASSWORD, or a strong random console password if unset.

    SSH password auth is disabled via cloud-init, so this only affects local
    console login on a throwaway VM. Provisioning surfaces the generated value
    (logs it and writes it beside the SSH key) so console access isn't lost.
    """
    return os.environ.get("VM_PASSWORD") or secrets.token_urlsafe(12)


def _default_target_dir() -> Path:
    return Path(os.environ.get("TARGET_DIR", "target")).resolve()


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    return int(raw) if raw is not None else default


def _env_bool(key: str, default: bool) -> bool:
    """Return a boolean env value; true/1/yes/on -> True (case-insensitive)."""
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in ("true", "1", "yes", "on")


def _detect_arch() -> str:
    """Return 'arm64' on Apple Silicon / ARM, 'amd64' on x86_64."""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return "amd64"


_HOST_ARCH = _detect_arch()


def _profile_or_server(key: str) -> OSProfile:
    """Return the profile for `key`, falling back to ubuntu-server if unknown.

    Module-level media defaults are derived from the profile named by $LAB_OS.
    A bad $LAB_OS must not blow up at import - load_config() validates it and
    raises a clean error - so here we degrade to the default profile.
    """
    try:
        return get_profile(key)
    except ValueError:
        return get_profile("ubuntu-server")


# The OS profile ($LAB_OS) selects which OS/install to run; default is a plain
# Ubuntu server, which yields exactly the media values used before profiles
# existed. VirtualBox on Apple Silicon ONLY runs ARM guests, and the ostype
# must match, so the profile auto-picks the right ISO+ostype from the host
# architecture. Override any individual media value via env vars if you want.
_DEFAULT_OS_PROFILE = _env("LAB_OS", "ubuntu-server")
_profile = _profile_or_server(_DEFAULT_OS_PROFILE)
_DEFAULT_ISO_FILENAME = _profile.iso_filename(_HOST_ARCH)
_DEFAULT_ISO_BASE = _profile.iso_base_url(_HOST_ARCH)
_DEFAULT_OSTYPE = _profile.ostype(_HOST_ARCH)
_DEFAULT_PLATFORM = _profile.platform(_HOST_ARCH)


@dataclass(frozen=True)
class LabConfig:
    """Configuration container for the lab.

    Read once at startup, passed to phases. Idempotent re-runs use the same
    config so the lab is deterministic.
    """

    # VM identity. `vm_name` reads the current-instance pointer (see
    # instance.py) at load_config() time so it picks up `msai use`/`msai
    # create` changes; fallback is a fixed name so --help doesn't blow up.
    vm_name: str = field(default_factory=_default_vm_name)
    vm_hostname: str = _env("VM_HOSTNAME", "")  # filled in load_config()
    vm_user: str = _env("VM_USER", "morten")
    vm_password: str = field(default_factory=_default_vm_password)
    vm_fullname: str = _env("VM_FULLNAME", "Morten Hansen")

    # VM hardware
    memory_mb: int = _env_int("VM_MEMORY_MB", 8192)
    cpus: int = _env_int("VM_CPUS", 4)
    vram_mb: int = _env_int("VM_VRAM_MB", 32)

    # Networking
    ssh_forward_port: int = _env_int("SSH_FORWARD_PORT", 2222)

    # Storage. Defaults to ./target relative to the current working
    # directory - run from the repo root and this lands at `./target/`,
    # which is already in .gitignore. Override via `TARGET_DIR=/abs/path`.
    target_dir: Path = field(default_factory=_default_target_dir)
    primary_disk_size_mb: int = _env_int("PRIMARY_DISK_SIZE_MB", 80000)
    lab_disk_count: int = _env_int("LAB_DISK_COUNT", 6)
    lab_disk_size_mb: int = _env_int("LAB_DISK_SIZE_MB", 8000)

    # Root-on-ZFS install disks, standing in for the MS-S1 MAX's two physical
    # NVMe drives (see docs/ubuntu/installation/zfs-root-alternative.md).
    #
    # These are the two dedicated stand-in drives the root-on-ZFS install flow
    # (`msai lab install-zfs-root`) partitions into rpool + tank. On the ext4
    # `msai create` VM they are also created (harmless, unused) so both VM
    # shapes share one config surface.
    #   index 1 = "fast" drive -> rpool (larger, EFI + pool member)
    #   index 2 = "slow" drive -> tank  (smaller, single pool member)
    # The size split is deliberate and load-bearing: the install playbook
    # identifies the two disks by stable /dev/disk/by-id/... path and treats the
    # LARGER as the fast/rpool drive and the smaller as slow/tank — mirroring the
    # real 4 TB (fast) vs 2 TB (slow) asymmetry. Keep fast > slow so that
    # ordering stays unambiguous.
    install_disk_count: int = _env_int("INSTALL_DISK_COUNT", 2)
    install_fast_disk_size_mb: int = _env_int("INSTALL_FAST_DISK_SIZE_MB", 24000)
    install_slow_disk_size_mb: int = _env_int("INSTALL_SLOW_DISK_SIZE_MB", 16000)

    # Ubuntu ISO + VirtualBox platform.
    #
    # Defaults auto-pick based on host architecture: arm Macs get the arm64
    # ISO + VBox ARM platform; everywhere else gets amd64 + x86. We drive the
    # Ubuntu install ourselves through a cloud-init CIDATA ISO (see
    # cloudinit.py), so VBoxManage's stale `unattended install` templates
    # don't enter the picture - any Ubuntu release works.
    #
    # The real MS-S1 MAX still targets 26.04 amd64; the lab is for exercising
    # the tools and workflow, not pinning the Ubuntu point release.
    #
    # `os_profile` ($LAB_OS) picks the OS/install flavour; it sources the four
    # media values below through the selected profile, so `ubuntu-server` (the
    # default) yields identical values to before profiles existed. Individual
    # env overrides (UBUNTU_ISO_FILENAME etc.) still win over the profile.
    os_profile: str = _env("LAB_OS", "ubuntu-server")
    # Boot the install with a visible GUI window by default (headless=False) so
    # the user can take over a stuck installer by hand. Set LAB_HEADLESS=1 for
    # a windowless headless boot.
    headless: bool = _env_bool("LAB_HEADLESS", False)
    host_arch: str = _HOST_ARCH
    platform: str = _env("VBOX_PLATFORM", _DEFAULT_PLATFORM)
    ubuntu_release: str = _env("UBUNTU_RELEASE", "26.04")
    ubuntu_iso_filename: str = _env("UBUNTU_ISO_FILENAME", _DEFAULT_ISO_FILENAME)
    ubuntu_iso_base_url: str = _env("UBUNTU_ISO_BASE_URL", _DEFAULT_ISO_BASE)
    vm_ostype: str = _env("VM_OSTYPE", _DEFAULT_OSTYPE)

    # SSH key to push to the VM via cloud-init.
    #
    # Default: a dedicated lab keypair generated under target/. This
    # isolates the lab from your main SSH keys (which may live in 1Password
    # SSH agent, a yubikey, etc) and makes the lab fully throwaway. Override
    # via $SSH_PUBLIC_KEY if you'd rather authorise a key you already have.
    ssh_public_key_path: Path = field(
        default_factory=lambda: Path(
            os.environ.get(
                "SSH_PUBLIC_KEY",
                str(_default_target_dir() / "lab_id_ed25519.pub"),
            )
        )
    )

    @property
    def iso_url(self) -> str:
        """Full download URL of the Ubuntu install ISO."""
        return f"{self.ubuntu_iso_base_url}/{self.ubuntu_iso_filename}"

    @property
    def iso_sha256_url(self) -> str:
        """URL of the SHA256SUMS file for the Ubuntu install ISO."""
        return f"{self.ubuntu_iso_base_url}/SHA256SUMS"

    @property
    def iso_path(self) -> Path:
        """Local path to the cached Ubuntu install ISO."""
        return self.target_dir / self.ubuntu_iso_filename

    @property
    def state_path(self) -> Path:
        """Local path to this instance's JSON state file."""
        return self.target_dir / f"{self.vm_name}-state.json"

    @property
    def primary_disk_path(self) -> Path:
        """Local path to this instance's primary VDI disk."""
        return self.target_dir / f"{self.vm_name}-primary.vdi"

    @property
    def cidata_iso_path(self) -> Path:
        """Local path to this instance's cloud-init CIDATA ISO."""
        return self.target_dir / f"{self.vm_name}-cidata.iso"

    @property
    def autoinstall_iso_path(self) -> Path:
        """Ubuntu ISO remastered with `autoinstall` baked into GRUB cmdline."""
        stem = Path(self.ubuntu_iso_filename).stem
        return self.target_dir / f"{stem}-autoinstall.iso"

    @property
    def console_password_path(self) -> Path:
        """File where the generated console password is recorded for the user."""
        return self.target_dir / f"{self.vm_name}-console-password.txt"

    def lab_disk_path(self, index: int) -> Path:
        """Local path to this instance's Nth extra lab VDI disk (1-indexed)."""
        return self.target_dir / f"{self.vm_name}-lab-{index:02d}.vdi"

    def install_disk_path(self, index: int) -> Path:
        """Local path to this instance's Nth root-on-ZFS install disk (1-indexed).

        Index 1 is the fast/rpool stand-in, index 2 the slow/tank stand-in.
        """
        return self.target_dir / f"{self.vm_name}-install-{index:02d}.vdi"

    def install_disk_size_mb(self, index: int) -> int:
        """Size (MiB) for the Nth install disk (1 = fast/rpool, 2 = slow/tank)."""
        return self.install_fast_disk_size_mb if index == 1 else self.install_slow_disk_size_mb

    @property
    def ssh_host(self) -> str:
        """Host the VM's forwarded SSH port is reachable on (always loopback)."""
        return "127.0.0.1"

    @property
    def profile(self) -> OSProfile:
        """The selected :class:`OSProfile` (validated by load_config)."""
        return get_profile(self.os_profile)

    @property
    def extra_packages(self) -> tuple[str, ...]:
        """Extra apt packages the profile folds into the autoinstall."""
        return self.profile.extra_packages

    @property
    def default_playbooks(self) -> tuple[str, ...]:
        """Ansible playbooks the profile wants applied post-provision."""
        return self.profile.default_playbooks


def load_config(vm_name: str | None = None) -> LabConfig:
    """Build a LabConfig.

    `vm_name` (if given) overrides the env / current-instance default and is
    used to scope all the per-instance paths (disks, ISOs, state file).
    """
    resolved_name = vm_name if vm_name is not None else _default_vm_name()
    config = LabConfig(vm_name=resolved_name)
    if not config.vm_hostname:
        config = LabConfig(vm_name=resolved_name, vm_hostname=f"{config.vm_name}.local")

    # Validate env-sourced identifiers that flow into filenames / VBox VM names
    # / sudoers paths, so a malformed value fails fast instead of producing
    # broken paths or bad VBoxManage arguments downstream.
    _validate_identifier("VM_NAME / instance name", config.vm_name)
    _validate_identifier("VM_USER", config.vm_user)
    _validate_target_dir(config.target_dir)
    _validate_os_profile(config.os_profile)

    config.target_dir.mkdir(parents=True, exist_ok=True)
    return config


def _validate_identifier(label: str, value: str) -> None:
    """Reject values unsafe as filename prefixes / VBox names / usernames."""
    try:
        _instance.validate_name(value)
    except ValueError as e:
        raise ValueError(f"invalid {label}: {e}") from e


def _validate_os_profile(value: str) -> None:
    """Reject an unknown $LAB_OS with a message listing the valid profiles."""
    if value not in PROFILES:
        valid = ", ".join(sorted(PROFILES))
        raise ValueError(f"invalid LAB_OS: unknown OS profile '{value}'. Valid: {valid}")


def _validate_target_dir(path: Path) -> None:
    """Reject a TARGET_DIR that contains control characters or is empty."""
    raw = str(path)
    if not raw or any(ord(ch) < 0x20 for ch in raw):
        raise ValueError(f"invalid TARGET_DIR: {raw!r} (empty or contains control characters)")
