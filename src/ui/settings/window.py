import os
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox
)

from src.i18n import i18n
from src.utils.version import get_logo_path
from src.ui.settings.asr_tab import ASRSettingsTab
from src.ui.settings.llm_tab import LLMSettingsTab
from src.ui.settings.webdav_tab import WebDAVSettingsTab
from src.ui.settings.proxy_tab import ProxySettingsTab
from src.ui.settings.hotkey_tab import HotkeySettingsTab
from src.ui.settings.debug_tab import DebugSettingsTab
from src.ui.settings.about_tab import AboutSettingsTab

DARK_QSS = """
QMainWindow, QDialog, QWidget {
    background-color: #12151e;
    color: #e5e7eb;
    font-family: 'Segoe UI', sans-serif;
    font-size: 13px;
}

QTabWidget::pane {
    border: 1px solid #242936;
    border-radius: 8px;
    background-color: #1a1d28;
    top: -1px;
}

QTabBar::tab {
    background-color: #12151e;
    color: #9ca3af;
    border: 1px solid transparent;
    border-bottom: 2px solid transparent;
    padding: 8px 14px;
    margin-right: 4px;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:hover {
    color: #e5e7eb;
    background-color: #1a1d28;
}

QTabBar::tab:selected {
    color: #818cf8;
    background-color: #1a1d28;
    border-bottom: 2.5px solid #6366f1;
    font-weight: bold;
}

QLabel {
    color: #e5e7eb;
}

QLineEdit, QComboBox, QSpinBox, QPlainTextEdit, QListWidget {
    background-color: #242936;
    color: #f3f4f6;
    border: 1px solid #374151;
    border-radius: 6px;
    padding: 6px 10px;
    selection-background-color: #6366f1;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QPlainTextEdit:focus, QListWidget:focus {
    border: 1.5px solid #6366f1;
}

QPushButton {
    background-color: #374151;
    color: #ffffff;
    border: 1px solid #4b5563;
    border-radius: 6px;
    padding: 6px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #4b5563;
    border-color: #6b7280;
}

QPushButton:pressed {
    background-color: #1f2937;
}

QPushButton#SaveBtn {
    background-color: #6366f1;
    border: 1px solid #4f46e5;
    color: #ffffff;
    font-weight: bold;
}

QPushButton#SaveBtn:hover {
    background-color: #4f46e5;
}

QCheckBox {
    color: #e5e7eb;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1.5px solid #4b5563;
    background-color: #242936;
}

QCheckBox::indicator:unchecked:hover {
    border-color: #6366f1;
}

QCheckBox::indicator:checked {
    background-color: #6366f1;
    border-color: #4f46e5;
}
"""

class SettingsWindow(QMainWindow):
    config_saved = Signal()

    def __init__(self, config_manager, parent=None) -> None:
        super().__init__(parent)
        self.config_manager = config_manager
        self.resize(640, 540)
        self.setStyleSheet(DARK_QSS)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Tab Widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Instantiate Tabs
        self.asr_tab = ASRSettingsTab(self.config_manager)
        self.llm_tab = LLMSettingsTab(self.config_manager)
        self.webdav_tab = WebDAVSettingsTab(self.config_manager)
        self.proxy_tab = ProxySettingsTab(self.config_manager)
        self.hotkey_tab = HotkeySettingsTab(self.config_manager)
        self.debug_tab = DebugSettingsTab(self.config_manager)
        self.about_tab = AboutSettingsTab(self.config_manager)

        self.tabs.addTab(self.asr_tab, "")
        self.tabs.addTab(self.llm_tab, "")
        self.tabs.addTab(self.webdav_tab, "")
        self.tabs.addTab(self.proxy_tab, "")
        self.tabs.addTab(self.hotkey_tab, "")
        self.tabs.addTab(self.debug_tab, "")
        self.tabs.addTab(self.about_tab, "")

        # Bottom Action Bar
        action_layout = QHBoxLayout()
        action_layout.addStretch()

        self.cancel_btn = QPushButton("")
        self.cancel_btn.setFixedWidth(90)
        self.cancel_btn.clicked.connect(self.close)
        action_layout.addWidget(self.cancel_btn)

        self.save_btn = QPushButton("")
        self.save_btn.setObjectName("SaveBtn")
        self.save_btn.setFixedWidth(110)
        self.save_btn.clicked.connect(self._save_config)
        action_layout.addWidget(self.save_btn)

        main_layout.addLayout(action_layout)

        self._load_config()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(f"{i18n.t('app_title')} - {i18n.t('tray_settings').rstrip('.')}")
        logo_path = get_logo_path()
        if logo_path and os.path.exists(logo_path):
            self.setWindowIcon(QIcon(logo_path))

        self.tabs.setTabText(0, i18n.t("tab_asr"))
        self.tabs.setTabText(1, i18n.t("tab_llm"))
        self.tabs.setTabText(2, i18n.t("tab_webdav"))
        self.tabs.setTabText(3, i18n.t("tab_proxy"))
        self.tabs.setTabText(4, i18n.t("tab_hotkey"))
        self.tabs.setTabText(5, i18n.t("tab_debug"))
        self.tabs.setTabText(6, i18n.t("tab_about"))

        self.cancel_btn.setText(i18n.t("btn_cancel"))
        self.save_btn.setText(i18n.t("btn_save"))

    def _load_config(self) -> None:
        self.asr_tab.load_config()
        self.llm_tab.load_config()
        self.webdav_tab.load_config()
        self.proxy_tab.load_config()
        self.hotkey_tab.load_config()
        self.debug_tab.load_config()
        self.about_tab.load_config()
        self.retranslate_ui()

    def _save_config(self) -> None:
        cfg = self.config_manager.config
        self.asr_tab.save_config(cfg)
        self.llm_tab.save_config(cfg)
        self.webdav_tab.save_config(cfg)
        self.proxy_tab.save_config(cfg)
        self.hotkey_tab.save_config(cfg)
        self.debug_tab.save_config(cfg)
        self.about_tab.save_config(cfg)

        self.config_manager.save_config(cfg)
        print("[Settings UI] Configuration saved to disk.")

        # Retranslate window after saving language
        self.retranslate_ui()
        self._load_config()

        self.config_saved.emit()

        QMessageBox.information(self, i18n.t("app_title"), i18n.t("btn_save") + " OK!")
        self.close()
