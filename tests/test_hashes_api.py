# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json
from pathlib import Path

from phone_scanner.hashes import malwarebazaar, virustotal

FIXTURES = Path(__file__).parent / "fixtures" / "hashes"
A = "a" * 64
B = "b" * 64


def _load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_mb_file_type_builds_hash_map():
    hashes = malwarebazaar.parse_file_type_response(_load("mb_filetype.json"))
    assert hashes[A] == "Cerberus"
    assert hashes[B] == "Hydra"  # null signature falls back to a non-generic tag


def test_mb_file_type_non_ok_is_empty():
    assert malwarebazaar.parse_file_type_response({"query_status": "error"}) == {}


def test_mb_get_info_known():
    result = malwarebazaar.parse_get_info_response(_load("mb_getinfo.json"))
    assert result.status == "known"
    assert result.label == "Cerberus"


def test_mb_get_info_not_found_is_unknown():
    result = malwarebazaar.parse_get_info_response(_load("mb_notfound.json"))
    assert result.status == "unknown"
    assert result.label is None


def test_mb_label_falls_back_when_only_generic_tags():
    entry = {"sha256_hash": A, "signature": None, "tags": ["Android", "apk", "signed"]}
    assert malwarebazaar._label(entry) == "malware (unlabeled)"


def test_vt_malicious():
    result = virustotal.parse_file_response(200, _load("vt_known.json"))
    assert result.status == "malicious"
    assert result.malicious == 22
    assert result.label == "trojan.ag1600498/abapplication"


def test_vt_clean():
    result = virustotal.parse_file_response(200, _load("vt_clean.json"))
    assert result.status == "clean"
    assert result.malicious == 0


def test_vt_not_found():
    assert (
        virustotal.parse_file_response(404, _load("vt_unknown.json")).status
        == "unknown"
    )


def test_vt_quota():
    assert virustotal.parse_file_response(429, {}).status == "quota"


def test_vt_bad_key():
    assert virustotal.parse_file_response(401, {}).status == "bad_key"


def test_vt_other_error():
    assert virustotal.parse_file_response(500, {}).status == "error"
