"""Tests for Fedora kickstart rendering + OEMDRV seed ISO (msai_setup.lab.kickstart)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from msai_setup.lab import kickstart

SSH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleKeyForTests lab@example"


def _render() -> str:
    return kickstart.render_kickstart(
        hostname="testvm",
        user="morten",
        full_user_name="Morten Hansen",
        password="s3cret",
        ssh_public_key=SSH_KEY,
    )


def test_kickstart_has_core_stanzas() -> None:
    ks = _render()
    for needle in (
        "lang en_US.UTF-8",
        "keyboard us",
        "timezone Europe/Oslo --utc",
        "network --bootproto=dhcp",
        "--hostname=testvm",
        "rootpw --lock",
        "clearpart --all --initlabel",
        "autopart",
        "bootloader",
        "firstboot --disable",
        "%packages",
        "openssh-server",
        "%end",
        "reboot",
    ):
        assert needle in ks, f"missing stanza: {needle!r}"


def test_kickstart_user_is_wheel_and_iscrypted() -> None:
    ks = _render()
    assert "user --name=morten" in ks
    assert "--groups=wheel" in ks
    assert "--iscrypted --password=$6$" in ks
    # The plaintext password must never appear in the file.
    assert "s3cret" not in ks


def test_kickstart_sshkey_present() -> None:
    ks = _render()
    assert f"sshkey --username=morten '{SSH_KEY}'" in ks


def test_kickstart_post_grants_passwordless_sudo_and_enables_sshd() -> None:
    ks = _render()
    assert "%post" in ks
    assert "sudoers.d/90-morten" in ks
    assert "morten ALL=(ALL) NOPASSWD:ALL" in ks
    assert "systemctl enable sshd" in ks


def test_kickstart_extra_packages_folded_in() -> None:
    ks = kickstart.render_kickstart(
        hostname="h",
        user="u",
        full_user_name="U",
        password="p",
        ssh_public_key=SSH_KEY,
        extra_packages=["vim-enhanced", "tmux"],
    )
    assert "vim-enhanced" in ks
    assert "tmux" in ks


def test_build_oemdrv_iso_argv_and_staging(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    calls: list[list[str]] = []
    staged: dict[str, str] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        # Capture the ks.cfg staged into the temp dir before xorriso "ran".
        ks_path = Path(cmd[-1])
        if ks_path.name == "ks.cfg" and ks_path.exists():
            staged["ks.cfg"] = ks_path.read_text()
        # xorriso is mocked, so create the output file the builder then stat()s.
        out_path = Path(cmd[cmd.index("-output") + 1])
        out_path.write_bytes(b"\x00" * 4096)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(kickstart.shutil, "which", lambda _name: "/usr/bin/xorriso")
    monkeypatch.setattr(kickstart.subprocess, "run", fake_run)
    out = tmp_path / "vm-oemdrv.iso"
    kickstart.build_oemdrv_iso(kickstart="# ks.cfg contents\n", output_path=out)

    assert len(calls) == 1
    argv = calls[0]
    assert argv[0] == "xorriso"
    assert argv[argv.index("-volid") + 1] == "OEMDRV"
    assert argv[argv.index("-output") + 1] == str(out)
    assert argv[-1].endswith("/ks.cfg")
    assert staged["ks.cfg"] == "# ks.cfg contents\n"
    assert out.exists()
