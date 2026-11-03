# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

DEFAULT_TIMEOUT = 20

# Only these adb shell subcommands are allowed. Each entry is the leading
# tokens a command must start with. Anything else is refused, so the tool can
# never change the phone.
ALLOWED_SHELL_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("pm", "list"),
    ("pm", "path"),
    ("dumpsys",),
    ("settings", "get"),
    ("getprop",),
    ("cmd", "package", "query-activities"),
)

STATE_FIXES: dict[str, str] = {
    "device": "Ready.",
    "unauthorized": (
        "Unlock the phone and tap Allow on the 'Allow USB debugging?' prompt. "
        "Tick 'Always allow from this computer'."
    ),
    "offline": ("Replug the phone, or run 'adb kill-server' then 'adb start-server'."),
    "no permissions": (
        "Your user cannot reach the phone over USB. On Linux, install udev "
        "rules (sudo apt install android-sdk-platform-tools-common) and replug, "
        "or add your user to the plugdev group."
    ),
    "no device": (
        "No phone found. Plug in the phone with a data cable and turn on USB debugging."
    ),
}


class AdbError(Exception):
    pass


class AdbNotFoundError(AdbError):
    pass


class AdbCommandError(AdbError):
    pass


class AdbTimeoutError(AdbError):
    pass


@dataclass
class Device:
    serial: str
    state: str
    model: str | None


@dataclass
class DeviceInfo:
    model: str | None
    android_release: str | None
    sdk: str | None
    security_patch: str | None
    boot_completed: bool


def find_adb() -> str | None:
    return shutil.which("adb")


def _install_hint() -> str:
    link = "https://developer.android.com/tools/releases/platform-tools"
    if sys.platform.startswith("win"):
        return (
            "adb was not found. Install it with "
            "'winget install -e --id Google.PlatformTools', or download "
            f"Platform-Tools from {link} and add the platform-tools folder to "
            "your PATH."
        )
    return (
        "adb was not found. Install it with 'sudo apt install adb', or download "
        f"Platform-Tools from {link}."
    )


def require_adb() -> str:
    path = find_adb()
    if path is None:
        raise AdbNotFoundError(_install_hint())
    return path


def fix_for_state(state: str) -> str:
    return STATE_FIXES.get(state, f"Unexpected device state: {state}.")


def _run(cmd: list[str], timeout: int) -> str:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        raise AdbTimeoutError(
            f"adb timed out after {timeout}s: {' '.join(cmd[1:])}"
        ) from exc
    except FileNotFoundError as exc:
        raise AdbNotFoundError(_install_hint()) from exc
    if result.returncode != 0:
        message = result.stderr.strip() or f"adb exited with {result.returncode}"
        raise AdbCommandError(message)
    return result.stdout


def _parse_state(rest: str) -> str:
    rest = rest.strip()
    if rest.startswith("no permissions"):
        return "no permissions"
    if rest.startswith("unauthorized"):
        return "unauthorized"
    if rest.startswith("offline"):
        return "offline"
    if rest.startswith("device"):
        return "device"
    return rest.split()[0] if rest else "unknown"


def parse_devices(output: str) -> list[Device]:
    devices: list[Device] = []
    for line in output.splitlines():
        line = line.rstrip()
        if not line or line.startswith("List of devices attached"):
            continue
        if line.startswith("*") or line.startswith("adb"):
            continue
        parts = line.split(None, 1)
        if len(parts) < 2:
            continue
        serial, rest = parts[0], parts[1]
        match = re.search(r"\bmodel:(\S+)", rest)
        model = match.group(1) if match else None
        devices.append(Device(serial=serial, state=_parse_state(rest), model=model))
    return devices


def list_devices(timeout: int = DEFAULT_TIMEOUT) -> list[Device]:
    adb = require_adb()
    output = _run([adb, "devices", "-l"], timeout)
    return parse_devices(output)


def ready_devices(devices: list[Device]) -> list[Device]:
    return [d for d in devices if d.state == "device"]


def _shell_allowed(args: list[str]) -> bool:
    return any(
        len(args) >= len(prefix) and tuple(args[: len(prefix)]) == prefix
        for prefix in ALLOWED_SHELL_PREFIXES
    )


def run_shell(serial: str, args: list[str], timeout: int = DEFAULT_TIMEOUT) -> str:
    if not _shell_allowed(args):
        raise AdbCommandError(f"refused shell command: {' '.join(args)}")
    adb = require_adb()
    return _run([adb, "-s", serial, "shell", *args], timeout)


def _getprop(serial: str, name: str, timeout: int) -> str | None:
    value = run_shell(serial, ["getprop", name], timeout).strip()
    return value or None


def get_device_info(serial: str, timeout: int = DEFAULT_TIMEOUT) -> DeviceInfo:
    boot = _getprop(serial, "sys.boot_completed", timeout)
    return DeviceInfo(
        model=_getprop(serial, "ro.product.model", timeout),
        android_release=_getprop(serial, "ro.build.version.release", timeout),
        sdk=_getprop(serial, "ro.build.version.sdk", timeout),
        security_patch=_getprop(serial, "ro.build.version.security_patch", timeout),
        boot_completed=boot == "1",
    )
