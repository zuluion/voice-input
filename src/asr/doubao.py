import io
import wave
import json
import requests
from src.asr.base import BaseASRProvider
from src.utils.logger import logger

class DoubaoASRProvider(BaseASRProvider):
    def __init__(self, config: dict = None) -> None:
        super().__init__(config)
        self.app_id = self.config.get("app_id", "")
        self.access_token = self.config.get("access_token", "")
        self.cluster = self.config.get("cluster", "volcengine_input_common")
        self.pcm_chunks = bytearray()

    def connect(self) -> None:
        self.pcm_chunks = bytearray()

    def send_audio_chunk(self, data: bytes) -> None:
        self.pcm_chunks.extend(data)

    def finish(self) -> str:
        if not self.pcm_chunks:
            logger.log("Doubao ASR", "No audio PCM chunks captured.")
            return ""

        if not self.app_id or not self.access_token:
            err_msg = "Doubao ASR Error: Missing app_id or access_token in config."
            logger.log("Doubao ASR", err_msg)
            self.error_occurred.emit(err_msg)
            return ""

        logger.log("Doubao ASR", f"Processing {len(self.pcm_chunks)} bytes of PCM audio...")

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(self.pcm_chunks)
        wav_bytes = wav_io.getvalue()

        url = "https://openspeech.bytedance.com/api/v1/vc/asr"
        headers = {
            "Authorization": f"Bearer; {self.access_token}",
            "Content-Type": "application/json"
        }
        import base64
        b64_audio = base64.b64encode(wav_bytes).decode('utf-8')
        payload = {
            "app": {"appid": self.app_id, "token": self.access_token, "cluster": self.cluster},
            "user": {"uid": "user_voice_input"},
            "audio": {"format": "wav", "audio_data": b64_audio}
        }

        try:
            logger.log("Doubao ASR", f"Sending POST request to {url}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            logger.log("Doubao ASR", f"Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                text = res_json.get("result", [{}])[0].get("text", "").strip()
                logger.log("Doubao ASR", f"Recognized text: '{text}'")
                self.text_updated.emit(text, True)
                return text
            else:
                err_msg = f"Doubao ASR Error ({resp.status_code}): {resp.text}"
                logger.log("Doubao ASR", err_msg)
                self.error_occurred.emit(err_msg)
                return ""
        except Exception as e:
            err_msg = f"Doubao ASR Exception: {str(e)}"
            logger.log("Doubao ASR", err_msg)
            self.error_occurred.emit(err_msg)
            return ""
