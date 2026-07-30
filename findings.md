# Findings - Technical Analysis & Insights

## 1. WebDAV Path Resolution Analysis
- **URL 拼接修复**：`WebDAVSync._get_url_for_path(rel_path)` refactored using `urllib.parse` to correctly preserve subpaths (e.g. `/dav/` or `/remote.php/webdav/`) without redundant `/` nesting.
- **Auto Directory Creation**: Automatically creates target local folders before saving downloaded WebDAV configuration.

## 2. Dynamic Version & Logo Single Source Analysis
- **Single Source of Truth**: Created `src/utils/version.py` (`get_app_version()`, `get_logo_path()`) supporting PyInstaller `_MEIPASS` and dynamic root resolution.
- **Icon Uniformity**: All windows, taskbar AppUserModelID (`Zuluion.VoiceInput.App.1`), system tray, and about tab render transparent background SVG-generated PNG (`assets/logo.png`) and `assets/logo.ico`.

## 3. Standalone Ollama Local Engine Architecture & Process Lifecycle
- **Zero-Compiler Migration**: Eliminated `llama-cpp-python` and Visual Studio C++ / CMake requirements on Windows. Local models run via a standalone, zero-dependency Ollama binary (`~/.voiceinput/bin/ollama.exe`).
- **Offline Model Probe**: `is_model_downloaded` combines online API tags check with offline disk manifest inspection (`~/.voiceinput/models/manifests/`), ensuring instant `Ready` state upon application startup even when Ollama HTTP server is silent.
- **Win32 Job Object & Tree Teardown**: Windows child/grandchild processes (`ollama.exe` and `ollama_llama_server.exe`) are bound to a Win32 Job Object with `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`. Process termination hooks execute `taskkill /F /T`, completely eliminating orphan zombie processes.
- **Provider-Decoupled System Prompts**: `LLMRefiner` supports per-provider system prompts (`DEFAULT_LOCAL_SYSTEM_PROMPT`). Local mode enforces unedited context preservation, prohibits prompt example leakage, and strips artificial outer quotes (`""`, `“”`).
