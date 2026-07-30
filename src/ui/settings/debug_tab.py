import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QMessageBox
)
from src.utils.logger import logger

class DebugSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_debug_cb = QCheckBox("Enable Debug Logging Mode (Log to File)")
        layout.addRow("", self.enable_debug_cb)

        desc_label = QLabel(
            "<b>Note:</b> When Debug Mode is enabled, the app writes timestamped plaintext logs "
            "(including ASR recognized text & LLM refined output) to a local <code>logs/</code> directory.<br>"
            "Turn OFF Debug Mode during normal usage to protect user privacy."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #9ca3af; font-size: 12px; margin-top: 6px; margin-bottom: 12px;")
        layout.addRow(desc_label)

        open_logs_btn = QPushButton("📂 Open Logs Directory")
        open_logs_btn.clicked.connect(self._open_logs_dir)
        layout.addRow("", open_logs_btn)

    def load_config(self) -> None:
        cfg = self.config_manager.config.get("debug", {})
        self.enable_debug_cb.setChecked(cfg.get("enabled", False))

    def save_config(self, cfg: dict) -> None:
        if "debug" not in cfg:
            cfg["debug"] = {}

        enabled = self.enable_debug_cb.isChecked()
        cfg["debug"]["enabled"] = enabled

        # Re-configure logger
        logger.configure(cfg["debug"], self.config_manager.config_path)

    def _open_logs_dir(self) -> None:
        if logger.log_dir and os.path.exists(logger.log_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(logger.log_dir))
        else:
            base = os.path.dirname(os.path.abspath(self.config_manager.config_path))
            log_dir = os.path.join(base, "logs")
            if os.path.exists(log_dir):
                QDesktopServices.openUrl(QUrl.fromLocalFile(log_dir))
            else:
                QMessageBox.information(self, "No Logs", "Logs directory does not exist yet. Enable Debug Mode to generate logs.")
