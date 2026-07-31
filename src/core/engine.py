import asyncio
from typing import Optional, Dict, Any
from src.config import ConfigManager
from src.core.event_bus import EventBus
from src.asr import create_asr_provider, BaseASRProvider
from src.refine.llm import LLMRefiner
from src.utils.logger import logger
from src.utils.proxy import get_current_proxy_str

class CoreEngine:
    """
    无头核心引擎 (Headless Core Engine)
    状态机、事件驱动流转、ASR 适配器管理与 LLM 文本精修全流程审计
    """
    STATE_IDLE = "IDLE"
    STATE_PREPARING = "PREPARING"
    STATE_LISTENING = "LISTENING"
    STATE_REFINING = "REFINING"

    EVENT_STATE_CHANGED = "engine_state_changed"
    EVENT_ASR_PARTIAL = "asr_partial_text"
    EVENT_REFINED_TEXT = "llm_refined_text"
    EVENT_ERROR = "engine_error"

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_manager = config_manager or ConfigManager()
        self.event_bus = EventBus()
        self.state = self.STATE_IDLE
        self.current_asr: Optional[BaseASRProvider] = None
        self.llm_refiner = LLMRefiner(self.config_manager.get("llm", default={}))
        self.last_trace_meta: Dict[str, Any] = {}

    def _set_state(self, new_state: str, detail: str = "") -> None:
        if self.state != new_state:
            old_state = self.state
            self.state = new_state
            logger.log("CoreEngine State", f"State switched from {old_state} -> {new_state} ({detail})")
            self.event_bus.emit(self.EVENT_STATE_CHANGED, new_state, detail)

    def start_session(self, override_asr_provider: Optional[str] = None) -> bool:
        """开启一次新的语音识别会话"""
        if self.state != self.STATE_IDLE:
            logger.log("CoreEngine", f"Cannot start session in state '{self.state}'. Forcing reset to IDLE first...")
            self.stop_session_and_refine()

        self._set_state(self.STATE_PREPARING, "正在准备麦克风与 ASR 引擎...")
        
        asr_p = override_asr_provider or self.config_manager.get("asr", "provider", default="xiaomi_mimo")
        asr_cfg = self.config_manager.get("asr", default={})

        try:
            if self.current_asr:
                try:
                    self.current_asr.disconnect()
                except Exception as clean_err:
                    logger.log("CoreEngine Clean Warning", f"Error disconnecting previous ASR provider: {clean_err}")
                self.current_asr = None

            self.current_asr = create_asr_provider(asr_p, asr_cfg)
            self.current_asr.on_partial_result = self._on_asr_text_updated
            self.current_asr.on_error = self._on_asr_error
            self.current_asr.connect()
            self._set_state(self.STATE_LISTENING, "正在监听麦克风输入...")
            return True
        except Exception as e:
            err_msg = f"Failed to start ASR provider '{asr_p}': {e}"
            logger.log("CoreEngine Error", err_msg)
            self.event_bus.emit(self.EVENT_ERROR, err_msg)
            self._set_state(self.STATE_IDLE)
            return False



    def process_audio_chunk(self, chunk: bytes) -> None:
        """处理由客户端推送进来的二进制 PCM 音频块"""
        if self.state in [self.STATE_PREPARING, self.STATE_LISTENING] and self.current_asr:
            if self.state == self.STATE_PREPARING:
                self._set_state(self.STATE_LISTENING, "收到音频数据块...")
            self.current_asr.send_audio_chunk(chunk)

    def stop_session_and_refine(self) -> str:
        """
        停止语音录制，提交 ASR 最终文本，调用 LLM 精修并生成全流程审计元数据 (保持 100% 纯 str 接口兼容)
        """
        if self.state == self.STATE_IDLE:
            return ""

        old_state = self.state
        self._set_state(self.STATE_REFINING, "正在精修文本...")
        raw_text = ""

        active_asr = self.config_manager.get("asr", "provider", default="xiaomi_mimo")
        active_llm = self.config_manager.get("llm", "provider", default="local")
        proxy_str = get_current_proxy_str()

        llm_model_val = getattr(self.llm_refiner, "model", "default")
        if not isinstance(llm_model_val, str):
            llm_model_val = "default"

        self.last_trace_meta = {
            "asr_provider": active_asr,
            "asr_proxy": proxy_str if proxy_str else "DIRECT",
            "raw_text": "",
            "llm_provider": active_llm,
            "llm_model": llm_model_val,
            "llm_proxy": "DIRECT" if active_llm == "local" else (proxy_str if proxy_str else "DIRECT"),
            "refined_text": ""
        }


        try:
            if self.current_asr and old_state in [self.STATE_PREPARING, self.STATE_LISTENING]:
                raw_text = self.current_asr.finish()
        except Exception as e:
            logger.log("CoreEngine ASR Error", f"Exception during ASR finish: {e}")

        self.last_trace_meta["raw_text"] = raw_text
        logger.log("CoreEngine ASR", f"Raw Recognized Text: '{raw_text}'")

        if not raw_text.strip():
            logger.log("CoreEngine", "No raw ASR text captured. Resetting engine to IDLE...")
            self._set_state(self.STATE_IDLE)
            self.event_bus.emit(self.EVENT_REFINED_TEXT, "")
            return ""

        refined_text = raw_text
        try:
            refined_text = self.llm_refiner.refine(raw_text)
            logger.log("CoreEngine LLM", f"Refined Output Text: '{refined_text}'")
        except Exception as e:
            logger.log("CoreEngine LLM Error", f"Exception during LLM refine: {e}. Falling back to raw text.")

        self.last_trace_meta["refined_text"] = refined_text
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
