from src.asr.base import BaseASRProvider
from src.asr.xiaomi_mimo import XiaomiMiMoASRProvider
from src.asr.openai_http import OpenAIHTTPASRProvider
from src.asr.doubao import DoubaoASRProvider
from src.asr.qwen import QwenASRProvider

def create_asr_provider(provider_name: str, config: dict) -> BaseASRProvider:
    name = provider_name.lower()
    if name == "xiaomi_mimo":
        return XiaomiMiMoASRProvider(config.get("xiaomi_mimo", {}))
    elif name == "openai":
        return OpenAIHTTPASRProvider(config.get("openai", {}))
    elif name == "doubao":
        return DoubaoASRProvider(config.get("doubao", {}))
    elif name == "qwen":
        return QwenASRProvider(config.get("qwen", {}))
    else:
        return XiaomiMiMoASRProvider(config.get("xiaomi_mimo", {}))
