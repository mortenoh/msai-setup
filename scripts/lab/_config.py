"""Configuration for the MS-S1 MAX VirtualBox lab.

All defaults are tunable via environment variables, so phases can be re-run with
different settings without editing this file. Defaults aim for a usable lab on a
modern Mac with 16+ GB of host RAM.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env(key: str, default: str) -> str:
    return os.environ.get(key, default)


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key)
    return int(raw) if raw is not None else default


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


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

    # Ubuntu ISO
    ubuntu_release: str = _env("UBUNTU_RELEASE", "26.04")
    ubuntu_iso_filename: str = _env(
        "UBUNTU_ISO_FILENAME",
        "ubuntu-26.04-live-server-amd64.iso",
    )

    # SSH key to push to the VM during bootstrap. Defaults to a sensible
    # location; override if you keep keys elsewhere.
    ssh_public_key_path: Path = Path(_env(
        "SSH_PUBLIC_KEY",
        str(Path.home() / ".ssh" / "id_ed25519.pub"),
    ))

    @property
    def iso_url(self) -> str:
        return f"https://releases.ubuntu.com/{self.ubuntu_release}/{self.ubuntu_iso_filename}"

    @property
    def iso_sha256_url(self) -> str:
        return f"https://releases.ubuntu.com/{self.ubuntu_release}/SHA256SUMS"

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
