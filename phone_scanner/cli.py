# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import argparse
import contextlib
import logging
import os
import time

from rich.console import Console

from phone_scanner import __version__, adb, config
from phone_scanner.adb import Device
from phone_scanner.ui import banner, menu

log = logging.getLogger("phone_scanner")

COMING_SOON = "[*] Coming in a later version."


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phone-scanner")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Phone-Scanner {__version__}",
    )
    parser.add_argument(
        "--no-banner", "-q", action="store_true", help="skip the start-up banner"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="turn off colour output"
    )
    parser.add_argument("--debug", action="store_true", help="show debug logging")
    return parser


def configure_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.WARNING
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")


def make_console(no_color_flag: bool) -> Console:
    no_color = no_color_flag or bool(os.environ.get("NO_COLOR"))
    return Console(no_color=no_color or None)


def ask_permission(console: Console) -> bool:
    console.print(
        "[?] Do you own this phone or have permission to scan it? [y/n]",
        style="yellow",
        markup=False,
    )
    try:
        answer = console.input("> ").strip().lower()
    except (KeyboardInterrupt, EOFError):
        return False
    return answer in ("y", "yes")


def read_status(timeout: int = 5) -> tuple[Device | None, str | None]:
    try:
        devices = adb.list_devices(timeout=timeout)
    except adb.AdbError as exc:
        log.debug("status lookup failed: %s", exc)
        return None, None
    ready = adb.ready_devices(devices)
    if not ready:
        return (devices[0] if devices else None), None
    device = ready[0]
    try:
        info = adb.get_device_info(device.serial, timeout=timeout)
        return device, info.android_release
    except adb.AdbError as exc:
        log.debug("device info failed: %s", exc)
        return device, None


def pause(console: Console) -> None:
    if console.is_terminal:
        time.sleep(1.2)


def show_about(console: Console) -> None:
    console.print("", markup=False)
    console.print(f"Phone-Scanner v{__version__}", style="cyan", markup=False)
    console.print(
        "An Android device scanner that runs over ADB. It flags signs worth "
        "checking, not proof.",
        style="cyan",
        markup=False,
    )
    console.print(
        "Free software under GPLv3. github.com/Antech-greyhat/PhoneScanner",
        style="cyan",
        markup=False,
    )
    with contextlib.suppress(KeyboardInterrupt, EOFError):
        console.input("[?] Press Enter to return ")


def toggle_mode(console: Console, cfg: config.Config) -> None:
    cfg.mode = "online" if cfg.mode == "offline" else "offline"
    config.save_config(cfg)
    console.print(
        f"[+] Mode set to {cfg.mode.capitalize()}.", style="cyan", markup=False
    )
    pause(console)


def toggle_format(console: Console, cfg: config.Config) -> None:
    cfg.report_format = "json" if cfg.report_format == "html" else "html"
    config.save_config(cfg)
    console.print(
        f"[+] Report format set to {cfg.report_format.upper()}.",
        style="cyan",
        markup=False,
    )
    pause(console)


def handle_choice(console: Console, cfg: config.Config, choice: str) -> bool:
    if choice == "00":
        return False
    if choice == "03":
        toggle_mode(console, cfg)
    elif choice == "04":
        toggle_format(console, cfg)
    elif choice == "99":
        show_about(console)
    else:
        console.print(COMING_SOON, style="cyan", markup=False)
        pause(console)
    return True


def run_menu(console: Console, cfg: config.Config, show_banner: bool) -> None:
    while True:
        if console.is_terminal:
            console.clear()
        if show_banner:
            banner.show_banner(console)
        device, android = read_status()
        console.print(
            menu.status_line(device, android, cfg.mode, cfg.report_format),
            style="cyan",
            markup=False,
        )
        menu.show_menu(console)
        try:
            raw = console.input("[?] Select an option: ")
        except (KeyboardInterrupt, EOFError):
            break
        choice = menu.normalize_choice(raw)
        if choice is None:
            console.print(
                "[!] Invalid option, try again.", style="yellow", markup=False
            )
            pause(console)
            continue
        if not handle_choice(console, cfg, choice):
            break


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.debug)
    config.load_env()
    console = make_console(args.no_color)
    cfg = config.load_config()
    if config.is_first_run() or not cfg.permission_granted:
        if not ask_permission(console):
            console.print("[-] Exiting.", style="red", markup=False)
            return 0
        cfg.permission_granted = True
        config.save_config(cfg)
    run_menu(console, cfg, show_banner=not args.no_banner)
    console.print("\n[-] Exiting.", style="red", markup=False)
    return 0
