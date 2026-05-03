from instant_translator.translation.tencent_provider import TencentTranslateTranslator


def test_tencent_provider_returns_target_text(requests_mock):
    requests_mock.post(
        "https://tmt.tencentcloudapi.com/",
        json={"Response": {"TargetText": "你好", "RequestId": "req-1"}},
    )
    translator = TencentTranslateTranslator(
        secret_id="id-demo",
        secret_key="key-demo",
        region="ap-beijing",
        project_id=0,
        timeout_seconds=30,
        timestamp_fn=lambda: 1_700_000_000,
    )

    result = translator.translate("hello", "en", "zh")

    assert result.text == "你好"
    assert result.error_code is None


def test_tencent_provider_sets_required_headers(requests_mock):
    requests_mock.post(
        "https://tmt.tencentcloudapi.com/",
        json={"Response": {"TargetText": "你好", "RequestId": "req-1"}},
    )
    translator = TencentTranslateTranslator(
        secret_id="id-demo",
        secret_key="key-demo",
        region="ap-beijing",
        project_id=0,
        timeout_seconds=30,
        timestamp_fn=lambda: 1_700_000_000,
    )

    translator.translate("hello", "en", "zh")

    request = requests_mock.request_history[0]
    assert request.headers["X-TC-Action"] == "TextTranslate"
    assert request.headers["X-TC-Version"] == "2018-03-21"
    assert request.headers["X-TC-Region"] == "ap-beijing"
    assert request.headers["Authorization"].startswith("TC3-HMAC-SHA256 Credential=id-demo/")
