import pytest
import json
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from src.backend.main_daemon import app, core_engine

client = TestClient(app)

def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "engine_state" in data
    assert "asr_provider" in data
    assert "llm_provider" in data

def test_get_and_update_config_endpoints():
    get_res = client.get("/api/v1/config")
    assert get_res.status_code == 200
    orig_config = get_res.json()
    assert isinstance(orig_config, dict)

    update_res = client.put("/api/v1/config", json={"language": "en"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "success"
    assert update_res.json()["config"]["language"] == "en"

def test_websocket_voice_session_flow():
    mock_asr = MagicMock()
    mock_asr.finish.return_value = "WebSocket 完整集成测试"
    mock_llm = MagicMock()
    mock_llm.refine.return_value = "WebSocket 完整集成测试。"

    with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
        core_engine.llm_refiner = mock_llm
        with client.websocket_connect("/ws/v1/voice-session") as websocket:
            # 1. 发送 session_start
            websocket.send_text(json.dumps({
                "type": "session_start",
                "payload": {}
            }))

            # 接收状态变更
            msg1 = json.loads(websocket.receive_text())
            assert msg1["type"] == "status_change"
            assert msg1["payload"]["state"] == "PREPARING"

            msg2 = json.loads(websocket.receive_text())
            assert msg2["type"] == "status_change"
            assert msg2["payload"]["state"] == "LISTENING"

            # 2. 发送二进制音频帧
            websocket.send_bytes(b"\x00\x00" * 800)

            # 3. 发送 session_stop
            websocket.send_text(json.dumps({
                "type": "session_stop"
            }))

            # 接收 REFINING 状态、session_complete 以及 IDLE 状态
            messages = []
            for _ in range(3):
                messages.append(json.loads(websocket.receive_text()))

            msg_types = [m["type"] for m in messages]
            assert "status_change" in msg_types
            assert "session_complete" in msg_types

            session_complete_msg = next(m for m in messages if m["type"] == "session_complete")
            assert session_complete_msg["payload"]["refined_text"] == "WebSocket 完整集成测试。"
