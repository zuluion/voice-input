import os
import unittest
from unittest.mock import patch, MagicMock
from src.utils.proxy import apply_proxy_config, test_proxy_connection

class TestProxyManager(unittest.TestCase):
    def tearDown(self):
        for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
            os.environ.pop(var, None)

    def test_apply_proxy_enabled(self):
        cfg = {"enabled": True, "protocol": "socks5", "host": "127.0.0.1", "port": 7890}
        apply_proxy_config(cfg)

        self.assertEqual(os.environ.get("HTTP_PROXY"), "socks5://127.0.0.1:7890")
        self.assertEqual(os.environ.get("HTTPS_PROXY"), "socks5://127.0.0.1:7890")
        self.assertEqual(os.environ.get("ALL_PROXY"), "socks5://127.0.0.1:7890")

    def test_apply_proxy_disabled(self):
        os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
        cfg = {"enabled": False, "protocol": "http", "host": "127.0.0.1", "port": 7890}
        apply_proxy_config(cfg)

        self.assertNotIn("HTTP_PROXY", os.environ)
        self.assertNotIn("HTTPS_PROXY", os.environ)

    @patch("requests.get")
    def test_test_proxy_connection_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"origin": "1.2.3.4"}
        mock_get.return_value = mock_resp

        cfg = {"enabled": True, "protocol": "http", "host": "127.0.0.1", "port": 7890}
        ok, msg = test_proxy_connection(cfg)
        self.assertTrue(ok)
        self.assertIn("1.2.3.4", msg)

if __name__ == "__main__":
    unittest.main()
