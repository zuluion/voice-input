import os
import requests
from PySide6.QtCore import Qt
from PySide6.QtGui import QDesktopServices, QUrl, QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QMessageBox
)

def get_current_version() -> str:
    version_file = "VERSION"
    if os.path.exists(version_file):
        try:
            with open(version_file, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            pass
    return "2026.07.30.001"

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
        title_label = QLabel("🎙️ Voice Input (语音输入法)")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #6366f1;")
        layout.addWidget(title_label)

        sub_label = QLabel("Windows 系统托盘语音输入法应用 · PySide6 & 多 Provider ASR/LLM 精修")
        sub_label.setStyleSheet("color: #9ca3af; font-size: 12px;")
        layout.addWidget(sub_label)

        layout.addSpacing(10)

        # Info Cards
        info_layout = QVBoxLayout()
        info_layout.setSpacing(8)

        author_label = QLabel(f"<b>Author / 开发者:</b> Zuluion")
        author_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(author_label)

        ver_label = QLabel(f"<b>Current Version / 当前版本:</b> v{self.version_str}")
        ver_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(ver_label)

        repo_label = QLabel("<b>GitHub Repository / 官方仓库:</b> <a href='https://github.com/zuluion/voice-input' style='color:#818cf8;'>https://github.com/zuluion/voice-input</a>")
        repo_label.setOpenExternalLinks(True)
        repo_label.setStyleSheet("font-size: 13px;")
        info_layout.addWidget(repo_label)

        license_label = QLabel("<b>License / 开源协议:</b> MIT License")
        license_label.setStyleSheet("color: #e5e7eb; font-size: 13px;")
        info_layout.addWidget(license_label)

        layout.addLayout(info_layout)
        layout.addSpacing(15)

        # Check for Updates Button
        btn_layout = QHBoxLayout()
        self.check_update_btn = QPushButton("🚀 Check for Updates")
        self.check_update_btn.setFixedHeight(36)
        self.check_update_btn.clicked.connect(self._check_for_updates)
        btn_layout.addWidget(self.check_update_btn)
        btn_layout.addStretch()

        layout.addLayout(btn_layout)
        layout.addStretch()

    def load_config(self) -> None:
        pass

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
                body = data.get("body", "")

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
