from instant_translator.bootstrap import build_application


def test_build_application_returns_runtime_container(tmp_path, qapp):
    runtime = build_application(settings_path=tmp_path / "settings.json", app=qapp, register_hotkey=False)

    assert runtime.main_window is not None
    assert runtime.popup_window is not None
    assert runtime.hotkey_manager is not None
    assert runtime.translation_controller is not None
