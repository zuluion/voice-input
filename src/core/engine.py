import asyncio
from typing import Optional, Dict, Any
from src.core.event_bus import EventBus
from src.config import ConfigManager
from src.asr import create_asr_provider
from src.refine.llm import LLMRefiner
from src.utils.logger import logger

class CoreEngine:
    """
    无头核心业务引擎 (Headless Core Engine)，解耦 PySide6 UI/Qt 依赖，
    管理语音会话生命周期、ASR 流式交互与 LLM 文本精修。
    """
    STATE_IDLE = "IDLE"
    STATE_PREPARING = "PREPARING"
    STATE_LISTENING = "LISTENING"
    STATE_REFINING = "REFINING"

    EVENT_STATE_CHANGED = "state_changed"
    EVENT_ASR_PARTIAL = "asr_partial"
    EVENT_REFINED_TEXT = "refined_text"
    EVENT_ERROR = "error"

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.event_bus = EventBus()
        self.state = self.STATE_IDLE
        self.current_asr = None
        self.llm_refiner = LLMRefiner(self.config_manager.get("llm", default={}))

    def _set_state(self, new_state: str, detail: str = "") -> None:
        self.state = new_state
        logger.log("CoreEngine State", f"State switched to {new_state} {detail}")
        self.event_bus.emit(self.EVENT_STATE_CHANGED, new_state, detail)

    def start_session(self, override_asr_provider: Optional[str] = None) -> None:
        """开始语音会话 (准备 ASR 链接)"""
        if self.state != self.STATE_IDLE:
            logger.log("CoreEngine", "Session start requested while not IDLE, resetting...")

        self._set_state(self.STATE_PREPARING)
        provider_name = override_asr_provider or self.config_manager.get("asr", "provider", default="xiaomi_mimo")
        asr_cfg = self.config_manager.get("asr", default={})

        self.current_asr = create_asr_provider(provider_name, asr_cfg)

        # 绑定 ASR 回调 (当前适配器使用 Qt Signal 或 Direct Connection)
        if hasattr(self.current_asr, "text_updated"):
            self.current_asr.text_updated.connect(self._on_asr_text_updated)
        if hasattr(self.current_asr, "error_occurred"):
            self.current_asr.error_occurred.connect(self._on_asr_error)

        self.current_asr.connect()
        self._set_state(self.STATE_LISTENING)

    def process_audio_chunk(self, chunk: bytes) -> None:
        """接收并转发音频分片"""
        if self.state == self.STATE_LISTENING and self.current_asr:
            self.current_asr.send_audio_chunk(chunk)

    def stop_session_and_refine(self) -> str:
        """停止语音录制，提交 ASR 最终文本并调用 LLM 精修 (同步阻塞或直接返回)"""
        if self.state != self.STATE_LISTENING:
            return ""

        self._set_state(self.STATE_REFINING, "正在精修文本...")
        raw_text = ""
        if self.current_asr:
            raw_text = self.current_asr.finish()

        logger.log("CoreEngine ASR", f"Raw Recognized Text: '{raw_text}'")

        if not raw_text.strip():
            self._set_state(self.STATE_IDLE)
            self.event_bus.emit(self.EVENT_REFINED_TEXT, "")
            return ""

        refined_text = self.llm_refiner.refine(raw_text)
        logger.log("CoreEngine LLM", f"Refined Output Text: '{refined_text}'")

        self.event_bus.emit(self.EVENT_REFINED_TEXT, refined_text)
        self._set_state(self.STATE_IDLE)
        return refined_text

    async def stop_session_and_refine_async(self) -> str:
        """异步方式处理停止录音与 LLM 精修"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self.stop_session_and_refine)

    def _on_asr_text_updated(self, text: str, is_final: bool) -> None:
        if text:
            self.event_bus.emit(self.EVENT_ASR_PARTIAL, text, is_final)

    def _on_asr_error(self, err_msg: str) -> None:
        logger.log("CoreEngine ASR Error", err_msg)
        self.event_bus.emit(self.EVENT_ERROR, err_msg)
