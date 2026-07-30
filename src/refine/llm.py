import os
import requests
from src.utils.logger import logger
from src.utils.proxy import get_current_proxy_str

DEFAULT_SYSTEM_PROMPT = """你是一个专业的语音输入文本精修与整理助手。请对输入的语音识别文本进行智能润色与纠错，严格遵循以下规则：

1. 移除口语冗余：自动删除语气词（如“呃”、“啊”、“那个”、“就是”）、口吃重叠字及无意义的语气停顿。

2. 口误与中途改口处理：
   - 识别用户的自我修正信号（如“不对”、“算了”、“改成”、“换成”、“还是”、“应该是”等）。
   - 当用户中途修正表达时，仅保留修正后的最新意图，自动剔除前面被废弃的内容。
   - 注意上下文连贯性与断句：严禁粗暴截断未修改的上下文！
     - 示例 A：用户说“买一杯美式，呃不对，改成拿铁”，应输出：“买一杯拿铁”。
     - 示例 B：用户说“xxx，然后 aaa，算了，还是 bbb”，应精准保留未修改的前文，输出：“xxx，bbb”。

3. 语音识别纠错：自动修复谐音错别字、中文拼音误写，以及英文/技术术语（例如将“配森”修正为“Python”，“杰森”修正为“JSON”）。

4. 语句流畅化：在保留用户真实意图的前提下，优化句式结构与标点符号，使口语转化为流畅通顺的书面表达。

5. 输出要求：仅输出精修与整理后的最终文本，不要包含任何解释、前言、括号或总结说明。"""

class LLMRefiner:
    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.system_prompt = self.config.get("system_prompt", "").strip() or DEFAULT_SYSTEM_PROMPT

        self.provider = self.config.get("provider", "openai")
        provider_cfg = self.config.get(self.provider, {})

        self.api_key = provider_cfg.get("api_key") or self.config.get("api_key", "")
        self.base_url = (provider_cfg.get("base_url") or self.config.get("base_url", "https://api.openai.com/v1")).rstrip("/")
        self.model = provider_cfg.get("model") or self.config.get("model", "gpt-4o-mini")

    def refine(self, transcript: str) -> str:
        if not transcript.strip():
            logger.log("LLM Refine", "Empty transcript. Skipping LLM refinement.")
            return transcript

        if not self.enabled:
            logger.log("LLM Refine", "LLM refinement is disabled in settings. Skipping LLM.")
            return transcript

        # 1. Local Model Provider Handling
        if self.provider == "local":
            return self._refine_local(transcript)

        # 2. Remote API Provider Handling
        if not self.api_key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            logger.log("LLM Refine", "LLM API Key is empty. Skipping LLM refinement.")
            return transcript

        proxy_info = get_current_proxy_str()
        proxy_tag = f" [VIA PROXY: {proxy_info}]" if proxy_info else " [DIRECT]"

        url = f"{self.base_url}/chat/completions"
        logger.log("LLM Refine", f"Starting LLM refinement{proxy_tag} -> Model '{self.model}' at {url}")
        logger.log("LLM Refine", f"Raw ASR Input: '{transcript}'")

        headers = {
            "Content-Type": "application/json"
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": transcript}
            ],
            "temperature": 0.2
        }

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            logger.log("LLM Refine", f"Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                choices = res_json.get("choices", [])
                if choices:
                    refined = choices[0].get("message", {}).get("content", "").strip()
                    if refined and refined != transcript:
                        logger.log("LLM Refine", f"Refined Output: '{refined}'")
                        return refined
                    else:
                        logger.log("LLM Refine", f"Text validated. No correction needed: '{transcript}'")
                        return transcript
            else:
                logger.log("LLM Refine", f"API Error ({resp.status_code}): {resp.text}")
                return transcript
        except Exception as e:
            logger.log("LLM Refine", f"Exception during refinement: {e}")
            return transcript

        return transcript

    def _refine_local(self, transcript: str) -> str:
        """运行本地 GGUF 模型纠错与精修。"""
        from src.utils.model_downloader import is_model_downloaded, get_model_file_path
        
        model_id = self.model
        if not is_model_downloaded(model_id):
            logger.log("LLM Refine", f"Local model '{model_id}' is not downloaded yet. Skipping refinement.")
            return transcript

        model_path = get_model_file_path(model_id)
        logger.log("LLM Refine", f"Refining using local model '{model_id}' at path: {model_path}")

        try:
            # 尝试使用 llama-cpp-python 本地推理
            from llama_cpp import Llama
            llm = Llama(model_path=model_path, verbose=False, n_ctx=2048)
            prompt = f"<|im_start|>system\n{self.system_prompt}<|im_end|>\n<|im_start|>user\n{transcript}<|im_end|>\n<|im_start|>assistant\n"
            output = llm(prompt, max_tokens=512, temperature=0.2, stop=["<|im_end|>"])
            
            refined = output["choices"][0]["text"].strip()
            if refined and refined != transcript:
                logger.log("LLM Refine", f"Local Refined Output: '{refined}'")
                return refined
        except ImportError:
            logger.log("LLM Refine", "llama-cpp-python is not installed. Falling back to local HTTP endpoint if available.")
            # 尝试通过本地默认 HTTP API 请求
            try:
                local_url = "http://127.0.0.1:8080/v1/chat/completions"
                payload = {
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": transcript}
                    ],
                    "temperature": 0.2
                }
                res = requests.post(local_url, json=payload, timeout=8)
                if res.status_code == 200:
                    refined = res.json()["choices"][0]["message"]["content"].strip()
                    if refined:
                        return refined
            except Exception as http_err:
                logger.log("LLM Refine", f"Local HTTP endpoint call failed: {http_err}")
        except Exception as e:
            logger.log("LLM Refine", f"Local GGUF model execution error: {e}")

        return transcript

