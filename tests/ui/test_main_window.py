from PySide6.QtCore import Qt

from instant_translator.settings.models import AppSettings
from instant_translator.ui.main_window import MainWindow


class FakeSettingsService:
    def __init__(self):
        self.current_settings = AppSettings()
        self.saved_settings = None

    def load(self):
        return self.current_settings

    def save(self, settings):
        self.saved_settings = settings
        self.current_settings = settings


def test_main_window_saves_provider_selection(qtbot):
    fake_settings_service = FakeSettingsService()
    window = MainWindow(settings_service=fake_settings_service, translation_controller=None)
    qtbot.addWidget(window)

    window.provider_combo.setCurrentText("Google Translate")
    window.google_api_key_edit.setText("demo-key")
    qtbot.mouseClick(window.save_button, Qt.LeftButton)

    assert fake_settings_service.saved_settings.provider.active == "google_translate"
    assert fake_settings_service.saved_settings.provider.google_translate.api_key == "demo-key"


def test_main_window_parses_openai_headers_as_json(qtbot):
    fake_settings_service = FakeSettingsService()
    window = MainWindow(settings_service=fake_settings_service, translation_controller=None)
    qtbot.addWidget(window)

    window.provider_combo.setCurrentText("OpenAI Compatible")
    window.openai_headers_edit.setText('{"X-Client": "InstantTranslator", "X-Trace": "1"}')
    settings = window.collect_settings()

    assert settings.provider.openai_compatible.custom_headers == {
        "X-Client": "InstantTranslator",
        "X-Trace": "1",
    }
