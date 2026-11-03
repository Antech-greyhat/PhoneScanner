# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import hashlib
from pathlib import Path

from phone_scanner.hashes import offline


def test_parse_sha256sum_valid_and_invalid():
    line = "DEAD" + "a" * 60 + "  /data/app/x/base.apk"
    assert offline.parse_sha256sum(line) == "dead" + "a" * 60
    assert offline.parse_sha256sum("no hash here") is None


def test_base_apk_path_prefers_base(monkeypatch):
    def run_shell(serial, args, timeout=offline.adb.DEFAULT_TIMEOUT):
        return (
            "package:/data/app/x/split_config.arm64_v8a.apk\n"
            "package:/data/app/x/base.apk\n"
        )

    monkeypatch.setattr(offline.adb, "run_shell", run_shell)
    assert offline.base_apk_path("S", "com.example").endswith("base.apk")


def test_hash_apk_uses_sha256sum(monkeypatch):
    def run_shell(serial, args, timeout=offline.adb.DEFAULT_TIMEOUT):
        if args[0] == "pm":
            return "package:/data/app/x/base.apk\n"
        if args[0] == "sha256sum":
            return "a" * 64 + "  /data/app/x/base.apk\n"
        return ""

    monkeypatch.setattr(offline.adb, "run_shell", run_shell)
    assert offline.hash_apk("S", "com.example") == "a" * 64


def test_hash_apk_falls_back_to_pull(monkeypatch):
    content = b"hello apk bytes"
    expected = hashlib.sha256(content).hexdigest()

    def run_shell(serial, args, timeout=offline.adb.DEFAULT_TIMEOUT):
        if args[0] == "pm":
            return "package:/data/app/x/base.apk\n"
        raise offline.adb.AdbCommandError("sha256sum: not found")

    def pull(serial, remote, local, timeout=60):
        Path(local).write_bytes(content)
        return ""

    monkeypatch.setattr(offline.adb, "run_shell", run_shell)
    monkeypatch.setattr(offline.adb, "pull", pull)
    assert offline.hash_apk("S", "com.example") == expected


def test_hash_list_roundtrip_lowercases(tmp_path):
    path = tmp_path / "hashes.json"
    offline.save_hash_list({"AB" * 32: "Trojan"}, path)
    assert offline.load_hash_list(path) == {"ab" * 32: "Trojan"}


def test_load_missing_returns_empty(tmp_path):
    assert offline.load_hash_list(tmp_path / "nope.json") == {}


def test_merge_keeps_existing():
    existing = {"a" * 64: "old"}
    new = {"A" * 64: "new", "b" * 64: "bee"}
    merged = offline.merge_hashes(existing, new)
    assert merged["a" * 64] == "old"
    assert merged["b" * 64] == "bee"


def test_lookup_case_insensitive():
    hashes = {"a" * 64: "Trojan"}
    assert offline.lookup("A" * 64, hashes) == "Trojan"
    assert offline.lookup("f" * 64, hashes) is None
