from __future__ import annotations

import json
from pathlib import Path

from instant_translator.settings.models import AppSettings


class SettingsService:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def load(self) -> AppSettings:
        if not self.path.exists():
            return AppSettings()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        return AppSettings.from_dict(payload)

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(settings.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
