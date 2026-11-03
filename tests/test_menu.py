# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import pytest

from phone_scanner.adb import Device
from phone_scanner.ui import menu


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1", "01"),
        ("01", "01"),
        ("2", "02"),
        ("99", "99"),
        ("0", "00"),
        ("00", "00"),
        ("q", "00"),
        ("exit", "00"),
        (" 03 ", "03"),
    ],
)
def test_normalize_valid(raw, expected):
    assert menu.normalize_choice(raw) == expected


@pytest.mark.parametrize("raw", ["", "abc", "50", "07", "100", "-1"])
def test_normalize_invalid(raw):
    assert menu.normalize_choice(raw) is None


def test_status_no_device():
    line = menu.status_line(None, None, "offline", "html")
    assert line == "Device: none | Mode: Offline | Report: HTML"


def test_status_unauthorized():
    device = Device(serial="SERIAL0002EFGH", state="unauthorized", model=None)
    line = menu.status_line(device, None, "offline", "html")
    assert line == "Device: unauthorized | Mode: Offline | Report: HTML"


def test_status_ready_with_android():
    device = Device(serial="SERIAL0001ABCD", state="device", model="SM_A515F")
    line = menu.status_line(device, "13", "online", "json")
    expected = (
        "Device: SM_A515F (SERIAL0001ABCD) | Android 13 | Mode: Online | Report: JSON"
    )
    assert line == expected


def test_shorten_serial_short_unchanged():
    assert menu.shorten_serial("ABC123") == "ABC123"


def test_shorten_serial_long_truncated():
    assert menu.shorten_serial("0123456789ABCDEF") == "0123456789A..."
