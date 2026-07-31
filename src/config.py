import json
import os
from typing import Any, Dict

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

DEFAULT_CONFIG: Dict[str, Any] = {
    "language": "auto",
    "hotkey": "Key.ctrl_r",
    "asr": {
        "provider": "xiaomi_mimo",
        "doubao": {
            "app_id": "",
            "access_token": "",
            "cluster": "volcengine_input_common"
        },
        "qwen": {
            "api_key": "",
            "app_key": ""
        },
        "xiaomi_mimo": {
            "api_key": "",
            "base_url": "https://api.xiaomimimo.com/v1",
            "model": "mimo-v2.5-asr"
        },
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "whisper-1"
        }
    },
    "llm": {
        "enabled": True,
        "provider": "local",
        "system_prompt": DEFAULT_SYSTEM_PROMPT,
        "openai": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        },
        "deepseek": {
            "api_key": "",
            "base_url": "https://api.deepseek.com/v1",
            "model": "deepseek-chat"
        },
        "xiaomi": {
            "api_key": "",
            "base_url": "https://api.xiaomimimo.com/v1",
            "model": "mimo-v2.5-asr"
        },
        "qwen": {
            "api_key": "",
            "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
            "model": "qwen-plus"
        },
        "ollama": {
            "api_key": "",
            "base_url": "http://localhost:11434/v1",
            "model": "qwen2.5:1.5b"
        },
        "local": {
            "model": "qwen2.5:1.5b",
            "system_prompt": ""
        },
        "custom": {
            "api_key": "",
            "base_url": "https://api.openai.com/v1",
            "model": "gpt-4o-mini"
        }
    },
    "proxy": {
        "enabled": False,
        "protocol": "http",
        "host": "127.0.0.1",
        "port": 7890
    },
    "webdav": {
        "enabled": False,
        "provider": "jianguoyun",
        "auto_sync_on_startup": False,
        "jianguoyun": {
            "server_url": "https://dav.jianguoyun.com/dav/",
            "username": "",
            "password": "",
            "remote_dir": "/VoiceInput",
            "max_backups": 5
        },
        "custom": {
            "server_url": "https://dav.jianguoyun.com/dav/",
            "username": "",
            "password": "",
            "remote_dir": "/VoiceInput",
            "max_backups": 5
        }
    },
    "debug": {
        "enabled": False
    },
    "ui": {
        "position": "bottom_center",
        "sound_feedback": False
    }
}

def resolve_config_path(config_path: str = None) -> str:
    if config_path:
        if os.path.isdir(config_path):
            print(f"[Config] Warning: Explicit path '{config_path}' is a directory. Falling back to AppData.")
        else:
            return config_path

    # Check local portable config.json
    local_path = "config.json"
    if os.path.isfile(local_path):
        return local_path
    elif os.path.isdir(local_path):
        print(f"[Config] Warning: '{local_path}' is a directory (created by misconfigured Scoop). Falling back to AppData.")

    # Standard Windows AppData directory (%APPDATA%\VoiceInput\config.json)
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    config_dir = os.path.join(appdata, "VoiceInput")
    os.makedirs(config_dir, exist_ok=True)
    return os.path.join(config_dir, "config.json")

class ConfigManager:
    def __init__(self, config_path: str = None) -> None:
        self.config_path = resolve_config_path(config_path)
        print(f"[Config] Using config file: {self.config_path}")
        self.config: Dict[str, Any] = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path) or os.path.isdir(self.config_path):
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG.copy()
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return self._merge_defaults(data, DEFAULT_CONFIG)
        except Exception:
            return DEFAULT_CONFIG.copy()

    def save_config(self, config: Dict[str, Any] = None) -> None:
        if config is not None:
            self.config = config

        parent_dir = os.path.dirname(self.config_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _merge_defaults(self, data: Dict[str, Any], default: Dict[str, Any]) -> Dict[str, Any]:
        result = default.copy()
        for key, value in data.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                result[key] = self._merge_defaults(value, result[key])
            else:
                result[key] = value
        return result

    def get(self, *keys: str, default: Any = None) -> Any:
        curr = self.config
        for key in keys:
            if isinstance(curr, dict) and key in curr:
                curr = curr[key]
            else:
                return default
        return curr
