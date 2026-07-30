import os
import shutil
import tempfile
import unittest
from src.config import ConfigManager, resolve_config_path, DEFAULT_CONFIG

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_default_config_load(self):
        cfg_path = os.path.join(self.test_dir, "config.json")
        manager = ConfigManager(cfg_path)
        self.assertEqual(manager.get("hotkey"), "Key.ctrl_r")
        self.assertEqual(manager.get("asr", "provider"), "xiaomi_mimo")
        self.assertTrue(manager.get("llm", "enabled"))

    def test_config_save_and_reload(self):
        cfg_path = os.path.join(self.test_dir, "config.json")
        manager = ConfigManager(cfg_path)
        manager.save_config({"hotkey": "Key.space", "llm": {"provider": "deepseek"}})

        new_manager = ConfigManager(cfg_path)
        self.assertEqual(new_manager.get("hotkey"), "Key.space")
        self.assertEqual(new_manager.get("llm", "provider"), "deepseek")
        # Ensure unmentioned defaults remain intact
        self.assertEqual(new_manager.get("asr", "provider"), "xiaomi_mimo")

    def test_directory_anomaly_resolution(self):
        # Create a directory named 'config.json'
        bad_dir_path = os.path.join(self.test_dir, "bad_config.json")
        os.makedirs(bad_dir_path, exist_ok=True)

        resolved = resolve_config_path(bad_dir_path)
        # Should return specified explicit path if given, but load_config shouldn't crash
        manager = ConfigManager(bad_dir_path)
        self.assertIsNotNone(manager.config)

if __name__ == "__main__":
    unittest.main()
