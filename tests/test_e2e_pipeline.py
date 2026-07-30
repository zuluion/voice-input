import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from PySide6.QtWidgets import QApplication
import sys

# Ensure QApplication is initialized for Qt tests
app = QApplication.instance() or QApplication(sys.argv)

from src.config import ConfigManager
from src.ui.capsule import FloatingCapsule
from src.refine.llm import LLMRefiner
from src.asr import create_asr_provider

class TestEndToEndPipeline(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cfg_path = os.path.join(self.test_dir, "config.json")
        self.config_manager = ConfigManager(self.cfg_path)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_capsule_positioning(self):
        capsule = FloatingCapsule()

        capsule.set_position("top_center")
        self.assertEqual(capsule.position, "top_center")

        capsule.set_position("center")
        self.assertEqual(capsule.position, "center")

        capsule.set_position("bottom_center")
        self.assertEqual(capsule.position, "bottom_center")

    @patch("requests.post")
    @patch("win32clipboard.OpenClipboard")
    @patch("win32clipboard.CloseClipboard")
    @patch("win32clipboard.GetClipboardData")
    def test_e2e_voice_input_pipeline(self, mock_get_clip, mock_close_clip, mock_open_clip, mock_post):
        # 1. Setup Mock ASR & LLM Responses
        mock_asr_resp = MagicMock()
        mock_asr_resp.status_code = 200
        mock_asr_resp.json.return_value = {
            "choices": [{"message": {"content": "今天去北京出差，不对，改成后天"}}]
        }

        mock_llm_resp = MagicMock()
        mock_llm_resp.status_code = 200
        mock_llm_resp.json.return_value = {
            "choices": [{"message": {"content": "后天去北京出差"}}]
        }

        def side_effect(url, **kwargs):
            if "xiaomimimo" in url or "audio" in url:
                return mock_asr_resp
            return mock_llm_resp

        mock_post.side_effect = side_effect

        # 2. Test Floating Capsule State Progression
        capsule = FloatingCapsule()
        self.assertEqual(capsule.current_state, FloatingCapsule.STATE_PREPARING)

        capsule.set_state(FloatingCapsule.STATE_PREPARING)
        self.assertEqual(capsule.status_text, "Preparing...")

        capsule.set_state(FloatingCapsule.STATE_LISTENING)
        self.assertEqual(capsule.status_text, "Listening...")

        # 3. Simulate ASR Processing
        asr_cfg = {
            "xiaomi_mimo": {
                "api_key": "test_mimo_key",
                "base_url": "https://api.xiaomimimo.com/v1",
                "model": "mimo-v2.5-asr"
            }
        }
        provider = create_asr_provider("xiaomi_mimo", asr_cfg)
        provider.connect()
        provider.send_audio_chunk(b"\x00\x00" * 1600)
        raw_asr_text = provider.finish()
        self.assertEqual(raw_asr_text, "今天去北京出差，不对，改成后天")

        # 4. Simulate LLM Refinement Pipeline
        capsule.set_state(FloatingCapsule.STATE_REFINING)
        self.assertEqual(capsule.status_text, "Refining...")

        llm_cfg = {
            "enabled": True,
            "provider": "openai",
            "openai": {
                "api_key": "test_openai_key",
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4o-mini"
            }
        }
        refiner = LLMRefiner(llm_cfg)
        final_text = refiner.refine(raw_asr_text)

        self.assertEqual(final_text, "后天去北京出差")

if __name__ == "__main__":
    unittest.main()
