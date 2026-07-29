import requests
from PySide6.QtCore import Qt, Signal, QMetaObject, Slot
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QLineEdit, QComboBox, QCheckBox, QPushButton, QMessageBox,
    QFrame, QPlainTextEdit
)
from pynput import keyboard

from src.config import ConfigManager
from src.asr import create_asr_provider
from src.refine.llm import LLMRefiner, DEFAULT_SYSTEM_PROMPT

PROVIDER_DEFAULTS = {
    "xiaomi_mimo": {
        "label_key": "MiMo API Key:",
        "base_url": "https://api.xiaomimimo.com/v1",
        "model": "mimo-v2.5-asr",
        "has_extra": False
    },
    "openai": {
        "label_key": "OpenAI API Key:",
        "base_url": "https://api.openai.com/v1",
        "model": "whisper-1",
        "has_extra": False
    },
    "doubao": {
        "label_key": "Access Token:",
        "base_url": "https://openspeech.bytedance.com/api/v1/vc/asr",
        "model": "volcengine_input_common",
        "has_extra": True,
        "label_extra": "App ID:"
    },
    "qwen": {
        "label_key": "DashScope API Key:",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "model": "qwen-audio-asr",
        "has_extra": False
    }
}

KEY_DISPLAY_MAP = {
    "key.alt_r": "Right Alt",
    "key.alt_gr": "Right Alt",
    "key.alt_l": "Left Alt",
    "key.alt": "Alt",
    "key.space": "Space",
    "key.ctrl_r": "Right Ctrl",
    "key.ctrl_l": "Left Ctrl",
    "key.shift": "Shift",
    "key.caps_lock": "Caps Lock",
    "key.tab": "Tab",
}

def get_friendly_key_name(key_str: str) -> str:
    lower_str = key_str.lower().strip()
    if lower_str in KEY_DISPLAY_MAP:
        return KEY_DISPLAY_MAP[lower_str]
    if lower_str.startswith("key.f") and len(lower_str) <= 6:
        return lower_str.replace("key.", "").upper()
    if lower_str.startswith("key."):
        return lower_str.replace("key.", "").title()
    return key_str.upper()

