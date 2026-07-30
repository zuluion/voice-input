import os
from PySide6.QtCore import Qt, Signal, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QFormLayout, QHBoxLayout, QLabel, QComboBox, QPushButton
)
from pynput import keyboard

def format_key_display(key_str: str) -> str:
    mapping = {
        "Key.ctrl_r": "Right Control",
        "Key.ctrl_l": "Left Control",
        "Key.alt_gr": "Right Alt",
        "Key.alt_r": "Right Alt",
        "Key.alt_l": "Left Alt",
        "Key.space": "Space",
        "Key.shift_r": "Right Shift",
        "Key.shift_l": "Left Shift"
    }
    if key_str in mapping:
        return mapping[key_str]
    if key_str.startswith("Key."):
        return key_str[4:].capitalize()
    if key_str.startswith("'") and key_str.endswith("'"):
        return key_str[1:-1].upper()
    return key_str.upper()

class HotkeyRecorderWidget(QWidget):
    key_recorded = Signal(str)

    def __init__(self, current_key: str = "Key.ctrl_r", parent=None) -> None:
        super().__init__(parent)
        self.current_key = current_key
        self.is_recording = False
        self.kb_listener = None

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.keycap_label = QLabel()
        self.keycap_label.setStyleSheet("""
            QLabel {
                background-color: #242936;
                color: #6366f1;
                border: 1.5px solid #6366f1;
                border-radius: 6px;
                padding: 6px 14px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
                font-weight: bold;
            }
        """)
        layout.addWidget(self.keycap_label)

        self.record_btn = QPushButton("🎙️ Click to Record")
        self.record_btn.setFixedWidth(140)
        self.record_btn.clicked.connect(self._toggle_recording)
        layout.addWidget(self.record_btn)

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setFixedWidth(70)
        self.reset_btn.clicked.connect(self._reset_key)
        layout.addWidget(self.reset_btn)

        self.update_display(self.current_key)

    def update_display(self, key_str: str) -> None:
        self.current_key = key_str
        display_name = format_key_display(key_str)
        self.keycap_label.setText(f"[ {display_name} ]")

    def _toggle_recording(self) -> None:
        if self.is_recording:
            self._stop_recording()
        else:
            self._start_recording()

    def _start_recording(self) -> None:
        self.is_recording = True
        self.record_btn.setText("🔴 Press any key...")
        self.keycap_label.setText("[ Waiting key... ]")

        self.kb_listener = keyboard.Listener(on_press=self._on_key_press)
        self.kb_listener.start()

    def _stop_recording(self) -> None:
        self.is_recording = False
        self.record_btn.setText("🎙️ Click to Record")
        if self.kb_listener:
            self.kb_listener.stop()
            self.kb_listener = None

    def _on_key_press(self, key) -> None:
        key_str = str(key)
        self._stop_recording()
        self.update_display(key_str)
        self.key_recorded.emit(key_str)

    def _reset_key(self) -> None:
        self._stop_recording()
        self.update_display("Key.ctrl_r")
        self.key_recorded.emit("Key.ctrl_r")

class HotkeySettingsTab(QWidget):
    def __init__(self, config_manager) -> None:
        super().__init__()
        self.config_manager = config_manager
        self.recorded_key_str = "Key.ctrl_r"
        self.setup_ui()

    def setup_ui(self) -> None:
        layout = QFormLayout(self)

        self.hotkey_recorder = HotkeyRecorderWidget()
        self.hotkey_recorder.key_recorded.connect(self._on_key_recorded)
        layout.addRow("Trigger Hotkey:", self.hotkey_recorder)

        self.pos_combo = QComboBox()
        self.pos_combo.addItems(["bottom_center", "top_center", "center"])
        layout.addRow("Capsule Position:", self.pos_combo)

        open_config_btn = QPushButton("📂 Open Config Location")
        open_config_btn.clicked.connect(self._open_config_dir)
        layout.addRow("", open_config_btn)

    def _on_key_recorded(self, key_str: str) -> None:
        self.recorded_key_str = key_str

    def load_config(self) -> None:
        hotkey = self.config_manager.get("hotkey", default="Key.ctrl_r")
        self.recorded_key_str = hotkey
        self.hotkey_recorder.update_display(hotkey)

        pos = self.config_manager.get("ui", "position", default="bottom_center")
        idx = self.pos_combo.findText(pos)
        if idx >= 0:
            self.pos_combo.setCurrentIndex(idx)

    def save_config(self, cfg: dict) -> None:
        cfg["hotkey"] = self.recorded_key_str
        if "ui" not in cfg:
            cfg["ui"] = {}
        cfg["ui"]["position"] = self.pos_combo.currentText()

    def _open_config_dir(self) -> None:
        path = self.config_manager.config_path
        parent_dir = os.path.dirname(os.path.abspath(path))
        if os.path.exists(parent_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(parent_dir))
