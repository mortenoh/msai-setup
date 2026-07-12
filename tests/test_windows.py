"""Tests for Windows autounattend rendering + UNATTEND seed ISO (msai_setup.lab.windows)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from xml.etree import ElementTree

import pytest

from msai_setup.lab import windows


def _render(*, edition: str = "Windows 11 Pro", bypass: bool = True) -> str:
    return windows.render_autounattend(
        hostname="wintest",
        user="morten",
        full_user_name="Morten Hansen",
        password="s3cret!",
        edition=edition,
        bypass_hw_checks=bypass,
    )


def test_autounattend_is_well_formed_xml() -> None:
    # Must parse as XML (catches escaping / tag-balance regressions).
    root = ElementTree.fromstring(_render())
    assert root.tag.endswith("unattend")


def test_autounattend_has_local_admin_and_autologon() -> None:
    xml = _render()
    assert "<Name>morten</Name>" in xml
    assert "<Group>Administrators</Group>" in xml
    assert "<DisplayName>Morten Hansen</DisplayName>" in xml
    assert "<AutoLogon>" in xml
    assert "<Username>morten</Username>" in xml
    # Password embedded as plaintext (Windows requires it in the answer file).
    assert "<Value>s3cret!</Value>" in xml
    assert "<PlainText>true</PlainText>" in xml


def test_autounattend_edition_and_arch() -> None:
    xml = _render(edition="Windows 11 Pro")
    assert "<Value>Windows 11 Pro</Value>" in xml
    assert 'processorArchitecture="amd64"' in xml
    # A generic install product key is present.
    assert "<Key>VK7JG-NPHTM-C97JM-9MPGT-3V66T</Key>" in xml


def test_win11_includes_labconfig_bypass_keys() -> None:
    xml = _render(edition="Windows 11 Pro", bypass=True)
    assert "<RunSynchronous>" in xml
    for key in ("BypassTPMCheck", "BypassSecureBootCheck", "BypassCPUCheck", "BypassRAMCheck"):
        assert key in xml


def test_win10_omits_labconfig_bypass_keys() -> None:
    xml = _render(edition="Windows 10 Pro", bypass=False)
    assert "<RunSynchronous>" not in xml
    assert "BypassTPMCheck" not in xml
    assert "<Value>Windows 10 Pro</Value>" in xml


def test_build_unattend_iso_argv_and_staging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: list[list[str]] = []
    staged: dict[str, str] = {}

    def fake_run(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        calls.append(list(cmd))
        xml_path = Path(cmd[-1])
        if xml_path.name == "autounattend.xml" and xml_path.exists():
            staged["autounattend.xml"] = xml_path.read_text()
        out_path = Path(cmd[cmd.index("-output") + 1])
        out_path.write_bytes(b"\x00" * 2048)
        return subprocess.CompletedProcess(args=cmd, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(windows.shutil, "which", lambda _name: "/usr/bin/xorriso")
    monkeypatch.setattr(windows.subprocess, "run", fake_run)
    out = tmp_path / "vm-unattend.iso"
    windows.build_unattend_iso(autounattend="<unattend/>\n", output_path=out)

    assert len(calls) == 1
    argv = calls[0]
    assert argv[0] == "xorriso"
    assert argv[argv.index("-volid") + 1] == "UNATTEND"
    assert argv[argv.index("-output") + 1] == str(out)
    assert argv[-1].endswith("/autounattend.xml")
    assert staged["autounattend.xml"] == "<unattend/>\n"
    assert out.exists()
