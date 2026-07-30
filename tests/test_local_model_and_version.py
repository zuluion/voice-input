import os
import pytest
from src.utils.version import get_app_version, get_logo_path
from src.utils.model_downloader import (
    PRESET_MODELS, get_models_dir, get_model_file_path, is_model_downloaded
)
from src.refine.llm import LLMRefiner

def test_version_utils():
    version = get_app_version()
    assert version is not None
    assert len(version) > 0

    logo_path = get_logo_path()
    assert logo_path != ""
    assert os.path.exists(logo_path)

def test_model_downloader_utils():
    models_dir = get_models_dir()
    assert os.path.exists(models_dir)
    assert ".voiceinput" in models_dir

    assert "qwen2.5-0.5b-instruct" in PRESET_MODELS
    path = get_model_file_path("qwen2.5-0.5b-instruct")
    assert path.endswith("qwen2.5-0.5b-instruct-q4_k_m.gguf")

def test_local_llm_refiner_fallback():
    cfg = {
        "enabled": True,
        "provider": "local",
        "local": {
            "model": "qwen2.5-0.5b-instruct"
        }
    }
    refiner = LLMRefiner(cfg)
    # When model is not downloaded, refine should return raw input safely
    text = "测试文本"
    res = refiner.refine(text)
    assert res == text
