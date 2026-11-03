# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json
import time
from pathlib import Path
from typing import Any

SEVEN_DAYS = 7 * 24 * 3600


def load_cache(path: Path) -> dict[str, dict[str, Any]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {str(k).lower(): v for k, v in data.items()}


def save_cache(cache: dict[str, dict[str, Any]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(cache, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def get_cached(
    cache: dict[str, dict[str, Any]],
    sha256: str,
    now: float | None = None,
    max_age: int = SEVEN_DAYS,
) -> dict[str, Any] | None:
    entry = cache.get(sha256.lower())
    if entry is None:
        return None
    now = time.time() if now is None else now
    if now - float(entry.get("time", 0)) > max_age:
        return None
    return entry


def put_cached(
    cache: dict[str, dict[str, Any]],
    sha256: str,
    source: str,
    verdict: str,
    label: str | None,
    now: float | None = None,
) -> None:
    cache[sha256.lower()] = {
        "source": source,
        "verdict": verdict,
        "label": label,
        "time": time.time() if now is None else now,
    }