class HotkeyRecorderWidget(QFrame):
    hotkey_changed = Signal(str)

    def __init__(self, initial_key: str = "Key.alt_r") -> None:
        super().__init__()
        self.current_key_str = initial_key
        self.is_recording = False
        self._rec_listener = None

        self.setStyleSheet("""
            HotkeyRecorderWidget {
                background-color: #1e222d;
                border: 1px solid #2d3243;
                border-radius: 10px;
                padding: 14px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header Title
        title_label = QLabel("Trigger Hotkey")
        title_label.setFont(QFont("Segoe UI", 11, QFont.Bold))
        title_label.setStyleSheet("color: #f3f4f6;")
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel("Hold this hotkey to record voice, release to inject text.")
        desc_label.setStyleSheet("color: #9ca3af; font-size: 11px;")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)

        # Key Display & Record Controls
        controls_layout = QHBoxLayout()

        self.badge_label = QLabel(get_friendly_key_name(initial_key))
        self.badge_label.setAlignment(Qt.AlignCenter)
        self.badge_label.setStyleSheet("""
            QLabel {
                background-color: #2b3040;
                color: #6366f1;
                border: 1.5px solid #4f46e5;
                border-radius: 6px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }
        """)
        controls_layout.addWidget(self.badge_label)

        controls_layout.addSpacing(10)

        self.record_btn = QPushButton("🎙️ Click to Record")
        self.record_btn.setCursor(Qt.PointingHandCursor)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #374151;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        self.record_btn.clicked.connect(self.toggle_recording)
        controls_layout.addWidget(self.record_btn)

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setCursor(Qt.PointingHandCursor)
        self.reset_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: 1px solid #4b5563;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                color: #ffffff;
                border-color: #9ca3af;
            }
        """)
        self.reset_btn.clicked.connect(self.reset_default)
        controls_layout.addWidget(self.reset_btn)

        controls_layout.addStretch()
        layout.addLayout(controls_layout)

    def set_key(self, key_str: str) -> None:
        self.current_key_str = key_str
        self.badge_label.setText(get_friendly_key_name(key_str))

    def reset_default(self) -> None:
        self.stop_recording()
        self.set_key("Key.alt_r")
        self.hotkey_changed.emit("Key.alt_r")

    def toggle_recording(self) -> None:
        if self.is_recording:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self) -> None:
        self.is_recording = True
        self.record_btn.setText("Press any key...")
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc2626;
                color: #ffffff;
                border: 1.5px solid #ef4444;
                border-radius: 6px;
                padding: 7px 14px;
                font-weight: bold;
            }
        """)
        self.badge_label.setText("Press key...")
        self.badge_label.setStyleSheet("""
            QLabel {
                background-color: #371b28;
                color: #f87171;
                border: 1.5px solid #ef4444;
                border-radius: 6px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
                font-size: 13px;
                font-weight: bold;
            }
        """)

        def on_press(key):
            if not self.is_recording:
                return False

            if hasattr(key, 'name') and key.name:
                pynput_key = f"Key.{key.name}"
            elif hasattr(key, 'char') and key.char:
                pynput_key = key.char.lower()
            else:
                pynput_key = str(key)

            if pynput_key in ["Key.alt_gr", "Key.alt_r", "Key.alt"]:
                vk = getattr(key, 'vk', None)
                if vk == 164:
                    pynput_key = "Key.alt_l"
                else:
                    pynput_key = "Key.alt_r"

            print(f"[HotkeyRecorder] Captured key event: {key} -> {pynput_key}")
            self.current_key_str = pynput_key
            QMetaObject.invokeMethod(self, "_on_key_captured", Qt.QueuedConnection)
            return False

        if self._rec_listener is not None:
            self._rec_listener.stop()

        self._rec_listener = keyboard.Listener(on_press=on_press)
        self._rec_listener.daemon = True
        self._rec_listener.start()

    @Slot()
    def _on_key_captured(self) -> None:
        self.stop_recording()
        self.hotkey_changed.emit(self.current_key_str)

    def stop_recording(self) -> None:
        if self._rec_listener is not None:
            self._rec_listener.stop()
            self._rec_listener = None

        if self.is_recording:
            self.is_recording = False
            self.record_btn.setText("🎙️ Click to Record")
            self.record_btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #ffffff;
                    border: none;
                    border-radius: 6px;
                    padding: 7px 14px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #4b5563;
                }
            """)
            self.badge_label.setText(get_friendly_key_name(self.current_key_str))
            self.badge_label.setStyleSheet("""
                QLabel {
                    background-color: #2b3040;
                    color: #6366f1;
                    border: 1.5px solid #4f46e5;
                    border-radius: 6px;
                    padding: 6px 16px;
                    font-family: 'Segoe UI';
                    font-size: 13px;
                    font-weight: bold;
                }
            """)

