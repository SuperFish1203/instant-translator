from __future__ import annotations

from PySide6.QtWidgets import QApplication


class TranslationController:
    def __init__(self, settings_service, translator_manager, capture_service, popup_window):
        self.settings_service = settings_service
        self.translator_manager = translator_manager
        self.capture_service = capture_service
        self.popup_window = popup_window
        self._busy = False

    def translate_selection(self) -> None:
        if self._busy:
            return
        self._busy = True
        try:
            settings = self.settings_service.load()
            self._apply_popup_preferences(settings)
            self.popup_window.show_loading()
            QApplication.processEvents()

            capture_result = self.capture_service.capture_selected_text()
            if capture_result.error_code:
                self.popup_window.show_error(capture_result.error_message or "未获取到可翻译文本")
                return

            translation_result = self.translator_manager.translate(settings, capture_result.text)
            if translation_result.ok:
                self.popup_window.show_result(translation_result.text)
                return
            self.popup_window.show_error(translation_result.error_message or "翻译失败")
        finally:
            self._busy = False

    def translate_demo_text(self) -> None:
        settings = self.settings_service.load()
        self._apply_popup_preferences(settings)
        self.popup_window.show_loading()
        QApplication.processEvents()
        result = self.translator_manager.translate(settings, "Hello world", "en", settings.general.target_language)
        if result.ok:
            self.popup_window.show_result(result.text)
            return
        self.popup_window.show_error(result.error_message or "翻译失败")

    def test_current_settings(self, settings):
        return self.translator_manager.translate(settings, "Hello world", "en", settings.general.target_language)

    def update_popup_width(self, width: int) -> None:
        settings = self.settings_service.load()
        if settings.general.popup_width == width:
            return
        settings.general.popup_width = width
        self.settings_service.save(settings)

    def _apply_popup_preferences(self, settings) -> None:
        self.popup_window.hide_on_focus_lost = settings.general.hide_on_focus_lost
        self.popup_window.resize(settings.general.popup_width, self.popup_window.height())
