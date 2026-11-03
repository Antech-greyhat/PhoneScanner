# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import re
from collections.abc import Callable
from dataclasses import dataclass, field

from phone_scanner import adb

# PowerShell writes a UTF-8 BOM, and adb output can carry carriage returns.
BOM = "﻿"


@dataclass
class PackageEntry:
    package: str
    apk_path: str | None
    installer: str | None


@dataclass
class DumpsysInfo:
    version_name: str | None
    first_install_time: str | None
    requested_permissions: set[str]
    granted_permissions: set[str]


@dataclass
class AppInfo:
    package: str
    apk_path: str | None
    installer: str | None
    version_name: str | None = None
    first_install_time: str | None = None
    requested_permissions: set[str] = field(default_factory=set)
    granted_permissions: set[str] = field(default_factory=set)
    has_launcher: bool = False


@dataclass
class ScanData:
    apps: list[AppInfo]
    accessibility_packages: set[str]
    admin_packages: set[str]


def _clean(text: str) -> str:
    return text.lstrip(BOM)


def parse_packages(text: str) -> list[PackageEntry]:
    entries: list[PackageEntry] = []
    for line in _clean(text).splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        body = line[len("package:") :]
        installer: str | None = None
        if "installer=" in body:
            path_pkg, rest = body.split("installer=", 1)
            tokens = rest.split()
            installer = tokens[0] if tokens else None
        else:
            path_pkg = body
        path_pkg = path_pkg.strip()
        # Android 11+ apk paths contain "==", so split on the last "=".
        if "=" in path_pkg:
            apk_path, package = path_pkg.rsplit("=", 1)
        else:
            apk_path, package = None, path_pkg
        if installer in (None, "null", ""):
            installer = None
        entries.append(PackageEntry(package.strip(), apk_path or None, installer))
    return entries


def parse_launchers(text: str) -> set[str]:
    packages: set[str] = set()
    for line in _clean(text).splitlines():
        match = re.match(r"([A-Za-z0-9_.]+)/", line.strip())
        if match:
            packages.add(match.group(1))
    return packages


def parse_accessibility(text: str) -> set[str]:
    cleaned = _clean(text).strip()
    if not cleaned or cleaned == "null":
        return set()
    packages: set[str] = set()
    for component in cleaned.split(":"):
        component = component.strip()
        if "/" in component:
            packages.add(component.split("/", 1)[0])
    return packages


def parse_device_admins(text: str) -> set[str]:
    cleaned = _clean(text)
    start = cleaned.find("Enabled Device Admins")
    if start == -1:
        return set()
    end = cleaned.find("Constants:", start)
    region = cleaned[start:end] if end != -1 else cleaned[start:]
    return set(re.findall(r"ComponentInfo\{([A-Za-z0-9_.]+)/", region))


def _first_value(text: str, marker: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith(marker):
            return stripped[len(marker) :].strip() or None
    return None


def _requested_permissions(text: str) -> set[str]:
    permissions: set[str] = set()
    collecting = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped == "requested permissions:":
            collecting = True
            continue
        if collecting:
            if re.fullmatch(r"[\w.]+", stripped):
                permissions.add(stripped)
            else:
                break
    return permissions


def parse_dumpsys_package(text: str) -> DumpsysInfo:
    cleaned = _clean(text)
    granted = set(re.findall(r"^\s*([\w.]+): granted=true", cleaned, re.MULTILINE))
    return DumpsysInfo(
        version_name=_first_value(cleaned, "versionName="),
        first_install_time=_first_value(cleaned, "firstInstallTime="),
        requested_permissions=_requested_permissions(cleaned),
        granted_permissions=granted,
    )


def _list_packages_raw(serial: str, timeout: int) -> str:
    base = ["pm", "list", "packages", "-3", "-i", "-f"]
    try:
        return adb.run_shell(serial, [*base, "-U"], timeout)
    except adb.AdbCommandError:
        # -U is not supported on every Android version.
        return adb.run_shell(serial, base, timeout)


ProgressHook = Callable[[int, int, str], None]


def collect(
    serial: str,
    timeout: int = adb.DEFAULT_TIMEOUT,
    on_progress: ProgressHook | None = None,
) -> ScanData:
    entries = parse_packages(_list_packages_raw(serial, timeout))
    launchers = parse_launchers(
        adb.run_shell(
            serial,
            [
                "cmd",
                "package",
                "query-activities",
                "--brief",
                "-a",
                "android.intent.action.MAIN",
                "-c",
                "android.intent.category.LAUNCHER",
            ],
            timeout,
        )
    )
    accessibility = parse_accessibility(
        adb.run_shell(
            serial,
            ["settings", "get", "secure", "enabled_accessibility_services"],
            timeout,
        )
    )
    admins = parse_device_admins(
        adb.run_shell(serial, ["dumpsys", "device_policy"], timeout)
    )
    apps: list[AppInfo] = []
    total = len(entries)
    for index, entry in enumerate(entries, start=1):
        if on_progress is not None:
            on_progress(index, total, entry.package)
        info = parse_dumpsys_package(
            adb.run_shell(serial, ["dumpsys", "package", entry.package], timeout)
        )
        apps.append(
            AppInfo(
                package=entry.package,
                apk_path=entry.apk_path,
                installer=entry.installer,
                version_name=info.version_name,
                first_install_time=info.first_install_time,
                requested_permissions=info.requested_permissions,
                granted_permissions=info.granted_permissions,
                has_launcher=entry.package in launchers,
            )
        )
    return ScanData(
        apps=apps, accessibility_packages=accessibility, admin_packages=admins
    )
