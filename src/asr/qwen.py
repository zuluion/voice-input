import io
import wave
import requests
from src.asr.base import BaseASRProvider
from src.utils.logger import logger

class QwenASRProvider(BaseASRProvider):
    def __init__(self, config: dict = None) -> None:
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.app_key = self.config.get("app_key", "")
        self.pcm_chunks = bytearray()

    def connect(self) -> None:
        self.pcm_chunks = bytearray()

    def send_audio_chunk(self, data: bytes) -> None:
        self.pcm_chunks.extend(data)

    def finish(self) -> str:
        if not self.pcm_chunks:
            logger.log("Qwen ASR", "No audio PCM chunks captured.")
            return ""

        if not self.api_key:
            err_msg = "Qwen ASR Error: Missing api_key in config."
            logger.log("Qwen ASR", err_msg)
            self.error_occurred.emit(err_msg)
            return ""

        logger.log("Qwen ASR", f"Processing {len(self.pcm_chunks)} bytes of PCM audio...")

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(self.pcm_chunks)
        wav_bytes = wav_io.getvalue()

        # DashScope OpenAI-compatible Audio API Endpoint
        url = "https://dashscope.aliyuncs.com/compatible-mode/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav")
        }
        data = {
            "model": "qwen-audio-asr"
        }

        try:
            logger.log("Qwen ASR", f"Sending POST request to {url}...")
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=12)
            logger.log("Qwen ASR", f"Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                text = resp.json().get("text", "").strip()
                logger.log("Qwen ASR", f"Recognized text: '{text}'")
                self.text_updated.emit(text, True)
                return text
            else:
                err_msg = f"Qwen ASR Error ({resp.status_code}): {resp.text}"
                logger.log("Qwen ASR", err_msg)
                self.error_occurred.emit(err_msg)
                return ""
        except Exception as e:
            err_msg = f"Qwen ASR Exception: {str(e)}"
            logger.log("Qwen ASR", err_msg)
            self.error_occurred.emit(err_msg)
            return ""
