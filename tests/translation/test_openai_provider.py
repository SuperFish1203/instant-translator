from instant_translator.translation.openai_provider import OpenAICompatibleTranslator


def test_openai_provider_extracts_message_content(requests_mock):
    requests_mock.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={"choices": [{"message": {"content": "你好世界"}}]},
    )
    translator = OpenAICompatibleTranslator(
        base_url="http://127.0.0.1:8000/v1",
        api_key="sk-demo",
        model="demo-model",
        custom_headers={"X-Client": "InstantTranslator"},
        timeout_seconds=30,
    )

    result = translator.translate("hello world", "en", "zh-CN")

    assert result.text == "你好世界"
    assert result.error_code is None


def test_openai_provider_includes_custom_headers(requests_mock):
    requests_mock.post(
        "http://127.0.0.1:8000/v1/chat/completions",
        json={"choices": [{"message": {"content": "bonjour"}}]},
    )
    translator = OpenAICompatibleTranslator(
        base_url="http://127.0.0.1:8000/v1",
        api_key="sk-demo",
        model="demo-model",
        custom_headers={"X-Client": "InstantTranslator"},
        timeout_seconds=30,
    )

    translator.translate("hello", "en", "fr")

    history = requests_mock.request_history
    assert history[0].headers["X-Client"] == "InstantTranslator"
    assert history[0].headers["Authorization"] == "Bearer sk-demo"
