# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import time
from collections.abc import Callable
from dataclasses import dataclass

from phone_scanner.hashes import cache, malwarebazaar, offline, virustotal

# The free VirusTotal API allows 4 requests a minute, so wait 15s between calls.
VT_MIN_INTERVAL = 15


@dataclass
class HashVerdict:
    sha256: str
    source: str  # cache | offline | malwarebazaar | virustotal | none
    verdict: str  # malicious | clean | unknown
    label: str | None = None


class HashResolver:
    def __init__(
        self,
        local_list: dict[str, str],
        cache_data: dict[str, dict],
        mb_key: str | None = None,
        vt_key: str | None = None,
        mb_lookup: Callable[
            [str, str], malwarebazaar.HashResult
        ] = malwarebazaar.lookup_hash,
        vt_lookup: Callable[[str, str], virustotal.VtResult] = virustotal.lookup_hash,
        now: Callable[[], float] = time.time,
        sleep: Callable[[float], None] = time.sleep,
        vt_interval: int = VT_MIN_INTERVAL,
    ) -> None:
        self.local_list = local_list
        self.cache = cache_data
        self.mb_key = mb_key
        self.vt_key = vt_key
        self.mb_lookup = mb_lookup
        self.vt_lookup = vt_lookup
        self.now = now
        self.sleep = sleep
        self.vt_interval = vt_interval
        self.vt_quota_hit = False
        self._vt_last = 0.0

    def resolve_offline(self, sha256: str) -> HashVerdict:
        label = offline.lookup(sha256, self.local_list)
        if label is not None:
            return HashVerdict(sha256, "offline", "malicious", label)
        return HashVerdict(sha256, "none", "unknown", None)

    def _store(
        self, sha256: str, source: str, verdict: str, label: str | None
    ) -> HashVerdict:
        cache.put_cached(self.cache, sha256, source, verdict, label, now=self.now())
        return HashVerdict(sha256, source, verdict, label)

    def _respect_rate_limit(self) -> None:
        wait = self.vt_interval - (self.now() - self._vt_last)
        if wait > 0:
            self.sleep(wait)
        self._vt_last = self.now()

    def _try_virustotal(self, sha256: str) -> HashVerdict | None:
        if not self.vt_key or self.vt_quota_hit:
            return None
        self._respect_rate_limit()
        result = self.vt_lookup(self.vt_key, sha256)
        if result.status == "quota":
            self.vt_quota_hit = True
            return None
        if result.status in ("bad_key", "error"):
            return None
        verdict = "malicious" if result.status == "malicious" else result.status
        return self._store(sha256, "virustotal", verdict, result.label)

    def resolve_online(self, sha256: str) -> HashVerdict:
        cached = cache.get_cached(self.cache, sha256, now=self.now())
        if cached is not None:
            return HashVerdict(sha256, "cache", cached["verdict"], cached.get("label"))
        label = offline.lookup(sha256, self.local_list)
        if label is not None:
            return self._store(sha256, "offline", "malicious", label)
        if self.mb_key:
            mb = self.mb_lookup(self.mb_key, sha256)
            if mb.status == "known":
                return self._store(sha256, "malwarebazaar", "malicious", mb.label)
        via_vt = self._try_virustotal(sha256)
        if via_vt is not None:
            return via_vt
        return HashVerdict(sha256, "none", "unknown", None)
