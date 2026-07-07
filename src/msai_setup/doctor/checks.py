"""Individual health check functions."""

import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from msai_setup.utils.formatting import CheckStatus
from msai_setup.utils.shell import command_exists, is_service_running, run_command


class Category(Enum):
    """Check categories."""

    SYSTEM = "system"
    ZFS = "zfs"
    DOCKER = "docker"
    INCUS = "incus"
    KVM = "kvm"
    GPU = "gpu"
    INFERENCE = "inference"
    TAILSCALE = "tailscale"


@dataclass
class CheckResult:
    """Result of a health check."""

    name: str
    status: CheckStatus
    message: str
    category: Category
    detail: str | None = None
    fix: str | None = None


# Type alias for check functions
CheckFunction = Callable[[], CheckResult]


@dataclass
class Check:
    """A health check definition."""

    name: str
    run: CheckFunction


def _default_checks() -> list[tuple[Category, Check]]:
    return []


@dataclass
class CheckRegistry:
    """Registry of all health checks."""

    checks: list[tuple[Category, Check]] = field(default_factory=_default_checks)

    def register(self, category: Category, check: Check) -> None:
        """Register a check under a category."""
        self.checks.append((category, check))

    def get_checks(self, categories: list[Category] | None = None) -> list[tuple[Category, Check]]:
        """Get checks, optionally filtered by category."""
        if categories is None:
            return self.checks
        return [(cat, check) for cat, check in self.checks if cat in categories]


# Global registry
registry = CheckRegistry()


def register_check(category: Category, name: str) -> Callable[[CheckFunction], CheckFunction]:
    """Decorator to register a check function."""

    def decorator(func: CheckFunction) -> CheckFunction:
        check = Check(name=name, run=func)
        registry.register(category, check)
        return func

    return decorator


# =============================================================================
# System Checks
# =============================================================================


@register_check(Category.SYSTEM, "Ubuntu version")
def check_ubuntu_version() -> CheckResult:
    """Check Ubuntu version is 26.04 LTS."""
    result = run_command("lsb_release -rs")
    if not result.success:
        return CheckResult(
            name="Ubuntu version",
            status=CheckStatus.FAIL,
            message="Could not determine Ubuntu version",
            category=Category.SYSTEM,
            detail=result.stderr,
        )

    version = result.output
    if version.startswith("26.04"):
        # Get full description
        desc_result = run_command("lsb_release -ds")
        desc = desc_result.output if desc_result.success else f"Ubuntu {version}"
        return CheckResult(
            name="Ubuntu version",
            status=CheckStatus.OK,
            message=desc,
            category=Category.SYSTEM,
        )

    return CheckResult(
        name="Ubuntu version",
        status=CheckStatus.WARN,
        message=f"Ubuntu {version} (expected 26.04 LTS)",
        category=Category.SYSTEM,
    )


@register_check(Category.SYSTEM, "Kernel version")
def check_kernel_version() -> CheckResult:
    """Check kernel version is 7.0+ (26.04 default); 6.18+ is the gfx1151 floor."""
    result = run_command("uname -r")
    if not result.success:
        return CheckResult(
            name="Kernel version",
            status=CheckStatus.FAIL,
            message="Could not determine kernel version",
            category=Category.SYSTEM,
        )

    kernel = result.output
    # Extract major.minor version
    match = re.match(r"(\d+)\.(\d+)", kernel)
    if match:
        major, minor = int(match.group(1)), int(match.group(2))
        if major >= 7 or (major == 6 and minor >= 18):
            return CheckResult(
                name="Kernel version",
                status=CheckStatus.OK,
                message=f"Kernel {kernel}",
                category=Category.SYSTEM,
            )

    return CheckResult(
        name="Kernel version",
        status=CheckStatus.WARN,
        message=f"Kernel {kernel} (recommend 7.0+ (26.04 default); 6.18+ is the documented gfx1151 floor)",
        category=Category.SYSTEM,
    )


