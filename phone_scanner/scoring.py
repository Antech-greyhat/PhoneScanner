# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from phone_scanner.checks import AppFindings

DATA_DIR = Path(__file__).parent / "data"
RULES_PATH = DATA_DIR / "rules.json"
ALLOWLIST_PATH = DATA_DIR / "allowlist.json"

# An allowlisted app only has its score lowered when it really came from the
# Play Store. A sideloaded fake can copy a trusted package name.
PLAY_STORE = "com.android.vending"


@dataclass
class Reason:
    key: str
    points: int
    text: str


@dataclass
class ScoreResult:
    package: str
    installer: str | None
    score: int
    level: str
    reasons: list[Reason] = field(default_factory=list)
    allowlisted: bool = False


def load_rules(path: Path = RULES_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_allowlist(path: Path = ALLOWLIST_PATH) -> set[str]:
    return set(json.loads(path.read_text(encoding="utf-8")))


def level_for(score: int, levels: dict[str, int]) -> str:
    if score <= levels["low_max"]:
        return "Low"
    if score <= levels["medium_max"]:
        return "Medium"
    return "High"


def _combo_matches(finding_set: set[str], combo: dict[str, Any]) -> bool:
    return all(any(key in finding_set for key in group) for group in combo["all_of"])


def score_app(
    app: AppFindings,
    rules: dict[str, Any],
    allowlist: set[str],
) -> ScoreResult:
    finding_set = set(app.findings)
    score = 0
    reasons: list[Reason] = []
    for finding in app.findings:
        rule = rules["findings"].get(finding)
        if rule is not None:
            score += rule["points"]
            reasons.append(Reason(finding, rule["points"], rule["reason"]))
    for combo in rules.get("combos", []):
        if _combo_matches(finding_set, combo):
            score += combo["points"]
            reasons.append(Reason(combo["name"], combo["points"], combo["reason"]))
    allowlisted = app.package in allowlist and app.installer == PLAY_STORE
    if allowlisted:
        score = 0
        reasons = [
            Reason(
                "allowlisted",
                0,
                "On the allowlist and installed from the Play Store.",
            )
        ]
    return ScoreResult(
        package=app.package,
        installer=app.installer,
        score=score,
        level=level_for(score, rules["levels"]),
        reasons=reasons,
        allowlisted=allowlisted,
    )


def score_all(
    apps: list[AppFindings],
    rules: dict[str, Any],
    allowlist: set[str],
) -> list[ScoreResult]:
    return [score_app(app, rules, allowlist) for app in apps]


def summarize(results: list[ScoreResult]) -> dict[str, int]:
    counts = {"Low": 0, "Medium": 0, "High": 0}
    for result in results:
        counts[result.level] += 1
    return counts
