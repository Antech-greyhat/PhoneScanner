# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from rich.console import Console

from phone_scanner.adb import Device

MENU: tuple[tuple[str, str, str], ...] = (
    ("01", "Quick scan", "(apps, permissions, services; no hashes)"),
    ("02", "Full scan", "(quick scan + APK hash check)"),
    ("03", "Mode", "(Online / Offline)"),
    ("04", "Report format", "(HTML / JSON)"),
    ("05", "View last report", ""),
    ("06", "Update offline hash list", ""),
    ("99", "About", ""),
    ("00", "Exit", ""),
)

VALID_CODES = frozenset(code for code, _, _ in MENU)
EXIT_WORDS = frozenset({"q", "quit", "exit"})


def normalize_choice(raw: str) -> str | None:
    text = raw.strip().lower()
    if text in EXIT_WORDS:
        return "00"
    if text.isdigit():
        code = text.zfill(2)
        if code in VALID_CODES:
            return code
    return None


def shorten_serial(serial: str) -> str:
    return serial if len(serial) <= 14 else serial[:11] + "..."


def status_line(
    device: Device | None,
    android: str | None,
    mode: str,
    report_format: str,
) -> str:
    if device is None:
        shown = "none"
    elif device.state != "device":
        shown = device.state
    else:
        name = device.model or device.serial
        shown = f"{name} ({shorten_serial(device.serial)})"
    parts = [f"Device: {shown}"]
    if device is not None and device.state == "device" and android:
        parts.append(f"Android {android}")
    parts.append(f"Mode: {mode.capitalize()}")
    parts.append(f"Report: {report_format.upper()}")
    return " | ".join(parts)


def show_menu(console: Console) -> None:
    console.print("", markup=False)
    for code, label, hint in MENU:
        if code in ("99", "00"):
            console.print("", markup=False)
        text = f"  [{code}] {label}"
        if hint:
            text = f"{text:<30} {hint}"
        console.print(text, style="cyan", markup=False, highlight=False)
    console.print("", markup=False)