@register_check(Category.SYSTEM, "Memory")
def check_memory() -> CheckResult:
    """Check system memory is 128GB."""
    result = run_command("grep MemTotal /proc/meminfo")
    if not result.success:
        return CheckResult(
            name="Memory",
            status=CheckStatus.FAIL,
            message="Could not read memory info",
            category=Category.SYSTEM,
        )

    # Parse "MemTotal:       131890068 kB"
    match = re.search(r"(\d+)", result.output)
    if match:
        kb = int(match.group(1))
        gb = kb / (1024 * 1024)
        gb_rounded = round(gb)

        if gb_rounded >= 120:  # Allow some tolerance
            return CheckResult(
                name="Memory",
                status=CheckStatus.OK,
                message=f"Memory: {gb_rounded}GB",
                category=Category.SYSTEM,
            )

        return CheckResult(
            name="Memory",
            status=CheckStatus.WARN,
            message=f"Memory: {gb_rounded}GB (expected 128GB)",
            category=Category.SYSTEM,
        )

    return CheckResult(
        name="Memory",
        status=CheckStatus.FAIL,
        message="Could not parse memory info",
        category=Category.SYSTEM,
    )


@register_check(Category.SYSTEM, "CPU")
def check_cpu() -> CheckResult:
    """Check CPU is AMD Ryzen AI Max (Strix Halo)."""
    result = run_command("grep 'model name' /proc/cpuinfo")
    if not result.success:
        return CheckResult(
            name="CPU",
            status=CheckStatus.FAIL,
            message="Could not read CPU info",
            category=Category.SYSTEM,
        )

    # Get first match
    lines = result.output.strip().split("\n")
    if lines:
        cpu_name = lines[0].split(":")[-1].strip()
        if "ryzen ai max" in cpu_name.lower():
            return CheckResult(
                name="CPU",
                status=CheckStatus.OK,
                message=f"CPU: {cpu_name} (Strix Halo)",
                category=Category.SYSTEM,
            )

        return CheckResult(
            name="CPU",
            status=CheckStatus.WARN,
            message=f"CPU: {cpu_name}",
            category=Category.SYSTEM,
        )

    return CheckResult(
        name="CPU",
        status=CheckStatus.FAIL,
        message="Could not parse CPU info",
        category=Category.SYSTEM,
    )


@register_check(Category.SYSTEM, "SSH hardened")
def check_ssh_hardened() -> CheckResult:
    """Check SSH is hardened (password auth disabled)."""
    sshd_config = Path("/etc/ssh/sshd_config")
    if not sshd_config.exists():
        return CheckResult(
            name="SSH hardened",
            status=CheckStatus.SKIP,
            message="sshd_config not found",
            category=Category.SYSTEM,
        )

    result = run_command("grep -i '^PasswordAuthentication' /etc/ssh/sshd_config")
    if result.success:
        if "no" in result.output.lower():
            return CheckResult(
                name="SSH hardened",
                status=CheckStatus.OK,
                message="PasswordAuthentication disabled",
                category=Category.SYSTEM,
            )

    # Check sshd_config.d directory
    result_d = run_command("grep -ri '^PasswordAuthentication' /etc/ssh/sshd_config.d/")
    if result_d.success and "no" in result_d.output.lower():
        return CheckResult(
            name="SSH hardened",
            status=CheckStatus.OK,
            message="PasswordAuthentication disabled",
            category=Category.SYSTEM,
        )

    return CheckResult(
        name="SSH hardened",
        status=CheckStatus.WARN,
        message="Password authentication may be enabled",
        category=Category.SYSTEM,
        fix="Add 'PasswordAuthentication no' to /etc/ssh/sshd_config",
    )


_AUDIO_POWERSAVE_FIX = (
    "echo 'options snd_hda_intel power_save=0 power_save_controller=N' "
    "| sudo tee /etc/modprobe.d/audio-disable-powersave.conf"
)


