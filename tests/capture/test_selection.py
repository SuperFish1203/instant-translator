from instant_translator.capture.selection import SelectionCaptureService


class FakeClipboardGateway:
    def __init__(self, text: str):
        self.text = text
        self.snapshot_value = {"formats": ["text"], "text": "previous"}
        self.restore_calls = []

    def snapshot(self):
        return self.snapshot_value

    def read_text(self):
        return self.text

    def restore(self, snapshot):
        self.restore_calls.append(snapshot)


class FakeInputGateway:
    def __init__(self):
        self.copy_calls = 0

    def send_copy(self):
        self.copy_calls += 1


def test_capture_returns_error_when_clipboard_text_missing():
    clipboard = FakeClipboardGateway("")
    input_gateway = FakeInputGateway()
    service = SelectionCaptureService(
        clipboard_gateway=clipboard,
        input_gateway=input_gateway,
        sleep_fn=lambda *_: None,
    )

    result = service.capture_selected_text()

    assert result.error_code == "EMPTY_TEXT"
    assert input_gateway.copy_calls == 1
    assert clipboard.restore_calls == [clipboard.snapshot_value]


def test_capture_returns_trimmed_text_and_restores_clipboard():
    clipboard = FakeClipboardGateway("  hello world  ")
    input_gateway = FakeInputGateway()
    service = SelectionCaptureService(
        clipboard_gateway=clipboard,
        input_gateway=input_gateway,
        sleep_fn=lambda *_: None,
    )

    result = service.capture_selected_text()

    assert result.text == "hello world"
    assert result.error_code is None
    assert clipboard.restore_calls == [clipboard.snapshot_value]
