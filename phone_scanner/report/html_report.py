# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from html import escape
from pathlib import Path
from typing import Any

LEVEL_COLORS = {
    "High": "#b00020",
    "Medium": "#b26a00",
    "Low": "#2e7d32",
}

STYLE = """
body { font-family: system-ui, Arial, sans-serif; margin: 2rem; color: #1a1a1a; }
h1 { margin-bottom: 0.2rem; }
.meta { color: #555; font-size: 0.9rem; margin-bottom: 1rem; }
.summary span { display: inline-block; padding: 0.3rem 0.7rem; border-radius: 4px;
  color: #fff; margin-right: 0.5rem; font-weight: bold; }
table { border-collapse: collapse; width: 100%; margin-top: 1rem; }
th, td { border: 1px solid #ddd; padding: 0.5rem; text-align: left;
  vertical-align: top; }
th { background: #f4f4f4; }
.level { font-weight: bold; color: #fff; padding: 0.15rem 0.5rem; border-radius: 3px; }
ul { margin: 0; padding-left: 1.1rem; }
.notes { margin-top: 1.5rem; padding: 0.8rem; background: #fff8e1;
  border-left: 4px solid #b26a00; font-size: 0.9rem; }
"""


def _device_line(device: dict[str, Any]) -> str:
    parts = [
        f"Model: {escape(str(device.get('model') or 'unknown'))}",
        f"Android {escape(str(device.get('android_version') or '?'))}",
        f"Patch {escape(str(device.get('security_patch') or '?'))}",
        f"Serial {escape(str(device.get('serial') or '?'))}",
    ]
    return " &middot; ".join(parts)


def _summary_html(summary: dict[str, int]) -> str:
    chips = []
    for level in ("High", "Medium", "Low"):
        color = LEVEL_COLORS[level]
        count = summary.get(level, 0)
        chips.append(f'<span style="background:{color}">{level}: {count}</span>')
    return '<div class="summary">' + "".join(chips) + "</div>"


def _reasons_html(reasons: list[dict[str, Any]]) -> str:
    if not reasons:
        return ""
    items = [
        f"<li>{escape(str(r['text']))} (+{escape(str(r['points']))})</li>"
        for r in reasons
    ]
    return "<ul>" + "".join(items) + "</ul>"


def _row_html(app: dict[str, Any]) -> str:
    color = LEVEL_COLORS.get(app["level"], "#555")
    level = (
        f'<span class="level" style="background:{color}">'
        f"{escape(str(app['level']))}</span>"
    )
    return (
        "<tr>"
        f"<td>{escape(str(app['package']))}</td>"
        f"<td>{escape(str(app['installer'] or 'none (sideloaded)'))}</td>"
        f"<td>{level}</td>"
        f"<td>{escape(str(app['score']))}</td>"
        f"<td>{_reasons_html(app['reasons'])}</td>"
        "</tr>"
    )


def render(report: dict[str, Any]) -> str:
    rows = "".join(_row_html(app) for app in report["apps"])
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        "<title>Phone-Scanner report</title>"
        f"<style>{STYLE}</style></head><body>"
        "<h1>Phone-Scanner report</h1>"
        f'<div class="meta">{_device_line(report["device"])}<br>'
        f"Scan type: {escape(str(report['scan_type']))} &middot; "
        f"Mode: {escape(str(report['mode']))} &middot; "
        f"Time: {escape(str(report['scan_time']))} &middot; "
        f"Tool v{escape(str(report['tool_version']))}</div>"
        f"{_summary_html(report['summary'])}"
        "<table><thead><tr><th>App</th><th>Installer</th><th>Level</th>"
        "<th>Score</th><th>Why</th></tr></thead>"
        f"<tbody>{rows}</tbody></table>"
        f'<div class="notes">{escape(report["notes"])}</div>'
        "</body></html>\n"
    )


def write_html(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(report), encoding="utf-8")
    return path