@register_check(Category.SYSTEM, "Audio power save")
def check_audio_powersave() -> CheckResult:
    """Check the snd_hda_intel codec power save is disabled persistently.

    The MS-S1 MAX emits idle static/pop when the HD-audio codec suspends. The
    fix is a modprobe drop-in setting power_save=0; a runtime-only value does
    not survive reboot. See docs/ubuntu/troubleshooting/audio-noise.md.
    """
    param = Path("/sys/module/snd_hda_intel/parameters/power_save")
    if not param.exists():
        return CheckResult(
            name="Audio power save",
            status=CheckStatus.SKIP,
            message="snd_hda_intel not loaded (no HD-audio codec)",
            category=Category.SYSTEM,
        )

    # A persistent drop-in is the only thing that survives reboot.
    persistent = run_command(
        "grep -rlE 'snd_hda_intel.*power_save[[:space:]]*=[[:space:]]*0' /etc/modprobe.d/"
    )
    if persistent.success and persistent.output.strip():
        return CheckResult(
            name="Audio power save",
            status=CheckStatus.OK,
            message=f"Disabled persistently ({persistent.output.splitlines()[0].strip()})",
            category=Category.SYSTEM,
        )

    runtime = param.read_text().strip()
    if runtime == "0":
        return CheckResult(
            name="Audio power save",
            status=CheckStatus.WARN,
            message="Disabled at runtime only, not persistent (static noise returns on reboot)",
            category=Category.SYSTEM,
            fix=_AUDIO_POWERSAVE_FIX,
        )

    return CheckResult(
        name="Audio power save",
        status=CheckStatus.WARN,
        message=f"Enabled (power_save={runtime}); codec suspend causes idle static noise",
        category=Category.SYSTEM,
        fix=_AUDIO_POWERSAVE_FIX,
    )


# =============================================================================
# ZFS Checks
# =============================================================================


@register_check(Category.ZFS, "Pool exists")
def check_zfs_pool_exists() -> CheckResult:
    """Check tank pool is imported."""
    result = run_command("zpool list tank")
    if result.success:
        return CheckResult(
            name="Pool exists",
            status=CheckStatus.OK,
            message="Pool 'tank' is imported",
            category=Category.ZFS,
        )

    if "no such pool" in result.stderr.lower():
        return CheckResult(
            name="Pool exists",
            status=CheckStatus.FAIL,
            message="Pool 'tank' not found",
            category=Category.ZFS,
            fix="sudo zpool import tank",
        )

    return CheckResult(
        name="Pool exists",
        status=CheckStatus.FAIL,
        message="ZFS not available",
        category=Category.ZFS,
        detail=result.stderr,
    )


@register_check(Category.ZFS, "Pool health")
def check_zfs_pool_health() -> CheckResult:
    """Check tank pool is healthy (ONLINE, no errors)."""
    result = run_command("zpool status tank")
    if not result.success:
        return CheckResult(
            name="Pool health",
            status=CheckStatus.SKIP,
            message="Pool health: skipped (pool 'tank' not available)",
            category=Category.ZFS,
        )

    output = result.output
    if "ONLINE" in output:
        # Check for errors
        if "errors: No known data errors" in output:
            return CheckResult(
                name="Pool health",
                status=CheckStatus.OK,
                message="Pool 'tank' is ONLINE, no errors",
                category=Category.ZFS,
            )

        return CheckResult(
            name="Pool health",
            status=CheckStatus.WARN,
            message="Pool 'tank' is ONLINE but has errors",
            category=Category.ZFS,
            fix="sudo zpool scrub tank",
        )

    if "DEGRADED" in output:
        return CheckResult(
            name="Pool health",
            status=CheckStatus.FAIL,
            message="Pool 'tank' is DEGRADED",
            category=Category.ZFS,
            detail="Check zpool status for details",
        )

    return CheckResult(
        name="Pool health",
        status=CheckStatus.FAIL,
        message="Pool 'tank' has issues",
        category=Category.ZFS,
        detail=output[:200],
    )


