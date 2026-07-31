import asyncio
import json
from typing import Dict, Any, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from src.config import ConfigManager
from src.core.engine import CoreEngine
from src.refine.llm import LLMRefiner
from src.utils.webdav import WebDAVSync
from src.utils.logger import logger

app = FastAPI(
    title="Voice Input Headless Core Daemon",
    description="前后端分离架构下的无头后端守护进程，提供 RESTful 控制面与 WebSocket 实时流通道。",
    version="1.0.0"
)

config_manager = ConfigManager()
core_engine = CoreEngine(config_manager)

@app.get("/api/v1/health")
async def get_health_status() -> Dict[str, Any]:
    """检查后端守护进程运行健康状态与当前配置概要"""
    return {
        "status": "ok",
        "engine_state": core_engine.state,
        "asr_provider": config_manager.get("asr", "provider", default="xiaomi_mimo"),
        "llm_provider": config_manager.get("llm", "provider", default="ollama"),
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
        # 重新实例化 llm_refiner
        core_engine.llm_refiner = LLMRefiner(config_manager.get("llm", default={}))
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

    # 注册事件总线通知转发给 WebSocket 客户端
    async def on_state_changed(state: str, detail: str) -> None:
        await websocket.send_text(json.dumps({
            "type": "status_change",
            "payload": {"state": state, "detail": detail}
        }))

    async def on_asr_partial(text: str, is_final: bool) -> None:
        await websocket.send_text(json.dumps({
            "type": "asr_partial_result",
            "payload": {"text": text, "is_final": is_final}
        }))

    async def on_error(err_msg: str) -> None:
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
                    override_asr = data.get("payload", {}).get("override_config", {}).get("asr_provider")
                    core_engine.start_session(override_asr_provider=override_asr)

                elif msg_type == "session_stop":
                    refined_text = await core_engine.stop_session_and_refine_async()
                    await websocket.send_text(json.dumps({
                        "type": "session_complete",
                        "payload": {
                            "refined_text": refined_text
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

def start_daemon(host: str = "127.0.0.1", port: int = 28080) -> None:
    """本地拉起 Daemon 守护进程"""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")

if __name__ == "__main__":
    start_daemon()
