# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import argparse
import contextlib
import json
import logging
import os
import time
import webbrowser

import requests
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn
from rich.table import Table
from rich.text import Text

from phone_scanner import __version__, adb, checks, collect, config, scoring
from phone_scanner.adb import Device
from phone_scanner.hashes import cache, malwarebazaar, offline
from phone_scanner.hashes.lookup import HashResolver, HashVerdict
from phone_scanner.report import html_report, json_report
from phone_scanner.ui import banner, menu

LEVEL_STYLES = {"High": "red", "Medium": "yellow", "Low": "green"}

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


def pick_device(console: Console, devices: list[Device]) -> Device | None:
    ready = adb.ready_devices(devices)
    if not ready:
        return None
    if len(ready) == 1:
        return ready[0]
    console.print(
        "[?] More than one phone is ready. Pick one:", style="cyan", markup=False
    )
    for index, device in enumerate(ready, start=1):
        label = f"  [{index}] {device.model or device.serial} ({device.serial})"
        console.print(label, style="cyan", markup=False)
    try:
        raw = console.input("> ").strip()
    except (KeyboardInterrupt, EOFError):
        return None
    if raw.isdigit() and 1 <= int(raw) <= len(ready):
        return ready[int(raw) - 1]
    return None


def results_table(report: dict) -> Table:
    table = Table(show_lines=False)
    table.add_column("App")
    table.add_column("Installer")
    table.add_column("Level")
    table.add_column("Score", justify="right")
    table.add_column("Top reasons")
    for app in report["apps"]:
        reasons = "; ".join(r["text"] for r in app["reasons"][:2]) or "-"
        table.add_row(
            Text(app["package"]),
            Text(app["installer"] or "none (sideloaded)"),
            Text(app["level"], style=LEVEL_STYLES.get(app["level"], "")),
            Text(str(app["score"])),
            Text(reasons),
        )
    return table


def hash_list_path() -> object:
    return config.data_dir() / "hashes.json"


def cache_path() -> object:
    return config.data_dir() / "hash_cache.json"


def _progress_columns() -> tuple:
    return (
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("{task.completed}/{task.total}"),
    )


def _collect(console: Console, device: Device) -> collect.ScanData:
    with Progress(*_progress_columns(), console=console, transient=True) as progress:
        task = progress.add_task("Collecting apps", total=None)

        def on_progress(done: int, total: int, package: str) -> None:
            progress.update(
                task, total=total, completed=done, description=f"Scanning {package}"
            )

        return collect.collect(device.serial, on_progress=on_progress)


def _hash_apps(
    console: Console, cfg: config.Config, device: Device, data: collect.ScanData
) -> dict[str, HashVerdict]:
    local_list = offline.load_hash_list(hash_list_path())
    online = cfg.mode == "online"
    cache_data = cache.load_cache(cache_path()) if online else {}
    resolver = HashResolver(
        local_list,
        cache_data,
        mb_key=os.environ.get("MB_AUTH_KEY") if online else None,
        vt_key=os.environ.get("VT_API_KEY") if online else None,
    )
    verdicts: dict[str, HashVerdict] = {}
    with Progress(*_progress_columns(), console=console, transient=True) as progress:
        task = progress.add_task("Hashing apps", total=len(data.apps))
        for app in data.apps:
            progress.update(task, advance=1, description=f"Hashing {app.package}")
            sha = offline.hash_apk(device.serial, app.package)
            if sha is None:
                continue
            verdicts[app.package] = (
                resolver.resolve_online(sha)
                if online
                else resolver.resolve_offline(sha)
            )
    if online:
        cache.save_cache(cache_data, cache_path())
    return verdicts


def _assemble_report(
    cfg: config.Config,
    device: Device,
    info: adb.DeviceInfo,
    data: collect.ScanData,
    scan_type: str,
    verdicts: dict[str, HashVerdict],
) -> dict:
    findings = checks.check_all(
        data.apps, data.accessibility_packages, data.admin_packages
    )
    for finding in findings:
        verdict = verdicts.get(finding.package)
        if verdict is not None and verdict.verdict == "malicious":
            finding.findings.append("malware_hash_match")
    scores = scoring.score_all(findings, scoring.load_rules(), scoring.load_allowlist())
    results: list[json_report.AppResult] = []
    for app, finding, score in zip(data.apps, findings, scores, strict=True):
        verdict = verdicts.get(app.package)
        hash_result = None
        if verdict is not None:
            hash_result = {
                "source": verdict.source,
                "verdict": verdict.verdict,
                "label": verdict.label,
            }
            if verdict.verdict == "malicious" and verdict.label:
                for reason in score.reasons:
                    if reason.key == "malware_hash_match":
                        reason.text = (
                            f"Matches known malware: {verdict.label} "
                            f"(via {verdict.source})."
                        )
        results.append(json_report.AppResult(app, finding, score, hash_result))
    device_dict = {
        "model": info.model,
        "android_version": info.android_release,
        "security_patch": info.security_patch,
        "serial": menu.shorten_serial(device.serial),
    }
    return json_report.build_report(
        __version__, scan_type, cfg.mode, device_dict, results
    )


