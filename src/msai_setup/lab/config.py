"""Configuration for the MS-S1 MAX VirtualBox lab.

All defaults are tunable via environment variables, so phases can be re-run with
different settings without editing this file. Defaults aim for a usable lab on a
modern Mac with 16+ GB of host RAM.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass, field
from pathlib import Path

from msai_setup.lab import instance as _instance


def _default_vm_name() -> str:
    return os.environ.get("VM_NAME") or _instance.get_current() or "ms-s1-max-lab"


def _default_target_dir() -> Path:
    return Path(os.environ.get("TARGET_DIR", "target")).resolve()


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    return int(raw) if raw is not None else default


def _detect_arch() -> str:
    """Return 'arm64' on Apple Silicon / ARM, 'amd64' on x86_64."""
    machine = platform.machine().lower()
    if machine in ("arm64", "aarch64"):
        return "arm64"
    return "amd64"


_HOST_ARCH = _detect_arch()

# Ubuntu ISO locations differ by architecture:
#   - amd64: https://releases.ubuntu.com/<release>/...
#   - arm64: https://cdimage.ubuntu.com/releases/<release>/release/...
#
# VirtualBox on Apple Silicon ONLY runs ARM guests, and the ostype must
# match. The defaults below auto-pick the right ISO+ostype based on the
# host architecture; override anything via env vars if you want.
if _HOST_ARCH == "arm64":
    _DEFAULT_ISO_FILENAME = "ubuntu-26.04-live-server-arm64.iso"
    _DEFAULT_ISO_BASE = "https://cdimage.ubuntu.com/releases/26.04/release"
    # VBox 7.2 doesn't ship an Ubuntu26_LTS_arm64 ostype yet; the generic
    # ARM64 Ubuntu type is fine - it only affects hardware hints, not boot.
    _DEFAULT_OSTYPE = "Ubuntu_arm64"
    _DEFAULT_PLATFORM = "arm"
else:
    _DEFAULT_ISO_FILENAME = "ubuntu-26.04-live-server-amd64.iso"
    _DEFAULT_ISO_BASE = "https://releases.ubuntu.com/26.04"
    _DEFAULT_OSTYPE = "Ubuntu_64"
    _DEFAULT_PLATFORM = "x86"


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
    vm_password: str = _env("VM_PASSWORD", "changeme")
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
        return f"{self.ubuntu_iso_base_url}/{self.ubuntu_iso_filename}"

    @property
    def iso_sha256_url(self) -> str:
        return f"{self.ubuntu_iso_base_url}/SHA256SUMS"

    @property
    def iso_path(self) -> Path:
        return self.target_dir / self.ubuntu_iso_filename

    @property
    def state_path(self) -> Path:
        return self.target_dir / f"{self.vm_name}-state.json"

    @property
    def primary_disk_path(self) -> Path:
        return self.target_dir / f"{self.vm_name}-primary.vdi"

    @property
    def cidata_iso_path(self) -> Path:
        return self.target_dir / f"{self.vm_name}-cidata.iso"

    @property
    def autoinstall_iso_path(self) -> Path:
        """Ubuntu ISO remastered with `autoinstall` baked into GRUB cmdline."""
        stem = Path(self.ubuntu_iso_filename).stem
        return self.target_dir / f"{stem}-autoinstall.iso"

    def lab_disk_path(self, index: int) -> Path:
        return self.target_dir / f"{self.vm_name}-lab-{index:02d}.vdi"

    @property
    def ssh_host(self) -> str:
        return "127.0.0.1"


def load_config(vm_name: str | None = None) -> LabConfig:
    """Build a LabConfig.

    `vm_name` (if given) overrides the env / current-instance default and is
    used to scope all the per-instance paths (disks, ISOs, state file).
    """
    overrides: dict[str, str] = {}
    if vm_name is not None:
        overrides["vm_name"] = vm_name
    config = LabConfig(**overrides) if overrides else LabConfig()
    if not config.vm_hostname:
        config = LabConfig(**{**overrides, "vm_hostname": f"{config.vm_name}.local"})
    config.target_dir.mkdir(parents=True, exist_ok=True)
    return config
