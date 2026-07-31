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

DEFAULT_LOCAL_SYSTEM_PROMPT = """你是一个专业的语音文本校对与整理器。你的唯一任务是整理和优化用户所引用的语音识别文本，严格遵循以下规则：

1. 【保留完整上下文（极为重要）】：
   - 当文本中出现自我修正（如“A，呃不对，是B”）时，仅替换被修正的局部字词，必须完整保留修正之前和之后的所有未修改前文与上下文！
   - 示例：若输入为“今天天气很好。明天上午开会，呃不对，是明天下午开会”，前面“今天天气很好”绝对不能删掉！正确输出应为：“今天天气很好。明天下午开会。”

2. 【隔离提示词示例】：提示词中的任何示例词汇仅供逻辑参考，绝对禁止将示例中的无关词汇引入或拼接到用户的文本中！

3. 移除口语冗余：删除语气词（如“呃”、“啊”、“那个”、“就是”）、重复停顿词及口吃词汇。

4. 语音识别与术语纠错：自动修正谐音错别字、拼音误写及英文/技术术语（如“配森”->“Python”）。

5. 【绝对纯净输出（禁止输出引号）】：仅直接输出修改后的纯文本内容本身！绝对禁止使用任何引号（如双引号" "、中文引号“”或单引号）将输出文本包裹起来！绝对禁止输出任何解释、聊天回复、标语、前缀或总结说明。"""

class LLMRefiner:
    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

        self.provider = self.config.get("provider", "openai")
        provider_cfg = self.config.get(self.provider, {})

        provider_prompt = provider_cfg.get("system_prompt", "").strip()
        global_prompt = self.config.get("system_prompt", "").strip()

        if self.provider == "local":
            self.system_prompt = provider_prompt or DEFAULT_LOCAL_SYSTEM_PROMPT
        else:
            self.system_prompt = provider_prompt or global_prompt or DEFAULT_SYSTEM_PROMPT

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
            logger.log("LLM Refine", f"LLM API Key is empty for provider '{self.provider}'. Skipping LLM refinement.")
            return transcript

        proxy_info = get_current_proxy_str()
        proxy_tag = f" [VIA PROXY: {proxy_info}]" if proxy_info else " [DIRECT]"

        url = f"{self.base_url}/chat/completions"
        logger.log("LLM Refine", f"Starting LLM refinement{proxy_tag} -> Provider '{self.provider}', Model '{self.model}' at {url}")
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
            # 远程 API 请求受系统代理环境变量调控，超时设为 8 秒
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
            logger.log("LLM Refine Exception", f"Exception during refinement via '{self.provider}': {e}")
            return transcript

        return transcript

    def _refine_local(self, transcript: str) -> str:
        """运行本地免编译 Ollama 引擎极速纠错与精修 (强制本地直连，绝不走代理)。"""
        from src.utils.model_downloader import ensure_ollama_server_running, is_model_downloaded
        
        model_id = self.model or "qwen2.5:1.5b"
        if not ensure_ollama_server_running():
            logger.log("LLM Refine", "Local Ollama engine server is not running. Skipping refinement.")
            return transcript

        if not is_model_downloaded(model_id):
            logger.log("LLM Refine", f"Local model '{model_id}' is not downloaded yet. Skipping refinement.")
            return transcript

        logger.log("LLM Refine", f"Refining using local model '{model_id}' via Ollama engine...")

        try:
            url = "http://127.0.0.1:11434/api/generate"
            user_prompt = f"请精修并整理以下由语音识别生成的原始文本：\n\"{transcript}\""
            payload = {
                "model": model_id,
                "system": self.system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1
                }
            }
            # 关键修补: 本地 Ollama 必须加 proxies={"http": None, "https": None}，强制绕过代理，防止被全局代理把 127.0.0.1 卡住
            resp = requests.post(url, json=payload, timeout=8, proxies={"http": None, "https": None})
            if resp.status_code == 200:
                refined = resp.json().get("response", "").strip()
                quote_chars = '"\'“”‘’`'
                while len(refined) >= 2 and (
                    (refined[0] in quote_chars and refined[-1] in quote_chars)
                ):
                    refined = refined[1:-1].strip()

                if refined and refined != transcript:
                    logger.log("LLM Refine", f"Local Refined Output: '{refined}'")
                    return refined
                else:
                    logger.log("LLM Refine", f"Text validated. No correction needed: '{transcript}'")
                    return transcript
            else:
                logger.log("LLM Refine", f"Ollama API Error ({resp.status_code}): {resp.text}")
        except Exception as e:
            logger.log("LLM Refine Exception", f"Local Ollama execution exception: {e}")

        return transcript
