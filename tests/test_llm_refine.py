import unittest
from unittest.mock import patch, MagicMock
from src.refine.llm import LLMRefiner

class TestLLMRefine(unittest.TestCase):
    def test_refine_disabled(self):
        refiner = LLMRefiner({"enabled": False})
        text = "我喜欢用配森写代码"
        result = refiner.refine(text)
        self.assertEqual(result, text)

    @patch("requests.post")
    def test_refine_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [
                {"message": {"content": "我喜欢用 Python 写代码"}}
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        refiner = LLMRefiner({"enabled": True, "api_key": "test_key"})
        result = refiner.refine("我喜欢用配森写代码")
        self.assertEqual(result, "我喜欢用 Python 写代码")

if __name__ == '__main__':
    unittest.main()
