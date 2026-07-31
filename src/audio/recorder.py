import random
import numpy as np
import sounddevice as sd
from typing import Callable, Optional, List, Dict, Any
from PySide6.QtCore import QObject, Signal

BAR_WEIGHTS = [0.5, 0.8, 1.0, 0.75, 0.55]

class AudioRecorder(QObject):
    volume_changed = Signal(list)
    audio_chunk_ready = Signal(bytes)
    recording_ready = Signal()
    error_occurred = Signal(str)

    def __init__(self, sample_rate: int = 16000, channels: int = 1) -> None:
        super().__init__()
        self.sample_rate = sample_rate
        self.channels = channels
        self.stream = None
        self.is_recording = False
        self.audio_data = bytearray()
        self._prev_envelope = 0.0
        self._first_frame_emitted = False

        # 纯 Python 回调支持 (无 Qt 事件循环环境使用)
        self.on_chunk_cb: Optional[Callable[[bytes], None]] = None
        self.on_volume_cb: Optional[Callable[[List[float]], None]] = None
        self.on_ready_cb: Optional[Callable[[], None]] = None
        self.on_error_cb: Optional[Callable[[str], None]] = None

    @staticmethod
    def get_input_device_name() -> str:
        """获取当前默认的输入麦克风设备名称"""
        try:
            default_device_idx = sd.default.device[0]
            if default_device_idx is not None and default_device_idx >= 0:
                dev_info = sd.query_devices(default_device_idx, 'input')
                return str(dev_info.get('name', '默认麦克风'))
            
            # 回退检索第一个有效 input 设备
            devices = sd.query_devices()
            for d in devices:
                if d.get('max_input_channels', 0) > 0:
                    return str(d.get('name', '未知名麦克风'))
            return "未检测到输入设备"
        except Exception:
            return "系统默认麦克风"

    def start(self) -> None:
        self.audio_data = bytearray()
        self.is_recording = True
        self._prev_envelope = 0.0
        self._first_frame_emitted = False

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
                self._emit_error(err_msg)
                return
        except Exception as e:
            err_msg = f"麦克风设备检测异常: {str(e)}"
            print(f"[Audio Engine Error] {err_msg}")
            self.is_recording = False
            self._emit_error(err_msg)
            return

        def callback(indata, frames, time_info, status):
            if not self.is_recording:
                return

            if not self._first_frame_emitted:
                self._first_frame_emitted = True
                self.recording_ready.emit()
                if self.on_ready_cb:
                    try:
                        self.on_ready_cb()
                    except Exception:
                        pass

            pcm_bytes = indata.tobytes()
            self.audio_data.extend(pcm_bytes)
            
            # Qt Signal 触发
            self.audio_chunk_ready.emit(pcm_bytes)
            # 纯 Python 回调触发 (确保无 Qt 循环环境 100% 收到音频块)
            if self.on_chunk_cb:
                try:
                    self.on_chunk_cb(pcm_bytes)
                except Exception as e:
                    print(f"[Audio Callback Error] {e}")

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

            # Compute 5 bar heights
            bars = []
            for weight in BAR_WEIGHTS:
                jitter = random.uniform(-0.04, 0.04)
                val = max(0.0, min(1.0, envelope * weight + jitter))
                bars.append(val)

            self.volume_changed.emit(bars)
            if self.on_volume_cb:
                try:
                    self.on_volume_cb(bars)
                except Exception:
                    pass

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
            self._emit_error(err_msg)

    def _emit_error(self, err_msg: str) -> None:
        self.error_occurred.emit(err_msg)
        if self.on_error_cb:
            try:
                self.on_error_cb(err_msg)
            except Exception:
                pass

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