@register_check(Category.ZFS, "Scrub recent")
def check_zfs_scrub() -> CheckResult:
    """Check last scrub was within 30 days."""
    result = run_command("zpool status tank")
    if not result.success:
        return CheckResult(
            name="Scrub recent",
            status=CheckStatus.SKIP,
            message="Scrub age: skipped (pool 'tank' not available)",
            category=Category.ZFS,
        )

    output = result.output

    # Look for "scan: scrub repaired" or similar
    if "scrub repaired" in output or "scrub in progress" in output:
        # Try to extract date info
        # Format: "scan: scrub repaired 0B in 04:23:45 with 0 errors on Sun Jan 5 03:24:01 2025"
        import re
        from datetime import datetime

        match = re.search(r"on (\w+ \w+ \d+ \d+:\d+:\d+ \d+)", output)
        if match:
            try:
                date_str = match.group(1)
                scrub_date = datetime.strptime(date_str, "%a %b %d %H:%M:%S %Y")
                days_ago = (datetime.now() - scrub_date).days

                if days_ago <= 30:
                    return CheckResult(
                        name="Scrub recent",
                        status=CheckStatus.OK,
                        message=f"Last scrub: {days_ago} days ago",
                        category=Category.ZFS,
                    )

                return CheckResult(
                    name="Scrub recent",
                    status=CheckStatus.WARN,
                    message=f"Last scrub: {days_ago} days ago",
                    category=Category.ZFS,
                    fix="sudo zpool scrub tank",
                )
            except ValueError:
                pass

        return CheckResult(
            name="Scrub recent",
            status=CheckStatus.OK,
            message="Scrub completed (date unknown)",
            category=Category.ZFS,
        )

    if "none requested" in output:
        return CheckResult(
            name="Scrub recent",
            status=CheckStatus.WARN,
            message="No scrub has been run",
            category=Category.ZFS,
            fix="sudo zpool scrub tank",
        )

    return CheckResult(
        name="Scrub recent",
        status=CheckStatus.WARN,
        message="Could not determine scrub status",
        category=Category.ZFS,
    )


@register_check(Category.ZFS, "Auto-snapshots")
def check_zfs_snapshots() -> CheckResult:
    """Check if auto-snapshots are configured."""
    # Check for zfs-auto-snapshot or sanoid
    if command_exists("zfs-auto-snapshot"):
        return CheckResult(
            name="Auto-snapshots",
            status=CheckStatus.OK,
            message="zfs-auto-snapshot installed",
            category=Category.ZFS,
        )

    if command_exists("sanoid"):
        return CheckResult(
            name="Auto-snapshots",
            status=CheckStatus.OK,
            message="sanoid installed",
            category=Category.ZFS,
        )

    # Check for any recent snapshots
    result = run_command("zfs list -t snapshot -o name -H")
    if result.success and result.output:
        return CheckResult(
            name="Auto-snapshots",
            status=CheckStatus.OK,
            message="Snapshots present",
            category=Category.ZFS,
        )

    return CheckResult(
        name="Auto-snapshots",
        status=CheckStatus.WARN,
        message="No auto-snapshot tool detected",
        category=Category.ZFS,
        fix="sudo apt install zfs-auto-snapshot",
    )


# =============================================================================
# Docker Checks
# =============================================================================


@register_check(Category.DOCKER, "Daemon running")
def check_docker_daemon() -> CheckResult:
    """Check Docker daemon is running."""
    if is_service_running("docker"):
        return CheckResult(
            name="Daemon running",
            status=CheckStatus.OK,
            message="Docker daemon running",
            category=Category.DOCKER,
        )

    return CheckResult(
        name="Daemon running",
        status=CheckStatus.FAIL,
        message="Docker daemon not running",
        category=Category.DOCKER,
        fix="sudo systemctl start docker",
    )


def _user_groups() -> tuple[set[str], set[str]]:
    """Return (session_groups, account_groups) for the current user.

    ``id -nG`` with no argument reflects the *running session*; with an explicit
    username it computes the account's configured groups from the group DB. The
    two differ right after ``usermod -aG`` and before the next login, which is
    exactly the case we want to report distinctly rather than as "not in group".
    """
    session = set(run_command("id -nG").output.split())
    user = run_command("id -un").output
    account = set(run_command(f"id -nG {user}").output.split()) if user else set[str]()
    return session, account


