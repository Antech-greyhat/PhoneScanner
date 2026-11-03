# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from phone_scanner.checks import AppFindings
from phone_scanner.collect import AppInfo
from phone_scanner.scoring import ScoreResult, summarize

NOTES = (
    "A clean result does not prove the phone is safe. These findings are signs "
    "worth checking, not proof. An app with no hash match is unknown, not "
    "confirmed safe."
)

LEVEL_ORDER = {"High": 0, "Medium": 1, "Low": 2}


@dataclass
class AppResult:
    info: AppInfo
    findings: AppFindings
    score: ScoreResult


def _app_dict(result: AppResult) -> dict[str, Any]:
    return {
        "package": result.info.package,
        "installer": result.info.installer,
        "version_name": result.info.version_name,
        "first_install_time": result.info.first_install_time,
        "permissions": {
            "requested": sorted(result.info.requested_permissions),
            "granted": sorted(result.info.granted_permissions),
        },
        "findings": result.findings.findings,
        "score": result.score.score,
        "level": result.score.level,
        "reasons": [
            {"key": r.key, "points": r.points, "text": r.text}
            for r in result.score.reasons
        ],
        "hash": None,
    }


def _sort_key(result: AppResult) -> tuple[int, int]:
    return (LEVEL_ORDER.get(result.score.level, 9), -result.score.score)


def build_report(
    tool_version: str,
    scan_type: str,
    mode: str,
    device: dict[str, str | None],
    results: list[AppResult],
) -> dict[str, Any]:
    ordered = sorted(results, key=_sort_key)
    scan_time = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "tool_version": tool_version,
        "scan_time": scan_time,
        "scan_type": scan_type,
        "mode": mode,
        "device": device,
        "summary": summarize([r.score for r in results]),
        "apps": [_app_dict(r) for r in ordered],
        "notes": NOTES,
    }


def timestamp_name(now: datetime | None = None) -> str:
    now = now or datetime.now(timezone.utc)
    return now.strftime("scan-%Y%m%d-%H%M%S")


def write_json(report: dict[str, Any], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return path
