import os
import requests
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)
from src.i18n import i18n

def get_current_version() -> str:
    version_file = "VERSION"
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "2026.07.30.007"

class AboutSettingsTab(QWidget):
    def __init__(self, config_manager=None) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.version_str = get_current_version()
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # Title & Logo
        self.title_label = QLabel(i18n.t("about_title"))
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #6366f1;")
        layout.addWidget(self.title_label)

        self.sub_label = QLabel(i18n.t("about_subtitle"))
        self.sub_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(self.sub_label)

        layout.addSpacing(10)

        # Info Cards
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        self.author_label = QLabel(f"<b>{i18n.t('about_author')}</b> Zuluion")
        self.author_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(self.author_label)

        self.ver_label = QLabel(f"<b>{i18n.t('about_version')}</b> v{self.version_str}")
        self.ver_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(self.ver_label)

        self.repo_label = QLabel(f"<b>{i18n.t('about_repo')}</b> <a href='https://github.com/zuluion/voice-input' style='color:#818cf8;'>https://github.com/zuluion/voice-input</a>")
        self.repo_label.setOpenExternalLinks(True)
        self.repo_label.setStyleSheet("font-size: 13px;")
        info_layout.addWidget(self.repo_label)

        self.license_label = QLabel(f"<b>{i18n.t('about_license')}</b> MIT License")
        self.license_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(self.license_label)

        layout.addLayout(info_layout)
        layout.addSpacing(15)

        # Check for Updates Button
        btn_layout = QHBoxLayout()
        self.check_update_btn = QPushButton(i18n.t("btn_check_update"))
        self.check_update_btn.setFixedHeight(36)
        self.check_update_btn.clicked.connect(self._check_for_updates)
        btn_layout.addWidget(self.check_update_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

    def load_config(self) -> None:
        self.title_label.setText(i18n.t("about_title"))
        self.sub_label.setText(i18n.t("about_subtitle"))
        self.author_label.setText(f"<b>{i18n.t('about_author')}</b> Zuluion")
        self.ver_label.setText(f"<b>{i18n.t('about_version')}</b> v{self.version_str}")
        self.repo_label.setText(f"<b>{i18n.t('about_repo')}</b> <a href='https://github.com/zuluion/voice-input' style='color:#818cf8;'>https://github.com/zuluion/voice-input</a>")
        self.license_label.setText(f"<b>{i18n.t('about_license')}</b> MIT License")
        self.check_update_btn.setText(i18n.t("btn_check_update"))

    def save_config(self, cfg: dict) -> None:
        pass

    def _check_for_updates(self) -> None:
        url = "https://api.github.com/repos/zuluion/voice-input/releases/latest"
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                tag_name = data.get("tag_name", "").lstrip("v")
                html_url = data.get("html_url", "https://github.com/zuluion/voice-input/releases")

                if tag_name and tag_name != self.version_str:
                    msg = f"New version available!\nLatest: v{tag_name}\nCurrent: v{self.version_str}\n\nWould you like to open the release page?"
                    reply = QMessageBox.question(self, "Update Available", msg, QMessageBox.Yes | QMessageBox.No)
                    if reply == QMessageBox.Yes:
                        QDesktopServices.openUrl(QUrl(html_url))
                else:
                    QMessageBox.information(self, "Up to Date", f"You are running the latest version (v{self.version_str})!")
            else:
                QMessageBox.warning(self, "Check Failed", f"HTTP Status: {resp.status_code}")
        except Exception as e:
            QMessageBox.warning(self, "Check Failed", f"Network Exception:\n{str(e)}")
