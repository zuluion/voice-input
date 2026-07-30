import os
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QPushButton, QCheckBox, QMessageBox
)
from src.i18n import i18n
from src.utils.logger import logger

class DebugSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_debug_cb = QCheckBox(i18n.t("debug_enable"))
        layout.addRow("", self.enable_debug_cb)

        self.desc_label = QLabel(i18n.t("debug_desc"))
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #9ca3af; font-size: 12px; margin-top: 6px; margin-bottom: 12px;")
        layout.addRow(self.desc_label)

        self.open_logs_btn = QPushButton(i18n.t("btn_open_logs_dir"))
        self.open_logs_btn.clicked.connect(self._open_logs_dir)
        layout.addRow("", self.open_logs_btn)

    def load_config(self) -> None:
        # Refresh static i18n labels
        self.enable_debug_cb.setText(i18n.t("debug_enable"))
        self.desc_label.setText(i18n.t("debug_desc"))
        self.open_logs_btn.setText(i18n.t("btn_open_logs_dir"))

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
