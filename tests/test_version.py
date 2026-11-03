# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import subprocess
import sys

from phone_scanner import __version__


def test_version_constant() -> None:
    assert __version__ == "0.1.0"


def test_cli_version_output() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "phone_scanner", "--version"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0
    assert result.stdout.strip() == "Phone-Scanner 0.1.0"
