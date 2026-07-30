import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox
)
from src.i18n import i18n
from src.asr import create_asr_provider

PROVIDER_DEFAULTS = {
    "xiaomi_mimo": {
        "label_key_i18n": "asr_mimo_api_key",
        "base_url": "https://api.xiaomimimo.com/v1",
        "model": "mimo-v2.5-asr",
        "has_extra": False
    },
    "openai": {
        "label_key_i18n": "asr_openai_api_key",
        "base_url": "https://api.openai.com/v1",
        "model": "whisper-1",
        "has_extra": False
    },
    "doubao": {
        "label_key_i18n": "asr_doubao_token",
        "base_url": "https://openspeech.bytedance.com/api/v1/vc/asr",
        "model": "volcengine_input_common",
        "has_extra": True,
        "label_extra_i18n": "asr_doubao_app_id"
    },
    "qwen": {
        "label_key_i18n": "asr_qwen_api_key",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-audio-asr",
        "has_extra": False
    }
}

class ASRSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self._updating_ui = False
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.lbl_provider = QLabel(i18n.t("asr_provider"))
        self.asr_provider_combo = QComboBox()
        self.asr_provider_combo.addItems(["xiaomi_mimo", "openai", "doubao", "qwen"])
        self.asr_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addRow(self.lbl_provider, self.asr_provider_combo)

        # Dynamic Key Label & Input
        self.asr_key_label = QLabel(i18n.t("lbl_api_key"))
        self.asr_key_input = QLineEdit()
        self.asr_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow(self.asr_key_label, self.asr_key_input)

        # Extra Input (e.g. Doubao App ID)
        self.asr_extra_label = QLabel(i18n.t("asr_doubao_app_id"))
        self.asr_extra_input = QLineEdit()
        layout.addRow(self.asr_extra_label, self.asr_extra_input)

        # Base URL
        self.lbl_base_url = QLabel(i18n.t("lbl_base_url"))
        self.asr_url_input = QLineEdit()
        layout.addRow(self.lbl_base_url, self.asr_url_input)

        # Model Name + Fetch Button
        self.lbl_model_name = QLabel(i18n.t("lbl_model_name"))
        model_layout = QHBoxLayout()
        self.asr_model_combo = QComboBox()
        self.asr_model_combo.setEditable(True)
        model_layout.addWidget(self.asr_model_combo)

        self.fetch_asr_btn = QPushButton(i18n.t("btn_fetch_models"))
        self.fetch_asr_btn.clicked.connect(self._fetch_models)
        model_layout.addWidget(self.fetch_asr_btn)

        layout.addRow(self.lbl_model_name, model_layout)

        # Test Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_asr_btn = QPushButton(i18n.t("btn_test_asr"))
        self.test_asr_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_asr_btn)
        layout.addRow("", test_layout)

    def _on_provider_changed(self, provider: str) -> None:
        if self._updating_ui:
            return

        defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["xiaomi_mimo"])
        self.asr_key_label.setText(i18n.t(defaults["label_key_i18n"]))

        if defaults["has_extra"]:
            self.asr_extra_label.setText(i18n.t(defaults.get("label_extra_i18n", "asr_doubao_app_id")))
            self.asr_extra_label.show()
            self.asr_extra_input.show()
        else:
            self.asr_extra_label.hide()
            self.asr_extra_input.hide()

        asr_cfg = self.config_manager.get("asr", provider, default={})
        saved_url = asr_cfg.get("base_url", "")
        saved_model = asr_cfg.get("model", "")
        saved_key = asr_cfg.get("api_key", "") or asr_cfg.get("access_token", "")
        saved_extra = asr_cfg.get("app_id", "")

        self.asr_url_input.setText(saved_url if saved_url else defaults["base_url"])
        self.asr_key_input.setText(saved_key)
        self.asr_extra_input.setText(saved_extra)

        model_val = saved_model if saved_model else defaults["model"]
        self.asr_model_combo.clear()
        self.asr_model_combo.setEditText(model_val)

    def load_config(self) -> None:
        self._updating_ui = True

        # Refresh static i18n labels
        self.lbl_provider.setText(i18n.t("asr_provider"))
        self.lbl_base_url.setText(i18n.t("lbl_base_url"))
        self.lbl_model_name.setText(i18n.t("lbl_model_name"))
        self.fetch_asr_btn.setText(i18n.t("btn_fetch_models"))
        self.test_asr_btn.setText(i18n.t("btn_test_asr"))

        cfg = self.config_manager.config.get("asr", {})
        provider = cfg.get("provider", "xiaomi_mimo")
        idx = self.asr_provider_combo.findText(provider)
        if idx >= 0:
            self.asr_provider_combo.setCurrentIndex(idx)

        self._updating_ui = False
        self._on_provider_changed(provider)

    def save_config(self, cfg: dict) -> None:
        provider = self.asr_provider_combo.currentText()
        if "asr" not in cfg:
            cfg["asr"] = {}
        cfg["asr"]["provider"] = provider
        if provider not in cfg["asr"]:
            cfg["asr"][provider] = {}

        cfg["asr"][provider]["base_url"] = self.asr_url_input.text().strip()
        cfg["asr"][provider]["model"] = self.asr_model_combo.currentText().strip()

        if provider == "doubao":
            cfg["asr"][provider]["access_token"] = self.asr_key_input.text().strip()
            cfg["asr"][provider]["app_id"] = self.asr_extra_input.text().strip()
        else:
            cfg["asr"][provider]["api_key"] = self.asr_key_input.text().strip()

    def _fetch_models(self) -> None:
        url = self.asr_url_input.text().strip()
        key = self.asr_key_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Fetch Failed", "Please enter a Base URL.")
            return

        clean_url = url.rstrip("/")
        models_url = f"{clean_url}/models"
        headers = {}
        if key:
            headers["Authorization"] = f"Bearer {key}"

        try:
            resp = requests.get(models_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                data = resp.json().get("data", [])
                model_ids = [item["id"] if isinstance(item, dict) and "id" in item else str(item) for item in data]
                if model_ids:
                    asr_keywords = ["asr", "whisper", "audio", "mimo", "speech"]
                    asr_models = [m for m in model_ids if any(kw in m.lower() for kw in asr_keywords)]
                    other_models = [m for m in model_ids if m not in asr_models]
                    model_ids = asr_models + other_models

                    curr_text = self.asr_model_combo.currentText()
                    self.asr_model_combo.clear()
                    self.asr_model_combo.addItems(model_ids)

                    if curr_text and curr_text in model_ids:
                        self.asr_model_combo.setCurrentText(curr_text)
                    elif model_ids:
                        self.asr_model_combo.setCurrentIndex(0)

                    QMessageBox.information(self, "Success", f"Successfully fetched {len(model_ids)} available models!")
                else:
                    QMessageBox.warning(self, "Fetch Warning", "No models found in payload.")
            else:
                QMessageBox.warning(self, "Fetch Failed", f"HTTP Status: {resp.status_code}\n{resp.text}")
        except Exception as e:
            QMessageBox.warning(self, "Fetch Failed", f"Exception: {str(e)}")

    def _test_connection(self) -> None:
        provider = self.asr_provider_combo.currentText()
        url = self.asr_url_input.text().strip()
        model = self.asr_model_combo.currentText().strip()
        key = self.asr_key_input.text().strip()
        extra = self.asr_extra_input.text().strip()

        if not key:
            QMessageBox.warning(self, "Test Failed", f"Please enter the API Key.")
            return

        temp_cfg = {
            provider: {
                "api_key": key,
                "access_token": key,
                "app_id": extra,
                "base_url": url,
                "model": model
            }
        }

        try:
            asr_instance = create_asr_provider(provider, temp_cfg)
            asr_instance.connect()
            asr_instance.send_audio_chunk(b"\x00\x00" * 8000)
            res = asr_instance.finish()
            QMessageBox.information(self, "Connection Succeeded", f"ASR connection test succeeded!\nProvider: {provider}\nEndpoint: {url}\nModel: {model}")
        except Exception as e:
            QMessageBox.warning(self, "Connection Failed", f"ASR connection test failed:\n{str(e)}")
