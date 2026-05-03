from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class GeneralSettings:
    source_language_mode: str = "auto"
    source_language: str = "en"
    target_language: str = "zh-CN"
    popup_width: int = 420
    popup_position_mode: str = "cursor"
    hotkey: str = "Alt+T"
    hide_on_focus_lost: bool = True

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "GeneralSettings":
        payload = payload or {}
        return cls(
            source_language_mode=payload.get("source_language_mode", "auto"),
            source_language=payload.get("source_language", "en"),
            target_language=payload.get("target_language", "zh-CN"),
            popup_width=int(payload.get("popup_width", 420)),
            popup_position_mode=payload.get("popup_position_mode", "cursor"),
            hotkey=payload.get("hotkey", "Alt+T"),
            hide_on_focus_lost=bool(payload.get("hide_on_focus_lost", True)),
        )


@dataclass
class OpenAICompatibleSettings:
    base_url: str = "http://127.0.0.1:8000/v1"
    api_key: str = ""
    model: str = ""
    custom_headers: dict[str, str] = field(default_factory=dict)
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "OpenAICompatibleSettings":
        payload = payload or {}
        headers = payload.get("custom_headers") or {}
        return cls(
            base_url=payload.get("base_url", "http://127.0.0.1:8000/v1"),
            api_key=payload.get("api_key", ""),
            model=payload.get("model", ""),
            custom_headers={str(key): str(value) for key, value in headers.items()},
            timeout_seconds=int(payload.get("timeout_seconds", 30)),
        )


@dataclass
class GoogleTranslateSettings:
    api_key: str = ""
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "GoogleTranslateSettings":
        payload = payload or {}
        return cls(
            api_key=payload.get("api_key", ""),
            timeout_seconds=int(payload.get("timeout_seconds", 30)),
        )


@dataclass
class TencentTranslateSettings:
    secret_id: str = ""
    secret_key: str = ""
    region: str = "ap-beijing"
    project_id: int = 0
    timeout_seconds: int = 30

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "TencentTranslateSettings":
        payload = payload or {}
        return cls(
            secret_id=payload.get("secret_id", ""),
            secret_key=payload.get("secret_key", ""),
            region=payload.get("region", "ap-beijing"),
            project_id=int(payload.get("project_id", 0)),
            timeout_seconds=int(payload.get("timeout_seconds", 30)),
        )


@dataclass
class ProviderSettings:
    active: str = "openai_compatible"
    openai_compatible: OpenAICompatibleSettings = field(default_factory=OpenAICompatibleSettings)
    google_translate: GoogleTranslateSettings = field(default_factory=GoogleTranslateSettings)
    tencent_translate: TencentTranslateSettings = field(default_factory=TencentTranslateSettings)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "ProviderSettings":
        payload = payload or {}
        return cls(
            active=payload.get("active", "openai_compatible"),
            openai_compatible=OpenAICompatibleSettings.from_dict(payload.get("openai_compatible")),
            google_translate=GoogleTranslateSettings.from_dict(payload.get("google_translate")),
            tencent_translate=TencentTranslateSettings.from_dict(payload.get("tencent_translate")),
        )


@dataclass
class AppSettings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    provider: ProviderSettings = field(default_factory=ProviderSettings)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> "AppSettings":
        payload = payload or {}
        return cls(
            general=GeneralSettings.from_dict(payload.get("general")),
            provider=ProviderSettings.from_dict(payload.get("provider")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
