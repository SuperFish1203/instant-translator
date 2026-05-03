from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TranslationResult:
    text: str = ""
    error_code: str | None = None
    error_message: str | None = None

    @property
    def ok(self) -> bool:
        return self.error_code is None


class BaseTranslator:
    provider_key: str = ""

    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> TranslationResult:
        raise NotImplementedError
