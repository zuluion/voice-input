import os
import shutil
import tempfile
import unittest
from datetime import datetime
from src.utils.logger import AppLogger

class TestAppLogger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cfg_path = os.path.join(self.test_dir, "config.json")
        self.logger = AppLogger()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_logger_disabled_mode(self):
        self.logger.configure({"enabled": False}, self.cfg_path)
        self.assertFalse(self.logger.enabled)
        self.logger.log("TEST", "Should not be logged to disk")

        log_dir = os.path.join(self.test_dir, "logs")
        self.assertFalse(os.path.exists(log_dir))

    def test_logger_enabled_mode(self):
        self.logger.configure({"enabled": True}, self.cfg_path)
        self.assertTrue(self.logger.enabled)
        self.logger.log("ASR", "Plaintext ASR Output Test: Hello World")

        log_dir = os.path.join(self.test_dir, "logs")
        self.assertTrue(os.path.exists(log_dir))

        today_str = datetime.now().strftime("%Y%m%d")
        expected_log = os.path.join(log_dir, f"voice_input_{today_str}.log")
        self.assertTrue(os.path.exists(expected_log))

        with open(expected_log, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("[ASR] Plaintext ASR Output Test: Hello World", content)

if __name__ == "__main__":
    unittest.main()
