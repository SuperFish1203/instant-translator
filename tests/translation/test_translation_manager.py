from instant_translator.settings.models import AppSettings
from instant_translator.translation.manager import TranslatorManager


def test_manager_rejects_empty_input():
    manager = TranslatorManager()

    result = manager.translate(AppSettings(), "", None, "zh-CN")

    assert result.error_code == "EMPTY_TEXT"


def test_manager_reports_missing_google_key():
    manager = TranslatorManager()
    settings = AppSettings()
    settings.provider.active = "google_translate"

    result = manager.translate(settings, "hello", None, "zh-CN")

    assert result.error_code == "CONFIG_ERROR"
