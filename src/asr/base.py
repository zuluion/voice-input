from PySide6.QtCore import QObject, Signal

class BaseASRProvider(QObject):
    text_updated = Signal(str, bool)  # (text, is_final)
    error_occurred = Signal(str)

    def __init__(self, config: dict = None) -> None:
        super().__init__()
        self.config = config or {}

    def connect(self) -> None:
        pass

    def send_audio_chunk(self, data: bytes) -> None:
        pass

    def finish(self) -> str:
        return ""
