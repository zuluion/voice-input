import random
import numpy as np
import sounddevice as sd
from PySide6.QtCore import QObject, Signal

BAR_WEIGHTS = [0.5, 0.8, 1.0, 0.75, 0.55]

class AudioRecorder(QObject):
    volume_changed = Signal(list)  # List[float] representing 5 normalized bar levels
    audio_chunk_ready = Signal(bytes)
    recording_ready = Signal()  # Emitted when microphone captures first audio frame
    error_occurred = Signal(str)  # Emitted when no microphone device is found or stream fails

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        self.is_recording = False
        self.audio_data = bytearray()
        self._prev_envelope = 0.0
        self._first_frame_emitted = False

    def start(self) -> None:
        self.audio_data = bytearray()
        self.is_recording = True
        self._prev_envelope = 0.0
        self._first_frame_emitted = False

        # Dynamic hotplug re-scan of audio devices every time user presses hotkey
        try:
            try:
                sd._terminate()
                sd._initialize()
            except Exception:
                pass

            devices = sd.query_devices()
            input_devices = [d for d in devices if d.get('max_input_channels', 0) > 0]
            if not input_devices:
                err_msg = "未检测到可用的麦克风/语音输入设备，请连接麦克风后再试！"
                print(f"[Audio Engine Error] {err_msg}")
                self.is_recording = False
                self.error_occurred.emit(err_msg)
                return
        except Exception as e:
            err_msg = f"麦克风设备检测异常: {str(e)}"
            print(f"[Audio Engine Error] {err_msg}")
            self.is_recording = False
            self.error_occurred.emit(err_msg)
            return

        def callback(indata, frames, time_info, status):
            if not self.is_recording:
                return

            if not self._first_frame_emitted:
                self._first_frame_emitted = True
                self.recording_ready.emit()

            pcm_bytes = indata.tobytes()
            self.audio_data.extend(pcm_bytes)
            self.audio_chunk_ready.emit(pcm_bytes)

            # RMS Calculation
            audio_samples = indata.flatten()
            if len(audio_samples) == 0:
                rms = 0.0
            else:
                rms = float(np.sqrt(np.mean(audio_samples.astype(np.float32) ** 2)))

            # Normalize RMS assuming int16 range 32768
            normalized_rms = min(1.0, rms / 32768.0 * 10.0)

            # Attack / Release Envelope Smoothing
            attack = 0.4
            release = 0.15
            if normalized_rms > self._prev_envelope:
                envelope = attack * normalized_rms + (1 - attack) * self._prev_envelope
            else:
                envelope = release * normalized_rms + (1 - release) * self._prev_envelope
            self._prev_envelope = envelope

            # Compute 5 bar heights with weights and random jitter
            bars = []
            for weight in BAR_WEIGHTS:
                jitter = random.uniform(-0.04, 0.04)
                val = max(0.0, min(1.0, envelope * weight + jitter))
                bars.append(val)

            self.volume_changed.emit(bars)

        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype='int16',
                callback=callback,
                blocksize=1024
            )
            self.stream.start()
        except Exception as e:
            err_msg = f"无法启动麦克风录音: {str(e)}"
            print(f"[Audio Engine Error] {err_msg}")
            self.is_recording = False
            self.error_occurred.emit(err_msg)

    def stop(self) -> bytes:
        self.is_recording = False
        if self.stream is not None:
            try:
                self.stream.stop()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        return bytes(self.audio_data)
