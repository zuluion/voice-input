import threading
from PySide6.QtCore import QObject, Signal
from pynput import keyboard

class HotkeyListener(QObject):
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, target_key_str: str = "Key.alt_r") -> None:
        super().__init__()
        self.target_key_str = target_key_str
        self.is_pressed = False
        self._listener = None
        self._target_key = self._parse_key(target_key_str)

    def _parse_key(self, key_str: str):
        key_str_clean = key_str.strip()
        if key_str_clean.startswith("Key."):
            attr = key_str_clean.split(".")[1]
            return getattr(keyboard.Key, attr, keyboard.Key.alt_r)
        if hasattr(keyboard.Key, key_str_clean):
            return getattr(keyboard.Key, key_str_clean)
        return keyboard.KeyCode.from_char(key_str_clean)

    def set_target_key(self, target_key_str: str) -> None:
        self.target_key_str = target_key_str
        self._target_key = self._parse_key(target_key_str)
        print(f"[Hotkey] Target hotkey set to: {self.target_key_str}")

    def start(self) -> None:
        if self._listener is not None:
            return
        print(f"[Hotkey] Starting listener for key: {self.target_key_str}")
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self) -> None:
        if self._listener is not None:
            self._listener.stop()
            self._listener = None

    def _match_key(self, key) -> bool:
        if key is None:
            return False
        if self._target_key == key:
            return True

        target_name = getattr(self._target_key, 'name', None) or str(self.target_key_str).lower().replace("key.", "")
        key_name = getattr(key, 'name', None)
        key_vk = getattr(key, 'vk', None)

        # Match Alt variants on Windows (alt_r, alt_gr, alt_l, alt, VK 164/165)
        if target_name in ["alt_r", "alt_gr", "alt_l", "alt"]:
            if key_name in ["alt_r", "alt_gr", "alt_l", "alt"]:
                return True
            if key_vk in [164, 165]:
                return True

        if hasattr(self._target_key, 'vk') and self._target_key.vk is not None and self._target_key.vk == key_vk:
            return True

        if key_name and target_name and key_name.lower() == target_name.lower():
            return True

        return False

    def _on_press(self, key) -> None:
        if self._match_key(key):
            if not self.is_pressed:
                print(f"[Hotkey Triggered] Key pressed: {key} -> starting recording")
                self.is_pressed = True
                self.recording_started.emit()

    def _on_release(self, key) -> None:
        if self._match_key(key):
            if self.is_pressed:
                print(f"[Hotkey Triggered] Key released: {key} -> stopping recording")
                self.is_pressed = False
                self.recording_stopped.emit()
