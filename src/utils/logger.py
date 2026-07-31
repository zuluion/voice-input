import os
from datetime import datetime

class AppLogger:
    _instance = None

    def __init__(self) -> None:
        self.enabled = False
        self.log_dir = None

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
            print(f"[AppLogger] Debug mode ENABLED. Logging to directory: {self.log_dir}")
        else:
            self.log_dir = None
            print("[AppLogger] Debug mode DISABLED. Plaintext logging turned off.")

    def log(self, tag: str, message: str) -> None:
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        formatted = f"[{ts}] [{tag}] {message}"
        try:
            print(formatted, flush=True)
        except Exception:
            try:
                import sys
                encoding = getattr(sys.stdout, "encoding", "utf-8") or "utf-8"
                safe_str = formatted.encode(encoding, errors="replace").decode(encoding, errors="replace")
                sys.stdout.write(safe_str + "\n")
                sys.stdout.flush()
            except Exception:
                pass

        if self.enabled and self.log_dir:
            today_str = datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(self.log_dir, f"voice_input_{today_str}.log")
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(formatted + "\n")
            except Exception as e:
                try:
                    print(f"[AppLogger Error] {e}")
                except Exception:
                    pass


logger = AppLogger.get_instance()