def _group_membership(
    group: str, *, name: str, category: Category, fix: str
) -> CheckResult:
    """OK if the group is active now, OK-with-note if pending re-login, else WARN."""
    session, account = _user_groups()
    if group in session:
        return CheckResult(
            name=name,
            status=CheckStatus.OK,
            message=f"User in {group} group",
            category=category,
        )
    if group in account:
        return CheckResult(
            name=name,
            status=CheckStatus.OK,
            message=f"User in {group} group (log out/in to activate in this session)",
            category=category,
        )
    return CheckResult(
        name=name,
        status=CheckStatus.WARN,
        message=f"User not in {group} group",
        category=category,
        fix=fix,
    )


@register_check(Category.DOCKER, "User in group")
def check_docker_group() -> CheckResult:
    """Check current user is in docker group."""
    return _group_membership(
        "docker",
        name="User in group",
        category=Category.DOCKER,
        fix="sudo usermod -aG docker $USER && newgrp docker",
    )


@register_check(Category.DOCKER, "Compose v2")
def check_docker_compose() -> CheckResult:
    """Check Docker Compose v2 is available."""
    result = run_command("docker compose version")
    if result.success:
        # Extract version
        match = re.search(r"v?(\d+\.\d+\.\d+)", result.output)
        version = match.group(1) if match else "installed"
        return CheckResult(
            name="Compose v2",
            status=CheckStatus.OK,
            message=f"Compose v{version}",
            category=Category.DOCKER,
        )

    return CheckResult(
        name="Compose v2",
        status=CheckStatus.FAIL,
        message="Docker Compose not available",
        category=Category.DOCKER,
        fix="sudo apt install docker-compose-plugin",
    )


# =============================================================================
# KVM Checks
# =============================================================================


@register_check(Category.KVM, "libvirtd running")
def check_libvirtd() -> CheckResult:
    """Check libvirtd service is running."""
    if is_service_running("libvirtd"):
        return CheckResult(
            name="libvirtd running",
            status=CheckStatus.OK,
            message="libvirtd running",
            category=Category.KVM,
        )

    return CheckResult(
        name="libvirtd running",
        status=CheckStatus.FAIL,
        message="libvirtd not running",
        category=Category.KVM,
        fix="sudo systemctl start libvirtd",
    )


@register_check(Category.KVM, "IOMMU enabled")
def check_iommu() -> CheckResult:
    """Check IOMMU is enabled for GPU passthrough."""
    iommu_path = Path("/sys/kernel/iommu_groups")
    if iommu_path.exists():
        # Count groups
        groups = list(iommu_path.iterdir())
        if groups:
            return CheckResult(
                name="IOMMU enabled",
                status=CheckStatus.OK,
                message=f"IOMMU enabled ({len(groups)} groups)",
                category=Category.KVM,
            )

    return CheckResult(
        name="IOMMU enabled",
        status=CheckStatus.FAIL,
        message="IOMMU not enabled",
        category=Category.KVM,
        detail="Add 'amd_iommu=on iommu=pt' to kernel parameters",
    )


@register_check(Category.KVM, "vfio-pci loaded")
def check_vfio() -> CheckResult:
    """Check vfio-pci module is loaded."""
    result = run_command("lsmod")
    if result.success and "vfio_pci" in result.output:
        return CheckResult(
            name="vfio-pci loaded",
            status=CheckStatus.OK,
            message="vfio-pci module loaded",
            category=Category.KVM,
        )

    return CheckResult(
        name="vfio-pci loaded",
        status=CheckStatus.WARN,
        message="vfio-pci module not loaded",
        category=Category.KVM,
        detail="Module may load on-demand when GPU is passed through",
    )


# =============================================================================
# GPU Checks
# =============================================================================


