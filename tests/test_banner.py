# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from types import SimpleNamespace

from phone_scanner.ui import banner


def test_choose_big_when_wide_and_unicode():
    assert banner.choose_art(100, unicode_ok=True) is banner.BIG


def test_choose_small_when_wide_but_not_unicode():
    assert banner.choose_art(100, unicode_ok=False) is banner.SMALL


def test_choose_small_when_medium_width():
    assert banner.choose_art(50, unicode_ok=True) is banner.SMALL


def test_choose_plain_when_narrow():
    assert banner.choose_art(30, unicode_ok=True) == banner.PLAIN


def test_supports_unicode_utf8():
    assert banner.supports_unicode(SimpleNamespace(encoding="utf-8")) is True


def test_supports_unicode_cp1252():
    assert banner.supports_unicode(SimpleNamespace(encoding="cp1252")) is False


def test_big_art_has_twelve_lines():
    assert len(banner.BIG.splitlines()) == 12


def test_small_art_is_pure_ascii():
    assert banner.SMALL.isascii()
