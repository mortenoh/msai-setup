"""Configuration for the MS-S1 MAX VirtualBox lab.

All defaults are tunable via environment variables, so phases can be re-run with
different settings without editing this file. Defaults aim for a usable lab on a
modern Mac with 16+ GB of host RAM.
"""

from __future__ import annotations

import os
import platform
from dataclasses import dataclass
from pathlib import Path


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


REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_HOST_ARCH = _detect_arch()

# Ubuntu ISO locations differ by architecture:
#   - amd64: https://releases.ubuntu.com/<release>/...
#   - arm64: https://cdimage.ubuntu.com/releases/<release>/release/...
#
# VirtualBox on Apple Silicon ONLY runs ARM guests, and the ostype must
# match. The defaults below auto-pick the right ISO+ostype based on the
# host architecture; override anything via env vars if you want.
if _HOST_ARCH == "arm64":
    _DEFAULT_ISO_FILENAME = "ubuntu-24.04.3-live-server-arm64.iso"
    _DEFAULT_ISO_BASE = "https://cdimage.ubuntu.com/releases/24.04/release"
    _DEFAULT_OSTYPE = "Ubuntu24_LTS_arm64"
else:
    _DEFAULT_ISO_FILENAME = "ubuntu-24.04.4-live-server-amd64.iso"
    _DEFAULT_ISO_BASE = "https://releases.ubuntu.com/24.04"
    _DEFAULT_OSTYPE = "Ubuntu24_LTS_64"


@dataclass(frozen=True)
class LabConfig:
    """Configuration container for the lab.

    Read once at startup, passed to phases. Idempotent re-runs use the same
    config so the lab is deterministic.
    """

    # VM identity
    vm_name: str = _env("VM_NAME", "ms-s1-max-lab")
    vm_hostname: str = _env("VM_HOSTNAME", "ms-s1-max-lab.local")
    vm_user: str = _env("VM_USER", "morten")
    vm_password: str = _env("VM_PASSWORD", "changeme")
    vm_fullname: str = _env("VM_FULLNAME", "Morten Hansen")

    # VM hardware
    memory_mb: int = _env_int("VM_MEMORY_MB", 8192)
    cpus: int = _env_int("VM_CPUS", 4)
    vram_mb: int = _env_int("VM_VRAM_MB", 32)

    # Networking
    ssh_forward_port: int = _env_int("SSH_FORWARD_PORT", 2222)

    # Storage
    target_dir: Path = REPO_ROOT / _env("TARGET_DIR", "target")
    primary_disk_size_mb: int = _env_int("PRIMARY_DISK_SIZE_MB", 80000)
    lab_disk_count: int = _env_int("LAB_DISK_COUNT", 6)
    lab_disk_size_mb: int = _env_int("LAB_DISK_SIZE_MB", 8000)

    # Ubuntu ISO.
    #
    # Defaults auto-pick based on host architecture (Apple Silicon Macs need
    # arm64; everywhere else amd64). VirtualBox 7.2.x ships unattended-install
    # templates up to ~Ubuntu 25.04; for newer releases the script falls back
    # to interactive install automatically (see 01_provision.py).
    #
    # The real MS-S1 MAX install still targets 26.04 amd64; the lab is for
    # exercising the tools and workflow, not pinning the Ubuntu point release.
    host_arch: str = _HOST_ARCH
    ubuntu_release: str = _env("UBUNTU_RELEASE", "24.04")
    ubuntu_iso_filename: str = _env("UBUNTU_ISO_FILENAME", _DEFAULT_ISO_FILENAME)
    ubuntu_iso_base_url: str = _env("UBUNTU_ISO_BASE_URL", _DEFAULT_ISO_BASE)
    vm_ostype: str = _env("VM_OSTYPE", _DEFAULT_OSTYPE)

    # SSH key to push to the VM during bootstrap. Defaults to a sensible
    # location; override if you keep keys elsewhere.
    ssh_public_key_path: Path = Path(_env(
        "SSH_PUBLIC_KEY",
        str(Path.home() / ".ssh" / "id_ed25519.pub"),
    ))

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

    def lab_disk_path(self, index: int) -> Path:
        return self.target_dir / f"{self.vm_name}-lab-{index:02d}.vdi"

    @property
    def ssh_host(self) -> str:
        return "127.0.0.1"


def load_config() -> LabConfig:
    """Build a LabConfig from current env. Call once per phase."""
    config = LabConfig()
    config.target_dir.mkdir(parents=True, exist_ok=True)
    return config
