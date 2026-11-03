# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import argparse

from phone_scanner import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="phone-scanner")
    parser.add_argument(
        "--version",
        action="version",
        version=f"Phone-Scanner {__version__}",
    )
    return parser


def main() -> int:
    parser = build_parser()
    parser.parse_args()
    return 0
