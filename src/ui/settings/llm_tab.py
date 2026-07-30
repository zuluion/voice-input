import threading
import requests
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton,
    QCheckBox, QPlainTextEdit, QMessageBox, QProgressDialog
)
from src.i18n import i18n
from src.refine.llm import LLMRefiner, DEFAULT_SYSTEM_PROMPT
from src.utils.model_downloader import PRESET_MODELS, is_model_downloaded, download_model, delete_model, get_model_file_path

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
    "local": {
        "base_url": "local",
        "model": "qwen2.5-0.5b-instruct"
    },
    "custom": {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini"
    }
}

class ModelDownloadThread(QThread):
    progress_signal = Signal(int, int, int)
    finished_signal = Signal(bool, str)

    def __init__(self, model_id: str):
        super().__init__()
        self.model_id = model_id
        self._is_cancelled = False

    def run(self):
        def cb(downloaded, total, percent):
            self.progress_signal.emit(downloaded, total, percent)

        def cancel_check():
            return self._is_cancelled

        ok, msg = download_model(self.model_id, progress_callback=cb, cancel_checker=cancel_check)
        self.finished_signal.emit(ok, msg)

    def cancel(self):
        self._is_cancelled = True

class LLMSettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self._updating_ui = False
        self.download_thread = None
        self.progress_dialog = None
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.enable_llm_cb = QCheckBox(i18n.t("llm_enable"))
        layout.addRow("", self.enable_llm_cb)

        self.lbl_provider = QLabel(i18n.t("llm_provider"))
        self.llm_provider_combo = QComboBox()
        self.llm_provider_combo.addItems(["openai", "deepseek", "xiaomi", "qwen", "ollama", "local", "custom"])
        self.llm_provider_combo.currentTextChanged.connect(self._on_provider_changed)
        layout.addRow(self.lbl_provider, self.llm_provider_combo)

        # Standard Remote API Controls
        self.lbl_api_key = QLabel(i18n.t("lbl_api_key"))
        self.llm_key_input = QLineEdit()
        self.llm_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow(self.lbl_api_key, self.llm_key_input)

        self.lbl_base_url = QLabel(i18n.t("lbl_base_url"))
        self.llm_url_input = QLineEdit()
        layout.addRow(self.lbl_base_url, self.llm_url_input)

        self.lbl_model_name = QLabel(i18n.t("lbl_model_name"))
        model_layout = QHBoxLayout()
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.setEditable(True)
        self.llm_model_combo.currentTextChanged.connect(self._on_model_selection_changed)
        model_layout.addWidget(self.llm_model_combo)

        self.fetch_llm_btn = QPushButton(i18n.t("btn_fetch_models"))
        self.fetch_llm_btn.clicked.connect(self._fetch_models)
        model_layout.addWidget(self.fetch_llm_btn)

        layout.addRow(self.lbl_model_name, model_layout)

        # Local Model Specific Controls
        self.lbl_local_status_title = QLabel(i18n.t("lbl_local_model_status"))
        self.lbl_local_status_val = QLabel()
        self.lbl_local_status_val.setStyleSheet("font-weight: bold;")
        layout.addRow(self.lbl_local_status_title, self.lbl_local_status_val)

        local_btn_layout = QHBoxLayout()
        self.download_model_btn = QPushButton(i18n.t("btn_download_local_model"))
        self.download_model_btn.clicked.connect(self._download_local_model)
        local_btn_layout.addWidget(self.download_model_btn)

        self.delete_model_btn = QPushButton(i18n.t("btn_delete_local_model"))
        self.delete_model_btn.setStyleSheet("color: #ef4444;")
        self.delete_model_btn.clicked.connect(self._delete_local_model)
        local_btn_layout.addWidget(self.delete_model_btn)
        local_btn_layout.addStretch()

        layout.addRow("", local_btn_layout)

        # System Prompt Section
        prompt_header_layout = QHBoxLayout()
        self.prompt_label = QLabel(i18n.t("llm_system_prompt"))
        self.reset_prompt_btn = QPushButton(i18n.t("btn_reset_prompt"))
        self.reset_prompt_btn.setFixedWidth(120)
        self.reset_prompt_btn.clicked.connect(self._reset_prompt)
        prompt_header_layout.addWidget(self.prompt_label)
        prompt_header_layout.addStretch()
        prompt_header_layout.addWidget(self.reset_prompt_btn)

        layout.addRow(prompt_header_layout)

        self.prompt_edit = QPlainTextEdit()
        self.prompt_edit.setMinimumHeight(120)
        layout.addRow(self.prompt_edit)

        # Test Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_llm_btn = QPushButton(i18n.t("btn_test_llm"))
        self.test_llm_btn.clicked.connect(self._test_connection)
        test_layout.addWidget(self.test_llm_btn)

        layout.addRow("", test_layout)

    def _on_provider_changed(self, provider: str) -> None:
        if self._updating_ui:
            return

        is_local = (provider == "local")
        self.lbl_api_key.setVisible(not is_local)
        self.llm_key_input.setVisible(not is_local)
        self.lbl_base_url.setVisible(not is_local)
        self.llm_url_input.setVisible(not is_local)
        self.fetch_llm_btn.setVisible(not is_local)

        self.lbl_local_status_title.setVisible(is_local)
        self.lbl_local_status_val.setVisible(is_local)
        self.download_model_btn.setVisible(is_local)
        self.delete_model_btn.setVisible(is_local)

        defaults = LLM_PROVIDER_DEFAULTS.get(provider, LLM_PROVIDER_DEFAULTS["openai"])
        saved_provider_cfg = self.config_manager.get("llm", provider, default={})

        saved_url = saved_provider_cfg.get("base_url", "")
        saved_model = saved_provider_cfg.get("model", "")
        saved_key = saved_provider_cfg.get("api_key", "")

        self.llm_url_input.setText(saved_url if saved_url else defaults["base_url"])
        self.llm_key_input.setText(saved_key)

        model_val = saved_model if saved_model else defaults["model"]
        self.llm_model_combo.clear()

        if is_local:
            self.llm_model_combo.setEditable(False)
            self.llm_model_combo.addItems(list(PRESET_MODELS.keys()))
            idx = self.llm_model_combo.findText(model_val)
            if idx >= 0:
                self.llm_model_combo.setCurrentIndex(idx)
            else:
                self.llm_model_combo.setCurrentIndex(0)
            self._update_local_model_status()
        else:
            self.llm_model_combo.setEditable(True)
            self.llm_model_combo.setEditText(model_val)

    def _on_model_selection_changed(self, model_id: str) -> None:
        if self.llm_provider_combo.currentText() == "local":
            self._update_local_model_status()

    def _update_local_model_status(self) -> None:
        model_id = self.llm_model_combo.currentText().strip()
        if not model_id:
            return

        downloaded = is_model_downloaded(model_id)
        if downloaded:
            fpath = get_model_file_path(model_id)
            self.lbl_local_status_val.setText(i18n.t("local_model_ready"))
            self.lbl_local_status_val.setStyleSheet("color: #10b981; font-weight: bold;")
            self.download_model_btn.setEnabled(False)
            self.delete_model_btn.setEnabled(True)
        else:
            info = PRESET_MODELS.get(model_id, {})
            sz = info.get("size_str", "Unknown")
            self.lbl_local_status_val.setText(f"{i18n.t('local_model_missing')} ({sz})")
            self.lbl_local_status_val.setStyleSheet("color: #f59e0b; font-weight: bold;")
            self.download_model_btn.setEnabled(True)
            self.delete_model_btn.setEnabled(False)

    def _download_local_model(self) -> None:
        model_id = self.llm_model_combo.currentText().strip()
        info = PRESET_MODELS.get(model_id)
        if not info:
            QMessageBox.warning(self, "Error", f"Unknown model ID: {model_id}")
            return

        msg = i18n.t("confirm_download_model_msg").format(
            model_id=model_id,
            size_str=info["size_str"]
        )
        reply = QMessageBox.question(
            self,
            i18n.t("confirm_download_model_title"),
            msg,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        # Start Async Download with Progress Dialog
        self.progress_dialog = QProgressDialog(f"Downloading {model_id}...", "Cancel", 0, 100, self)
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setAutoClose(True)

        self.download_thread = ModelDownloadThread(model_id)
        self.download_thread.progress_signal.connect(self._on_download_progress)
        self.download_thread.finished_signal.connect(self._on_download_finished)
        self.progress_dialog.canceled.connect(self.download_thread.cancel)

        self.download_thread.start()
        self.progress_dialog.show()

    def _on_download_progress(self, downloaded: int, total: int, percent: int) -> None:
        if self.progress_dialog:
            mb_dl = downloaded / (1024 * 1024)
            mb_tot = total / (1024 * 1024)
            self.progress_dialog.setLabelText(f"Downloading {self.download_thread.model_id}: {mb_dl:.1f} MB / {mb_tot:.1f} MB ({percent}%)")
            self.progress_dialog.setValue(percent)

    def _on_download_finished(self, ok: bool, msg: str) -> None:
        if self.progress_dialog:
            self.progress_dialog.close()
        self._update_local_model_status()

        if ok:
            QMessageBox.information(self, "Download Complete", f"Local model '{self.download_thread.model_id}' downloaded successfully!")
        else:
            QMessageBox.warning(self, "Download Failed", f"Model download failed or cancelled:\n{msg}")

    def _delete_local_model(self) -> None:
        model_id = self.llm_model_combo.currentText().strip()
        msg = i18n.t("confirm_delete_model_msg").format(model_id=model_id)
        reply = QMessageBox.question(
            self,
            i18n.t("confirm_delete_model_title"),
            msg,
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            ok, err_msg = delete_model(model_id)
            self._update_local_model_status()
            if ok:
                QMessageBox.information(self, "Deleted", f"Local model [{model_id}] has been deleted.")
            else:
                QMessageBox.warning(self, "Delete Failed", err_msg)

    def load_config(self) -> None:
        self._updating_ui = True

        self.enable_llm_cb.setText(i18n.t("llm_enable"))
        self.lbl_provider.setText(i18n.t("llm_provider"))
        self.lbl_api_key.setText(i18n.t("lbl_api_key"))
        self.lbl_base_url.setText(i18n.t("lbl_base_url"))
        self.lbl_model_name.setText(i18n.t("lbl_model_name"))
        self.fetch_llm_btn.setText(i18n.t("btn_fetch_models"))
        self.lbl_local_status_title.setText(i18n.t("lbl_local_model_status"))
        self.download_model_btn.setText(i18n.t("btn_download_local_model"))
        self.delete_model_btn.setText(i18n.t("btn_delete_local_model"))
        self.prompt_label.setText(i18n.t("llm_system_prompt"))
        self.reset_prompt_btn.setText(i18n.t("btn_reset_prompt"))
        self.test_llm_btn.setText(i18n.t("btn_test_llm"))

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

        if provider == "local":
            if not is_model_downloaded(model):
                QMessageBox.warning(self, "Local Model Missing", f"Local model '{model}' is not downloaded yet. Please download it first.")
                return
        elif not key and "localhost" not in url and "127.0.0.1" not in url:
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