@register_check(Category.GPU, "AMD driver")
def check_amd_driver() -> CheckResult:
    """Check amdgpu module is loaded."""
    result = run_command("lsmod")
    if result.success and "amdgpu" in result.output:
        return CheckResult(
            name="AMD driver",
            status=CheckStatus.OK,
            message="amdgpu module loaded",
            category=Category.GPU,
        )

    # Check if GPU is passed through to VM
    result_vfio = run_command("lspci -nnk | grep -A3 'VGA.*AMD'")
    if result_vfio.success and "vfio-pci" in result_vfio.output:
        return CheckResult(
            name="AMD driver",
            status=CheckStatus.OK,
            message="GPU passed through (vfio-pci)",
            category=Category.GPU,
        )

    return CheckResult(
        name="AMD driver",
        status=CheckStatus.WARN,
        message="amdgpu module not loaded",
        category=Category.GPU,
    )


@register_check(Category.GPU, "Render/video groups")
def check_gpu_groups() -> CheckResult:
    """Check the user is in render+video groups (needed for /dev/kfd + /dev/dri)."""
    needed = ("render", "video")
    session, account = _user_groups()

    if all(g in session for g in needed):
        return CheckResult(
            name="Render/video groups",
            status=CheckStatus.OK,
            message="User in render and video groups",
            category=Category.GPU,
        )
    if all(g in account for g in needed):
        return CheckResult(
            name="Render/video groups",
            status=CheckStatus.OK,
            message="User in render and video groups (log out/in to activate in this session)",
            category=Category.GPU,
        )

    missing = [g for g in needed if g not in account]
    return CheckResult(
        name="Render/video groups",
        status=CheckStatus.WARN,
        message=f"User not in {', '.join(missing)} group(s); ROCm compute needs /dev/kfd access",
        category=Category.GPU,
        detail="Group change takes effect on next login",
        fix="sudo usermod -aG render,video $USER",
    )


@register_check(Category.GPU, "ROCm installed")
def check_rocm() -> CheckResult:
    """Check ROCm is installed and working."""
    if not command_exists("rocminfo"):
        return CheckResult(
            name="ROCm installed",
            status=CheckStatus.FAIL,
            message="ROCm not installed",
            category=Category.GPU,
            detail="26.04 ships ROCm 7.x with native gfx1151 support; see docs ai/gpu/rocm-installation",
            fix="sudo apt install rocm",
        )

    result = run_command("rocminfo")
    if result.success:
        return CheckResult(
            name="ROCm installed",
            status=CheckStatus.OK,
            message="ROCm working",
            category=Category.GPU,
        )

    return CheckResult(
        name="ROCm installed",
        status=CheckStatus.WARN,
        message="ROCm installed but not working",
        category=Category.GPU,
        detail=result.stderr[:100] if result.stderr else None,
    )


@register_check(Category.GPU, "Vulkan")
def check_vulkan() -> CheckResult:
    """Check Vulkan is working."""
    if not command_exists("vulkaninfo"):
        return CheckResult(
            name="Vulkan",
            status=CheckStatus.WARN,
            message="vulkaninfo not installed",
            category=Category.GPU,
            fix="sudo apt install vulkan-tools",
        )

    result = run_command("vulkaninfo --summary")
    if result.success and "deviceName" in result.output:
        return CheckResult(
            name="Vulkan",
            status=CheckStatus.OK,
            message="Vulkan working",
            category=Category.GPU,
        )

    return CheckResult(
        name="Vulkan",
        status=CheckStatus.WARN,
        message="Vulkan not working",
        category=Category.GPU,
    )


# =============================================================================
# Inference Checks (llama.cpp)
# =============================================================================


@register_check(Category.INFERENCE, "llama.cpp installed")
def check_llamacpp_installed() -> CheckResult:
    """Check llama.cpp's server binary is installed."""
    if command_exists("llama-server"):
        return CheckResult(
            name="llama.cpp installed",
            status=CheckStatus.OK,
            message="llama-server present",
            category=Category.INFERENCE,
        )

    return CheckResult(
        name="llama.cpp installed",
        status=CheckStatus.FAIL,
        message="llama.cpp not installed",
        category=Category.INFERENCE,
        fix="msai bootstrap llamacpp",
    )


