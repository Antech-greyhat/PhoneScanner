# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from dataclasses import dataclass

from phone_scanner.collect import AppInfo

# Installers that mean the app did not come from a vetted store. null means
# sideloaded or installed by adb; the package installer means a user tapped an
# APK file. Store installers (Play, a vendor store) are not treated as
# sideloaded. Tune this list with Antech if a store is missing.
SIDELOAD_INSTALLERS: frozenset[str | None] = frozenset(
    {None, "com.google.android.packageinstaller"}
)

# Permissions worth flagging when granted. Scoring points live in rules.json
# (Phase 6); this is the set that produces a risky_permission finding.
RISKY_PERMISSIONS: frozenset[str] = frozenset(
    {
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.SEND_SMS",
        "android.permission.READ_CALL_LOG",
        "android.permission.READ_CONTACTS",
        "android.permission.SYSTEM_ALERT_WINDOW",
        "android.permission.REQUEST_INSTALL_PACKAGES",
        "android.permission.BIND_ACCESSIBILITY_SERVICE",
    }
)


@dataclass
class AppFindings:
    package: str
    installer: str | None
    findings: list[str]


def _short(permission: str) -> str:
    return permission.rsplit(".", 1)[-1]


def check_app(
    app: AppInfo,
    accessibility_packages: set[str],
    admin_packages: set[str],
    risky_permissions: frozenset[str] = RISKY_PERMISSIONS,
) -> AppFindings:
    findings: list[str] = []
    if app.installer in SIDELOAD_INSTALLERS:
        findings.append("sideloaded")
    for permission in sorted(app.granted_permissions & risky_permissions):
        findings.append(f"risky_permission:{_short(permission)}")
    if app.package in accessibility_packages:
        findings.append("accessibility_enabled")
    if app.package in admin_packages:
        findings.append("device_admin")
    if not app.has_launcher:
        findings.append("no_launcher_icon")
    return AppFindings(app.package, app.installer, findings)


def check_all(
    apps: list[AppInfo],
    accessibility_packages: set[str],
    admin_packages: set[str],
    risky_permissions: frozenset[str] = RISKY_PERMISSIONS,
) -> list[AppFindings]:
    return [
        check_app(app, accessibility_packages, admin_packages, risky_permissions)
        for app in apps
    ]
