# Task Plan: Local LLM Engine, WebDAV Fix, Logo & UI Single Source

## Completed Tasks
- [x] **WebDAV Subpath Concatenation & Folder Creation Fix**: Fixed URL path deduplication in `src/utils/webdav.py` and auto-created target directories before download.
- [x] **Transparent Logo Generation & Asset Integration**: Generated transparent background PNG (`assets/logo.png`) and multi-size ICO (`assets/logo.ico`), integrated into About tab, System Tray, Settings Window, Taskbar, and PyInstaller build.
- [x] **Single-Source Versioning**: Created `src/utils/version.py` binding `VERSION` file as the single source of truth across UI components.
- [x] **Zero-Build Ollama Engine Integration**: Migrated from `llama-cpp-python` to standalone `ollama.exe` (`~/.voiceinput/bin/`), resolving Windows C++ compiler and Python 3.14 wheel absence completely.
- [x] **Offline Model Probe**: Added offline disk manifest inspection to `is_model_downloaded` for instant startup model state verification.
- [x] **Provider-Decoupled System Prompts & Quote Stripping**: Added `DEFAULT_LOCAL_SYSTEM_PROMPT` preserving unedited context, preventing prompt example leakage, and stripping artificial outer quotes.
- [x] **Model Preset Refinement**: Pinned `qwen2.5:1.5b` (986MB) and `qwen2.5:3b` (1.9GB) as default local models, removing 0.5B model.
- [x] **Linked Process Tree Lifecycle Teardown**: Bound Ollama process to Win32 Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) and added `taskkill /F /T` tree termination on app exit.
- [x] **Testing & Verification**: Verified via `pytest` (30/30 passed).
