import os
from src.utils.version import get_app_version, get_logo_path
from src.utils.model_downloader import (
    PRESET_MODELS,
    get_models_dir,
    get_bin_dir,
    is_model_downloaded,
    is_ollama_installed
)
from src.refine.llm import LLMRefiner

def test_version_single_source():
    version = get_app_version()
    assert version is not None
    assert len(version) > 0
    assert "2026." in version

def test_logo_path_exists():
    logo_path = get_logo_path()
    assert os.path.exists(logo_path)
    assert logo_path.endswith("logo.png")

def test_preset_models():
    assert "qwen2.5:1.5b" in PRESET_MODELS
    assert "qwen2.5:3b" in PRESET_MODELS
    assert "qwen2.5:0.5b" not in PRESET_MODELS
    models_dir = get_models_dir()
    assert os.path.exists(models_dir)
    bin_dir = get_bin_dir()
    assert os.path.exists(bin_dir)

def test_ollama_status_check():
    # 测试函数能否安全调用且不崩溃
    installed = is_ollama_installed()
    assert isinstance(installed, bool)
    downloaded = is_model_downloaded("qwen2.5:1.5b")
    assert isinstance(downloaded, bool)

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
