import os
import sys
import threading

# Ensure project root & PyInstaller _MEIPASS are in sys.path
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtCore import QObject, Signal, QThread

from src.config import ConfigManager
from src.core.hotkey import HotkeyListener
from src.audio.recorder import AudioRecorder
from src.asr import create_asr_provider
from src.refine.llm import LLMRefiner
from src.utils.injector import TextInjector
from src.ui.capsule import FloatingCapsule
from src.ui.tray import SystemTrayApp
from src.ui.settings import SettingsWindow

class ASRProcessingWorker(QThread):
    status_changed = Signal(str)
    processing_finished = Signal(str)

    def __init__(self, asr_provider, llm_refiner) -> None:
        super().__init__()
        self.asr_provider = asr_provider
        self.llm_refiner = llm_refiner

    def run(self) -> None:
        raw_text = ""
        if self.asr_provider:
            raw_text = self.asr_provider.finish()

        if not raw_text.strip():
            self.processing_finished.emit("")
            return

        self.status_changed.emit("Refining...")
        refined_text = self.llm_refiner.refine(raw_text)
        self.processing_finished.emit(refined_text)

class VoiceInputController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()
        self.capsule = FloatingCapsule()
        self.tray_app = SystemTrayApp()
        self.injector = TextInjector()
        self.settings_window = None

        hotkey_str = self.config_manager.get("hotkey", default="Key.alt_r")
        self.hotkey_listener = HotkeyListener(target_key_str=hotkey_str)
        self.audio_recorder = AudioRecorder()

        self.current_asr = None
        self.llm_refiner = LLMRefiner(self.config_manager.get("llm", default={}))
        self.worker = None

        # Signal connections
        self.hotkey_listener.recording_started.connect(self._on_recording_started)
        self.hotkey_listener.recording_stopped.connect(self._on_recording_stopped)

        self.audio_recorder.recording_ready.connect(self._on_recording_ready)
        self.audio_recorder.volume_changed.connect(self.capsule.set_volume_levels)
        self.audio_recorder.audio_chunk_ready.connect(self._on_audio_chunk)
        self.audio_recorder.error_occurred.connect(self._on_audio_error)

        self.tray_app.open_settings_requested.connect(self._open_settings)
        self.tray_app.quit_requested.connect(self._quit_app)

    def start(self) -> None:
        self.tray_app.show()
        self.hotkey_listener.start()

    def _on_recording_started(self) -> None:
        print("[Main] Recording started signal received")
        if not self.tray_app.is_enabled():
            print("[Main] Tray app is disabled, ignoring hotkey")
            return
        
        self.capsule.set_state(FloatingCapsule.STATE_PREPARING)
        self.capsule.show_capsule()

        provider_name = self.config_manager.get("asr", "provider", default="xiaomi_mimo")
        asr_cfg = self.config_manager.get("asr", default={})
        self.current_asr = create_asr_provider(provider_name, asr_cfg)
        self.current_asr.text_updated.connect(self._on_asr_text_updated)
        self.current_asr.error_occurred.connect(self._on_asr_error)

        self.current_asr.connect()
        self.audio_recorder.start()

    def _on_recording_ready(self) -> None:
        print("[Main] Microphone captured first audio frame -> Switching to LISTENING state")
        self.capsule.set_state(FloatingCapsule.STATE_LISTENING)

    def _on_audio_chunk(self, chunk: bytes) -> None:
        if self.current_asr:
            self.current_asr.send_audio_chunk(chunk)

    def _on_audio_error(self, err_msg: str) -> None:
        print(f"[Main Audio Error] {err_msg}")
        self.capsule.hide_capsule()
        # Show Tray Notification
        self.tray_app.tray_icon.showMessage(
            "语音输入设备错误",
            err_msg,
            QSystemTrayIcon.Warning,
            4000
        )
        # Show Modal Warning Popup
        QMessageBox.warning(None, "语音输入设备错误", err_msg)

    def _on_asr_text_updated(self, text: str, is_final: bool) -> None:
        if text:
            self.capsule.set_status_text(text)

    def _on_asr_error(self, err_msg: str) -> None:
        print(f"[Main ASR Error] {err_msg}")
        self.capsule.set_status_text("ASR Error")

    def _on_recording_stopped(self) -> None:
        print("[Main] Recording stopped signal received")
        if not self.tray_app.is_enabled():
            return
        self.audio_recorder.stop()
        self.capsule.set_state(FloatingCapsule.STATE_REFINING)

        self.worker = ASRProcessingWorker(self.current_asr, self.llm_refiner)
        self.worker.status_changed.connect(self.capsule.set_status_text)
        self.worker.processing_finished.connect(self._on_processing_finished)
        self.worker.start()

    def _on_processing_finished(self, text: str) -> None:
        print(f"[Main] Processing finished. Final text: '{text}'")
        if text.strip():
            self.injector.inject(text)
        self.capsule.hide_capsule()

    def _open_settings(self) -> None:
        if self.settings_window is None:
            self.settings_window = SettingsWindow(self.config_manager)
            self.settings_window.config_saved.connect(self._on_config_saved)
        self.settings_window.show()
        self.settings_window.raise_()

    def _on_config_saved(self) -> None:
        new_hotkey = self.config_manager.get("hotkey", default="Key.alt_r")
        self.hotkey_listener.set_target_key(new_hotkey)
        self.llm_refiner = LLMRefiner(self.config_manager.get("llm", default={}))

    def _quit_app(self) -> None:
        self.hotkey_listener.stop()
        QApplication.quit()

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = VoiceInputController()
    controller.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
