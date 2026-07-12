"""Tests for the Incus CLI wrapper (msai_setup.lab.incus).

All tests mock `subprocess.run` so no real Incus is invoked. We assert the exact
argv lists the module builds and that JSON parsing / idempotency behave.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from msai_setup.lab import incus


class FakeRun:
    """Records `incus` argv and returns canned stdout keyed by subcommand shape."""

    def __init__(self, *, list_json: str = "", volumes_json: str = "", devices: str = "") -> None:
        self.calls: list[list[str]] = []
        self.list_json = list_json
        self.volumes_json = volumes_json
        self.devices = devices

    def __call__(self, cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        self.calls.append(list(cmd))
        stdout = ""
        # cmd[0] == "incus"; strip any leading --project <x> for shape matching.
        rest = cmd[1:]
        if rest[:1] == ["--project"]:
            rest = rest[2:]
        if rest[:1] == ["list"] and "--format" in rest:
            stdout = self.list_json
        elif rest[:3] == ["storage", "volume", "list"]:
            stdout = self.volumes_json
        elif rest[:3] == ["config", "device", "list"]:
            stdout = self.devices
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout=stdout, stderr="")

    def argv_for(self, *prefix: str) -> list[str]:
        for call in self.calls:
            if call[1:1 + len(prefix)] == list(prefix):
                return call
        raise AssertionError(f"no call starting incus {prefix}; calls={self.calls}")

    def has_call(self, *prefix: str) -> bool:
        return any(call[1:1 + len(prefix)] == list(prefix) for call in self.calls)


@pytest.fixture
def fake_run(monkeypatch: pytest.MonkeyPatch) -> FakeRun:
    fr = FakeRun()
    monkeypatch.setattr(incus.subprocess, "run", fr)
    return fr


def test_init_vm_empty_argv(fake_run: FakeRun) -> None:
    incus.init_vm("win", empty=True, cpu=8, memory_mb=16384, disk_size_mb=100000)
    argv = fake_run.argv_for("init")
    assert argv == [
        "incus", "init", "win", "--vm", "--empty",
        "-c", "limits.cpu=8",
        "-c", "limits.memory=16384MiB",
        "-d", "root,size=100000MiB",
    ]


def test_init_vm_from_image_and_project(fake_run: FakeRun) -> None:
    incus.init_vm(
        "u", image="images:ubuntu/24.04", cpu=4, memory_mb=8192, disk_size_mb=80000,
        project="user-1000",
    )
    argv = fake_run.argv_for("init")
    # The --project flag follows the subcommand, then the image + name.
    assert argv[:6] == ["incus", "init", "--project", "user-1000", "images:ubuntu/24.04", "u"]
    assert "--vm" in argv and "--empty" not in argv


def test_launch_vm_passes_cloud_init_config(fake_run: FakeRun) -> None:
    incus.launch_vm(
        "u", image="images:ubuntu/24.04", cpu=4, memory_mb=8192, disk_size_mb=80000,
        config={"user.user-data": "#cloud-config\n"},
    )
    argv = fake_run.argv_for("launch")
    assert argv[:5] == ["incus", "launch", "images:ubuntu/24.04", "u", "--vm"]
    assert "-c" in argv
    assert "user.user-data=#cloud-config\n" in argv


def test_init_vm_idempotent_when_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    fr = FakeRun(list_json=json.dumps([{"name": "u", "status": "Stopped"}]))
    monkeypatch.setattr(incus.subprocess, "run", fr)
    incus.init_vm("u", empty=True, cpu=4, memory_mb=8192, disk_size_mb=80000)
    assert not fr.has_call("init")  # already exists -> no init


def test_storage_volume_import_type_iso(fake_run: FakeRun) -> None:
    incus.storage_volume_import("lab", Path("/data/Win.iso"), "win-iso")
    argv = fake_run.argv_for("storage", "volume", "import")
    assert argv == [
        "incus", "storage", "volume", "import",
        "lab", "/data/Win.iso", "win-iso", "--type=iso",
    ]


def test_storage_volume_import_skips_existing(monkeypatch: pytest.MonkeyPatch) -> None:
    fr = FakeRun(volumes_json=json.dumps([{"name": "win-iso"}]))
    monkeypatch.setattr(incus.subprocess, "run", fr)
    incus.storage_volume_import("lab", Path("/data/Win.iso"), "win-iso")
    assert not fr.has_call("storage", "volume", "import")


def test_attach_iso_volume_boot_priority(fake_run: FakeRun) -> None:
    incus.attach_iso_volume("win", "install", pool="lab", vol_name="win-iso", boot_priority=10)
    argv = fake_run.argv_for("config", "device", "add")
    assert argv == [
        "incus", "config", "device", "add", "win", "install", "disk",
        "pool=lab", "source=win-iso", "boot.priority=10",
    ]


def test_add_vtpm_argv(fake_run: FakeRun) -> None:
    incus.add_vtpm("win")
    argv = fake_run.argv_for("config", "device", "add")
    assert argv == ["incus", "config", "device", "add", "win", "vtpm", "tpm"]


def test_set_secure_boot_argv(fake_run: FakeRun) -> None:
    incus.set_secure_boot("win", enabled=True)
    argv = fake_run.argv_for("config", "set")
    assert argv == ["incus", "config", "set", "win", "security.secureboot", "true"]
    incus.set_secure_boot("win", enabled=False)
    assert fake_run.calls[-1][-1] == "false"


def test_add_gpu_and_kfd_devices_argv(fake_run: FakeRun) -> None:
    incus.add_gpu_device("ai", gid=993)
    gpu = fake_run.argv_for("config", "device", "add")
    assert gpu == [
        "incus", "config", "device", "add", "ai", "gpu0", "gpu",
        "gputype=physical", "id=0", "gid=993",
    ]
    fake_run.calls.clear()
    incus.add_kfd_device("ai", gid=993)
    kfd = fake_run.argv_for("config", "device", "add")
    assert kfd == [
        "incus", "config", "device", "add", "ai", "dev_kfd", "unix-char",
        "source=/dev/kfd", "path=/dev/kfd", "gid=993",
    ]


def test_add_proxy_device_argv(fake_run: FakeRun) -> None:
    incus.add_proxy_device(
        "win", "rdp", listen="tcp:0.0.0.0:3389", connect="tcp:127.0.0.1:3389",
    )
    argv = fake_run.argv_for("config", "device", "add")
    assert argv == [
        "incus", "config", "device", "add", "win", "rdp", "proxy",
        "listen=tcp:0.0.0.0:3389", "connect=tcp:127.0.0.1:3389", "bind=host",
    ]


def test_get_ipv4_parses_json(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = [
        {
            "name": "u",
            "state": {
                "network": {
                    "lo": {"addresses": [{"family": "inet", "scope": "local",
                                          "address": "127.0.0.1"}]},
                    "eth0": {"addresses": [
                        {"family": "inet6", "scope": "global", "address": "fe80::1"},
                        {"family": "inet", "scope": "global", "address": "10.0.0.42"},
                    ]},
                }
            },
        }
    ]
    fr = FakeRun(list_json=json.dumps(payload))
    monkeypatch.setattr(incus.subprocess, "run", fr)
    assert incus.get_ipv4("u") == "10.0.0.42"


def test_get_ipv4_none_when_no_address(monkeypatch: pytest.MonkeyPatch) -> None:
    fr = FakeRun(list_json=json.dumps([{"name": "u", "state": {"network": {}}}]))
    monkeypatch.setattr(incus.subprocess, "run", fr)
    assert incus.get_ipv4("u") is None


def test_start_stop_delete_argv(fake_run: FakeRun) -> None:
    # Not running/existing per empty list JSON: start issues `incus start`.
    incus.start("u")
    assert fake_run.argv_for("start") == ["incus", "start", "u"]


def test_stop_noop_when_not_running(fake_run: FakeRun) -> None:
    incus.stop("u", force=True)
    assert not fake_run.has_call("stop")  # empty list -> not running -> no stop


def test_delete_force_argv(monkeypatch: pytest.MonkeyPatch) -> None:
    fr = FakeRun(list_json=json.dumps([{"name": "u", "status": "Stopped"}]))
    monkeypatch.setattr(incus.subprocess, "run", fr)
    incus.delete("u", force=True)
    assert fr.argv_for("delete") == ["incus", "delete", "u", "--force"]


def test_exec_argv(fake_run: FakeRun) -> None:
    incus.exec_("u", ["uname", "-a"])
    assert fake_run.argv_for("exec") == ["incus", "exec", "u", "--", "uname", "-a"]
