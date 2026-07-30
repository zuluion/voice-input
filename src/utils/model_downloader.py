import os
import sys
import json
import zipfile
import shutil
import subprocess
import requests
from src.utils.logger import logger
from src.utils.proxy import get_requests_proxies

# 预设本地 GGUF LLM 模型列表 (基于免编译 Ollama 引擎托管)
PRESET_MODELS = {
    "qwen2.5:1.5b": {
        "name": "Qwen2.5-1.5B-Instruct (Recommended)",
        "ollama_tag": "qwen2.5:1.5b",
        "size_str": "986 MB",
        "size_bytes": 1033830400
    },
    "qwen2.5:3b": {
        "name": "Qwen2.5-3B-Instruct (High Quality)",
        "ollama_tag": "qwen2.5:3b",
        "size_str": "1.9 GB",
        "size_bytes": 2040109465
    }
}

OLLAMA_WIN_URL = "https://github.com/ollama/ollama/releases/download/v0.5.7/ollama-windows-amd64.zip"
OLLAMA_WIN_MIRROR = "https://hf-mirror.com/ollama/ollama-releases/resolve/main/ollama-windows-amd64.zip"

def get_bin_dir() -> str:
    """获取用户 Home 目录下的二进制可执行程序目录 ~/.voiceinput/bin"""
    bin_dir = os.path.expanduser(os.path.join("~", ".voiceinput", "bin"))
    os.makedirs(bin_dir, exist_ok=True)
    return os.path.abspath(bin_dir)

def get_models_dir() -> str:
    """获取用户 Home 目录下的模型文件夹路径 ~/.voiceinput/models"""
    models_dir = os.path.expanduser(os.path.join("~", ".voiceinput", "models"))
    os.makedirs(models_dir, exist_ok=True)
    return os.path.abspath(models_dir)

def get_ollama_exe_path() -> str:
    """获取系统中的 ollama.exe 路径，优先检测全局 PATH，其次检测 ~/.voiceinput/bin/ollama.exe"""
    sys_path = shutil.which("ollama")
    if sys_path and os.path.exists(sys_path):
        return sys_path

    local_exe = os.path.join(get_bin_dir(), "ollama.exe")
    if os.path.exists(local_exe):
        return local_exe
    return ""

def is_ollama_installed() -> bool:
    """判断 Ollama 本地免编译引擎是否就绪"""
    return bool(get_ollama_exe_path())

