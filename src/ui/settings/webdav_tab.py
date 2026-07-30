from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QSpinBox, QPushButton, QCheckBox,
    QMessageBox, QDialog, QVBoxLayout, QListWidget, QListWidgetItem, QDialogButtonBox
)
from src.i18n import i18n
from src.utils.webdav import WebDAVSync

WEBDAV_PROVIDER_DEFAULTS = {
    "jianguoyun": {
        "server_url": "https://dav.jianguoyun.com/dav/",
        "remote_dir": "/VoiceInput",
        "max_backups": 5
    },
    "custom": {
        "server_url": "https://dav.jianguoyun.com/dav/",
        "remote_dir": "/VoiceInput",
        "max_backups": 5
    }
}

class WebDAVHistoryDialog(QDialog):
    def __init__(self, backups: list[dict], parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(i18n.t("webdav_history_title"))
        self.setMinimumSize(480, 320)
        self.selected_filename = None

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(i18n.t("webdav_history_label")))

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
        self._updating_ui = False
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_webdav_cb = QCheckBox(i18n.t("webdav_enable"))
        layout.addRow("", self.enable_webdav_cb)

        self.lbl_provider = QLabel(i18n.t("webdav_provider"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["jianguoyun", "custom"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addRow(self.lbl_provider, self.provider_combo)

        self.lbl_server_url = QLabel(i18n.t("webdav_server_url"))
        self.server_url_input = QLineEdit()
        self.server_url_input.setPlaceholderText("https://dav.jianguoyun.com/dav/")
        layout.addRow(self.lbl_server_url, self.server_url_input)

        self.lbl_username = QLabel(i18n.t("webdav_username"))
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("your_account@example.com")
        layout.addRow(self.lbl_username, self.username_input)

        self.lbl_password = QLabel(i18n.t("webdav_password"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("App Password / Secret")
        layout.addRow(self.lbl_password, self.password_input)

        self.lbl_remote_dir = QLabel(i18n.t("webdav_remote_dir"))
        self.remote_dir_input = QLineEdit()
        self.remote_dir_input.setPlaceholderText("/VoiceInput")
        layout.addRow(self.lbl_remote_dir, self.remote_dir_input)

        self.lbl_max_backups = QLabel(i18n.t("webdav_max_backups"))
        self.max_backups_spin = QSpinBox()
        self.max_backups_spin.setRange(1, 50)
        self.max_backups_spin.setValue(5)
        layout.addRow(self.lbl_max_backups, self.max_backups_spin)

        self.auto_sync_cb = QCheckBox(i18n.t("webdav_auto_sync"))
        layout.addRow("", self.auto_sync_cb)

        # Action Buttons
        btn_layout1 = QHBoxLayout()
        self.upload_btn = QPushButton(i18n.t("btn_upload_webdav"))
        self.upload_btn.clicked.connect(self._upload_config)
        btn_layout1.addWidget(self.upload_btn)

        self.download_btn = QPushButton(i18n.t("btn_download_webdav"))
        self.download_btn.clicked.connect(self._download_config)
        btn_layout1.addWidget(self.download_btn)

        layout.addRow("", btn_layout1)

        btn_layout2 = QHBoxLayout()
        self.list_history_btn = QPushButton(i18n.t("btn_history_webdav"))
        self.list_history_btn.clicked.connect(self._list_history)
        btn_layout2.addWidget(self.list_history_btn)

        layout.addRow("", btn_layout2)

    def _on_provider_changed(self, provider: str) -> None:
        if self._updating_ui:
            return

        defaults = WEBDAV_PROVIDER_DEFAULTS.get(provider, WEBDAV_PROVIDER_DEFAULTS["jianguoyun"])
        saved_provider_cfg = self.config_manager.get("webdav", provider, default={})

        saved_url = saved_provider_cfg.get("server_url", "")
        saved_user = saved_provider_cfg.get("username", "")
        saved_pwd = saved_provider_cfg.get("password", "")
        saved_dir = saved_provider_cfg.get("remote_dir", "")
        saved_max = saved_provider_cfg.get("max_backups", 5)

        self.server_url_input.setText(saved_url if saved_url else defaults["server_url"])
        self.username_input.setText(saved_user)
        self.password_input.setText(saved_pwd)
        self.remote_dir_input.setText(saved_dir if saved_dir else defaults["remote_dir"])
        self.max_backups_spin.setValue(int(saved_max))

    def load_config(self) -> None:
        self._updating_ui = True

        # Refresh static i18n labels
        self.enable_webdav_cb.setText(i18n.t("webdav_enable"))
        self.lbl_provider.setText(i18n.t("webdav_provider"))
        self.lbl_server_url.setText(i18n.t("webdav_server_url"))
        self.lbl_username.setText(i18n.t("webdav_username"))
        self.lbl_password.setText(i18n.t("webdav_password"))
        self.lbl_remote_dir.setText(i18n.t("webdav_remote_dir"))
        self.lbl_max_backups.setText(i18n.t("webdav_max_backups"))
        self.auto_sync_cb.setText(i18n.t("webdav_auto_sync"))

        self.upload_btn.setText(i18n.t("btn_upload_webdav"))
        self.download_btn.setText(i18n.t("btn_download_webdav"))
        self.list_history_btn.setText(i18n.t("btn_history_webdav"))

        cfg = self.config_manager.config.get("webdav", {})
        self.enable_webdav_cb.setChecked(cfg.get("enabled", False))

        provider = cfg.get("provider", "jianguoyun")
        idx = self.provider_combo.findText(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        self.auto_sync_cb.setChecked(cfg.get("auto_sync_on_startup", False))

        self._updating_ui = False
        self._on_provider_changed(provider)

    def save_config(self, cfg: dict) -> None:
        if "webdav" not in cfg:
            cfg["webdav"] = {}

        cfg["webdav"]["enabled"] = self.enable_webdav_cb.isChecked()
        provider = self.provider_combo.currentText()
        cfg["webdav"]["provider"] = provider

        if provider not in cfg["webdav"]:
            cfg["webdav"][provider] = {}

        cfg["webdav"][provider]["server_url"] = self.server_url_input.text().strip() or "https://dav.jianguoyun.com/dav/"
        cfg["webdav"][provider]["username"] = self.username_input.text().strip()
        cfg["webdav"][provider]["password"] = self.password_input.text().strip()
        cfg["webdav"][provider]["remote_dir"] = self.remote_dir_input.text().strip() or "/VoiceInput"
        cfg["webdav"][provider]["max_backups"] = self.max_backups_spin.value()
        cfg["webdav"]["auto_sync_on_startup"] = self.auto_sync_cb.isChecked()

    def _get_webdav_instance(self) -> WebDAVSync:
        provider = self.provider_combo.currentText()
        temp_cfg = {
            "enabled": self.enable_webdav_cb.isChecked(),
            "provider": provider,
            provider: {
                "server_url": self.server_url_input.text().strip(),
                "username": self.username_input.text().strip(),
                "password": self.password_input.text().strip(),
                "remote_dir": self.remote_dir_input.text().strip() or "/VoiceInput",
                "max_backups": self.max_backups_spin.value()
            }
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
