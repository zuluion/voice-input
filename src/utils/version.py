import os
import sys

def get_project_root() -> str:
    """获取项目根目录，支持开发环境与 PyInstaller 打包环境。"""
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        return getattr(sys, '_MEIPASS')
    
    # 从 src/utils/version.py 向上退两层获取项目根目录
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(curr_dir, "..", ".."))
    return root_dir

def get_app_version() -> str:
    """读取单源 VERSION 文件获取最新应用版本号。"""
    root = get_project_root()
    possible_paths = [
        os.path.join(root, "VERSION"),
        os.path.join(os.getcwd(), "VERSION"),
        "VERSION"
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    ver = f.read().strip()
                    if ver:
                        return ver
            except Exception:
                pass
    return "2026.07.30.011"

def get_logo_path() -> str:
    """获取 Logo 图片的绝对路径 (统一存放在根目录 assets/logo.png)。"""
    root = get_project_root()
    candidates = [
        os.path.join(root, "assets", "logo.png"),
        os.path.join(os.getcwd(), "assets", "logo.png")
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return ""
