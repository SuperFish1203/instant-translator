from __future__ import annotations

from copy import deepcopy
import json

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from instant_translator.settings.models import AppSettings


LANGUAGE_OPTIONS = [
    ("自动识别", "auto"),
    ("中文", "zh-CN"),
    ("英文", "en"),
    ("日文", "ja"),
    ("韩文", "ko"),
    ("法文", "fr"),
    ("德文", "de"),
]

PROVIDER_OPTIONS = [
    ("OpenAI Compatible", "openai_compatible"),
    ("Google Translate", "google_translate"),
    ("Tencent Translate", "tencent_translate"),
]


class MainWindow(QMainWindow):
    def __init__(self, settings_service, translation_controller=None):
        super().__init__()
        self.settings_service = settings_service
        self.translation_controller = translation_controller
        self.settings = settings_service.load()

        self.setWindowTitle("Instant Translator 设置")
        self.resize(720, 520)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(16)

        root_layout.addWidget(self._build_general_group())
        root_layout.addWidget(self._build_provider_group())
        root_layout.addLayout(self._build_button_row())
        root_layout.addStretch(1)

        self._apply_settings_to_form(self.settings)

    def _build_general_group(self) -> QGroupBox:
        group = QGroupBox("常规设置", self)
        layout = QFormLayout(group)

        self.source_language_mode_combo = QComboBox(group)
        self.source_language_mode_combo.addItem("自动识别", "auto")
        self.source_language_mode_combo.addItem("手动指定", "manual")

        self.source_language_combo = QComboBox(group)
        self.target_language_combo = QComboBox(group)
        for label, value in LANGUAGE_OPTIONS[1:]:
            self.source_language_combo.addItem(label, value)
            self.target_language_combo.addItem(label, value)

        layout.addRow("源语言模式", self.source_language_mode_combo)
        layout.addRow("源语言", self.source_language_combo)
        layout.addRow("目标语言", self.target_language_combo)
        return group

    def _build_provider_group(self) -> QGroupBox:
        group = QGroupBox("翻译服务", self)
        layout = QVBoxLayout(group)

        provider_row = QHBoxLayout()
        provider_row.addWidget(QLabel("当前服务商", group))
        self.provider_combo = QComboBox(group)
        for label, value in PROVIDER_OPTIONS:
            self.provider_combo.addItem(label, value)
        self.provider_combo.currentIndexChanged.connect(self._sync_provider_stack)
        provider_row.addWidget(self.provider_combo, 1)
        layout.addLayout(provider_row)

        self.provider_stack = QStackedWidget(group)
        self.provider_stack.addWidget(self._build_openai_form())
        self.provider_stack.addWidget(self._build_google_form())
        self.provider_stack.addWidget(self._build_tencent_form())
        layout.addWidget(self.provider_stack)
        return group

    def _build_openai_form(self) -> QWidget:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        self.openai_base_url_edit = QLineEdit(widget)
        self.openai_api_key_edit = QLineEdit(widget)
        self.openai_model_edit = QLineEdit(widget)
        self.openai_headers_edit = QLineEdit(widget)
        self.openai_timeout_spin = QSpinBox(widget)
        self.openai_timeout_spin.setRange(5, 300)
        self.openai_timeout_spin.setValue(30)

        layout.addRow("Base URL", self.openai_base_url_edit)
        layout.addRow("API Key", self.openai_api_key_edit)
        layout.addRow("Model", self.openai_model_edit)
        layout.addRow("Custom Headers(JSON)", self.openai_headers_edit)
        layout.addRow("Timeout(秒)", self.openai_timeout_spin)
        return widget

    def _build_google_form(self) -> QWidget:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        self.google_api_key_edit = QLineEdit(widget)
        self.google_timeout_spin = QSpinBox(widget)
        self.google_timeout_spin.setRange(5, 300)
        self.google_timeout_spin.setValue(30)

        layout.addRow("API Key", self.google_api_key_edit)
        layout.addRow("Timeout(秒)", self.google_timeout_spin)
        return widget

    def _build_tencent_form(self) -> QWidget:
        widget = QWidget(self)
        layout = QFormLayout(widget)
        self.tencent_secret_id_edit = QLineEdit(widget)
        self.tencent_secret_key_edit = QLineEdit(widget)
        self.tencent_region_edit = QLineEdit(widget)
        self.tencent_project_id_spin = QSpinBox(widget)
        self.tencent_project_id_spin.setRange(0, 999999)
        self.tencent_timeout_spin = QSpinBox(widget)
        self.tencent_timeout_spin.setRange(5, 300)
        self.tencent_timeout_spin.setValue(30)

        layout.addRow("SecretId", self.tencent_secret_id_edit)
        layout.addRow("SecretKey", self.tencent_secret_key_edit)
        layout.addRow("Region", self.tencent_region_edit)
        layout.addRow("ProjectId", self.tencent_project_id_spin)
        layout.addRow("Timeout(秒)", self.tencent_timeout_spin)
        return widget

    def _build_button_row(self) -> QHBoxLayout:
        row = QHBoxLayout()
        row.addStretch(1)

        self.test_button = QPushButton("测试连接", self)
        self.test_button.clicked.connect(self.test_connection)
        self.test_button.setEnabled(self.translation_controller is not None)

        self.save_button = QPushButton("保存配置", self)
        self.save_button.clicked.connect(self.save_settings)

        row.addWidget(self.test_button)
        row.addWidget(self.save_button)
        return row

    def _apply_settings_to_form(self, settings: AppSettings) -> None:
        self._set_combo_data(self.source_language_mode_combo, settings.general.source_language_mode)
        self._set_combo_data(self.source_language_combo, settings.general.source_language)
        self._set_combo_data(self.target_language_combo, settings.general.target_language)
        self._set_combo_data(self.provider_combo, settings.provider.active)

        self.openai_base_url_edit.setText(settings.provider.openai_compatible.base_url)
        self.openai_api_key_edit.setText(settings.provider.openai_compatible.api_key)
        self.openai_model_edit.setText(settings.provider.openai_compatible.model)
        self.openai_headers_edit.setText(self._headers_to_text(settings.provider.openai_compatible.custom_headers))
        self.openai_timeout_spin.setValue(settings.provider.openai_compatible.timeout_seconds)

        self.google_api_key_edit.setText(settings.provider.google_translate.api_key)
        self.google_timeout_spin.setValue(settings.provider.google_translate.timeout_seconds)

        self.tencent_secret_id_edit.setText(settings.provider.tencent_translate.secret_id)
        self.tencent_secret_key_edit.setText(settings.provider.tencent_translate.secret_key)
        self.tencent_region_edit.setText(settings.provider.tencent_translate.region)
        self.tencent_project_id_spin.setValue(settings.provider.tencent_translate.project_id)
        self.tencent_timeout_spin.setValue(settings.provider.tencent_translate.timeout_seconds)

        self._sync_provider_stack()

    def collect_settings(self) -> AppSettings:
        settings = deepcopy(self.settings)
        settings.general.source_language_mode = self.source_language_mode_combo.currentData()
        settings.general.source_language = self.source_language_combo.currentData()
        settings.general.target_language = self.target_language_combo.currentData()

        settings.provider.active = self.provider_combo.currentData()
        settings.provider.openai_compatible.base_url = self.openai_base_url_edit.text().strip()
        settings.provider.openai_compatible.api_key = self.openai_api_key_edit.text().strip()
        settings.provider.openai_compatible.model = self.openai_model_edit.text().strip()
        settings.provider.openai_compatible.custom_headers = self._parse_headers(self.openai_headers_edit.text())
        settings.provider.openai_compatible.timeout_seconds = self.openai_timeout_spin.value()

        settings.provider.google_translate.api_key = self.google_api_key_edit.text().strip()
        settings.provider.google_translate.timeout_seconds = self.google_timeout_spin.value()

        settings.provider.tencent_translate.secret_id = self.tencent_secret_id_edit.text().strip()
        settings.provider.tencent_translate.secret_key = self.tencent_secret_key_edit.text().strip()
        settings.provider.tencent_translate.region = self.tencent_region_edit.text().strip() or "ap-beijing"
        settings.provider.tencent_translate.project_id = self.tencent_project_id_spin.value()
        settings.provider.tencent_translate.timeout_seconds = self.tencent_timeout_spin.value()
        return settings

    def save_settings(self) -> None:
        settings = self.collect_settings()
        self.settings_service.save(settings)
        self.settings = settings
        self.statusBar().showMessage("配置已保存。", 3000)

    def test_connection(self) -> None:
        if self.translation_controller is None:
            return
        settings = self.collect_settings()
        result = self.translation_controller.test_current_settings(settings)
        if result.ok:
            self.statusBar().showMessage("服务连接正常。", 3000)
            return
        self.statusBar().showMessage(result.error_message or "连接失败", 5000)

    def closeEvent(self, event) -> None:  # noqa: N802
        event.ignore()
        self.hide()

    def _sync_provider_stack(self) -> None:
        self.provider_stack.setCurrentIndex(self.provider_combo.currentIndex())

    @staticmethod
    def _headers_to_text(headers: dict[str, str]) -> str:
        if not headers:
            return ""
        return ", ".join(f"{key}:{value}" for key, value in headers.items())

    @staticmethod
    def _parse_headers(text: str) -> dict[str, str]:
        headers: dict[str, str] = {}
        if not text.strip():
            return headers
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return {str(key): str(value) for key, value in parsed.items()}
        for item in text.split(","):
            if ":" not in item:
                continue
            key, value = item.split(":", 1)
            key = key.strip()
            value = value.strip()
            if key:
                headers[key] = value
        return headers

    @staticmethod
    def _set_combo_data(combo: QComboBox, value: str) -> None:
        index = combo.findData(value, role=Qt.UserRole)
        if index >= 0:
            combo.setCurrentIndex(index)
