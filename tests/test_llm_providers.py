import unittest
from unittest.mock import patch, MagicMock
from src.refine.llm import LLMRefiner

class TestLLMProviders(unittest.TestCase):
    @patch("requests.post")
    def test_deepseek_provider_config(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "买一杯拿铁"}}]
        }
        mock_post.return_value = mock_resp

        cfg = {
            "enabled": True,
            "provider": "deepseek",
            "deepseek": {
                "api_key": "test_deepseek_key",
                "base_url": "https://api.deepseek.com/v1",
                "model": "deepseek-chat"
            }
        }

        refiner = LLMRefiner(cfg)
        self.assertEqual(refiner.model, "deepseek-chat")
        self.assertEqual(refiner.base_url, "https://api.deepseek.com/v1")

        result = refiner.refine("买一杯美式，呃不对，改成拿铁")
        self.assertEqual(result, "买一杯拿铁")

    @patch("requests.post")
    def test_ollama_provider_config(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "写一个 Go 脚本"}}]
        }
        mock_post.return_value = mock_resp

        cfg = {
            "enabled": True,
            "provider": "ollama",
            "ollama": {
                "api_key": "",
                "base_url": "http://localhost:11434/v1",
                "model": "qwen2.5:7b"
            }
        }

        refiner = LLMRefiner(cfg)
        self.assertEqual(refiner.model, "qwen2.5:7b")
        # Ollama local endpoints shouldn't require API key
        result = refiner.refine("写一个 Python 脚本，算了，还是用 Go 吧")
        self.assertEqual(result, "写一个 Go 脚本")

if __name__ == "__main__":
    unittest.main()