class SettingsWindow(QWidget):
    config_saved = Signal()

    def __init__(self, config_manager: ConfigManager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.setWindowTitle("Voice Input Settings")
        self.setFixedSize(560, 520)

        # Dark theme styling
        self.setStyleSheet("""
            QWidget {
                background-color: #12151e;
                color: #e5e7eb;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #272c3d;
                border-radius: 8px;
                background-color: #1a1e29;
                padding: 8px;
            }
            QTabBar::tab {
                background-color: #12151e;
                color: #9ca3af;
                padding: 8px 16px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                font-weight: 500;
            }
            QTabBar::tab:selected {
                background-color: #1a1e29;
                color: #6366f1;
                font-weight: bold;
                border-bottom: 2px solid #6366f1;
            }
            QLineEdit, QComboBox, QPlainTextEdit {
                background-color: #242936;
                border: 1px solid #374151;
                border-radius: 6px;
                padding: 6px 10px;
                color: #f3f4f6;
            }
            QLineEdit:focus, QComboBox:focus, QPlainTextEdit:focus {
                border: 1.5px solid #6366f1;
            }
            QPushButton {
                background-color: #4f46e5;
                color: #ffffff;
                border: none;
                border-radius: 6px;
                padding: 7px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6366f1;
            }
            QCheckBox {
                color: #f3f4f6;
                font-size: 13px;
                font-weight: 500;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border: 1.5px solid #4b5563;
                border-radius: 4px;
                background-color: #242936;
            }
            QCheckBox::indicator:hover {
                border-color: #6366f1;
            }
            QCheckBox::indicator:checked {
                background-color: #6366f1;
                border: 1.5px solid #818cf8;
            }
        """)

        self._updating_ui = False

        main_layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: ASR Settings
        self.asr_tab = QWidget()
        self.setup_asr_tab()
        self.tabs.addTab(self.asr_tab, "ASR Settings")

        # Tab 2: LLM Refinement
        self.llm_tab = QWidget()
        self.setup_llm_tab()
        self.tabs.addTab(self.llm_tab, "LLM Refinement")

        # Tab 3: Hotkey Settings
        self.hotkey_tab = QWidget()
        self.setup_hotkey_tab()
        self.tabs.addTab(self.hotkey_tab, "Hotkey & General")

        # Main Save Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = QPushButton("Save Config")
        self.save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(self.save_btn)

        main_layout.addLayout(btn_layout)

        self.load_config_to_ui()

    def setup_asr_tab(self) -> None:
        layout = QFormLayout(self.asr_tab)

        self.asr_provider_combo = QComboBox()
        self.asr_provider_combo.addItems(["xiaomi_mimo", "openai", "doubao", "qwen"])
        self.asr_provider_combo.currentTextChanged.connect(self._on_asr_provider_changed)
        layout.addRow("ASR Provider:", self.asr_provider_combo)

        # Dynamic Key Label & Input
        self.asr_key_label = QLabel("API Key:")
        self.asr_key_input = QLineEdit()
        self.asr_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow(self.asr_key_label, self.asr_key_input)

        # Extra Input (e.g. Doubao App ID)
        self.asr_extra_label = QLabel("App ID:")
        self.asr_extra_input = QLineEdit()
        layout.addRow(self.asr_extra_label, self.asr_extra_input)

        # Base URL
        self.asr_url_input = QLineEdit()
        layout.addRow("Base URL:", self.asr_url_input)

        # Model Name + Fetch Button
        model_layout = QHBoxLayout()
        self.asr_model_combo = QComboBox()
        self.asr_model_combo.setEditable(True)
        model_layout.addWidget(self.asr_model_combo)

        self.fetch_asr_btn = QPushButton("🔄 Fetch Models")
        self.fetch_asr_btn.clicked.connect(self._fetch_asr_models)
        model_layout.addWidget(self.fetch_asr_btn)

        layout.addRow("Model Name:", model_layout)

        # Test Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_asr_btn = QPushButton("Test ASR Connection")
        self.test_asr_btn.clicked.connect(self._test_asr_connection)
        test_layout.addWidget(self.test_asr_btn)
        layout.addRow("", test_layout)

    def setup_llm_tab(self) -> None:
        layout = QFormLayout(self.llm_tab)

        self.llm_enable_cb = QCheckBox("Enable LLM Refinement & Polishing")
        layout.addRow("", self.llm_enable_cb)

        self.llm_key_input = QLineEdit()
        self.llm_key_input.setEchoMode(QLineEdit.Password)
        layout.addRow("API Key:", self.llm_key_input)

        self.llm_url_input = QLineEdit()
        layout.addRow("Base URL:", self.llm_url_input)

        # LLM Model Name + Fetch Button
        model_layout = QHBoxLayout()
        self.llm_model_combo = QComboBox()
        self.llm_model_combo.setEditable(True)
        model_layout.addWidget(self.llm_model_combo)

        self.fetch_llm_btn = QPushButton("🔄 Fetch Models")
        self.fetch_llm_btn.clicked.connect(self._fetch_llm_models)
        model_layout.addWidget(self.fetch_llm_btn)

        layout.addRow("Model Name:", model_layout)

        # System Prompt Section
        prompt_label_layout = QHBoxLayout()
        prompt_label_layout.addWidget(QLabel("System Prompt:"))
        prompt_label_layout.addStretch()

        self.reset_prompt_btn = QPushButton("↺ Reset Prompt")
        self.reset_prompt_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #9ca3af;
                border: 1px solid #4b5563;
                border-radius: 4px;
                padding: 3px 10px;
                font-size: 11px;
            }
            QPushButton:hover {
                color: #ffffff;
                border-color: #9ca3af;
            }
        """)
        self.reset_prompt_btn.clicked.connect(self._reset_default_prompt)
        prompt_label_layout.addWidget(self.reset_prompt_btn)

        layout.addRow(prompt_label_layout)

        self.llm_prompt_input = QPlainTextEdit()
        self.llm_prompt_input.setPlaceholderText("Enter custom System Prompt...")
        self.llm_prompt_input.setFixedHeight(110)
        layout.addRow(self.llm_prompt_input)

        # LLM Test Connection Button
        test_layout = QHBoxLayout()
        test_layout.addStretch()
        self.test_llm_btn = QPushButton("Test LLM Connection")
        self.test_llm_btn.clicked.connect(self._test_llm_connection)
        test_layout.addWidget(self.test_llm_btn)
        layout.addRow("", test_layout)

    def setup_hotkey_tab(self) -> None:
        layout = QVBoxLayout(self.hotkey_tab)
        layout.setContentsMargins(10, 10, 10, 10)

        # Modern Interactive Hotkey Card Widget
        self.hotkey_widget = HotkeyRecorderWidget()
        layout.addWidget(self.hotkey_widget)
        layout.addStretch()

    def _reset_default_prompt(self) -> None:
        self.llm_prompt_input.setPlainText(DEFAULT_SYSTEM_PROMPT)

    def _on_asr_provider_changed(self, provider: str) -> None:
        if self._updating_ui:
            return

        defaults = PROVIDER_DEFAULTS.get(provider, PROVIDER_DEFAULTS["xiaomi_mimo"])
        self.asr_key_label.setText(defaults["label_key"])

        if defaults["has_extra"]:
            self.asr_extra_label.setText(defaults.get("label_extra", "App ID:"))
            self.asr_extra_label.show()
            self.asr_extra_input.show()
        else:
            self.asr_extra_label.hide()
            self.asr_extra_input.hide()

        # Update Base URL & Model dynamically
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

    def load_config_to_ui(self) -> None:
        self._updating_ui = True
        cfg = self.config_manager.config

        # ASR
        asr_cfg = cfg.get("asr", {})
        provider = asr_cfg.get("provider", "xiaomi_mimo")
        idx = self.asr_provider_combo.findText(provider)
        if idx >= 0:
            self.asr_provider_combo.setCurrentIndex(idx)

        self._updating_ui = False
        self._on_asr_provider_changed(provider)

        # LLM
        llm_cfg = cfg.get("llm", {})
        self.llm_enable_cb.setChecked(llm_cfg.get("enabled", True))
        self.llm_key_input.setText(llm_cfg.get("api_key", ""))
        self.llm_url_input.setText(llm_cfg.get("base_url", "https://api.openai.com/v1"))
        
        self.llm_model_combo.clear()
        self.llm_model_combo.setEditText(llm_cfg.get("model", "gpt-4o-mini"))

        saved_prompt = llm_cfg.get("system_prompt", "")
        self.llm_prompt_input.setPlainText(saved_prompt if saved_prompt else DEFAULT_SYSTEM_PROMPT)

        # Hotkey
        hotkey_str = cfg.get("hotkey", "Key.alt_r")
        self.hotkey_widget.set_key(hotkey_str)

    def save_config(self) -> None:
        cfg = self.config_manager.config
        provider = self.asr_provider_combo.currentText()

        cfg["asr"]["provider"] = provider
        if provider not in cfg["asr"]:
            cfg["asr"][provider] = {}

        # Save active provider fields
        cfg["asr"][provider]["base_url"] = self.asr_url_input.text().strip()
        cfg["asr"][provider]["model"] = self.asr_model_combo.currentText().strip()

        if provider == "doubao":
            cfg["asr"][provider]["access_token"] = self.asr_key_input.text().strip()
            cfg["asr"][provider]["app_id"] = self.asr_extra_input.text().strip()
        else:
            cfg["asr"][provider]["api_key"] = self.asr_key_input.text().strip()

        # LLM
        cfg["llm"]["enabled"] = self.llm_enable_cb.isChecked()
        cfg["llm"]["api_key"] = self.llm_key_input.text().strip()
        cfg["llm"]["base_url"] = self.llm_url_input.text().strip()
        cfg["llm"]["model"] = self.llm_model_combo.currentText().strip()
        cfg["llm"]["system_prompt"] = self.llm_prompt_input.toPlainText().strip()

        # Hotkey
        cfg["hotkey"] = self.hotkey_widget.current_key_str.strip()

        self.config_manager.save_config(cfg)
        self.config_saved.emit()
        QMessageBox.information(self, "Success", "Configuration saved successfully!")
        self.close()

    def _fetch_asr_models(self) -> None:
        url = self.asr_url_input.text().strip()
        key = self.asr_key_input.text().strip()
        self._fetch_models_from_api(url, key, self.asr_model_combo, is_asr=True)

    def _fetch_llm_models(self) -> None:
        url = self.llm_url_input.text().strip()
        key = self.llm_key_input.text().strip()
        self._fetch_models_from_api(url, key, self.llm_model_combo, is_asr=False)

    def _fetch_models_from_api(self, base_url: str, api_key: str, model_combo: QComboBox, is_asr: bool = False) -> None:
        if not base_url:
            QMessageBox.warning(self, "Fetch Failed", "Please enter a Base URL.")
            return

        clean_url = base_url.rstrip("/")
        models_url = f"{clean_url}/models"
        headers = {}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        try:
            resp = requests.get(models_url, headers=headers, timeout=8)
            if resp.status_code == 200:
                res_json = resp.json()
                data = res_json.get("data", [])
                model_ids = []
                if isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and "id" in item:
                            model_ids.append(item["id"])
                        elif isinstance(item, str):
                            model_ids.append(item)

                if model_ids:
                    if is_asr:
                        asr_keywords = ["asr", "whisper", "audio", "mimo", "speech"]
                        asr_models = [m for m in model_ids if any(kw in m.lower() for kw in asr_keywords)]
                        other_models = [m for m in model_ids if m not in asr_models]
                        model_ids = asr_models + other_models

                    curr_text = model_combo.currentText()
                    model_combo.clear()
                    model_combo.addItems(model_ids)

                    if curr_text and curr_text in model_ids:
                        model_combo.setCurrentText(curr_text)
                    elif model_ids:
                        model_combo.setCurrentIndex(0)

                    QMessageBox.information(self, "Success", f"Successfully fetched {len(model_ids)} available models!")
                else:
                    QMessageBox.warning(self, "Fetch Warning", "Endpoint responded HTTP 200, but no models list was found in payload.")
            else:
                QMessageBox.warning(self, "Fetch Failed", f"Failed to fetch models from {models_url}\nHTTP Status: {resp.status_code}\nResponse: {resp.text}")
        except Exception as e:
            QMessageBox.warning(self, "Fetch Failed", f"Exception while fetching models from {models_url}:\n{str(e)}")

    def _test_asr_connection(self) -> None:
        provider = self.asr_provider_combo.currentText()
        url = self.asr_url_input.text().strip()
        model = self.asr_model_combo.currentText().strip()
        key = self.asr_key_input.text().strip()
        extra = self.asr_extra_input.text().strip()

        if not key:
            QMessageBox.warning(self, "Test Failed", f"Please enter the {self.asr_key_label.text().replace(':', '')}")
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
            # Send 0.5s of silent 16kHz PCM audio
            asr_instance.send_audio_chunk(b"\x00\x00" * 8000)
            res = asr_instance.finish()
            QMessageBox.information(self, "Connection Succeeded", f"ASR connection test succeeded!\nProvider: {provider}\nEndpoint: {url}\nModel: {model}")
        except Exception as e:
            QMessageBox.warning(self, "Connection Failed", f"ASR connection test failed:\n{str(e)}")

    def _test_llm_connection(self) -> None:
        url = self.llm_url_input.text().strip()
        model = self.llm_model_combo.currentText().strip()
        key = self.llm_key_input.text().strip()
        prompt = self.llm_prompt_input.toPlainText().strip()

        if not key:
            QMessageBox.warning(self, "Test Failed", "Please enter the LLM API Key.")
            return

        temp_cfg = {
            "enabled": True,
            "api_key": key,
            "base_url": url,
            "model": model,
            "system_prompt": prompt
        }

        refiner = LLMRefiner(temp_cfg)
        test_input = "呃，那个，我今天想写一个配森脚本，啊对。"
        result = refiner.refine(test_input)
        if result:
            QMessageBox.information(self, "Connection Succeeded", f"LLM connection test succeeded!\n\nRaw Input:\n'{test_input}'\n\nRefined Output:\n'{result}'")
        else:
            QMessageBox.warning(self, "Connection Failed", "LLM connection test failed or returned empty result.")
