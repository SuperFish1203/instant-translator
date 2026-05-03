from __future__ import annotations

import ctypes
from ctypes import wintypes
from typing import Callable


WM_HOTKEY = 0x0312
MOD_ALT = 0x0001
DEFAULT_HOTKEY_ID = 1
DEFAULT_KEY_VK = 0x54


class HotkeyManager:
    def __init__(
        self,
        register_fn: Callable[[], None] | None = None,
        unregister_fn: Callable[[], None] | None = None,
        hotkey_id: int = DEFAULT_HOTKEY_ID,
    ) -> None:
        self.hotkey_id = hotkey_id
        self.handler: Callable[[], None] | None = None
        self._native_filter = None
        self._register_fn = register_fn or self._register_hotkey
        self._unregister_fn = unregister_fn or self._unregister_hotkey

    def set_handler(self, handler: Callable[[], None]) -> None:
        self.handler = handler

    def register(self) -> None:
        self._register_fn()

    def unregister(self) -> None:
        self._unregister_fn()

    def handle_hotkey_message(self) -> None:
        if self.handler is not None:
            self.handler()

    def install_native_event_filter(self, app) -> None:
        try:
            from PySide6.QtCore import QAbstractNativeEventFilter
        except ImportError:
            return

        manager = self

        class NativeHotkeyFilter(QAbstractNativeEventFilter):
            def nativeEventFilter(self, event_type, message):
                if event_type not in ("windows_generic_MSG", "windows_dispatcher_MSG"):
                    return False, 0
                msg = wintypes.MSG.from_address(int(message))
                if msg.message == WM_HOTKEY and msg.wParam == manager.hotkey_id:
                    manager.handle_hotkey_message()
                return False, 0

        self._native_filter = NativeHotkeyFilter()
        app.installNativeEventFilter(self._native_filter)

    def _register_hotkey(self) -> None:
        user32 = ctypes.windll.user32
        success = user32.RegisterHotKey(None, self.hotkey_id, MOD_ALT, DEFAULT_KEY_VK)
        if not success:
            raise RuntimeError("无法注册全局快捷键 Alt+T")

    def _unregister_hotkey(self) -> None:
        user32 = ctypes.windll.user32
        user32.UnregisterHotKey(None, self.hotkey_id)
