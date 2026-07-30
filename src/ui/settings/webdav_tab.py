from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QCheckBox,
    QMessageBox, QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
)
from src.utils.webdav import WebDAVSync

class WebDAVHistoryDialog(QDialog):
    def __init__(self, backups: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("📋 Select WebDAV Backup to Restore")
        self.setMinimumSize(480, 320)
        self.selected_filename = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Remote WebDAV Backups Found:"))

        self.list_widget = QListWidget()
        for item in backups:
            fname = item["filename"]
            mod = item.get("modified", "")
            display_str = f"📄 {fname}  ({mod})" if mod else f"📄 {fname}"
            list_item = QListWidgetItem(display_str)
            list_item.setData(Qt.UserRole, fname)
            self.list_widget.addItem(list_item)

        layout.addWidget(self.list_widget)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        curr = self.list_widget.currentItem()
        if curr:
            self.selected_filename = curr.data(Qt.UserRole)
            self.accept()
        else:
            QMessageBox.warning(self, "No Selection", "Please select a backup file to restore.")

class WebDAVSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_webdav_cb = QCheckBox("Enable WebDAV Configuration Sync")
        layout.addRow("", self.enable_webdav_cb)

        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://dav.jianguoyun.com/dav/")
        layout.addRow("WebDAV Server URL:", self.server_url_input)

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("your_account@example.com")
        layout.addRow("Username / Account:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("App Password / Secret")
        layout.addRow("Password / Secret:", self.password_input)

        self.remote_path_input = QLineEdit()
        self.remote_path_input.setPlaceholderText("/VoiceInput/config.json")
        layout.addRow("Remote Path:", self.remote_path_input)

        self.auto_sync_cb = QCheckBox("Auto-sync from WebDAV on application startup")
        layout.addRow("", self.auto_sync_cb)

        # Action Buttons
        btn_layout1 = QHBoxLayout()
        self.upload_btn = QPushButton("📤 Upload Current Config")
        self.upload_btn.clicked.connect(self._upload_config)
        btn_layout1.addWidget(self.upload_btn)

        self.download_btn = QPushButton("📥 Download Latest Config")
        self.download_btn.clicked.connect(self._download_config)
        btn_layout1.addWidget(self.download_btn)

        layout.addRow("", btn_layout1)

        btn_layout2 = QHBoxLayout()
        self.list_history_btn = QPushButton("📋 View Remote Backups & Restore")
        self.list_history_btn.clicked.connect(self._list_history)
        btn_layout2.addWidget(self.list_history_btn)

        layout.addRow("", btn_layout2)

    def load_config(self) -> None:
        cfg = self.config_manager.config.get("webdav", {})
        self.enable_webdav_cb.setChecked(cfg.get("enabled", False))
        self.server_url_input.setText(cfg.get("server_url", "https://dav.jianguoyun.com/dav/"))
        self.username_input.setText(cfg.get("username", ""))
        self.password_input.setText(cfg.get("password", ""))
        self.remote_path_input.setText(cfg.get("remote_path", "/VoiceInput/config.json"))
        self.auto_sync_cb.setChecked(cfg.get("auto_sync_on_startup", False))

    def save_config(self, cfg: dict) -> None:
        if "webdav" not in cfg:
            cfg["webdav"] = {}

        cfg["webdav"]["enabled"] = self.enable_webdav_cb.isChecked()
        cfg["webdav"]["server_url"] = self.server_url_input.text().strip()
        cfg["webdav"]["username"] = self.username_input.text().strip()
        cfg["webdav"]["password"] = self.password_input.text().strip()
        cfg["webdav"]["remote_path"] = self.remote_path_input.text().strip() or "/VoiceInput/config.json"
        cfg["webdav"]["auto_sync_on_startup"] = self.auto_sync_cb.isChecked()

    def _get_webdav_instance(self) -> WebDAVSync:
        temp_cfg = {
            "enabled": self.enable_webdav_cb.isChecked(),
            "server_url": self.server_url_input.text().strip(),
            "username": self.username_input.text().strip(),
            "password": self.password_input.text().strip(),
            "remote_path": self.remote_path_input.text().strip() or "/VoiceInput/config.json"
        }
        return WebDAVSync(temp_cfg)

    def _upload_config(self) -> None:
        sync = self._get_webdav_instance()
        ok, msg = sync.upload_config(self.config_manager.config_path, save_history=True)
        if ok:
            QMessageBox.information(self, "Upload Success", msg)
        else:
            QMessageBox.warning(self, "Upload Failed", msg)

    def _download_config(self) -> None:
        sync = self._get_webdav_instance()
        ok, msg = sync.download_config(self.config_manager.config_path)
        if ok:
            self.config_manager.config = self.config_manager.load_config()
            QMessageBox.information(self, "Download Success", f"{msg}\nPlease reopen Settings to see updated values.")
        else:
            QMessageBox.warning(self, "Download Failed", msg)

    def _list_history(self) -> None:
        sync = self._get_webdav_instance()
        ok, backups, msg = sync.list_backups()
        if not ok:
            QMessageBox.warning(self, "Failed to List Backups", msg)
            return

        if not backups:
            QMessageBox.information(self, "No Backups Found", "No remote backup files found on WebDAV server.")
            return

        dlg = WebDAVHistoryDialog(backups, self)
        if dlg.exec() == QDialog.Accepted and dlg.selected_filename:
            selected_file = dlg.selected_filename
            res_ok, res_msg = sync.download_config(self.config_manager.config_path, remote_filename=selected_file)
            if res_ok:
                self.config_manager.config = self.config_manager.load_config()
                QMessageBox.information(self, "Restored Success", f"Successfully restored '{selected_file}'!\nPlease reopen Settings to see updated values.")
            else:
                QMessageBox.warning(self, "Restore Failed", res_msg)
