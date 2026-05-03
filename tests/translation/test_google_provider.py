from instant_translator.translation.google_provider import GoogleTranslateTranslator


def test_google_provider_returns_translated_text(requests_mock):
    requests_mock.post(
        "https://translation.googleapis.com/language/translate/v2",
        json={"data": {"translations": [{"translatedText": "你好"}]}},
    )
    translator = GoogleTranslateTranslator(api_key="demo-key", timeout_seconds=30)

    result = translator.translate("hello", "en", "zh-CN")

    assert result.text == "你好"
    assert result.error_code is None


def test_google_provider_skips_source_when_auto_detecting(requests_mock):
    requests_mock.post(
        "https://translation.googleapis.com/language/translate/v2",
        json={"data": {"translations": [{"translatedText": "你好"}]}},
    )
    translator = GoogleTranslateTranslator(api_key="demo-key", timeout_seconds=30)

    translator.translate("hello", None, "zh-CN")

    request = requests_mock.request_history[0]
    payload = request.json()
    assert payload["q"] == "hello"
    assert payload["target"] == "zh-CN"
    assert "source" not in payload