def save_report(cfg: config.Config, report: dict) -> object:
    name = json_report.timestamp_name()
    reports_dir = config.reports_dir()
    if cfg.report_format == "json":
        return json_report.write_json(report, reports_dir / f"{name}.json")
    return html_report.write_html(report, reports_dir / f"{name}.html")


def _pick_ready_device(console: Console) -> Device | None:
    try:
        devices = adb.list_devices()
    except adb.AdbError as exc:
        console.print(f"[!] {exc}", style="red", markup=False)
        pause(console)
        return None
    device = pick_device(console, devices)
    if device is None:
        state = devices[0].state if devices else "no device"
        console.print(
            f"[!] No phone ready to scan ({state}). {adb.fix_for_state(state)}",
            style="yellow",
            markup=False,
        )
        pause(console)
    return device


def _run_scan(console: Console, cfg: config.Config, scan_type: str) -> None:
    device = _pick_ready_device(console)
    if device is None:
        return
    if scan_type == "full" and cfg.mode == "online":
        console.print(
            "[!] Online full scan can be slow: VirusTotal allows 4 lookups a "
            "minute, so unknown apps wait 15s each.",
            style="yellow",
            markup=False,
        )
    try:
        info = adb.get_device_info(device.serial)
        data = _collect(console, device)
        verdicts = _hash_apps(console, cfg, device, data) if scan_type == "full" else {}
        report = _assemble_report(cfg, device, info, data, scan_type, verdicts)
    except KeyboardInterrupt:
        console.print("\n[!] Scan cancelled.", style="yellow", markup=False)
        pause(console)
        return
    except adb.AdbError as exc:
        console.print(f"[!] Scan failed: {exc}", style="red", markup=False)
        pause(console)
        return
    console.print(results_table(report))
    path = save_report(cfg, report)
    console.print(f"[+] Report saved to {path}", style="cyan", markup=False)
    with contextlib.suppress(KeyboardInterrupt, EOFError):
        console.input("[?] Press Enter to return ")


def run_quick_scan(console: Console, cfg: config.Config) -> None:
    _run_scan(console, cfg, "quick")


def run_full_scan(console: Console, cfg: config.Config) -> None:
    _run_scan(console, cfg, "full")


def update_offline_list(console: Console, cfg: config.Config) -> None:
    mb_key = os.environ.get("MB_AUTH_KEY")
    if not mb_key:
        console.print(
            "[!] No MalwareBazaar key. Get a free one at https://auth.abuse.ch "
            "and put MB_AUTH_KEY in .env.",
            style="yellow",
            markup=False,
        )
        pause(console)
        return
    try:
        with console.status("Downloading hashes from MalwareBazaar..."):
            new = malwarebazaar.fetch_hashes(mb_key, limit=1000)
    except requests.RequestException as exc:
        console.print(f"[!] Update failed: {exc}", style="red", markup=False)
        pause(console)
        return
    path = hash_list_path()
    existing = offline.load_hash_list(path)
    merged = offline.merge_hashes(existing, new)
    offline.save_hash_list(merged, path)
    added = len(merged) - len(existing)
    console.print(
        f"[+] Offline hash list now has {len(merged)} hashes ({added} new).",
        style="cyan",
        markup=False,
    )
    pause(console)


def _print_json_summary(console: Console, path) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    summary = data.get("summary", {})
    console.print(
        f"[+] {path.name}: High {summary.get('High', 0)}, "
        f"Medium {summary.get('Medium', 0)}, Low {summary.get('Low', 0)}",
        style="cyan",
        markup=False,
    )
    for app in data.get("apps", [])[:5]:
        console.print(
            f"  {app['level']:<6} {app['score']:>2}  {app['package']}",
            style="cyan",
            markup=False,
        )


def view_last_report(console: Console, cfg: config.Config) -> None:
    reports_dir = config.reports_dir()
    files = list(reports_dir.glob("scan-*.*")) if reports_dir.exists() else []
    if not files:
        console.print(
            "[!] No reports yet. Run a scan first.", style="yellow", markup=False
        )
        pause(console)
        return
    latest = max(files, key=lambda p: p.stat().st_mtime)
    if latest.suffix == ".html":
        webbrowser.open(latest.resolve().as_uri())
        console.print(
            f"[+] Opened {latest} in your browser.", style="cyan", markup=False
        )
    else:
        _print_json_summary(console, latest)
    pause(console)


def handle_choice(console: Console, cfg: config.Config, choice: str) -> bool:
    if choice == "00":
        return False
    if choice == "01":
        run_quick_scan(console, cfg)
    elif choice == "02":
        run_full_scan(console, cfg)
    elif choice == "03":
        toggle_mode(console, cfg)
    elif choice == "04":
        toggle_format(console, cfg)
    elif choice == "05":
        view_last_report(console, cfg)
    elif choice == "06":
        update_offline_list(console, cfg)
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
