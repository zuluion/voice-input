import pytest
import time
from unittest.mock import MagicMock, patch
from src.utils.daemon_process import DaemonProcessManager

def test_daemon_process_manager_mock():
    manager = DaemonProcessManager()
    
    # 模拟连通检查成功
    mock_res = MagicMock()
    mock_res.status_code = 200
    mock_res.json.return_value = {"status": "ok"}
    
    with patch("requests.get", return_value=mock_res):
        assert manager.is_daemon_running() is True

def test_daemon_process_manager_start_and_stop():
    manager = DaemonProcessManager()
    
    with patch("requests.get", return_value=MagicMock(status_code=200, json=lambda: {"status": "ok"})):
        # 已经在运行时不拉起新进程
        started = manager.ensure_daemon_started()
        assert started is True
        assert manager.process is None

    # 停止无崩溃
    manager.stop_daemon()

def test_main_headless_daemon_dispatch():
    import sys
    from src.main import main
    with patch.object(sys, 'argv', ['VoiceInput', '--headless-daemon']):
        with patch('src.backend.main_daemon.start_daemon') as mock_start_daemon:
            main()
            mock_start_daemon.assert_called_once()

