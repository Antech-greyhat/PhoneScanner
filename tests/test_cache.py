# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from phone_scanner.hashes import cache

A = "a" * 64


def test_put_then_get_within_age():
    data: dict = {}
    cache.put_cached(data, A, "virustotal", "malicious", "Cerberus", now=1000.0)
    entry = cache.get_cached(data, A, now=1000.0 + 3600)
    assert entry is not None
    assert entry["verdict"] == "malicious"
    assert entry["label"] == "Cerberus"


def test_get_expired_returns_none():
    data: dict = {}
    cache.put_cached(data, A, "virustotal", "clean", None, now=0.0)
    assert cache.get_cached(data, A, now=cache.SEVEN_DAYS + 1) is None


def test_get_missing_returns_none():
    assert cache.get_cached({}, A, now=1.0) is None


def test_roundtrip(tmp_path):
    data: dict = {}
    cache.put_cached(data, A, "offline", "malicious", "Hydra", now=5.0)
    path = tmp_path / "cache.json"
    cache.save_cache(data, path)
    loaded = cache.load_cache(path)
    assert loaded[A]["label"] == "Hydra"


def test_load_missing_is_empty(tmp_path):
    assert cache.load_cache(tmp_path / "none.json") == {}
