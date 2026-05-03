from instant_translator.hotkey.manager import HotkeyManager


def test_hotkey_manager_emits_callback_for_registered_hotkey():
    calls = []
    manager = HotkeyManager(register_fn=lambda: None, unregister_fn=lambda: None)
    manager.set_handler(lambda: calls.append("triggered"))

    manager.handle_hotkey_message()

    assert calls == ["triggered"]


def test_hotkey_manager_ignores_missing_handler():
    manager = HotkeyManager(register_fn=lambda: None, unregister_fn=lambda: None)

    manager.handle_hotkey_message()

    assert manager.handler is None
