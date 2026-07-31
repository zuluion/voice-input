import pytest
from unittest.mock import MagicMock, patch
from typer.testing import CliRunner
from src.cli.main import app

runner = CliRunner()

def test_cli_config_show():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "Voice Input Global Configuration" in result.stdout

def test_cli_config_set():
    result = runner.invoke(app, ["config", "set", "language", "zh_CN"])
    assert result.exit_code == 0
    assert "Updated configuration key 'language' -> zh_CN" in result.stdout

def test_cli_daemon_status_mock():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "ok",
        "engine_state": "IDLE",
        "asr_provider": "xiaomi_mimo",
        "llm_provider": "ollama",
        "language": "auto"
    }

    with patch("requests.get", return_value=mock_response):
        result = runner.invoke(app, ["daemon", "status"])
        assert result.exit_code == 0
        assert "Core Backend Daemon is Running" in result.stdout

def test_cli_record_full_flow_raw_output():
    mock_asr = MagicMock()
    mock_asr.finish.return_value = "CLI 全流程测试识别文本"
    mock_llm = MagicMock()
    mock_llm.refine.return_value = "CLI 全流程测试识别文本。"

    with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
        with patch("src.core.engine.LLMRefiner", return_value=mock_llm):
            with patch("src.audio.recorder.AudioRecorder", side_effect=Exception("No mic in CI")):
                result = runner.invoke(app, ["record", "--duration", "1", "--raw"])
                assert result.exit_code == 0
                assert "CLI 全流程测试识别文本。" in result.stdout

def test_cli_record_full_flow_normal_output():
    mock_asr = MagicMock()
    mock_asr.finish.return_value = "命令行终端录音测试"
    mock_llm = MagicMock()
    mock_llm.refine.return_value = "命令行终端录音测试。"

    with patch("src.core.engine.create_asr_provider", return_value=mock_asr):
        with patch("src.core.engine.LLMRefiner", return_value=mock_llm):
            with patch("src.audio.recorder.AudioRecorder", side_effect=Exception("No mic in CI")):
                result = runner.invoke(app, ["record", "--duration", "1", "--no-copy"])
                assert result.exit_code == 0
                assert "命令行终端录音测试。" in result.stdout
