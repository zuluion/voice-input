import os
import sys
import time
import subprocess
import requests
from typing import Optional
from src.utils.logger import logger

DEFAULT_DAEMON_URL = "http://127.0.0.1:28080"

class DaemonProcessManager:
    """
    负责桌面 GUI 自动托管管理无头 Daemon 子进程的生命周期:
    检查连通性、自动启动 Daemon、优雅停止 Daemon
    """
    def __init__(self, daemon_url: str = DEFAULT_DAEMON_URL) -> None:
        self.daemon_url = daemon_url.rstrip("/")
        self.process: Optional[subprocess.Popen] = None

    def is_daemon_running(self) -> bool:
        """检查 Daemon 是否已经在 127.0.0.1:28080 正常运行"""
        try:
            res = requests.get(f"{self.daemon_url}/api/v1/health", timeout=1.5, proxies={"http": None, "https": None})
            return res.status_code == 200 and res.json().get("status") == "ok"
        except Exception:
            return False

    def ensure_daemon_started(self) -> bool:
        """若 Daemon 未运行则自动在后台启动子进程"""
        if self.is_daemon_running():
            logger.log("DaemonManager", "Daemon is already running.")
            return True

        logger.log("DaemonManager", "Daemon not detected. Launching background process...")
        try:
            # 兼容打包环境与源码环境
            if getattr(sys, 'frozen', False):
                cmd = [sys.executable, "--headless-daemon"]
            else:
                cmd = [sys.executable, "-m", "src.backend.main_daemon"]

            # 创建隐蔽后台子进程
            creationflags = 0
            if sys.platform == "win32":
                creationflags = subprocess.CREATE_NO_WINDOW

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=creationflags
            )

            # 等待最多 5 秒让 Daemon 启动
            for _ in range(25):
                time.sleep(0.2)
                if self.is_daemon_running():
                    logger.log("DaemonManager", "Daemon started successfully!")
                    return True

            logger.log("DaemonManager", "Daemon process started but health check timed out.")
            return False

        except Exception as e:
            logger.log("DaemonManager Error", f"Failed to start daemon process: {e}")
            return False

    def stop_daemon(self) -> None:
        """停止托管的 Daemon 子进程"""
        if self.process and self.process.poll() is None:
            logger.log("DaemonManager", "Terminating managed daemon process...")
            try:
                self.process.terminate()
                self.process.wait(timeout=2)
            except Exception:
                self.process.kill()
            self.process = None
