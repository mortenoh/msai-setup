"""Tests for VBoxManage command construction (msai_setup.lab.vbox).

All tests mock `subprocess.run` so no real VirtualBox is invoked. We assert the
exact argv lists the module builds and that "idempotent" operations short-circuit
when VBoxManage reports the resource already exists.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from msai_setup.lab import vbox


class FakeRun:
    """Records subprocess.run argv and returns canned stdout per subcommand."""

    def __init__(self, list_vms_output: str = "") -> None:
        self.calls: list[list[str]] = []
        self.list_vms_output = list_vms_output

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        stdout = ""
        # cmd[0] == "VBoxManage"; cmd[1] is the subcommand.
        if cmd[1:3] == ["list", "vms"]:
            stdout = self.list_vms_output
        elif cmd[1:3] == ["list", "runningvms"]:
            stdout = ""
        elif cmd[1] == "showvminfo":
            stdout = ""
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=stdout, stderr="")

    def argv_for(self, subcommand: str) -> list[str]:
        for call in self.calls:
            if len(call) > 1 and call[1] == subcommand:
                return call
        raise AssertionError(f"no call for subcommand {subcommand!r}; calls={self.calls}")

    def count(self, subcommand: str) -> int:
        return sum(1 for c in self.calls if len(c) > 1 and c[1] == subcommand)


@pytest.fixture
def fake_run(monkeypatch: pytest.MonkeyPatch) -> FakeRun:
    fr = FakeRun()
    monkeypatch.setattr(vbox.subprocess, "run", fr)
    return fr


def test_create_vm_x86_argv(fake_run: FakeRun) -> None:
    vbox.create_vm("lab", ostype="Ubuntu_64", platform="x86")
    argv = fake_run.argv_for("createvm")
    assert argv == [
        "VBoxManage", "createvm",
        "--name", "lab",
        "--ostype", "Ubuntu_64",
        "--platform-architecture", "x86",
        "--register",
    ]


def test_create_vm_arm_argv(fake_run: FakeRun) -> None:
    vbox.create_vm("lab", ostype="Ubuntu_arm64", platform="arm")
    argv = fake_run.argv_for("createvm")
    assert "--platform-architecture" in argv
    assert argv[argv.index("--platform-architecture") + 1] == "arm"
    assert argv[argv.index("--ostype") + 1] == "Ubuntu_arm64"


def test_create_vm_idempotent_when_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    fr = FakeRun(list_vms_output='"lab" {uuid-1234}')
    monkeypatch.setattr(vbox.subprocess, "run", fr)
    vbox.create_vm("lab", platform="x86")
    # Existing VM: it should list, then NOT createvm.
    assert fr.count("createvm") == 0


def test_configure_vm_x86_includes_efi_and_usb_toggles(fake_run: FakeRun) -> None:
    vbox.configure_vm("lab", memory_mb=8192, cpus=4, vram_mb=32, platform="x86")
    argv = fake_run.argv_for("modifyvm")
    assert argv[:4] == ["VBoxManage", "modifyvm", "lab", "--memory"]
    assert "8192" in argv
    assert argv[argv.index("--firmware") + 1] == "efi64"
    assert "--usbohci" in argv and "--usbxhci" in argv
    # x86 must NOT set the ARM-only graphics controller.
    assert "qemuramfb" not in argv


def test_configure_vm_arm_uses_qemuramfb_no_usb(fake_run: FakeRun) -> None:
    vbox.configure_vm("lab", memory_mb=4096, cpus=2, vram_mb=16, platform="arm")
    argv = fake_run.argv_for("modifyvm")
    assert argv[argv.index("--graphicscontroller") + 1] == "qemuramfb"
    assert "--firmware" not in argv
    assert "--usbohci" not in argv


def test_attach_disk_argv_hdd_flags(fake_run: FakeRun) -> None:
    vbox.attach_disk(
        "lab", controller="SATA", port=1, device=0, medium=Path("/tmp/d.vdi"),
    )
    argv = fake_run.argv_for("storageattach")
    assert argv == [
        "VBoxManage", "storageattach", "lab",
        "--storagectl", "SATA",
        "--port", "1",
        "--device", "0",
        "--type", "hdd",
        "--medium", "/tmp/d.vdi",
        "--nonrotational", "on",
        "--discard", "on",
    ]


def test_attach_disk_detach_medium_none(fake_run: FakeRun) -> None:
    vbox.attach_disk("lab", controller="SATA", port=1, device=0, medium=None)
    argv = fake_run.argv_for("storageattach")
    assert argv[argv.index("--medium") + 1] == "none"
    # No nonrotational/discard flags when detaching.
    assert "--nonrotational" not in argv
    assert "--discard" not in argv


def test_attach_iso_is_dvddrive(fake_run: FakeRun) -> None:
    vbox.attach_iso("lab", controller="IDE", port=0, device=0, iso=Path("/tmp/x.iso"))
    argv = fake_run.argv_for("storageattach")
    assert argv[argv.index("--type") + 1] == "dvddrive"
    assert argv[argv.index("--medium") + 1] == "/tmp/x.iso"
    assert "--nonrotational" not in argv


def test_create_disk_skips_existing(tmp_path: Path, fake_run: FakeRun) -> None:
    existing = tmp_path / "disk.vdi"
    existing.write_text("stub")
    vbox.create_disk(existing, size_mb=1000)
    assert fake_run.count("createmedium") == 0


def test_create_disk_builds_createmedium(tmp_path: Path, fake_run: FakeRun) -> None:
    disk = tmp_path / "new.vdi"
    vbox.create_disk(disk, size_mb=8000)
    argv = fake_run.argv_for("createmedium")
    assert argv == [
        "VBoxManage", "createmedium", "disk",
        "--filename", str(disk),
        "--size", "8000",
        "--format", "VDI",
    ]


def test_snapshot_restore_argv(fake_run: FakeRun) -> None:
    vbox.snapshot_restore("lab", "fresh-install")
    argv = fake_run.argv_for("snapshot")
    assert argv == ["VBoxManage", "snapshot", "lab", "restore", "fresh-install"]
