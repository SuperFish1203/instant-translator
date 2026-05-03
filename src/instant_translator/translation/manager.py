from __future__ import annotations

from instant_translator.settings.models import AppSettings
from instant_translator.translation.base import TranslationResult
from instant_translator.translation.google_provider import GoogleTranslateTranslator
from instant_translator.translation.openai_provider import OpenAICompatibleTranslator
from instant_translator.translation.tencent_provider import TencentTranslateTranslator


class TranslatorManager:
    def translate(
        self,
        settings: AppSettings,
        text: str,
        source_language: str | None = None,
        target_language: str | None = None,
    ) -> TranslationResult:
        cleaned_text = text.strip()
        if not cleaned_text:
            return TranslationResult(error_code="EMPTY_TEXT", error_message="未获取到可翻译文本")

        resolved_source = source_language
        if resolved_source is None and settings.general.source_language_mode == "manual":
            resolved_source = settings.general.source_language
        resolved_target = target_language or settings.general.target_language

        provider_key = settings.provider.active
        if provider_key == "openai_compatible":
            provider_settings = settings.provider.openai_compatible
            if not provider_settings.base_url.strip() or not provider_settings.model.strip():
                return TranslationResult(error_code="CONFIG_ERROR", error_message="请补全 OpenAI 兼容接口地址和模型名")
            translator = OpenAICompatibleTranslator(
                base_url=provider_settings.base_url,
                api_key=provider_settings.api_key,
                model=provider_settings.model,
                custom_headers=provider_settings.custom_headers,
                timeout_seconds=provider_settings.timeout_seconds,
            )
            return translator.translate(cleaned_text, resolved_source, resolved_target)

        if provider_key == "google_translate":
            provider_settings = settings.provider.google_translate
            if not provider_settings.api_key.strip():
                return TranslationResult(error_code="CONFIG_ERROR", error_message="请填写 Google Translate API Key")
            translator = GoogleTranslateTranslator(
                api_key=provider_settings.api_key,
                timeout_seconds=provider_settings.timeout_seconds,
            )
            return translator.translate(cleaned_text, resolved_source, resolved_target)

        if provider_key == "tencent_translate":
            provider_settings = settings.provider.tencent_translate
            if not provider_settings.secret_id.strip() or not provider_settings.secret_key.strip():
                return TranslationResult(error_code="CONFIG_ERROR", error_message="请填写腾讯翻译密钥信息")
            translator = TencentTranslateTranslator(
                secret_id=provider_settings.secret_id,
                secret_key=provider_settings.secret_key,
                region=provider_settings.region,
                project_id=provider_settings.project_id,
                timeout_seconds=provider_settings.timeout_seconds,
            )
            return translator.translate(cleaned_text, resolved_source, resolved_target)

        return TranslationResult(error_code="CONFIG_ERROR", error_message="未识别的翻译服务商")
