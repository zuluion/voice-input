import unittest
from unittest.mock import patch, MagicMock
from src.asr.xiaomi_mimo import XiaomiMiMoASRProvider

class TestXiaomiMiMoASR(unittest.TestCase):
    @patch("requests.post")
    def test_xiaomi_mimo_finish(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {"message": {"content": "使用小米语音识别测试"}}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        provider = XiaomiMiMoASRProvider({"api_key": "test_mimo_key"})
        provider.connect()
        provider.send_audio_chunk(b"\x00\x00" * 8000)

        result = provider.finish()
        self.assertEqual(result, "使用小米语音识别测试")

if __name__ == '__main__':
    unittest.main()
