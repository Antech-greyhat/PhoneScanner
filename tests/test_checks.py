# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from phone_scanner import checks
from phone_scanner.collect import AppInfo


def _app(**kwargs) -> AppInfo:
    base = {
        "package": "com.example.app",
        "apk_path": "/data/app/base.apk",
        "installer": "com.android.vending",
    }
    base.update(kwargs)
    return AppInfo(**base)


def test_sideloaded_with_sms_and_no_launcher():
    app = _app(
        package="com.example.sideloaded",
        installer=None,
        granted_permissions={
            "android.permission.READ_SMS",
            "android.permission.SYSTEM_ALERT_WINDOW",
        },
        has_launcher=False,
    )
    result = checks.check_app(app, set(), set())
    assert "sideloaded" in result.findings
    assert "risky_permission:READ_SMS" in result.findings
    assert "risky_permission:SYSTEM_ALERT_WINDOW" in result.findings
    assert "no_launcher_icon" in result.findings


def test_store_app_with_normal_permissions_is_clean():
    app = _app(
        installer="com.android.vending",
        granted_permissions={"android.permission.INTERNET"},
        has_launcher=True,
    )
    result = checks.check_app(app, set(), set())
    assert result.findings == []


def test_manual_install_is_sideloaded():
    app = _app(installer="com.google.android.packageinstaller", has_launcher=True)
    result = checks.check_app(app, set(), set())
    assert "sideloaded" in result.findings


def test_accessibility_and_device_admin_findings():
    app = _app(package="com.example.spy", installer=None, has_launcher=True)
    result = checks.check_app(app, {"com.example.spy"}, {"com.example.spy"})
    assert "accessibility_enabled" in result.findings
    assert "device_admin" in result.findings


def test_denied_risky_permission_not_flagged():
    app = _app(
        installer="com.android.vending",
        requested_permissions={"android.permission.READ_SMS"},
        granted_permissions=set(),
        has_launcher=True,
    )
    result = checks.check_app(app, set(), set())
    assert result.findings == []


def test_check_all_runs_over_list():
    apps = [
        _app(package="a", has_launcher=True),
        _app(package="b", installer=None, has_launcher=True),
    ]
    results = checks.check_all(apps, set(), set())
    assert len(results) == 2
    assert results[1].findings == ["sideloaded"]
