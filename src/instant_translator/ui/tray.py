from __future__ import annotations

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon


class AppTrayIcon(QSystemTrayIcon):
    def __init__(self, main_window, on_test_translation, on_quit, parent=None):
        icon = main_window.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        super().__init__(icon, parent)
        self.main_window = main_window
        self.activated.connect(self._handle_activation)

        menu = QMenu()
        open_action = QAction("打开设置", self)
        open_action.triggered.connect(self.main_window.showNormal)

        test_action = QAction("立即测试翻译", self)
        test_action.triggered.connect(on_test_translation)

        quit_action = QAction("退出", self)
        quit_action.triggered.connect(on_quit)

        menu.addAction(open_action)
        menu.addAction(test_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.setContextMenu(menu)

    def _handle_activation(self, reason) -> None:
        if reason == QSystemTrayIcon.DoubleClick:
            self.main_window.showNormal()
            self.main_window.raise_()
            self.main_window.activateWindow()
