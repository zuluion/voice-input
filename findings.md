# Findings - Technical Analysis & Insights

## 1. WebDAV Path Resolution Analysis
- **URL 拼接修复**：`WebDAVSync._get_url_for_path(rel_path)` refactored using `urllib.parse` to correctly preserve subpaths (e.g. `/dav/` or `/remote.php/webdav/`) without redundant `/` nesting.
- **Auto Directory Creation**: Automatically creates target local folders before saving downloaded WebDAV configuration.

## 2. Dynamic Version & Logo Single Source Analysis
- **Single Source of Truth**: Created `src/utils/version.py` (`get_app_version()`, `get_logo_path()`) supporting PyInstaller `_MEIPASS` and dynamic root resolution.
- **Icon Uniformity**: All windows, taskbar AppUserModelID (`Zuluion.VoiceInput.App.1`), system tray, and about tab render transparent background SVG-generated PNG (`assets/logo.png`).

## 3. Standalone Ollama Local Engine Architecture
- **Zero-Compiler Migration**: Eliminated `llama-cpp-python` and Visual Studio C++ / CMake requirements on Windows. Local models run via a standalone, zero-dependency Ollama binary (`~/.voiceinput/bin/ollama.exe`).
- **Provider-Decoupled System Prompts**: `LLMRefiner` supports per-provider system prompts (`DEFAULT_LOCAL_SYSTEM_PROMPT`). Local mode enforces unedited context preservation, prohibits prompt example leakage, and strips artificial outer quotes (`""`, `“”`).
- **Linked Process Lifecycle**: Background Ollama processes are automatically shut down upon VoiceInput exit via `QApplication.aboutToQuit` to free system RAM and CPU.
