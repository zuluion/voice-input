import sys
import os

# Guard against PyInstaller --noconsole mode where sys.stdout and sys.stderr are None
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w', encoding='utf-8', errors='ignore')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w', encoding='utf-8', errors='ignore')


import asyncio
import json
from typing import Dict, Any, Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from src.config import ConfigManager, DEFAULT_DAEMON_HOST, DEFAULT_DAEMON_PORT
from src.core.engine import CoreEngine
from src.refine.llm import LLMRefiner
from src.utils.webdav import WebDAVSync
from src.utils.logger import logger
from src.utils.proxy import get_current_proxy_str

app = FastAPI(
    title="Voice Input Headless Core Daemon",
    description="前后端分离架构下的无头后端守护进程，提供 RESTful 控制面与 WebSocket 实时流通道。",
    version="1.0.0"
)

config_manager = ConfigManager()
logger.configure(config_manager.get("debug", default={}), config_manager.config_path)
core_engine = CoreEngine(config_manager)

@app.get("/api/v1/health")
async def get_health_status() -> Dict[str, Any]:
    """检查后端守护进程运行健康状态与当前配置概要"""
    return {
        "status": "ok",
        "engine_state": core_engine.state,
        "asr_provider": config_manager.get("asr", "provider", default="xiaomi_mimo"),
        "llm_provider": config_manager.get("llm", "provider", default="local"),
        "language": config_manager.get("language", default="auto")
    }

@app.get("/api/v1/config")
async def get_config() -> Dict[str, Any]:
    """获取当前全局配置对象"""
    return config_manager.config

@app.put("/api/v1/config")
async def update_config(new_config: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """更新全局配置项并实时生效"""
    try:
        config_manager.config.update(new_config)
        config_manager.save_config()
        # 热重载 Logger 与 LLM Refiner
        logger.configure(config_manager.get("debug", default={}), config_manager.config_path)
        core_engine.llm_refiner = LLMRefiner(config_manager.get("llm", default={}))
        asr_p = config_manager.get("asr", "provider", default="xiaomi_mimo")
        llm_p = config_manager.get("llm", "provider", default="local")
        logger.log("Daemon Config", f"Config updated & hot-reloaded via REST API. Active ASR: '{asr_p}', Active LLM: '{llm_p}'")
        return {"status": "success", "config": config_manager.config}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update config: {e}")

@app.post("/api/v1/config/sync")
async def trigger_webdav_sync() -> Dict[str, Any]:
    """手动触发 WebDAV 增量同步"""
    webdav_cfg = config_manager.get("webdav", default={})
    if not webdav_cfg.get("enabled"):
        return {"status": "skipped", "message": "WebDAV sync is not enabled"}
    
    sync = WebDAVSync(webdav_cfg)
    loop = asyncio.get_running_loop()
    ok, msg = await loop.run_in_executor(None, sync.download_config, config_manager.config_path)
    
    if ok:
        config_manager.config = config_manager.load_config()
        return {"status": "success", "message": "Configuration successfully synced from WebDAV"}
    else:
        raise HTTPException(status_code=500, detail=f"WebDAV sync failed: {msg}")

@app.websocket("/ws/v1/voice-session")
async def voice_session_websocket(websocket: WebSocket) -> None:
    """
    双向 WebSocket 语音会话通道:
    - 接收 JSON 命令: session_start / session_stop
    - 接收二进制帧: PCM/Opus Audio Chunk
    - 推送 JSON 响应: status_change / asr_partial_result / session_complete
    """
    await websocket.accept()
    logger.log("Daemon WS", "Client connected to WebSocket voice session")

    current_loop = asyncio.get_running_loop()
    core_engine.event_bus.set_loop(current_loop)

    async def on_state_changed(state: str, detail: str) -> None:
        logger.log("Daemon WS", f"Broadcasting State Change -> '{state}' ({detail})")
        await websocket.send_text(json.dumps({
            "type": "status_change",
            "payload": {"state": state, "detail": detail}
        }))

    async def on_asr_partial(text: str, is_final: bool) -> None:
        logger.log("Daemon ASR", f"Live ASR Partial -> '{text}' (Final: {is_final})")
        await websocket.send_text(json.dumps({
            "type": "asr_partial_result",
            "payload": {"text": text, "is_final": is_final}
        }))

    async def on_error(err_msg: str) -> None:
        logger.log("Daemon Error", f"Broadcasting Error -> {err_msg}")
        await websocket.send_text(json.dumps({
            "type": "error",
            "payload": {"message": err_msg}
        }))

    core_engine.event_bus.subscribe(CoreEngine.EVENT_STATE_CHANGED, on_state_changed)
    core_engine.event_bus.subscribe(CoreEngine.EVENT_ASR_PARTIAL, on_asr_partial)
    core_engine.event_bus.subscribe(CoreEngine.EVENT_ERROR, on_error)

    try:
        while True:
            message = await websocket.receive()
            if "bytes" in message and message["bytes"]:
                # 音频数据帧
                core_engine.process_audio_chunk(message["bytes"])
            elif "text" in message and message["text"]:
                # 控制命令帧
                data = json.loads(message["text"])
                msg_type = data.get("type")

                if msg_type == "session_start":
                    if core_engine.state != CoreEngine.STATE_IDLE:
                        logger.log("Daemon Session Warning", f"Rejected 'session_start': Engine is currently in state '{core_engine.state}'")
                        await websocket.send_text(json.dumps({
                            "type": "error",
                            "payload": {"message": f"Session busy: Core engine is currently in state '{core_engine.state}'"}
                        }))
                        continue

                    override_asr = data.get("payload", {}).get("override_config", {}).get("asr_provider")
                    active_asr = override_asr or config_manager.get("asr", "provider", default="xiaomi_mimo")
                    active_llm = config_manager.get("llm", "provider", default="local")
                    proxy_str = get_current_proxy_str()
                    proxy_tag = f" [VIA PROXY: {proxy_str}]" if proxy_str else " [DIRECT]"

                    logger.log("Daemon Session", f"▶ Session Started{proxy_tag} | Active ASR: '{active_asr}' | Active LLM: '{active_llm}'")
                    core_engine.start_session(override_asr_provider=override_asr)

                elif msg_type == "session_stop":
                    logger.log("Daemon Session", "⏹ Session Stop command received. Processing audio & triggering LLM refinement...")
                    refined_text = await core_engine.stop_session_and_refine_async()
                    trace_meta = getattr(core_engine, "last_trace_meta", {})
                    logger.log("Daemon Session", f"✔ Session Completed. Final Text: '{refined_text}'")

                    await websocket.send_text(json.dumps({
                        "type": "session_complete",
                        "payload": {
                            "refined_text": refined_text,
                            "meta": trace_meta
                        }
                    }))

    except WebSocketDisconnect:
        logger.log("Daemon WS", "Client disconnected from WebSocket voice session")
    except Exception as e:
        logger.log("Daemon WS Error", f"WebSocket exception: {e}")
    finally:
        core_engine.event_bus.unsubscribe(CoreEngine.EVENT_STATE_CHANGED, on_state_changed)
        core_engine.event_bus.unsubscribe(CoreEngine.EVENT_ASR_PARTIAL, on_asr_partial)
        core_engine.event_bus.unsubscribe(CoreEngine.EVENT_ERROR, on_error)

def start_daemon(host: str = DEFAULT_DAEMON_HOST, port: int = DEFAULT_DAEMON_PORT) -> None:
    """本地拉起 Daemon 守护进程"""
    import sys
    import os
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w')

    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info", use_colors=False)


if __name__ == "__main__":
    start_daemon()
