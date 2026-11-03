# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

import json
import os
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

from dotenv import load_dotenv

APP_DIR_NAME_WINDOWS = "Phone-Scanner"
APP_DIR_NAME_LINUX = "phone-scanner"
ENV_DATA_DIR = "PHONE_SCANNER_DATA_DIR"
ENV_REPORTS_DIR = "PHONE_SCANNER_REPORTS_DIR"

VALID_MODES = ("offline", "online")
VALID_FORMATS = ("html", "json")


@dataclass
class Config:
    permission_granted: bool = False
    mode: str = "offline"
    report_format: str = "html"


def data_dir() -> Path:
    override = os.environ.get(ENV_DATA_DIR)
    if override:
        return Path(override)
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or str(Path.home())
        return Path(base) / APP_DIR_NAME_WINDOWS
    return Path.home() / ".local" / "share" / APP_DIR_NAME_LINUX


def config_path() -> Path:
    return data_dir() / "config.json"


def reports_dir() -> Path:
    override = os.environ.get(ENV_REPORTS_DIR)
    return Path(override) if override else Path("reports")


def is_first_run() -> bool:
    return not config_path().exists()


def load_env() -> None:
    load_dotenv()


def _coerce(value: str, allowed: tuple[str, ...], default: str) -> str:
    return value if value in allowed else default


def load_config() -> Config:
    path = config_path()
    if not path.exists():
        return Config()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return Config()
    return Config(
        permission_granted=bool(data.get("permission_granted", False)),
        mode=_coerce(data.get("mode", "offline"), VALID_MODES, "offline"),
        report_format=_coerce(data.get("report_format", "html"), VALID_FORMATS, "html"),
    )


def save_config(cfg: Config) -> None:
    path = config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(cfg), indent=2) + "\n", encoding="utf-8")
