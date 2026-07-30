from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QMessageBox
)
from src.i18n import i18n
from src.utils.proxy import apply_proxy_config, test_proxy_connection

class ProxySettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_proxy_cb = QCheckBox(i18n.t("proxy_enable"))
        layout.addRow("", self.enable_proxy_cb)

        self.lbl_protocol = QLabel(i18n.t("proxy_protocol"))
        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(["http", "socks4", "socks5"])
        layout.addRow(self.lbl_protocol, self.protocol_combo)

        self.lbl_host = QLabel(i18n.t("proxy_host"))
        self.host_input = QLineEdit()
        self.host_input.setPlaceholderText("127.0.0.1")
        layout.addRow(self.lbl_host, self.host_input)

        self.lbl_port = QLabel(i18n.t("proxy_port"))
        self.port_input = QLineEdit()
        self.port_input.setPlaceholderText("7890")
        layout.addRow(self.lbl_port, self.port_input)

        # Test Proxy Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_proxy_btn = QPushButton(i18n.t("btn_test_proxy"))
        self.test_proxy_btn.clicked.connect(self._test_proxy)
        test_layout.addWidget(self.test_proxy_btn)

        layout.addRow("", test_layout)

    def load_config(self) -> None:
        # Refresh static i18n labels
        self.enable_proxy_cb.setText(i18n.t("proxy_enable"))
        self.lbl_protocol.setText(i18n.t("proxy_protocol"))
        self.lbl_host.setText(i18n.t("proxy_host"))
        self.lbl_port.setText(i18n.t("proxy_port"))
        self.test_proxy_btn.setText(i18n.t("btn_test_proxy"))

        cfg = self.config_manager.config.get("proxy", {})
        self.enable_proxy_cb.setChecked(cfg.get("enabled", False))

        protocol = cfg.get("protocol", "http").lower()
        idx = self.protocol_combo.findText(protocol)
        if idx >= 0:
            self.protocol_combo.setCurrentIndex(idx)

        self.host_input.setText(cfg.get("host", ""))
        port_val = cfg.get("port", 7890)
        self.port_input.setText(str(port_val) if port_val else "7890")

    def save_config(self, cfg: dict) -> None:
        if "proxy" not in cfg:
            cfg["proxy"] = {}

        enabled = self.enable_proxy_cb.isChecked()
        protocol = self.protocol_combo.currentText()
        host = self.host_input.text().strip() or "127.0.0.1"

        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            port = 7890

        cfg["proxy"]["enabled"] = enabled
        cfg["proxy"]["protocol"] = protocol
        cfg["proxy"]["host"] = host
        cfg["proxy"]["port"] = port

        # Apply proxy to environment immediately
        apply_proxy_config(cfg["proxy"])

    def _test_proxy(self) -> None:
        protocol = self.protocol_combo.currentText()
        host = self.host_input.text().strip() or "127.0.0.1"
        try:
            port = int(self.port_input.text().strip())
        except ValueError:
            port = 7890

        temp_cfg = {
            "enabled": True,
            "protocol": protocol,
            "host": host,
            "port": port
        }

        ok, msg = test_proxy_connection(temp_cfg)
        if ok:
            QMessageBox.information(self, "Proxy Test Success", msg)
        else:
            QMessageBox.warning(self, "Proxy Test Failed", msg)
