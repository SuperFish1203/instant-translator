from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PySide6.QtWidgets import QApplication

from instant_translator.capture.clipboard import WindowsClipboardGateway
from instant_translator.capture.selection import SelectionCaptureService, WindowsInputGateway
from instant_translator.controllers.translation_controller import TranslationController
from instant_translator.hotkey.manager import HotkeyManager
from instant_translator.settings.service import SettingsService
from instant_translator.translation.manager import TranslatorManager
from instant_translator.ui.main_window import MainWindow
from instant_translator.ui.popup_window import PopupWindow
from instant_translator.ui.tray import AppTrayIcon
from instant_translator.utils.logging import configure_logging
from instant_translator.utils.paths import get_default_settings_path


@dataclass
class AppRuntime:
    app: QApplication
    settings_service: SettingsService
    main_window: MainWindow
    popup_window: PopupWindow
    tray_icon: AppTrayIcon
    hotkey_manager: HotkeyManager
    translation_controller: TranslationController


def build_application(
    settings_path: str | Path | None = None,
    app: QApplication | None = None,
    register_hotkey: bool = True,
) -> AppRuntime:
    qt_app = app or QApplication.instance() or QApplication([])
    qt_app.setQuitOnLastWindowClosed(False)
    logger = configure_logging()
    logger.info("building application runtime")

    settings_service = SettingsService(settings_path or get_default_settings_path())
    translator_manager = TranslatorManager()
    capture_service = SelectionCaptureService(
        clipboard_gateway=WindowsClipboardGateway(),
        input_gateway=WindowsInputGateway(),
    )
    popup_window = PopupWindow()
    translation_controller = TranslationController(
        settings_service=settings_service,
        translator_manager=translator_manager,
        capture_service=capture_service,
        popup_window=popup_window,
    )
    popup_window.on_width_changed = translation_controller.update_popup_width

    main_window = MainWindow(settings_service=settings_service, translation_controller=translation_controller)
    tray_icon = AppTrayIcon(
        main_window=main_window,
        on_test_translation=translation_controller.translate_demo_text,
        on_quit=qt_app.quit,
        parent=main_window,
    )
    hotkey_manager = HotkeyManager()
    hotkey_manager.set_handler(translation_controller.translate_selection)

    if register_hotkey:
        hotkey_manager.install_native_event_filter(qt_app)
        try:
            hotkey_manager.register()
        except RuntimeError as exc:
            logger.exception("failed to register hotkey: %s", exc)

    qt_app.aboutToQuit.connect(hotkey_manager.unregister)
    qt_app.aboutToQuit.connect(tray_icon.hide)
    return AppRuntime(
        app=qt_app,
        settings_service=settings_service,
        main_window=main_window,
        popup_window=popup_window,
        tray_icon=tray_icon,
        hotkey_manager=hotkey_manager,
        translation_controller=translation_controller,
    )
