import unittest
from unittest.mock import patch, MagicMock
import numpy as np
from src.audio.recorder import AudioRecorder

class TestAudioRMSEnvelope(unittest.TestCase):
    @patch("sounddevice.InputStream")
    def test_sine_wave_volume(self, mock_input_stream):
        mock_stream_instance = MagicMock()
        mock_input_stream.return_value = mock_stream_instance

        recorder = AudioRecorder()
        received_bars = []

        def handle_bars(bars):
            received_bars.append(bars)

        recorder.volume_changed.connect(handle_bars)

        # Generate 16kHz sine wave audio chunk
        sample_rate = 16000
        t = np.linspace(0, 0.1, int(sample_rate * 0.1), endpoint=False)
        sine_wave = (np.sin(2 * np.pi * 440 * t) * 16000).astype(np.int16)

        recorder.start()

        # Retrieve the callback passed to InputStream
        callback = mock_input_stream.call_args[1]['callback']
        callback(sine_wave.reshape(-1, 1), len(sine_wave), None, None)

        recorder.stop()
        self.assertTrue(len(received_bars) > 0)
        self.assertEqual(len(received_bars[0]), 5)

if __name__ == '__main__':
    unittest.main()
