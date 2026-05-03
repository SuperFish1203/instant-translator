from __future__ import annotations

from dataclasses import dataclass
from time import sleep


@dataclass
class CaptureResult:
    text: str = ""
    error_code: str | None = None
    error_message: str | None = None


class WindowsInputGateway:
    def send_copy(self) -> None:
        import ctypes

        user32 = ctypes.windll.user32
        vk_control = 0x11
        vk_c = 0x43
        key_up = 0x0002

        user32.keybd_event(vk_control, 0, 0, 0)
        user32.keybd_event(vk_c, 0, 0, 0)
        user32.keybd_event(vk_c, 0, key_up, 0)
        user32.keybd_event(vk_control, 0, key_up, 0)


class SelectionCaptureService:
    def __init__(self, clipboard_gateway, input_gateway, sleep_fn=sleep):
        self.clipboard_gateway = clipboard_gateway
        self.input_gateway = input_gateway
        self.sleep_fn = sleep_fn

    def capture_selected_text(self) -> CaptureResult:
        snapshot = self.clipboard_gateway.snapshot()
        try:
            self.input_gateway.send_copy()
            self.sleep_fn(0.12)
            text = self.clipboard_gateway.read_text()
            if not text or not text.strip():
                return CaptureResult(error_code="EMPTY_TEXT", error_message="未获取到可翻译文本")
            return CaptureResult(text=text.strip())
        finally:
            self.clipboard_gateway.restore(snapshot)