@register_check(Category.INFERENCE, "GPU backend")
def check_llamacpp_gpu() -> CheckResult:
    """Check llama.cpp enumerates a GPU device (Vulkan or ROCm).

    The GPU backend lives in a separate ``libggml-*.so`` that ggml loads at
    runtime, so inspecting the binary's direct links misses it. Asking
    llama.cpp itself to list devices is the reliable signal. The default build
    is Vulkan (fastest here); a ROCm/HIP build is equally valid.
    """
    if not command_exists("llama-cli"):
        return CheckResult(
            name="GPU backend",
            status=CheckStatus.SKIP,
            message="llama.cpp not installed",
            category=Category.INFERENCE,
        )

    result = run_command("llama-cli --list-devices")
    device = next(
        (line.strip() for line in result.output.splitlines() if "Vulkan" in line or "ROCm" in line),
        None,
    )
    if result.success and device:
        return CheckResult(
            name="GPU backend",
            status=CheckStatus.OK,
            message=f"GPU offload available ({device})",
            category=Category.INFERENCE,
        )

    return CheckResult(
        name="GPU backend",
        status=CheckStatus.WARN,
        message="no GPU device listed by llama.cpp (CPU-only build?)",
        category=Category.INFERENCE,
        detail="Rebuild with a GPU backend (Vulkan or HIP) for offload",
        fix="msai bootstrap llamacpp-vulkan --force",
    )


# =============================================================================
# Incus Checks
# =============================================================================


@register_check(Category.INCUS, "Incus installed")
def check_incus_installed() -> CheckResult:
    """Check the incus client is installed."""
    if command_exists("incus"):
        return CheckResult(
            name="Incus installed",
            status=CheckStatus.OK,
            message="Incus installed",
            category=Category.INCUS,
        )
    return CheckResult(
        name="Incus installed",
        status=CheckStatus.FAIL,
        message="Incus not installed",
        category=Category.INCUS,
        fix="msai bootstrap incus",
    )


@register_check(Category.INCUS, "Daemon running")
def check_incus_daemon() -> CheckResult:
    """Check the incus daemon (socket-activated) is available."""
    if not command_exists("incus"):
        return CheckResult(
            name="Daemon running",
            status=CheckStatus.SKIP,
            message="incus not installed",
            category=Category.INCUS,
        )
    if is_service_running("incus.socket") or is_service_running("incus"):
        return CheckResult(
            name="Daemon running",
            status=CheckStatus.OK,
            message="incus daemon active",
            category=Category.INCUS,
        )
    return CheckResult(
        name="Daemon running",
        status=CheckStatus.FAIL,
        message="incus daemon not running",
        category=Category.INCUS,
        fix="sudo systemctl enable --now incus.socket",
    )


@register_check(Category.INCUS, "Initialized")
def check_incus_initialized() -> CheckResult:
    """Check incus has been set up (a storage pool exists)."""
    if not command_exists("incus"):
        return CheckResult(
            name="Initialized",
            status=CheckStatus.SKIP,
            message="incus not installed",
            category=Category.INCUS,
        )
    result = run_command("incus storage list -f csv")
    if not result.success:
        stderr = result.stderr.lower()
        if "restricted" in stderr or "permission" in stderr:
            # Restricted cert => only the 'incus' group is active, not 'incus-admin'.
            return CheckResult(
                name="Initialized",
                status=CheckStatus.WARN,
                message="restricted access; need incus-admin active (log out/in), then 'sudo incus admin init'",
                category=Category.INCUS,
            )
        return CheckResult(
            name="Initialized",
            status=CheckStatus.WARN,
            message="cannot query incus (daemon issue?)",
            category=Category.INCUS,
            detail=result.stderr[:120] if result.stderr else None,
        )
    if result.output.strip():
        pools = [line.split(",")[0] for line in result.output.splitlines() if line.strip()]
        return CheckResult(
            name="Initialized",
            status=CheckStatus.OK,
            message=f"initialized (storage pool: {', '.join(pools)})",
            category=Category.INCUS,
        )
    return CheckResult(
        name="Initialized",
        status=CheckStatus.WARN,
        message="no storage pool; incus not initialized",
        category=Category.INCUS,
        fix="sudo incus admin init",
    )


