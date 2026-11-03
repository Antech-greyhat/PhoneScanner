# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json

from phone_scanner.checks import AppFindings
from phone_scanner.collect import AppInfo
from phone_scanner.report import html_report, json_report
from phone_scanner.scoring import Reason, ScoreResult

DEVICE = {
    "model": "SM_A515F",
    "android_version": "13",
    "security_patch": "2024-05-01",
    "serial": "SERIAL0001AB",
}


def _result(
    package, installer, level, score, findings, reasons
) -> json_report.AppResult:
    return json_report.AppResult(
        info=AppInfo(package=package, apk_path=None, installer=installer),
        findings=AppFindings(package=package, installer=installer, findings=findings),
        score=ScoreResult(package, installer, score, level, reasons),
    )


def _sample_results():
    return [
        _result(
            "com.example.safe",
            "com.android.vending",
            "Low",
            0,
            [],
            [],
        ),
        _result(
            "com.example.bad",
            None,
            "High",
            10,
            ["sideloaded", "risky_permission:READ_SMS"],
            [Reason("sideloaded", 3, "Installed from outside an app store.")],
        ),
    ]


def test_build_report_sorts_high_first_and_counts():
    report = json_report.build_report(
        "0.1.0", "quick", "offline", DEVICE, _sample_results()
    )
    assert report["apps"][0]["package"] == "com.example.bad"
    assert report["summary"] == {"Low": 1, "Medium": 0, "High": 1}
    assert report["scan_type"] == "quick"
    assert report["device"]["model"] == "SM_A515F"
    assert report["apps"][0]["hash"] is None
    assert "not prove" in report["notes"]


def test_write_json_roundtrip(tmp_path):
    report = json_report.build_report(
        "0.1.0", "quick", "offline", DEVICE, _sample_results()
    )
    path = json_report.write_json(report, tmp_path / "scan.json")
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["apps"][0]["level"] == "High"


def test_html_report_escapes_values():
    evil = "com.evil<script>alert(1)</script>"
    results = [_result(evil, None, "High", 10, ["sideloaded"], [])]
    report = json_report.build_report("0.1.0", "quick", "offline", DEVICE, results)
    html = html_report.render(report)
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_html_report_is_self_contained():
    report = json_report.build_report(
        "0.1.0", "quick", "offline", DEVICE, _sample_results()
    )
    html = html_report.render(report)
    assert html.startswith("<!DOCTYPE html>")
    assert "http://" not in html and "https://" not in html
    assert "<style>" in html


def test_write_html(tmp_path):
    report = json_report.build_report(
        "0.1.0", "quick", "offline", DEVICE, _sample_results()
    )
    path = html_report.write_html(report, tmp_path / "scan.html")
    assert path.exists()
    assert "Phone-Scanner report" in path.read_text(encoding="utf-8")


def test_timestamp_name_format():
    name = json_report.timestamp_name()
    assert name.startswith("scan-")
    assert len(name) == len("scan-20260101-120000")
