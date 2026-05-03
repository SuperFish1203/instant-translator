from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ClipboardSnapshot:
    data: dict[int, Any] = field(default_factory=dict)


class WindowsClipboardGateway:
    def snapshot(self) -> ClipboardSnapshot:
        import win32clipboard

        snapshot: dict[int, Any] = {}
        win32clipboard.OpenClipboard()
        try:
            current_format = 0
            while True:
                current_format = win32clipboard.EnumClipboardFormats(current_format)
                if current_format == 0:
                    break
                try:
                    snapshot[current_format] = win32clipboard.GetClipboardData(current_format)
                except TypeError:
                    continue
            return ClipboardSnapshot(snapshot)
        finally:
            win32clipboard.CloseClipboard()

    def read_text(self) -> str:
        import win32clipboard
        import win32con

        win32clipboard.OpenClipboard()
        try:
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                return win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT) or ""
            return ""
        finally:
            win32clipboard.CloseClipboard()

    def restore(self, snapshot: ClipboardSnapshot) -> None:
        import win32clipboard

        win32clipboard.OpenClipboard()
        try:
            win32clipboard.EmptyClipboard()
            for format_id, value in snapshot.data.items():
                try:
                    win32clipboard.SetClipboardData(format_id, value)
                except TypeError:
                    continue
        finally:
            win32clipboard.CloseClipboard()
