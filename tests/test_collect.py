# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from pathlib import Path

from phone_scanner import collect

FIXTURES = Path(__file__).parent / "fixtures" / "adb"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text()


def test_parse_packages_count_and_fields():
    entries = collect.parse_packages(_load("pm_list.txt"))
    assert len(entries) == 4
    by_pkg = {e.package: e for e in entries}
    assert by_pkg["com.example.store"].installer == "com.android.vending"
    assert by_pkg["com.example.sideloaded"].installer is None
    assert (
        by_pkg["com.example.manual"].installer == "com.google.android.packageinstaller"
    )
    assert by_pkg["com.example.vendor"].installer == "com.xiaomi.mipicks"


def test_parse_packages_splits_on_last_equals():
    entries = collect.parse_packages(_load("pm_list.txt"))
    store = next(e for e in entries if e.package == "com.example.store")
    assert store.apk_path.endswith("base.apk")
    assert "==" in store.apk_path


def test_parse_packages_without_installer_or_path():
    line = "package:com.example.bare\n"
    entries = collect.parse_packages(line)
    assert entries[0].package == "com.example.bare"
    assert entries[0].apk_path is None
    assert entries[0].installer is None


def test_parse_packages_handles_bom():
    text = "﻿" + _load("pm_list.txt")
    assert len(collect.parse_packages(text)) == 4


def test_parse_launchers():
    packages = collect.parse_launchers(_load("launchers.txt"))
    assert packages == {"com.example.store", "com.example.vendor"}


def test_parse_accessibility_empty():
    assert collect.parse_accessibility(_load("accessibility_empty.txt")) == set()


def test_parse_accessibility_null():
    assert collect.parse_accessibility("null\n") == set()


def test_parse_accessibility_set():
    packages = collect.parse_accessibility(_load("accessibility_set.txt"))
    assert packages == {"com.example.sideloaded", "com.example.other"}


def test_parse_device_admins_none():
    assert collect.parse_device_admins(_load("device_policy_none.txt")) == set()


def test_parse_device_admins_present():
    packages = collect.parse_device_admins(_load("device_policy_admin.txt"))
    assert packages == {"com.example.sideloaded"}


def test_parse_dumpsys_package():
    info = collect.parse_dumpsys_package(_load("dumpsys_package.txt"))
    assert info.version_name == "1.2.3"
    assert info.first_install_time == "2026-01-02 10:00:00"
    assert "android.permission.READ_SMS" in info.requested_permissions
    assert "android.permission.READ_SMS" in info.granted_permissions
    assert "android.permission.SYSTEM_ALERT_WINDOW" in info.granted_permissions
    # granted=false must be excluded
    assert "android.permission.RECEIVE_SMS" not in info.granted_permissions


def test_parse_dumpsys_empty():
    info = collect.parse_dumpsys_package("")
    assert info.version_name is None
    assert info.granted_permissions == set()
    assert info.requested_permissions == set()
