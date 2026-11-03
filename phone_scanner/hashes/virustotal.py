# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from dataclasses import dataclass
from typing import Any

import requests

API_URL = "https://www.virustotal.com/api/v3/files/"


@dataclass
class VtResult:
    status: str  # malicious | clean | unknown | quota | bad_key | error
    malicious: int = 0
    suspicious: int = 0
    label: str | None = None


def parse_file_response(status_code: int, payload: dict[str, Any]) -> VtResult:
    if status_code == 404:
        return VtResult("unknown")
    if status_code == 429:
        return VtResult("quota")
    if status_code == 401:
        return VtResult("bad_key")
    if status_code != 200:
        return VtResult("error")
    attributes = (payload.get("data") or {}).get("attributes") or {}
    stats = attributes.get("last_analysis_stats") or {}
    malicious = int(stats.get("malicious", 0))
    suspicious = int(stats.get("suspicious", 0))
    classification = attributes.get("popular_threat_classification") or {}
    label = classification.get("suggested_threat_label")
    status = "malicious" if malicious > 0 or suspicious > 0 else "clean"
    return VtResult(status, malicious, suspicious, label)


def lookup_hash(api_key: str, sha256: str, timeout: int = 60) -> VtResult:
    resp = requests.get(
        API_URL + sha256, headers={"x-apikey": api_key}, timeout=timeout
    )
    payload: dict[str, Any] = {}
    try:
        payload = resp.json()
    except ValueError:
        payload = {}
    return parse_file_response(resp.status_code, payload)
