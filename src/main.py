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
from src.utils.proxy import apply_proxy_config
from src.utils.webdav import WebDAVSync
from src.utils.logger import logger
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

        logger.log("ASR Result", f"Raw Recognized Text: '{raw_text}'")

        if not raw_text.strip():
            self.processing_finished.emit("")
            return

        self.status_changed.emit("Refining...")
        refined_text = self.llm_refiner.refine(raw_text)
        logger.log("LLM Output", f"Refined Text: '{refined_text}'")
        self.processing_finished.emit(refined_text)

class VoiceInputController(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()

        # Configure Debug Logger
        logger.configure(self.config_manager.get("debug", default={}), self.config_manager.config_path)

        # Apply Proxy Config
        apply_proxy_config(self.config_manager.get("proxy", default={}))

        # Auto-sync WebDAV if enabled
        self._check_webdav_auto_sync()

        self.capsule = FloatingCapsule()
        self.tray_app = SystemTrayApp()
        self.injector = TextInjector()
        self.settings_window = None

        hotkey_str = self.config_manager.get("hotkey", default="Key.ctrl_r")
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

    def _check_webdav_auto_sync(self) -> None:
        webdav_cfg = self.config_manager.get("webdav", default={})
        if webdav_cfg.get("enabled") and webdav_cfg.get("auto_sync_on_startup"):
            logger.log("Main", "WebDAV Auto-sync on startup is enabled. Downloading latest config...")
            sync = WebDAVSync(webdav_cfg)
            threading.Thread(target=self._run_webdav_sync, args=(sync,), daemon=True).start()

    def _run_webdav_sync(self, sync: WebDAVSync) -> None:
        ok, msg = sync.download_config(self.config_manager.config_path)
        if ok:
            logger.log("Main", "WebDAV Auto-sync succeeded! Reloading config...")
            self.config_manager.config = self.config_manager.load_config()
            apply_proxy_config(self.config_manager.get("proxy", default={}))
            logger.configure(self.config_manager.get("debug", default={}), self.config_manager.config_path)
        else:
            logger.log("Main", f"WebDAV Auto-sync failed: {msg}")

    def start(self) -> None:
        self.tray_app.show()
        self.hotkey_listener.start()

    def _on_recording_started(self) -> None:
        logger.log("Main", "Recording started signal received")
        if not self.tray_app.is_enabled():
            logger.log("Main", "Tray app is disabled, ignoring hotkey")
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
        logger.log("Main", "Microphone captured first audio frame -> Switching to LISTENING state")
        self.capsule.set_state(FloatingCapsule.STATE_LISTENING)

    def _on_audio_chunk(self, chunk: bytes) -> None:
        if self.current_asr:
            self.current_asr.send_audio_chunk(chunk)

    def _on_audio_error(self, err_msg: str) -> None:
        logger.log("Main Audio Error", err_msg)
        self.capsule.hide_capsule()
        self.tray_app.tray_icon.showMessage(
            "语音输入设备错误",
            err_msg,
            QSystemTrayIcon.Warning,
            4000
        )
        QMessageBox.warning(None, "语音输入设备错误", err_msg)

    def _on_asr_text_updated(self, text: str, is_final: bool) -> None:
        if text:
            self.capsule.set_status_text(text)

    def _on_asr_error(self, err_msg: str) -> None:
        logger.log("Main ASR Error", err_msg)
        self.capsule.set_status_text("ASR Error")

    def _on_recording_stopped(self) -> None:
        logger.log("Main", "Recording stopped signal received")
        if not self.tray_app.is_enabled():
            return
        self.audio_recorder.stop()
        self.capsule.set_state(FloatingCapsule.STATE_REFINING)

        self.worker = ASRProcessingWorker(self.current_asr, self.llm_refiner)
        self.worker.status_changed.connect(self.capsule.set_status_text)
        self.worker.processing_finished.connect(self._on_processing_finished)
        self.worker.start()

    def _on_processing_finished(self, text: str) -> None:
        logger.log("Main", f"Processing finished. Final text to inject: '{text}'")
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
        new_hotkey = self.config_manager.get("hotkey", default="Key.ctrl_r")
        self.hotkey_listener.set_target_key(new_hotkey)
        self.llm_refiner = LLMRefiner(self.config_manager.get("llm", default={}))
        apply_proxy_config(self.config_manager.get("proxy", default={}))
        logger.configure(self.config_manager.get("debug", default={}), self.config_manager.config_path)

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