def install_ollama_engine(progress_callback=None) -> tuple[bool, str]:
    """免编译下载并安装单文件免配置 Ollama 引擎至 ~/.voiceinput/bin/"""
    if is_ollama_installed():
        return True, "Ollama engine is already installed."

    bin_dir = get_bin_dir()
    zip_path = os.path.join(bin_dir, "ollama_download.zip")
    proxies = get_requests_proxies()

    urls = [OLLAMA_WIN_MIRROR, OLLAMA_WIN_URL]
    download_success = False

    for url in urls:
        try:
            logger.log("OllamaInstaller", f"Downloading Ollama standalone engine from: {url}")
            resp = requests.get(url, stream=True, proxies=proxies, timeout=20)
            if resp.status_code != 200:
                continue

            total_size = int(resp.headers.get("content-length", 65000000))
            downloaded = 0

            with open(zip_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=1024 * 128):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            percent = int(downloaded * 100 / total_size) if total_size > 0 else 0
                            progress_callback(downloaded, total_size, percent)

            download_success = True
            break
        except Exception as e:
            logger.log("OllamaInstaller", f"Failed downloading from {url}: {e}")
            if os.path.exists(zip_path):
                try:
                    os.remove(zip_path)
                except Exception:
                    pass

    if not download_success or not os.path.exists(zip_path):
        return False, "Failed to download Ollama standalone binary."

    try:
        logger.log("OllamaInstaller", f"Extracting Ollama engine to {bin_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(bin_dir)
        
        if os.path.exists(zip_path):
            os.remove(zip_path)

        if is_ollama_installed():
            logger.log("OllamaInstaller", "Ollama standalone engine installed successfully!")
            return True, "Ollama engine installed successfully."
        else:
            return False, "Extraction completed but ollama.exe was not found."
    except Exception as extract_err:
        logger.log("OllamaInstaller", f"Extraction error: {extract_err}")
        return False, f"Extraction failed: {str(extract_err)}"

_OLLAMA_PROCESS = None
_OLLAMA_JOB_HANDLE = None

def _create_win32_job_object():
    """创建一个系统级的 Windows Job Object，确保 VoiceInput 退出时其调起的所有子孙进程自动强杀"""
    if os.name != 'nt':
        return None
    try:
        import ctypes
        from ctypes import wintypes

        kernel32 = ctypes.windll.kernel32
        job = kernel32.CreateJobObjectW(None, None)
        if not job:
            return None

        class JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                ('PerJobUserTimeLimit', wintypes.LARGE_INTEGER),
                ('LimitFlags', wintypes.DWORD),
                ('MinimumWorkingSetSize', ctypes.c_size_t),
                ('MaximumWorkingSetSize', ctypes.c_size_t),
                ('ActiveProcessLimit', wintypes.DWORD),
                ('Affinity', ctypes.c_size_t),
                ('PriorityClass', wintypes.DWORD),
                ('SchedulingClass', wintypes.DWORD),
            ]

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [
                ('ReadOperationCount', ctypes.c_ulonglong),
                ('WriteOperationCount', ctypes.c_ulonglong),
                ('OtherOperationCount', ctypes.c_ulonglong),
                ('ReadTransferCount', ctypes.c_ulonglong),
                ('WriteTransferCount', ctypes.c_ulonglong),
                ('OtherTransferCount', ctypes.c_ulonglong),
            ]

        class JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
            _fields_ = [
                ('BasicLimitInformation', JOBOBJECT_BASIC_LIMIT_INFORMATION),
                ('IoInfo', IO_COUNTERS),
                ('ProcessMemoryLimit', ctypes.c_size_t),
                ('JobMemoryLimit', ctypes.c_size_t),
                ('PeakProcessMemoryUsed', ctypes.c_size_t),
                ('PeakJobMemoryUsed', ctypes.c_size_t),
            ]

        info = JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

        JobObjectExtendedLimitInformation = 9
        res = kernel32.SetInformationJobObject(
            job,
            JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info)
        )
        if res:
            return job
    except Exception as e:
        logger.log("OllamaServer", f"Failed to create Win32 Job Object: {e}")
    return None

def stop_ollama_server():
    """退出应用时联动关闭由 VoiceInput 启动的 Ollama 及其派生的子/孙进程树 (如 ollama_llama_server.exe)"""
    global _OLLAMA_PROCESS, _OLLAMA_JOB_HANDLE
    logger.log("OllamaServer", "Linked shutdown: Terminating background Ollama server & process tree...")
    
    if _OLLAMA_PROCESS:
        try:
            _OLLAMA_PROCESS.terminate()
        except Exception:
            pass
        _OLLAMA_PROCESS = None

    if os.name == 'nt':
        try:
            # 使用 taskkill /F /T 树状终止所有 ollama.exe 与 ollama_llama_server.exe 进程
            subprocess.run(["taskkill", "/F", "/T", "/IM", "ollama.exe"], capture_output=True)
            subprocess.run(["taskkill", "/F", "/T", "/IM", "ollama_llama_server.exe"], capture_output=True)
        except Exception:
            pass

    _OLLAMA_JOB_HANDLE = None

def ensure_ollama_server_running() -> bool:
    """确保后台 Ollama 服务在 http://127.0.0.1:11434 启动运行"""
    global _OLLAMA_PROCESS, _OLLAMA_JOB_HANDLE
    # 1. 尝试请求健康检查接口
    try:
        r = requests.get("http://127.0.0.1:11434/api/version", timeout=1.5)
        if r.status_code == 200:
            return True
    except Exception:
        pass

    # 2. 未启动，则在后台静默启动
    exe_path = get_ollama_exe_path()
    if not exe_path:
        return False

    logger.log("OllamaServer", f"Starting background Ollama server: {exe_path} serve")
    try:
        startupinfo = None
        if os.name == 'nt':
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

        env = os.environ.copy()
        env["OLLAMA_MODELS"] = get_models_dir()

        _OLLAMA_PROCESS = subprocess.Popen(
            [exe_path, "serve"],
            env=env,
            startupinfo=startupinfo,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
        )

        # 在 Windows 上将新创建的进程挂载至 Job Object，确保同生共死
        if os.name == 'nt':
            _OLLAMA_JOB_HANDLE = _create_win32_job_object()
            if _OLLAMA_JOB_HANDLE and _OLLAMA_PROCESS:
                try:
                    import ctypes
                    kernel32 = ctypes.windll.kernel32
                    kernel32.AssignProcessToJobObject(_OLLAMA_JOB_HANDLE, int(_OLLAMA_PROCESS._handle))
                except Exception as job_err:
                    logger.log("OllamaServer", f"Failed to assign process to job: {job_err}")

        import time
        time.sleep(2)

        r = requests.get("http://127.0.0.1:11434/api/version", timeout=3)
        return r.status_code == 200
    except Exception as e:
        logger.log("OllamaServer", f"Failed to start Ollama server: {e}")
        return False

