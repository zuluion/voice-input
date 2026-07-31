import os
import sys
import json
import threading
import requests
from typing import Optional, Dict, Any

# Ensure project root & PyInstaller _MEIPASS are in sys.path
if getattr(sys, 'frozen', False):
    base_dir = getattr(sys, '_MEIPASS', os.path.abspath(os.path.dirname(__file__)))
else:
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

if base_dir not in sys.path:
    sys.path.insert(0, base_dir)

from PySide6.QtWidgets import QApplication, QMessageBox, QSystemTrayIcon
from PySide6.QtCore import QObject, Signal, QThread, QTimer

from src.i18n import i18n
from src.config import ConfigManager, DEFAULT_DAEMON_URL, DEFAULT_DAEMON_WS_URL
from src.core.hotkey import HotkeyListener
from src.audio.recorder import AudioRecorder
from src.utils.injector import TextInjector
from src.utils.proxy import apply_proxy_config
from src.utils.webdav import WebDAVSync
from src.utils.daemon_process import DaemonProcessManager
from src.utils.model_downloader import stop_ollama_server
from src.utils.logger import logger
from src.ui.capsule import FloatingCapsule
from src.ui.tray import SystemTrayApp
from src.ui.settings import SettingsWindow

import time
import websocket

class WebSocketClientWorker(QThread):
    """
    负责与 Headless Daemon 进行 WebSocket 双向通信的全透明 Qt 专用工作线程
    """
    status_changed = Signal(str, str)         # (state, detail)
    asr_partial = Signal(str, bool)          # (text, is_final)
    session_completed = Signal(str, dict)     # (refined_text, trace_meta)
    error_occurred = Signal(str)             # (err_msg)

    def __init__(self, ws_url: str = DEFAULT_DAEMON_WS_URL) -> None:
        super().__init__()
        self.ws_url = ws_url
        self.ws: Optional[websocket.WebSocketApp] = None
        self._is_running = True

    def run(self) -> None:
        def on_open(ws):
            logger.log("WS Client", f"Connected to Backend Daemon WebSocket endpoint at {self.ws_url}")

        def on_message(ws, message):
            try:
                data = json.loads(message)
                msg_type = data.get("type")
                payload = data.get("payload", {})

                if msg_type == "status_change":
                    logger.log("WS Client In", f"Status Change -> State: '{payload.get('state')}' ({payload.get('detail')})")
                    self.status_changed.emit(payload.get("state", ""), payload.get("detail", ""))
                elif msg_type == "asr_partial_result":
                    logger.log("WS Client In", f"Live ASR Partial -> '{payload.get('text')}' (Final: {payload.get('is_final')})")
                    self.asr_partial.emit(payload.get("text", ""), payload.get("is_final", False))
                elif msg_type == "session_complete":
                    refined_text = payload.get('refined_text', "")
                    meta = payload.get('meta', {})
                    logger.log("WS Client In", f"Session Complete -> Refined Text: '{refined_text}'")
                    self.session_completed.emit(refined_text, meta)
                elif msg_type == "error":
                    logger.log("WS Client Error", f"Daemon Error -> {payload.get('message')}")
                    self.error_occurred.emit(payload.get("message", ""))
            except Exception as e:
                logger.log("WSClient Exception", f"Error parsing message: {e}")

        def on_error(ws, error):
            logger.log("WSClient Error", f"WebSocket error: {error}")

        def on_close(ws, close_status_code, close_msg):
            logger.log("WSClient", f"WebSocket connection closed: {close_status_code} - {close_msg}")

        while self._is_running:
            try:
                self.ws = websocket.WebSocketApp(
                    self.ws_url,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                self.ws.run_forever(ping_interval=10, ping_timeout=5)
            except Exception as e:
                logger.log("WSClient Exception", f"Failed to connect to Daemon WebSocket: {e}")
            time.sleep(1)

    def send_start(self, override_asr: Optional[str] = None) -> None:
        if self.ws and self.ws.sock and self.ws.sock.connected:
            msg = {"type": "session_start", "payload": {}}
            if override_asr:
                msg["payload"]["override_config"] = {"asr_provider": override_asr}
            payload_str = json.dumps(msg)
            logger.log("WS Client Out", f"Sending 'session_start' -> {payload_str}")
            self.ws.send(payload_str)
        else:
            logger.log("WS Client Error", "Cannot send 'session_start': WebSocket is not connected!")

    def send_audio_chunk(self, chunk: bytes) -> None:
        if self.ws and self.ws.sock and self.ws.sock.connected:
            try:
                self.ws.send(chunk, opcode=websocket.ABNF.OPCODE_BINARY)
            except Exception as e:
                logger.log("WS Client Send Error", f"Failed to send binary audio chunk: {e}")

    def send_stop(self) -> None:
        if self.ws and self.ws.sock and self.ws.sock.connected:
            payload_str = json.dumps({"type": "session_stop"})
            logger.log("WS Client Out", f"Sending 'session_stop' -> {payload_str}")
            self.ws.send(payload_str)
        else:
            logger.log("WS Client Error", "Cannot send 'session_stop': WebSocket is not connected!")

    def stop(self) -> None:
        self._is_running = False
        if self.ws:
            self.ws.close()
        self.quit()

class VoiceInputController(QObject):
    """
    瘦客户端 UI 控制器 (Thin Desktop Client Controller)，
    彻底实现前后端分离——界面仅负责设备交互，业务解耦至 Backend Daemon。
    """
    def __init__(self) -> None:
        super().__init__()
        self.config_manager = ConfigManager()

        # 自动初始化与守护 Daemon 子进程
        self.daemon_manager = DaemonProcessManager()
        self.daemon_manager.ensure_daemon_started()

        # Initialize i18n Language
        lang_setting = self.config_manager.get("language", default="auto")
        i18n.set_language(lang_setting)

        # Configure Debug Logger & Proxy
        logger.configure(self.config_manager.get("debug", default={}), self.config_manager.config_path)
        apply_proxy_config(self.config_manager.get("proxy", default={}))

        # Initialize Components
        self.audio_recorder = AudioRecorder()
        self.hotkey_listener = HotkeyListener(self.config_manager.get("hotkey", default="Key.ctrl_r"))
        self.injector = TextInjector()
        self.capsule = FloatingCapsule()
        self.capsule.set_position(self.config_manager.get("ui", "position", default="bottom_center"))
        self.tray_app = SystemTrayApp()
        self._refine_timer: Optional[QTimer] = None

        # Check WebDAV Auto-sync
        self._check_webdav_auto_sync()

        # WebSocket Client Worker
        self.ws_worker = WebSocketClientWorker()
        self.ws_worker.status_changed.connect(self._on_daemon_status_changed)
        self.ws_worker.asr_partial.connect(self._on_asr_text_updated)
        self.ws_worker.session_completed.connect(self._on_processing_finished)
        self.ws_worker.error_occurred.connect(self._on_daemon_error)
        self.ws_worker.start()

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
            logger.log("Main", "WebDAV Auto-sync on startup is enabled. Download requested via Daemon API...")
            threading.Thread(target=self._run_webdav_sync, daemon=True).start()

    def _run_webdav_sync(self) -> None:
        try:
            res = requests.post(f"{DEFAULT_DAEMON_URL}/api/v1/config/sync", timeout=10, proxies={"http": None, "https": None})
            if res.status_code == 200:
                logger.log("Main", "WebDAV Auto-sync succeeded! Reloading local config...")
                self.config_manager.config = self.config_manager.load_config()
                i18n.set_language(self.config_manager.get("language", default="auto"))
                self.capsule.set_position(self.config_manager.get("ui", "position", default="bottom_center"))
                apply_proxy_config(self.config_manager.get("proxy", default={}))
            else:
                logger.log("Main", f"WebDAV Auto-sync via Daemon failed: {res.text}")
        except Exception as e:
            logger.log("Main", f"WebDAV Auto-sync exception: {e}")

    def start(self) -> None:
        self.tray_app.show()
        self.hotkey_listener.start()

    def _on_recording_started(self) -> None:
        logger.log("Main Thin Client", "Hotkey Pressed -> Triggering Recording Session")
        if not self.tray_app.is_enabled():
            logger.log("Main Thin Client", "Tray app is disabled, ignoring hotkey")
            return

        self.capsule.set_state(FloatingCapsule.STATE_PREPARING)
        self.capsule.show_capsule()

        provider_name = self.config_manager.get("asr", "provider", default="xiaomi_mimo")
        self.ws_worker.send_start(override_asr=provider_name)
        self.audio_recorder.start()

    def _on_recording_ready(self) -> None:
        logger.log("Main Thin Client", "Microphone audio stream active -> Switching Capsule to LISTENING state")
        self.capsule.set_state(FloatingCapsule.STATE_LISTENING)

    def _on_audio_chunk(self, chunk: bytes) -> None:
        self.ws_worker.send_audio_chunk(chunk)

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

    def _on_daemon_status_changed(self, state: str, detail: str) -> None:
        if state == "REFINING":
            self.capsule.set_state(FloatingCapsule.STATE_REFINING)
            if detail:
                self.capsule.set_status_text(detail)

    def _on_daemon_error(self, err_msg: str) -> None:
        logger.log("Daemon Error", err_msg)
        self.capsule.set_status_text("Daemon Error")

    def _on_recording_stopped(self) -> None:
        logger.log("Main Thin Client", "Hotkey Released -> Stopping Audio Stream & Requesting Refine")
        if not self.tray_app.is_enabled():
            return

        self.audio_recorder.stop()
        self.capsule.set_state(FloatingCapsule.STATE_REFINING)
        self.ws_worker.send_stop()

        if self._refine_timer:
            self._refine_timer.stop()
        self._refine_timer = QTimer(self)
        self._refine_timer.setSingleShot(True)
        self._refine_timer.timeout.connect(self._on_refine_safety_timeout)
        self._refine_timer.start(10000)

    def _on_refine_safety_timeout(self) -> None:
        if self.capsule.current_state == FloatingCapsule.STATE_REFINING:
            logger.log("Main Thin Client Warning", "Refine safety timeout reached (10s). Resetting capsule UI to IDLE.")
            self.capsule.hide_capsule()

    def _on_processing_finished(self, text: str, meta: Dict[str, Any]) -> None:
        if self._refine_timer:
            self._refine_timer.stop()
            self._refine_timer = None

        asr_p = meta.get("asr_provider", "(unknown)")
        asr_proxy = meta.get("asr_proxy", "DIRECT")
        raw_text = meta.get("raw_text", "")
        llm_p = meta.get("llm_provider", "(unknown)")
        llm_m = meta.get("llm_model", "(default)")
        llm_proxy = meta.get("llm_proxy", "DIRECT")
        refined_text = text

        print(
            "\n" + "=" * 80 + "\n"
            f" 🎤 语音输入全流程端到端审计日志 (End-to-End Execution Trace)\n"
            + "=" * 80 + "\n"
            f" 🎙️  ASR 识别阶段:\n"
            f"     • 服务商 (Provider): {asr_p}\n"
            f"     • 网络代理 (Proxy):    {asr_proxy}\n"
            f"     • 原始识别文本 (Raw ASR): '{raw_text}'\n\n"
            f" 🤖 LLM 精修阶段:\n"
            f"     • 服务商 (Provider): {llm_p}\n"
            f"     • 模型名称 (Model):   {llm_m}\n"
            f"     • 网络代理 (Proxy):    {llm_proxy}\n"
            f"     • 投喂原始文本 (Input): '{raw_text}'\n"
            f"     • 精修最终输出 (Output): '{refined_text}'\n"
            + "=" * 80,
            flush=True
        )

        logger.log("Main Thin Client", f"Refined text received from Daemon -> Injecting text: '{text}'")
        if text.strip():
            self.injector.inject(text)
            self.capsule.set_status_text("Copied/Injected")
        self.capsule.hide_capsule()

    def _open_settings(self) -> None:
        if not hasattr(self, 'settings_window') or self.settings_window is None:
            self.settings_window = SettingsWindow(self.config_manager)
            self.settings_window.config_saved.connect(self._on_settings_saved)
        self.settings_window.show()
        self.settings_window.raise_()
        self.settings_window.activateWindow()

    def _on_settings_saved(self) -> None:
        logger.log("Main", "Settings saved in UI. Restarting hotkey listener & updating Daemon...")
        self.hotkey_listener.stop()
        self.hotkey_listener = HotkeyListener(self.config_manager.get("hotkey", default="Key.ctrl_r"))
        self.hotkey_listener.recording_started.connect(self._on_recording_started)
        self.hotkey_listener.recording_stopped.connect(self._on_recording_stopped)
        self.hotkey_listener.start()

        i18n.set_language(self.config_manager.get("language", default="auto"))
        self.capsule.set_position(self.config_manager.get("ui", "position", default="bottom_center"))
        apply_proxy_config(self.config_manager.get("proxy", default={}))

        try:
            requests.put(f"{DEFAULT_DAEMON_URL}/api/v1/config", json=self.config_manager.config, timeout=2, proxies={"http": None, "https": None})
        except Exception as e:
            logger.log("Main Error", f"Failed to sync updated config to Daemon: {e}")

    def _quit_app(self) -> None:
        logger.log("Main", "Quitting application...")
        self.hotkey_listener.stop()
        stop_ollama_server()
        self.ws_worker.stop()
        self.daemon_manager.stop_daemon()
        QApplication.quit()

def main() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    controller = VoiceInputController()
    controller.start()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
