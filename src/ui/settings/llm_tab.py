import requests
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QPlainTextEdit, QMessageBox
)
from src.refine.llm import LLMRefiner, DEFAULT_SYSTEM_PROMPT

LLM_PROVIDER_DEFAULTS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "model": "deepseek-chat"
    },
    "xiaomi": {
        "base_url": "https://api.xiaomimimo.com/v1",
        "model": "mimo-v2.5-asr"
    },
    "qwen": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-plus"
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "model": "qwen2.5:7b"
    },
    "custom": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    }
}

class LLMSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self._updating_ui = False
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_llm_cb = QCheckBox("Enable LLM Refinement & Polishing")
        layout.addRow("", self.enable_llm_cb)

        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["openai", "deepseek", "xiaomi", "qwen", "ollama", "custom"])
        self.llm_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addRow("LLM Provider:", self.llm_provider_combo)

        self.llm_key_input = QLineEdit()
        self.llm_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.llm_key_input)

        self.llm_url_input = QLineEdit()
        layout.addRow("Base URL:", self.llm_url_input)

        model_layout = QHBoxLayout()
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.setEditable(True)
        model_layout.addWidget(self.llm_model_combo)

        self.fetch_llm_btn = QPushButton("🔄 Fetch Models")
        self.fetch_llm_btn.clicked.connect(self._fetch_models)
        model_layout.addWidget(self.fetch_llm_btn)

        layout.addRow("Model Name:", model_layout)

        # System Prompt Section
        prompt_header_layout = QHBoxLayout()
        prompt_label = QLabel("System Prompt Rules:")
        self.reset_prompt_btn = QPushButton("↺ Reset Prompt")
        self.reset_prompt_btn.setFixedWidth(110)
        self.reset_prompt_btn.clicked.connect(self._reset_prompt)
        prompt_header_layout.addWidget(prompt_label)
        prompt_header_layout.addStretch()
        prompt_header_layout.addWidget(self.reset_prompt_btn)

        layout.addRow(prompt_header_layout)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setMinimumHeight(130)
        layout.addRow(self.prompt_edit)

        # Test Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_llm_btn = QPushButton("Test LLM Connection")
        self.test_llm_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_llm_btn)

        layout.addRow("", test_layout)

    def _on_provider_changed(self, provider: str) -> None:
        if self._updating_ui:
            return

        defaults = LLM_PROVIDER_DEFAULTS.get(provider, LLM_PROVIDER_DEFAULTS["openai"])
        saved_provider_cfg = self.config_manager.get("llm", provider, default={})

        saved_url = saved_provider_cfg.get("base_url", "")
        saved_model = saved_provider_cfg.get("model", "")
        saved_key = saved_provider_cfg.get("api_key", "")

        self.llm_url_input.setText(saved_url if saved_url else defaults["base_url"])
        self.llm_key_input.setText(saved_key)

        model_val = saved_model if saved_model else defaults["model"]
        self.llm_model_combo.clear()
        self.llm_model_combo.setEditText(model_val)

    def load_config(self) -> None:
        self._updating_ui = True
        cfg = self.config_manager.config.get("llm", {})
        self.enable_llm_cb.setChecked(cfg.get("enabled", True))

        provider = cfg.get("provider", "openai")
        idx = self.llm_provider_combo.findText(provider)
        if idx >= 0:
            self.llm_provider_combo.setCurrentIndex(idx)

        prompt = cfg.get("system_prompt", "")
        self.prompt_edit.setPlainText(prompt if prompt else DEFAULT_SYSTEM_PROMPT)

        self._updating_ui = False
        self._on_provider_changed(provider)

    def save_config(self, cfg: dict) -> None:
        if "llm" not in cfg:
            cfg["llm"] = {}

        cfg["llm"]["enabled"] = self.enable_llm_cb.isChecked()
        provider = self.llm_provider_combo.currentText()
        cfg["llm"]["provider"] = provider

        if provider not in cfg["llm"]:
            cfg["llm"][provider] = {}

        cfg["llm"][provider]["api_key"] = self.llm_key_input.text().strip()
        cfg["llm"][provider]["base_url"] = self.llm_url_input.text().strip()
        cfg["llm"][provider]["model"] = self.llm_model_combo.currentText().strip()
        cfg["llm"]["system_prompt"] = self.prompt_edit.toPlainText().strip()

    def _reset_prompt(self) -> None:
        self.prompt_edit.setPlainText(DEFAULT_SYSTEM_PROMPT)

    def _fetch_models(self) -> None:
        url = self.llm_url_input.text().strip()
        key = self.llm_key_input.text().strip()
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
                    curr_text = self.llm_model_combo.currentText()
                    self.llm_model_combo.clear()
                    self.llm_model_combo.addItems(model_ids)

                    if curr_text and curr_text in model_ids:
                        self.llm_model_combo.setCurrentText(curr_text)
                    elif model_ids:
                        self.llm_model_combo.setCurrentIndex(0)

                    QMessageBox.information(self, "Success", f"Successfully fetched {len(model_ids)} available LLM models!")
                else:
                    QMessageBox.warning(self, "Fetch Warning", "No models found in payload.")
            else:
                QMessageBox.warning(self, "Fetch Failed", f"HTTP Status: {resp.status_code}\n{resp.text}")
        except Exception as e:
            QMessageBox.warning(self, "Fetch Failed", f"Exception: {str(e)}")

    def _test_connection(self) -> None:
        url = self.llm_url_input.text().strip()
        model = self.llm_model_combo.currentText().strip()
        key = self.llm_key_input.text().strip()
        prompt = self.prompt_edit.toPlainText().strip()
        provider = self.llm_provider_combo.currentText()

        if not key and "localhost" not in url and "127.0.0.1" not in url:
            QMessageBox.warning(self, "Test Failed", f"Please enter the LLM API Key.")
            return

        temp_cfg = {
            "enabled": True,
            "provider": provider,
            "system_prompt": prompt,
            provider: {
                "api_key": key,
                "base_url": url,
                "model": model
            }
        }

        refiner = LLMRefiner(temp_cfg)
        test_text = "买一杯美式，呃不对，改成拿铁"
        res = refiner.refine(test_text)
        QMessageBox.information(
            self,
            "Test Success",
            f"LLM Connection & Refinement Succeeded!\nProvider: {provider}\nModel: {model}\n\nInput: '{test_text}'\nRefined Output: '{res}'"
        )
