# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import subprocess
from pathlib import Path

import pytest

from phone_scanner import adb

FIXTURES = Path(__file__).parent / "fixtures" / "adb"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text()


def _fake_run(stdout: str = "", returncode: int = 0, stderr: str = ""):
    def runner(cmd, capture_output, text, timeout):
        return subprocess.CompletedProcess(cmd, returncode, stdout, stderr)

    return runner


def test_parse_device_ready():
    devices = adb.parse_devices(_load("devices_device.txt"))
    assert len(devices) == 1
    assert devices[0].state == "device"
    assert devices[0].serial == "SERIAL0001ABCD"
    assert devices[0].model == "SM_A515F"


def test_parse_unauthorized():
    devices = adb.parse_devices(_load("devices_unauthorized.txt"))
    assert devices[0].state == "unauthorized"
    assert devices[0].model is None


def test_parse_offline():
    devices = adb.parse_devices(_load("devices_offline.txt"))
    assert devices[0].state == "offline"


def test_parse_no_permissions():
    devices = adb.parse_devices(_load("devices_no_permissions.txt"))
    assert devices[0].state == "no permissions"


def test_parse_none_is_empty():
    assert adb.parse_devices(_load("devices_none.txt")) == []


def test_parse_multiple_and_ready():
    devices = adb.parse_devices(_load("devices_multiple.txt"))
    assert len(devices) == 2
    assert len(adb.ready_devices(devices)) == 2
    assert devices[1].model == "TECNO_KI5k"


def test_list_devices_uses_adb(monkeypatch):
    monkeypatch.setattr(adb.shutil, "which", lambda _: "adb")
    monkeypatch.setattr(
        adb.subprocess, "run", _fake_run(stdout=_load("devices_device.txt"))
    )
    devices = adb.list_devices()
    assert devices[0].serial == "SERIAL0001ABCD"


def test_require_adb_missing(monkeypatch):
    monkeypatch.setattr(adb.shutil, "which", lambda _: None)
    with pytest.raises(adb.AdbNotFoundError):
        adb.require_adb()


def test_run_shell_refuses_pm_uninstall():
    with pytest.raises(adb.AdbCommandError):
        adb.run_shell("S", ["pm", "uninstall", "com.example.app"])


def test_run_shell_refuses_settings_put():
    with pytest.raises(adb.AdbCommandError):
        adb.run_shell("S", ["settings", "put", "secure", "x", "1"])


def test_run_shell_refuses_pm_disable():
    with pytest.raises(adb.AdbCommandError):
        adb.run_shell("S", ["pm", "disable", "com.example.app"])


def test_run_shell_refuses_reboot():
    with pytest.raises(adb.AdbCommandError):
        adb.run_shell("S", ["reboot"])


def test_run_shell_allows_pm_list(monkeypatch):
    monkeypatch.setattr(adb.shutil, "which", lambda _: "adb")
    monkeypatch.setattr(
        adb.subprocess, "run", _fake_run(stdout="package:com.example.app\n")
    )
    out = adb.run_shell("S", ["pm", "list", "packages", "-3"])
    assert "com.example.app" in out


def test_run_shell_nonzero_raises(monkeypatch):
    monkeypatch.setattr(adb.shutil, "which", lambda _: "adb")
    monkeypatch.setattr(
        adb.subprocess, "run", _fake_run(returncode=1, stderr="device offline")
    )
    with pytest.raises(adb.AdbCommandError, match="device offline"):
        adb.run_shell("S", ["getprop", "ro.product.model"])


def test_run_shell_timeout_raises(monkeypatch):
    monkeypatch.setattr(adb.shutil, "which", lambda _: "adb")

    def timeout_run(cmd, capture_output, text, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)

    monkeypatch.setattr(adb.subprocess, "run", timeout_run)
    with pytest.raises(adb.AdbTimeoutError):
        adb.run_shell("S", ["dumpsys", "package", "com.example.app"])


def test_get_device_info(monkeypatch):
    props = {
        "ro.product.model": "SM_A515F\n",
        "ro.build.version.release": "13\n",
        "ro.build.version.sdk": "33\n",
        "ro.build.version.security_patch": "2024-05-01\n",
        "sys.boot_completed": "1\n",
    }

    def fake_run_shell(serial, args, timeout=adb.DEFAULT_TIMEOUT):
        return props[args[1]]

    monkeypatch.setattr(adb, "run_shell", fake_run_shell)
    info = adb.get_device_info("S")
    assert info.model == "SM_A515F"
    assert info.android_release == "13"
    assert info.sdk == "33"
    assert info.security_patch == "2024-05-01"
    assert info.boot_completed is True


def test_get_device_info_not_booted(monkeypatch):
    def fake_run_shell(serial, args, timeout=adb.DEFAULT_TIMEOUT):
        return "" if args[1] == "sys.boot_completed" else "x\n"

    monkeypatch.setattr(adb, "run_shell", fake_run_shell)
    info = adb.get_device_info("S")
    assert info.boot_completed is False


def test_fix_for_state_known_and_unknown():
    assert "Allow" in adb.fix_for_state("unauthorized")
    assert "Unexpected" in adb.fix_for_state("sideload")
