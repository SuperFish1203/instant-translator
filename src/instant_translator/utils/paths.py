from __future__ import annotations

import os
from pathlib import Path


APP_NAME = "InstantTranslator"


def get_app_data_dir() -> Path:
    base = os.getenv("APPDATA")
    if base:
        return Path(base) / APP_NAME
    return Path.home() / ".instant_translator"


def get_default_settings_path() -> Path:
    return get_app_data_dir() / "settings.json"


def get_default_log_path() -> Path:
    return get_app_data_dir() / "logs" / "app.log"
