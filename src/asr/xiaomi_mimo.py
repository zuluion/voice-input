import base64
import io
import wave
import requests
from src.asr.base import BaseASRProvider

class XiaomiMiMoASRProvider(BaseASRProvider):
    def __init__(self, config: dict = None) -> None:
        super().__init__(config)
        self.api_key = self.config.get("api_key", "")
        self.base_url = self.config.get("base_url", "https://api.xiaomimimo.com/v1").rstrip("/")
        self.model = self.config.get("model", "mimo-v2.5-asr")
        self.pcm_chunks = bytearray()

    def connect(self) -> None:
        self.pcm_chunks = bytearray()

    def send_audio_chunk(self, data: bytes) -> None:
        self.pcm_chunks.extend(data)

    def finish(self) -> str:
        if not self.pcm_chunks:
            print("[Xiaomi MiMo ASR] No audio PCM chunks captured.")
            return ""

        print(f"[Xiaomi MiMo ASR] Processing {len(self.pcm_chunks)} bytes of PCM audio...")

        # Convert raw PCM to WAV bytes
        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)  # 16-bit
            wf.setframerate(16000)
            wf.writeframes(self.pcm_chunks)
        wav_bytes = wav_io.getvalue()

        # Build payload according to Xiaomi MiMo API format
        b64_audio = base64.b64encode(wav_bytes).decode('utf-8')
        data_url = f"data:audio/wav;base64,{b64_audio}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_url
                            }
                        }
                    ]
                }
            ]
        }

        url = f"{self.base_url}/chat/completions"
        try:
            print(f"[Xiaomi MiMo ASR] Sending POST request to {url}...")
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            print(f"[Xiaomi MiMo ASR] Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                choices = res_json.get("choices", [])
                if choices:
                    text = choices[0].get("message", {}).get("content", "").strip()
                    print(f"[Xiaomi MiMo ASR] Recognized text: '{text}'")
                    self.text_updated.emit(text, True)
                    return text
            else:
                print(f"[Xiaomi MiMo ASR] Primary endpoint failed ({resp.status_code}): {resp.text}")
        except Exception as e:
            print(f"[Xiaomi MiMo ASR] Primary endpoint exception: {e}")

        # Fallback to audio/transcriptions endpoint
        try:
            tr_url = f"{self.base_url}/audio/transcriptions"
            print(f"[Xiaomi MiMo ASR] Trying fallback endpoint: {tr_url}...")
            files = {"file": ("audio.wav", wav_bytes, "audio/wav")}
            data = {"model": self.model}
            tr_headers = {"Authorization": f"Bearer {self.api_key}"}
            resp = requests.post(tr_url, headers=tr_headers, files=files, data=data, timeout=12)
            print(f"[Xiaomi MiMo ASR] Fallback response status: {resp.status_code}")
            if resp.status_code == 200:
                text = resp.json().get("text", "").strip()
                print(f"[Xiaomi MiMo ASR] Recognized text (fallback): '{text}'")
                self.text_updated.emit(text, True)
                return text
            else:
                print(f"[Xiaomi MiMo ASR] Fallback endpoint failed ({resp.status_code}): {resp.text}")
                err_msg = f"Xiaomi MiMo ASR Error ({resp.status_code}): {resp.text}"
                self.error_occurred.emit(err_msg)
                return ""
        except Exception as ex:
            err_msg = f"Xiaomi MiMo ASR Fallback Exception: {ex}"
            print(f"[Xiaomi MiMo ASR] {err_msg}")
            self.error_occurred.emit(err_msg)
            return ""
