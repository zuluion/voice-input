import os
import sys
from datetime import datetime

class StdoutTee:
    def __init__(self, original_stdout, logger_inst):
        self.original_stdout = original_stdout
        self.logger_inst = logger_inst
        self._buffer = ""

    def isatty(self):
        if self.original_stdout and hasattr(self.original_stdout, "isatty"):
            try:
                return self.original_stdout.isatty()
            except Exception:
                return False
        return False

    def write(self, s):
        if self.original_stdout:
            try:
                self.original_stdout.write(s)
                self.original_stdout.flush()
            except Exception:
                pass

        if self.logger_inst and self.logger_inst.enabled and self.logger_inst.log_dir:
            self._buffer += s
            while "\n" in self._buffer:
                line, self._buffer = self._buffer.split("\n", 1)
                line = line.rstrip("\r")
                if line and not line.startswith("[20") and not line.startswith("[AppLogger]"):
                    # 给捕获到的非 AppLogger 标准控制台输出补齐时间戳标签并打日志文件
                    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    formatted = f"[{ts}] [Console] {line}"
                    self.logger_inst._write_to_file(formatted)

    def flush(self):
        if self.original_stdout:
            try:
                self.original_stdout.flush()
            except Exception:
                pass

    def __getattr__(self, name):
        if self.original_stdout and hasattr(self.original_stdout, name):
            return getattr(self.original_stdout, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

class AppLogger:
    _instance = None

    def __init__(self) -> None:
        self.enabled = False
        self.log_dir = None
        self._tee_active = False
        self._original_stdout = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = AppLogger()
        return cls._instance

    def configure(self, debug_config: dict, config_path: str = None) -> None:
        self.enabled = debug_config.get("enabled", False)
        if self.enabled:
            if config_path:
                base = os.path.dirname(os.path.abspath(config_path))
            else:
                base = os.getcwd()
            self.log_dir = os.path.join(base, "logs")
            os.makedirs(self.log_dir, exist_ok=True)

            if not self._tee_active:
                self._original_stdout = sys.stdout
                sys.stdout = StdoutTee(self._original_stdout, self)
                self._tee_active = True

            print(f"[AppLogger] Debug mode ENABLED. Logging directory: {self.log_dir}")
        else:
            self.log_dir = None
            if self._tee_active and self._original_stdout:
                sys.stdout = self._original_stdout
                self._tee_active = False
            print("[AppLogger] Debug mode DISABLED. Plaintext logging turned off.")

    def _write_to_file(self, formatted_str: str) -> None:
        if self.enabled and self.log_dir:
            today_str = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(self.log_dir, f"voice_input_{today_str}.log")
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(formatted_str + "\n")
            except Exception:
                pass

    def log(self, tag: str, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{ts}] [{tag}] {message}"

        # 写入调试日志文件
        self._write_to_file(formatted)

        # 打印至控制台
        out = self._original_stdout if (self._tee_active and self._original_stdout) else sys.stdout
        if out is not None:
            try:
                out.write(formatted + "\n")
                out.flush()
            except Exception:
                try:
                    encoding = getattr(out, "encoding", "utf-8") or "utf-8"
                    safe_str = formatted.encode(encoding, errors="replace").decode(encoding, errors="replace")
                    out.write(safe_str + "\n")
                    out.flush()
                except Exception:
                    pass


logger = AppLogger.get_instance()
