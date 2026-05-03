from __future__ import annotations

import requests

from instant_translator.translation.base import BaseTranslator, TranslationResult


class GoogleTranslateTranslator(BaseTranslator):
    provider_key = "google_translate"
    endpoint = "https://translation.googleapis.com/language/translate/v2"

    def __init__(
        self,
        api_key: str,
        timeout_seconds: int = 30,
        session: requests.Session | None = None,
    ) -> None:
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.session = session or requests.Session()

    def translate(
        self,
        text: str,
        source_language: str | None,
        target_language: str,
    ) -> TranslationResult:
        payload = {
            "q": text,
            "target": target_language,
            "format": "text",
        }
        if source_language:
            payload["source"] = source_language

        try:
            response = self.session.post(
                self.endpoint,
                params={"key": self.api_key},
                json=payload,
                timeout=self.timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            translated_text = data["data"]["translations"][0]["translatedText"]
            return TranslationResult(text=translated_text)
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
