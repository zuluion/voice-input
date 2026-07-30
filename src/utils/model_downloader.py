import os
import requests
from src.utils.logger import logger
from src.utils.proxy import get_requests_proxies

# 预设本地 LLM GGUF 模型列表
PRESET_MODELS = {
    "qwen2.5-0.5b-instruct": {
        "name": "Qwen2.5-0.5B-Instruct (GGUF Q4_K_M)",
        "filename": "qwen2.5-0.5b-instruct-q4_k_m.gguf",
        "size_str": "398 MB",
        "size_bytes": 417333248,
        "urls": [
            "https://hf-mirror.com/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf",
            "https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct-GGUF/resolve/main/qwen2.5-0.5b-instruct-q4_k_m.gguf"
        ]
    },
    "qwen2.5-1.5b-instruct": {
        "name": "Qwen2.5-1.5B-Instruct (GGUF Q4_K_M)",
        "filename": "qwen2.5-1.5b-instruct-q4_k_m.gguf",
        "size_str": "986 MB",
        "size_bytes": 1033830400,
        "urls": [
            "https://hf-mirror.com/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf",
            "https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/resolve/main/qwen2.5-1.5b-instruct-q4_k_m.gguf"
        ]
    }
}

def get_models_dir() -> str:
    """获取用户 Home 目录下的模型文件夹路径 ~/.voiceinput/models"""
    models_dir = os.path.expanduser(os.path.join("~", ".voiceinput", "models"))
    os.makedirs(models_dir, exist_ok=True)
    return os.path.abspath(models_dir)

def get_model_file_path(model_id: str) -> str:
    info = PRESET_MODELS.get(model_id)
    if not info:
        return ""
    return os.path.join(get_models_dir(), info["filename"])

def is_model_downloaded(model_id: str) -> bool:
    path = get_model_file_path(model_id)
    return bool(path and os.path.exists(path) and os.path.getsize(path) > 1000000)

def delete_model(model_id: str) -> tuple[bool, str]:
    path = get_model_file_path(model_id)
    if not path or not os.path.exists(path):
        return False, "Model file does not exist."
    try:
        os.remove(path)
        logger.log("ModelDownloader", f"Successfully deleted local model file: {path}")
        return True, "Model deleted successfully."
    except Exception as e:
        logger.log("ModelDownloader", f"Failed to delete model file {path}: {e}")
        return False, f"Delete failed: {str(e)}"

def download_model(model_id: str, progress_callback=None, cancel_checker=None) -> tuple[bool, str]:
    info = PRESET_MODELS.get(model_id)
    if not info:
        return False, f"Unknown model ID: {model_id}"

    target_path = get_model_file_path(model_id)
    tmp_path = target_path + ".downloading"
    proxies = get_requests_proxies()

    logger.log("ModelDownloader", f"Starting download for model '{model_id}' into '{target_path}'")

    for url in info["urls"]:
        try:
            logger.log("ModelDownloader", f"Attempting download from: {url}")
            resp = requests.get(url, stream=True, proxies=proxies, timeout=15)
            if resp.status_code != 200:
                logger.log("ModelDownloader", f"HTTP Status {resp.status_code} from {url}, trying next URL...")
                continue

            total_size = int(resp.headers.get("content-length", info["size_bytes"]))
            downloaded = 0

            with open(tmp_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 128):
                    if cancel_checker and cancel_checker():
                        f.close()
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                        return False, "Download cancelled by user."
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
                            progress_callback(downloaded, total_size, percent)

            if os.path.exists(tmp_path):
                if os.path.exists(target_path):
                    os.remove(target_path)
                os.rename(tmp_path, target_path)
                logger.log("ModelDownloader", f"Download finished and saved to {target_path}")
                return True, "Model downloaded successfully."
        except Exception as e:
            logger.log("ModelDownloader", f"Download exception from {url}: {e}")
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
            continue

    return False, "Failed to download model from all available mirror URLs."