@register_check(Category.INCUS, "incus-admin group")
def check_incus_group() -> CheckResult:
    """Check the user can manage incus without sudo (incus-admin group)."""
    if not command_exists("incus"):
        return CheckResult(
            name="incus-admin group",
            status=CheckStatus.SKIP,
            message="incus not installed",
            category=Category.INCUS,
        )
    return _group_membership(
        "incus-admin",
        name="incus-admin group",
        category=Category.INCUS,
        fix="sudo usermod -aG incus-admin $USER",
    )


# =============================================================================
# Tailscale Checks
# =============================================================================


@register_check(Category.TAILSCALE, "Daemon running")
def check_tailscale_daemon() -> CheckResult:
    """Check tailscaled is running."""
    if is_service_running("tailscaled"):
        return CheckResult(
            name="Daemon running",
            status=CheckStatus.OK,
            message="tailscaled running",
            category=Category.TAILSCALE,
        )

    return CheckResult(
        name="Daemon running",
        status=CheckStatus.FAIL,
        message="tailscaled not running",
        category=Category.TAILSCALE,
        fix="sudo systemctl start tailscaled",
    )


@register_check(Category.TAILSCALE, "Connected")
def check_tailscale_connected() -> CheckResult:
    """Check Tailscale is connected to tailnet."""
    result = run_command("tailscale status --json")
    if not result.success:
        return CheckResult(
            name="Connected",
            status=CheckStatus.FAIL,
            message="Could not get Tailscale status",
            category=Category.TAILSCALE,
        )

    import json

    try:
        status = json.loads(result.output)
        if status.get("BackendState") == "Running":
            # Get tailnet name
            self_status = status.get("Self", {})
            dns_name = self_status.get("DNSName", "")
            if dns_name:
                # Extract tailnet from DNS name (format: hostname.tailnet.ts.net.)
                parts = dns_name.rstrip(".").split(".")
                if len(parts) >= 3:
                    tailnet = ".".join(parts[1:])
                    return CheckResult(
                        name="Connected",
                        status=CheckStatus.OK,
                        message=f"Connected to {tailnet}",
                        category=Category.TAILSCALE,
                    )
            return CheckResult(
                name="Connected",
                status=CheckStatus.OK,
                message="Connected to tailnet",
                category=Category.TAILSCALE,
            )
    except json.JSONDecodeError:
        pass

    return CheckResult(
        name="Connected",
        status=CheckStatus.WARN,
        message="Tailscale not connected",
        category=Category.TAILSCALE,
        fix="sudo tailscale up",
    )


@register_check(Category.TAILSCALE, "MagicDNS")
def check_tailscale_magicdns() -> CheckResult:
    """Check MagicDNS is enabled."""
    result = run_command("tailscale status --json")
    if not result.success:
        return CheckResult(
            name="MagicDNS",
            status=CheckStatus.SKIP,
            message="Could not get Tailscale status",
            category=Category.TAILSCALE,
        )

    import json

    try:
        status = json.loads(result.output)
        self_status = status.get("Self", {})
        if self_status.get("DNSName"):
            return CheckResult(
                name="MagicDNS",
                status=CheckStatus.OK,
                message="MagicDNS enabled",
                category=Category.TAILSCALE,
            )
    except json.JSONDecodeError:
        pass

    return CheckResult(
        name="MagicDNS",
        status=CheckStatus.WARN,
        message="MagicDNS may not be enabled",
        category=Category.TAILSCALE,
    )
