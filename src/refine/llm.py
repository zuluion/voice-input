import requests

DEFAULT_SYSTEM_PROMPT = """你是一个专业的语音输入文本精修与整理助手。请对输入的语音识别文本进行智能润色与纠错，严格遵循以下规则：
1. 移除口语冗余：自动删除语气词（如“呃”、“啊”、“那个”、“就是”）、口吃重叠字及不连贯的语气停顿。
2. 语音识别纠错：自动修复谐音错别字、中文拼音误写，以及英文/技术术语（例如将“配森”修正为“Python”，“杰森”修正为“JSON”）。
3. 语句顺畅化：在不改变用户原意的前提下，适当优化句式与标点符号，使口语转为流畅、通顺的书面表达。
4. 输出要求：仅输出精修与整理后的最终文本，不要包含任何解释、前言或总结说明。"""

class LLMRefiner:
    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
        self.api_key = self.config.get("api_key", "")
        self.base_url = self.config.get("base_url", "https://api.openai.com/v1").rstrip("/")
        self.model = self.config.get("model", "gpt-4o-mini")
        self.system_prompt = self.config.get("system_prompt", "").strip() or DEFAULT_SYSTEM_PROMPT

    def refine(self, transcript: str) -> str:
        if not transcript.strip():
            print("[LLM Refine] Empty transcript. Skipping LLM refinement.")
            return transcript

        if not self.enabled:
            print("[LLM Refine] LLM refinement is disabled in settings. Skipping LLM.")
            return transcript

        if not self.api_key:
            print("[LLM Refine] LLM API Key is empty. Skipping LLM refinement.")
            return transcript

        print(f"[LLM Refine] Starting LLM refinement using model '{self.model}' at {self.base_url}...")
        print(f"[LLM Refine] Raw ASR Input: '{transcript}'")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": transcript}
            ],
            "temperature": 0.2
        }
        url = f"{self.base_url}/chat/completions"
        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=8)
            print(f"[LLM Refine] Response HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                res_json = resp.json()
                choices = res_json.get("choices", [])
                if choices:
                    refined = choices[0].get("message", {}).get("content", "").strip()
                    if refined and refined != transcript:
                        print(f"[LLM Refine] Refined Output: '{refined}'")
                        return refined
                    else:
                        print(f"[LLM Refine] Text validated. No correction needed: '{transcript}'")
                        return transcript
            else:
                print(f"[LLM Refine] API Error ({resp.status_code}): {resp.text}")
                return transcript
        except Exception as e:
            print(f"[LLM Refine] Exception during refinement: {e}")
            return transcript

        return transcript
