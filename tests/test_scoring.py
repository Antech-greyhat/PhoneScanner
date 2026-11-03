# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from phone_scanner import scoring
from phone_scanner.checks import AppFindings

RULES = scoring.load_rules()


def _findings(package, installer, items) -> AppFindings:
    return AppFindings(package=package, installer=installer, findings=items)


def test_rules_and_allowlist_files_load():
    assert "findings" in RULES
    assert scoring.load_allowlist() == set()


def test_trojan_pattern_scores_high():
    app = _findings(
        "com.example.sideloaded",
        None,
        ["sideloaded", "risky_permission:READ_SMS", "accessibility_enabled"],
    )
    result = scoring.score_app(app, RULES, set())
    assert result.level == "High"
    assert result.score >= 8
    # the combo reason is included
    assert any(r.key == "banking_trojan_pattern" for r in result.reasons)


def test_play_store_app_normal_permissions_is_low():
    app = _findings(
        "com.example.store", "com.android.vending", ["risky_permission:READ_CONTACTS"]
    )
    result = scoring.score_app(app, RULES, set())
    assert result.level == "Low"
    assert result.score == 1


def test_clean_app_is_low_zero():
    app = _findings("com.example.store", "com.android.vending", [])
    result = scoring.score_app(app, RULES, set())
    assert result.score == 0
    assert result.level == "Low"


def test_allowlist_lowers_play_store_app():
    app = _findings(
        "com.example.bank",
        "com.android.vending",
        ["risky_permission:READ_SMS", "risky_permission:READ_CONTACTS"],
    )
    result = scoring.score_app(app, RULES, {"com.example.bank"})
    assert result.allowlisted is True
    assert result.score == 0
    assert result.level == "Low"


def test_allowlist_does_not_apply_to_sideloaded():
    # A sideloaded fake copies the allowlisted package name but is not from the
    # Play Store, so the allowlist must not lower its score.
    app = _findings(
        "com.example.bank",
        None,
        ["sideloaded", "risky_permission:READ_SMS", "accessibility_enabled"],
    )
    result = scoring.score_app(app, RULES, {"com.example.bank"})
    assert result.allowlisted is False
    assert result.level == "High"


def test_medium_band():
    app = _findings("com.example.app", None, ["sideloaded", "no_launcher_icon"])
    result = scoring.score_app(app, RULES, set())
    assert result.score == 5
    assert result.level == "Medium"


def test_malware_hash_match_scores_high():
    app = _findings("com.example.bad", None, ["sideloaded", "malware_hash_match"])
    result = scoring.score_app(app, RULES, set())
    assert result.score >= 10
    assert result.level == "High"
    assert any(r.key == "malware_hash_match" for r in result.reasons)


def test_summarize_counts():
    results = [
        scoring.ScoreResult("a", None, 0, "Low"),
        scoring.ScoreResult("b", None, 5, "Medium"),
        scoring.ScoreResult("c", None, 10, "High"),
        scoring.ScoreResult("d", None, 1, "Low"),
    ]
    assert scoring.summarize(results) == {"Low": 2, "Medium": 1, "High": 1}