def is_model_downloaded(model_id: str) -> bool:
    """检查指定的 Ollama 模型是否已下载 (结合在线 API 与本地物理磁盘双重检测)"""
    tag = PRESET_MODELS.get(model_id, {}).get("ollama_tag", model_id)
    
    # 1. 尝试在线 API 检测
    try:
        r = requests.get("http://127.0.0.1:11434/api/tags", timeout=1.5)
        if r.status_code == 200:
            models = r.json().get("models", [])
            for m in models:
                name = m.get("name", "")
                if tag in name or name in tag:
                    return True
    except Exception:
        pass

    # 2. 若 API 尚未连通/响应，离线检查本地物理磁盘 ~/.voiceinput/models/manifests/ 目录
    try:
        parts = tag.split(":")
        model_name = parts[0]
        model_ver = parts[1] if len(parts) > 1 else "latest"
        
        manifest_path = os.path.expanduser(os.path.join(
            "~", ".voiceinput", "models", "manifests", "registry.ollama.ai", "library", model_name, model_ver
        ))
        if os.path.exists(manifest_path) and os.path.getsize(manifest_path) > 0:
            return True
    except Exception:
        pass

    return False

def download_model(model_id: str, progress_callback=None, cancel_checker=None) -> tuple[bool, str]:
    """通过 Ollama REST API 带有进度地下载模型"""
    if not ensure_ollama_server_running():
        return False, "Ollama engine service is not running."

    tag = PRESET_MODELS.get(model_id, {}).get("ollama_tag", model_id)
    url = "http://127.0.0.1:11434/api/pull"
    payload = {"name": tag, "stream": True}

    logger.log("ModelDownloader", f"Pulling Ollama model '{tag}' via API...")

    try:
        resp = requests.post(url, json=payload, stream=True, timeout=10)
        if resp.status_code != 200:
            return False, f"API response HTTP Status: {resp.status_code}"

        for line in resp.iter_lines():
            if cancel_checker and cancel_checker():
                return False, "Model download cancelled by user."

            if line:
                try:
                    data = json.loads(line.decode("utf-8"))
                    completed = data.get("completed", 0)
                    total = data.get("total", 0)
                    if total > 0 and progress_callback:
                        percent = int(completed * 100 / total)
                        progress_callback(completed, total, percent)
                except Exception:
                    pass

        if is_model_downloaded(model_id):
            logger.log("ModelDownloader", f"Ollama model '{tag}' downloaded successfully!")
            return True, "Model downloaded successfully."
        return True, "Model pulled successfully."
    except Exception as e:
        logger.log("ModelDownloader", f"Model pull exception: {e}")
        return False, f"Download failed: {str(e)}"

def delete_model(model_id: str) -> tuple[bool, str]:
    """通过 Ollama REST API 删除指定模型"""
    if not ensure_ollama_server_running():
        return False, "Ollama engine service is not running."

    tag = PRESET_MODELS.get(model_id, {}).get("ollama_tag", model_id)
    url = "http://127.0.0.1:11434/api/delete"
    payload = {"name": tag}

    try:
        resp = requests.delete(url, json=payload, timeout=5)
        if resp.status_code == 200:
            logger.log("ModelDownloader", f"Successfully deleted Ollama model: {tag}")
            return True, "Model deleted successfully."
        else:
            return False, f"Delete response HTTP Status: {resp.status_code}"
    except Exception as e:
        logger.log("ModelDownloader", f"Failed to delete model {tag}: {e}")
        return False, f"Delete failed: {str(e)}"
