from __future__ import annotations

from typing import Any

import requests

from instant_translator.translation.base import BaseTranslator, TranslationResult


class OpenAICompatibleTranslator(BaseTranslator):
    provider_key = "openai_compatible"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        custom_headers: dict[str, str] | None = None,
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.custom_headers = custom_headers or {}
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> TranslationResult:
        headers = {
            "Content-Type": "application/json",
            **self.custom_headers,
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self._build_system_prompt(source_language, target_language)},
                {"role": "user", "content": text},
            ],
            "temperature": 0.1,
        }

        return self._request_translation(headers, payload)

    def _request_translation(self, headers: dict[str, str], payload: dict[str, Any]) -> TranslationResult:
        try:
            response = self.session.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"].strip()
            return TranslationResult(text=content)
        except requests.HTTPError as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (401, 403):
                return TranslationResult(error_code="AUTH_ERROR", error_message="认证失败，请检查密钥或权限")
            if status_code == 429:
                return TranslationResult(error_code="RATE_LIMIT", error_message="请求过于频繁，请稍后重试")
            return TranslationResult(error_code="NETWORK_ERROR", error_message="请求失败，请检查网络或服务地址")
        except requests.RequestException:
            return TranslationResult(error_code="NETWORK_ERROR", error_message="请求失败，请检查网络或服务地址")
        except (KeyError, IndexError, TypeError, ValueError):
            return TranslationResult(error_code="UNKNOWN_ERROR", error_message="翻译结果解析失败")

    @staticmethod
    def _build_system_prompt(source_language: str | None, target_language: str) -> str:
        if source_language:
            return (
                "You are a translation engine. "
                f"Translate the user text from {source_language} to {target_language}. "
                "Return only the translated text."
            )
        return (
            "You are a translation engine. "
            f"Detect the source language automatically and translate the user text to {target_language}. "
            "Return only the translated text."
        )
