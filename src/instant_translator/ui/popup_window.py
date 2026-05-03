from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import QPlainTextEdit, QVBoxLayout, QWidget


class PopupWindow(QWidget):
    def __init__(self, on_width_changed=None):
        super().__init__()
        self.on_width_changed = on_width_changed or (lambda _width: None)
        self.hide_on_focus_lost = True

        self.setWindowTitle("Instant Translator")
        self.setWindowFlags(Qt.Tool | Qt.WindowStaysOnTopHint)
        self.setMinimumWidth(320)
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        self.result_view = QPlainTextEdit(self)
        self.result_view.setReadOnly(True)
        self.result_view.setPlainText("翻译中")
        layout.addWidget(self.result_view)

    def show_loading(self) -> None:
        self.result_view.setPlainText("翻译中")
        self._show_near_cursor()

    def show_result(self, text: str) -> None:
        self.result_view.setPlainText(text)
        self._show_near_cursor()

    def show_error(self, text: str) -> None:
        self.result_view.setPlainText(text)
        self._show_near_cursor()

    def resizeEvent(self, event) -> None:  # noqa: N802
        self.on_width_changed(self.width())
        super().resizeEvent(event)

    def focusOutEvent(self, event) -> None:  # noqa: N802
        if self.hide_on_focus_lost:
            self.hide()
        super().focusOutEvent(event)

    def _show_near_cursor(self) -> None:
        cursor_pos = QCursor.pos()
        self.move(cursor_pos.x() + 16, cursor_pos.y() + 16)
        self.show()
        self.raise_()
        self.activateWindow()
