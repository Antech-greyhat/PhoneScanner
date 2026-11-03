# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import hashlib
import json
import re
import tempfile
from pathlib import Path

from phone_scanner import adb

# A local list of known-bad APK hashes, kept as sha256 -> label.
CHUNK = 1 << 16


def base_apk_path(
    serial: str, package: str, timeout: int = adb.DEFAULT_TIMEOUT
) -> str | None:
    # pm path lists every split; only base.apk carries the app code we hash.
    output = adb.run_shell(serial, ["pm", "path", package], timeout)
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("package:") and line.endswith("base.apk"):
            return line[len("package:") :]
    for line in output.splitlines():
        line = line.strip()
        if line.startswith("package:"):
            return line[len("package:") :]
    return None


def parse_sha256sum(output: str) -> str | None:
    match = re.match(r"([0-9a-fA-F]{64})\b", output.strip())
    return match.group(1).lower() if match else None


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def hash_apk(
    serial: str, package: str, timeout: int = adb.DEFAULT_TIMEOUT
) -> str | None:
    remote = base_apk_path(serial, package, timeout)
    if remote is None:
        return None
    # Hash on the phone when possible; it avoids pulling the whole apk.
    try:
        digest = parse_sha256sum(adb.run_shell(serial, ["sha256sum", remote], timeout))
    except adb.AdbError:
        digest = None
    if digest:
        return digest
    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp) / "base.apk"
        adb.pull(serial, remote, str(local), timeout)
        try:
            return _hash_file(local)
        finally:
            local.unlink(missing_ok=True)


def load_hash_list(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return {str(k).lower(): str(v) for k, v in data.items()}


def save_hash_list(hashes: dict[str, str], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def merge_hashes(existing: dict[str, str], new: dict[str, str]) -> dict[str, str]:
    merged = dict(existing)
    for key, value in new.items():
        merged.setdefault(key.lower(), value)
    return merged


def lookup(sha256: str, hashes: dict[str, str]) -> str | None:
    return hashes.get(sha256.lower())
