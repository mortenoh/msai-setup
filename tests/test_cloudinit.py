"""Tests for cloud-init / autoinstall generation (msai_setup.lab.cloudinit)."""

from __future__ import annotations

import re

import yaml

from msai_setup.lab import cloudinit

SSH_KEY = "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIExampleKeyForTests lab@example"


def _render() -> dict:
    text = cloudinit.render_user_data(
        hostname="testvm",
        user="morten",
        full_user_name="Morten Hansen",
        password="s3cret",
        ssh_public_key=SSH_KEY,
    )
    assert text.startswith("#cloud-config\n")
    return yaml.safe_load(text)


def test_user_data_is_valid_yaml_with_autoinstall() -> None:
    doc = _render()
    assert "autoinstall" in doc
    assert doc["autoinstall"]["version"] == 1


def test_password_auth_disabled() -> None:
    ai = _render()["autoinstall"]
    assert ai["ssh"]["allow-pw"] is False
    assert ai["ssh"]["install-server"] is True


def test_ssh_key_present() -> None:
    ai = _render()["autoinstall"]
    assert ai["ssh"]["authorized-keys"] == [SSH_KEY]


def test_sudoers_late_command_present() -> None:
    ai = _render()["autoinstall"]
    joined = "\n".join(ai["late-commands"])
    assert "sudoers.d/90-morten" in joined
    assert "morten ALL=(ALL) NOPASSWD:ALL" in joined


def test_password_is_sha512_crypt_not_plaintext() -> None:
    ai = _render()["autoinstall"]
    pw = ai["identity"]["password"]
    assert pw != "s3cret"
    assert pw.startswith("$6$")


def test_network_uses_interface_pattern_not_hardcoded_names() -> None:
    """Regression for H3: no hardcoded enp0s3/eth0; use a match-all pattern."""
    ai = _render()["autoinstall"]
    ethernets = ai["network"]["ethernets"]
    # The old, broken form keyed entries by literal interface names.
    assert "enp0s3" not in ethernets
    assert "eth0" not in ethernets
    # Exactly one match-all entry with DHCP.
    assert len(ethernets) == 1
    (entry,) = ethernets.values()
    assert entry["dhcp4"] is True
    pattern = entry["match"]["name"]
    # The pattern must actually match the real VirtualBox names we've seen.
    glob_re = re.compile("^" + pattern.replace("*", ".*") + "$")
    for iface in ("enp0s3", "enp0s8", "eth0"):
        assert glob_re.match(iface), f"{pattern!r} should match {iface}"


def test_crypt_password_is_pure_python_no_subprocess(monkeypatch) -> None:
    """Regression for H2: _crypt_password must not shell out to openssl."""
    import subprocess

    def _boom(*args: object, **kwargs: object) -> object:
        raise AssertionError("_crypt_password must not spawn a subprocess")

    monkeypatch.setattr(subprocess, "run", _boom)
    monkeypatch.setattr(subprocess, "Popen", _boom)

    out = cloudinit._crypt_password("hunter2", salt="abcdefgh")
    assert out == "$6$abcdefgh$" + out.split("$", 3)[3]
    assert out.startswith("$6$abcdefgh$")
    # 86-char SHA-512 crypt digest tail.
    assert len(out.split("$")[3]) == 86


def test_crypt_password_matches_known_vector() -> None:
    """Cross-check against a fixed SHA-512 crypt vector.

    The expected value was produced byte-for-byte by the reference C
    implementation via `openssl passwd -6 -salt saltstring "Hello world!"`,
    so this pins our pure-Python port to the canonical algorithm.
    """
    out = cloudinit._crypt_password("Hello world!", salt="saltstring")
    assert out == (
        "$6$saltstring$svn8UoSVapNtMuq1ukKS4tPQd8iKwSMHWjl/O817"
        "G3uBnIFNjnQJuesI68u4OTLiBFdcbYEdFCoEOfaS35inz1"
    )


def test_crypt_password_random_salt_differs() -> None:
    a = cloudinit._crypt_password("same-password")
    b = cloudinit._crypt_password("same-password")
    assert a != b  # random salt each call
    assert a.startswith("$6$") and b.startswith("$6$")


def test_meta_data_round_trips() -> None:
    text = cloudinit.render_meta_data(hostname="testvm")
    doc = yaml.safe_load(text)
    assert doc["local-hostname"] == "testvm"
    assert doc["instance-id"] == "iid-local-testvm"
