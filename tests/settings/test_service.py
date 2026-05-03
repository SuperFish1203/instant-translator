from instant_translator.settings.service import SettingsService


def test_load_returns_defaults_when_file_missing(tmp_path):
    service = SettingsService(tmp_path / "settings.json")

    settings = service.load()

    assert settings.general.target_language == "zh-CN"
    assert settings.provider.active == "openai_compatible"


def test_save_round_trip_preserves_provider_data(tmp_path):
    service = SettingsService(tmp_path / "settings.json")
    settings = service.load()
    settings.general.source_language_mode = "manual"
    settings.general.source_language = "en"
    settings.provider.active = "google_translate"
    settings.provider.google_translate.api_key = "demo-key"

    service.save(settings)
    loaded = service.load()

    assert loaded.general.source_language_mode == "manual"
    assert loaded.provider.active == "google_translate"
    assert loaded.provider.google_translate.api_key == "demo-key"
