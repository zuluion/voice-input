import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock
from src.utils.webdav import WebDAVSync

class TestWebDAVSync(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.local_cfg_path = os.path.join(self.test_dir, "config.json")
        with open(self.local_cfg_path, "w", encoding="utf-8") as f:
            json.dump({"hotkey": "Key.ctrl_r", "llm": {"enabled": True}}, f)

        self.webdav_cfg = {
            "enabled": True,
            "server_url": "https://dav.jianguoyun.com/dav",
            "username": "user@example.com",
            "password": "secret_password",
            "remote_dir": "/VoiceInput",
            "max_backups": 5
        }

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @patch("requests.put")
    @patch("requests.request")
    def test_upload_config_success(self, mock_req, mock_put):
        mock_put_resp = MagicMock()
        mock_put_resp.status_code = 200
        mock_put.return_value = mock_put_resp

        sync = WebDAVSync(self.webdav_cfg)
        ok, msg = sync.upload_config(self.local_cfg_path, save_history=False)
        self.assertTrue(ok)
        self.assertIn("successfully uploaded", msg)

    @patch("requests.get")
    def test_download_config_success(self, mock_get):
        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.json.return_value = {"hotkey": "Key.space", "llm": {"provider": "deepseek"}}
        mock_get.return_value = mock_get_resp

        target_path = os.path.join(self.test_dir, "downloaded.json")
        sync = WebDAVSync(self.webdav_cfg)
        ok, msg = sync.download_config(target_path)
        self.assertTrue(ok)
        self.assertTrue(os.path.exists(target_path))

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.assertEqual(data["hotkey"], "Key.space")

    @patch("requests.delete")
    @patch("requests.request")
    def test_max_backups_cleanup(self, mock_req, mock_delete):
        xml_content = """<?xml version="1.0" encoding="utf-8"?>
        <d:multistatus xmlns:d="DAV:">
            <d:response><d:href>/dav/VoiceInput/config.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_100000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_090000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_080000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_070000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_060000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_050000.json</d:href></d:response>
            <d:response><d:href>/dav/VoiceInput/config_20260730_040000.json</d:href></d:response>
        </d:multistatus>"""

        mock_resp = MagicMock()
        mock_resp.status_code = 207
        mock_resp.content = xml_content.encode("utf-8")
        mock_req.return_value = mock_resp

        mock_del_resp = MagicMock()
        mock_del_resp.status_code = 204
        mock_delete.return_value = mock_del_resp

        sync = WebDAVSync(self.webdav_cfg)
        sync._cleanup_old_backups()

        # Should delete 2 oldest files to keep only 5
        self.assertEqual(mock_delete.call_count, 2)

if __name__ == "__main__":
    unittest.main()
