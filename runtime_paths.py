"""
Runtime path helpers for writable user data.
Cross-platform and bundle-safe.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


APP_NAME = "HandControlAI"


def get_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    if os.name == "nt":
        base = os.getenv("APPDATA")
        if base:
            return Path(base) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    base = os.getenv("XDG_DATA_HOME")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".local" / "share" / APP_NAME


def get_logs_dir() -> Path:
    return get_data_dir() / "logs"


def get_screenshots_dir() -> Path:
    return get_data_dir() / "screenshots"


def get_calibration_path() -> Path:
    return get_data_dir() / "calibration.json"


def get_settings_path() -> Path:
    return get_data_dir() / "settings.json"


def get_crash_log_path() -> Path:
    return get_logs_dir() / "crash.log"


def ensure_runtime_dirs() -> Path:
    data_dir = get_data_dir()
    get_logs_dir().mkdir(parents=True, exist_ok=True)
    get_screenshots_dir().mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
