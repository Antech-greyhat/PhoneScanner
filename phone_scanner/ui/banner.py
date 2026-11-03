# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import sys
from typing import TextIO

from rich.console import Console

from phone_scanner import __version__

# Made once with pyfiglet (ansi_shadow font), then pasted here so pyfiglet is
# not a runtime dependency and the art cannot change by mistake.
BIG = """\
██████╗ ██╗  ██╗ ██████╗ ███╗   ██╗███████╗
██╔══██╗██║  ██║██╔═══██╗████╗  ██║██╔════╝
██████╔╝███████║██║   ██║██╔██╗ ██║█████╗
██╔═══╝ ██╔══██║██║   ██║██║╚██╗██║██╔══╝
██║     ██║  ██║╚██████╔╝██║ ╚████║███████╗
╚═╝     ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═══╝╚══════╝
███████╗ ██████╗ █████╗ ███╗   ██╗███╗   ██╗███████╗██████╗
██╔════╝██╔════╝██╔══██╗████╗  ██║████╗  ██║██╔════╝██╔══██╗
███████╗██║     ███████║██╔██╗ ██║██╔██╗ ██║█████╗  ██████╔╝
╚════██║██║     ██╔══██║██║╚██╗██║██║╚██╗██║██╔══╝  ██╔══██╗
███████║╚██████╗██║  ██║██║ ╚████║██║ ╚████║███████╗██║  ██║
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝╚═╝  ╚═╝"""

# Pure ASCII fallback (pyfiglet "small" font) for narrow or non-Unicode terminals.
SMALL = """\
 ___ _  _  ___  _  _ ___    ___  ___   _   _  _ _  _ ___ ___
| _ \\ || |/ _ \\| \\| | __|__/ __|/ __| /_\\ | \\| | \\| | __| _ \\
|  _/ __ | (_) | .` | _|___\\__ \\ (__ / _ \\| .` | .` | _||   /
|_| |_||_|\\___/|_|\\_|___|  |___/\\___/_/ \\_\\_|\\_|_|\\_|___|_|_\\"""

PLAIN = f"PHONE-SCANNER v{__version__}"

# BIG is 60 columns wide; SMALL is 61. Below TINY_MIN even SMALL will not fit.
WIDE_MIN = 64
TINY_MIN = 40

INFO_LINES = (
    f"Version : {__version__}",
    "Author  : Antech-greyhat",
    "GitHub  : github.com/Antech-greyhat/PhoneScanner",
)
GPL_LINE = "Free software under GPLv3. No warranty."
WARNING_LINE = "[!] Scan only phones you own or have permission to scan."


def supports_unicode(stream: TextIO | None = None) -> bool:
    encoding = getattr(stream or sys.stdout, "encoding", None) or ""
    return "utf" in encoding.lower()


def choose_art(width: int, unicode_ok: bool) -> str:
    if width >= WIDE_MIN and unicode_ok:
        return BIG
    if width >= TINY_MIN:
        return SMALL
    return PLAIN


def show_banner(console: Console) -> None:
    art = choose_art(console.width, supports_unicode(console.file))
    console.print(art, style="bold green", markup=False, highlight=False)
    for line in INFO_LINES:
        console.print(line, style="cyan", markup=False, highlight=False)
    console.print(GPL_LINE, style="cyan", markup=False, highlight=False)
    console.print(WARNING_LINE, style="yellow", markup=False, highlight=False)
