import pytest
import asyncio
from unittest.mock import MagicMock, patch
from src.core.engine import CoreEngine
from src.config import ConfigManager

def test_core_engine_initial_state():
    engine = CoreEngine()
    assert engine.state == CoreEngine.STATE_IDLE

def test_core_engine_session_lifecycle():
    engine = CoreEngine()
    state_changes = []

    def on_state_changed(state, detail):
        state_changes.append(state)

    engine.event_bus.subscribe(CoreEngine.EVENT_STATE_CHANGED, on_state_changed)

    mock_asr = MagicMock()
    mock_asr.finish.return_value = "测试语音识别结果"

    mock_llm = MagicMock()
    mock_llm.refine.return_value = "测试语音识别结果。"

    with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
        engine.llm_refiner = mock_llm

        engine.start_session()
        assert engine.state == CoreEngine.STATE_LISTENING

        engine.process_audio_chunk(b"\x00\x00" * 100)
        mock_asr.send_audio_chunk.assert_called_once()

        result = engine.stop_session_and_refine()

        assert result == "测试语音识别结果。"
        assert engine.state == CoreEngine.STATE_IDLE

        assert state_changes == [
            CoreEngine.STATE_PREPARING,
            CoreEngine.STATE_LISTENING,
            CoreEngine.STATE_REFINING,
            CoreEngine.STATE_IDLE
        ]

def test_core_engine_empty_asr_text():
    engine = CoreEngine()
    mock_asr = MagicMock()
    mock_asr.finish.return_value = ""

    with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
        engine.start_session()
        result = engine.stop_session_and_refine()

        assert result == ""
        assert engine.state == CoreEngine.STATE_IDLE

def test_core_engine_async_refine():
    async def _run():
        engine = CoreEngine()
        mock_asr = MagicMock()
        mock_asr.finish.return_value = "异步精修测试"
        mock_llm = MagicMock()
        mock_llm.refine.return_value = "异步精修测试。"

        with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
            engine.llm_refiner = mock_llm
            engine.start_session()
            result = await engine.stop_session_and_refine_async()
            assert result == "异步精修测试。"

    asyncio.run(_run())
