import io
import wave
import requests
from src.asr.base import BaseASRProvider
from src.utils.logger import logger

class OpenAIHTTPASRProvider(BaseASRProvider):
    def __init__(self, config: dict = None) -> None:
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self.model = self.config.get("model", "whisper-1")
        self.pcm_chunks = bytearray()

    def connect(self) -> None:
        self.pcm_chunks = bytearray()

    def send_audio_chunk(self, data: bytes) -> None:
        self.pcm_chunks.extend(data)

    def finish(self) -> str:
        if not self.pcm_chunks:
            logger.log("OpenAI ASR", "No audio PCM chunks captured.")
            return ""

        logger.log("OpenAI ASR", f"Processing {len(self.pcm_chunks)} bytes of PCM audio...")

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(self.pcm_chunks)
        wav_bytes = wav_io.getvalue()

        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        files = {
            "file": ("audio.wav", wav_bytes, "audio/wav")
        }
        data = {
            "model": self.model
        }

        url = f"{self.base_url}/audio/transcriptions"
        try:
            logger.log("OpenAI ASR", f"Sending POST request to {url}...")
            resp = requests.post(url, headers=headers, files=files, data=data, timeout=12)
            logger.log("OpenAI ASR", f"Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                text = resp.json().get("text", "").strip()
                logger.log("OpenAI ASR", f"Recognized text: '{text}'")
                self.text_updated.emit(text, True)
                return text
            else:
                err_msg = f"OpenAI ASR Error ({resp.status_code}): {resp.text}"
                logger.log("OpenAI ASR", err_msg)
                self.error_occurred.emit(err_msg)
                return ""
        except Exception as e:
            err_msg = f"OpenAI ASR Exception: {str(e)}"
            logger.log("OpenAI ASR", err_msg)
            self.error_occurred.emit(err_msg)
            return ""
