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
    KVM = "kvm"
    GPU = "gpu"
    OLLAMA = "ollama"
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
    """Check Ubuntu version is 24.04 LTS."""
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
    if version.startswith("24.04"):
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
        message=f"Ubuntu {version} (expected 24.04 LTS)",
        category=Category.SYSTEM,
    )


@register_check(Category.SYSTEM, "Kernel version")
def check_kernel_version() -> CheckResult:
    """Check kernel version is 6.8+."""
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
        if major > 6 or (major == 6 and minor >= 8):
            return CheckResult(
                name="Kernel version",
                status=CheckStatus.OK,
                message=f"Kernel {kernel}",
                category=Category.SYSTEM,
            )

    return CheckResult(
        name="Kernel version",
        status=CheckStatus.WARN,
        message=f"Kernel {kernel} (recommend 6.8+)",
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
    """Check CPU is AMD Ryzen 9."""
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
        if "AMD Ryzen 9" in cpu_name:
            return CheckResult(
                name="CPU",
                status=CheckStatus.OK,
                message=f"CPU: {cpu_name}",
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
    result_d = run_command("grep -ri '^PasswordAuthentication' /etc/ssh/sshd_config.d/ 2>/dev/null")
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
            message="Could not get pool status",
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
            message="Could not get pool status",
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
    result = run_command("zfs list -t snapshot -o name -H | head -5")
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


@register_check(Category.DOCKER, "User in group")
def check_docker_group() -> CheckResult:
    """Check current user is in docker group."""
    result = run_command("groups")
    if result.success and "docker" in result.output.split():
        return CheckResult(
            name="User in group",
            status=CheckStatus.OK,
            message="User in docker group",
            category=Category.DOCKER,
        )

    return CheckResult(
        name="User in group",
        status=CheckStatus.WARN,
        message="User not in docker group",
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
    result = run_command("lsmod | grep vfio_pci")
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
    result = run_command("lsmod | grep amdgpu")
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


@register_check(Category.GPU, "ROCm installed")
def check_rocm() -> CheckResult:
    """Check ROCm is installed and working."""
    if not command_exists("rocminfo"):
        return CheckResult(
            name="ROCm installed",
            status=CheckStatus.FAIL,
            message="ROCm not installed",
            category=Category.GPU,
            fix="sudo apt install rocm-libs",
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

    result = run_command("vulkaninfo --summary 2>/dev/null | head -20")
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
# Ollama Checks
# =============================================================================


@register_check(Category.OLLAMA, "Service running")
def check_ollama_service() -> CheckResult:
    """Check Ollama service is running."""
    # Check systemd service
    if is_service_running("ollama"):
        return CheckResult(
            name="Service running",
            status=CheckStatus.OK,
            message="Ollama service running",
            category=Category.OLLAMA,
        )

    # Check if running in Docker
    result = run_command("docker ps --format '{{.Names}}' | grep -i ollama")
    if result.success and result.output:
        return CheckResult(
            name="Service running",
            status=CheckStatus.OK,
            message=f"Ollama running in Docker ({result.output})",
            category=Category.OLLAMA,
        )

    return CheckResult(
        name="Service running",
        status=CheckStatus.FAIL,
        message="Ollama not running",
        category=Category.OLLAMA,
        fix="sudo systemctl start ollama",
    )


@register_check(Category.OLLAMA, "API responding")
def check_ollama_api() -> CheckResult:
    """Check Ollama API is responding."""
    result = run_command("curl -s -o /dev/null -w '%{http_code}' http://localhost:11434")
    if result.success and result.output == "200":
        return CheckResult(
            name="API responding",
            status=CheckStatus.OK,
            message="API responding on :11434",
            category=Category.OLLAMA,
        )

    return CheckResult(
        name="API responding",
        status=CheckStatus.FAIL,
        message="API not responding on :11434",
        category=Category.OLLAMA,
    )


@register_check(Category.OLLAMA, "Models present")
def check_ollama_models() -> CheckResult:
    """Check Ollama has models installed."""
    result = run_command("ollama list")
    if not result.success:
        return CheckResult(
            name="Models present",
            status=CheckStatus.SKIP,
            message="Could not list models",
            category=Category.OLLAMA,
        )

    lines = result.output.strip().split("\n")
    # First line is header
    if len(lines) > 1:
        models = [line.split()[0] for line in lines[1:] if line.strip()]
        model_list = ", ".join(models[:3])
        if len(models) > 3:
            model_list += f" (+{len(models) - 3} more)"
        return CheckResult(
            name="Models present",
            status=CheckStatus.OK,
            message=f"Models: {model_list}",
            category=Category.OLLAMA,
        )

    return CheckResult(
        name="Models present",
        status=CheckStatus.WARN,
        message="No models installed",
        category=Category.OLLAMA,
        fix="ollama pull llama3.3:70b",
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
