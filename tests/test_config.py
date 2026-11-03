# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Antony Mwendwa (Antech-greyhat)

from phone_scanner import config


def test_first_run_then_saved(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DATA_DIR, str(tmp_path))
    assert config.is_first_run() is True
    cfg = config.load_config()
    assert cfg == config.Config()
    cfg.permission_granted = True
    cfg.mode = "online"
    cfg.report_format = "json"
    config.save_config(cfg)
    assert config.is_first_run() is False


def test_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DATA_DIR, str(tmp_path))
    saved = config.Config(permission_granted=True, mode="online", report_format="json")
    config.save_config(saved)
    loaded = config.load_config()
    assert loaded == saved


def test_bad_values_coerced(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DATA_DIR, str(tmp_path))
    config.config_path().parent.mkdir(parents=True, exist_ok=True)
    config.config_path().write_text(
        '{"mode": "weird", "report_format": "pdf"}', encoding="utf-8"
    )
    loaded = config.load_config()
    assert loaded.mode == "offline"
    assert loaded.report_format == "html"


def test_corrupt_file_falls_back(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DATA_DIR, str(tmp_path))
    config.config_path().parent.mkdir(parents=True, exist_ok=True)
    config.config_path().write_text("not json", encoding="utf-8")
    assert config.load_config() == config.Config()


def test_data_dir_override(tmp_path, monkeypatch):
    monkeypatch.setenv(config.ENV_DATA_DIR, str(tmp_path))
    assert config.data_dir() == tmp_path
