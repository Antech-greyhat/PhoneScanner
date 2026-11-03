# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from phone_scanner.hashes import cache
from phone_scanner.hashes.lookup import HashResolver
from phone_scanner.hashes.malwarebazaar import HashResult
from phone_scanner.hashes.virustotal import VtResult

A = "a" * 64
B = "b" * 64


class Clock:
    def __init__(self):
        self.t = 1000.0
        self.slept: list[float] = []

    def now(self):
        return self.t

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.t += seconds


def _resolver(**kwargs):
    clock = Clock()
    defaults = dict(
        local_list={},
        cache_data={},
        now=clock.now,
        sleep=clock.sleep,
    )
    defaults.update(kwargs)
    return HashResolver(**defaults), clock


def test_offline_hit():
    resolver, _ = _resolver(local_list={A: "Cerberus"})
    verdict = resolver.resolve_offline(A)
    assert verdict.verdict == "malicious"
    assert verdict.source == "offline"
    assert verdict.label == "Cerberus"


def test_offline_miss():
    resolver, _ = _resolver()
    assert resolver.resolve_offline(A).verdict == "unknown"


def test_online_uses_cache_first():
    data: dict = {}
    cache.put_cached(data, A, "virustotal", "malicious", "Old", now=1000.0)
    resolver, _ = _resolver(cache_data=data)
    verdict = resolver.resolve_online(A)
    assert verdict.source == "cache"
    assert verdict.verdict == "malicious"


def test_online_offline_list_before_network():
    called = {"mb": 0}

    def mb(key, sha):
        called["mb"] += 1
        return HashResult("known", "x")

    resolver, _ = _resolver(local_list={A: "Hydra"}, mb_key="k", mb_lookup=mb)
    verdict = resolver.resolve_online(A)
    assert verdict.source == "offline"
    assert called["mb"] == 0


def test_online_malwarebazaar_then_virustotal():
    resolver, _ = _resolver(
        mb_key="k",
        vt_key="v",
        mb_lookup=lambda key, sha: HashResult("known", "Anubis"),
        vt_lookup=lambda key, sha: VtResult("malicious", 5, 0, "trojan"),
    )
    verdict = resolver.resolve_online(A)
    assert verdict.source == "malwarebazaar"
    assert verdict.label == "Anubis"


def test_online_falls_through_to_virustotal():
    resolver, _ = _resolver(
        mb_key="k",
        vt_key="v",
        mb_lookup=lambda key, sha: HashResult("unknown"),
        vt_lookup=lambda key, sha: VtResult("malicious", 9, 0, "trojan.x"),
    )
    verdict = resolver.resolve_online(A)
    assert verdict.source == "virustotal"
    assert verdict.verdict == "malicious"


def test_virustotal_quota_stops_further_vt_calls():
    calls = {"n": 0}

    def vt(key, sha):
        calls["n"] += 1
        return VtResult("quota")

    resolver, _ = _resolver(vt_key="v", vt_lookup=vt)
    first = resolver.resolve_online(A)
    second = resolver.resolve_online(B)
    assert first.verdict == "unknown"
    assert second.verdict == "unknown"
    assert calls["n"] == 1  # quota flag stops the second call


def test_rate_limit_waits_between_vt_calls():
    resolver, clock = _resolver(
        vt_key="v",
        vt_lookup=lambda key, sha: VtResult("unknown"),
        vt_interval=15,
    )
    resolver.resolve_online(A)
    resolver.resolve_online(B)
    # second call must have waited close to the interval
    assert resolver.vt_interval - 1 <= max(clock.slept) <= resolver.vt_interval
