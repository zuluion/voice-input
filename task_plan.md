# Task Plan: Local LLM Engine, WebDAV Fix, Logo & UI Single Source

## Completed Tasks
- [x] **WebDAV Subpath Concatenation & Folder Creation Fix**: Fixed URL path deduplication in `src/utils/webdav.py` and auto-created target directories before download.
- [x] **Transparent Logo Generation & Asset Integration**: Generated transparent background PNG (`assets/logo.png`), integrated into About tab, System Tray, Settings Window, and Taskbar.
- [x] **Single-Source Versioning**: Created `src/utils/version.py` binding `VERSION` file as the single source of truth across UI components.
- [x] **Zero-Build Ollama Engine Integration**: Migrated from `llama-cpp-python` to standalone `ollama.exe` (`~/.voiceinput/bin/`), resolving Windows C++ compiler and Python 3.14 wheel absence completely.
- [x] **Provider-Decoupled System Prompts & Quote Stripping**: Added `DEFAULT_LOCAL_SYSTEM_PROMPT` preserving unedited context, preventing prompt example leakage, and stripping artificial outer quotes.
- [x] **Model List Optimization**: Pinned `qwen2.5:1.5b` (986MB) and `qwen2.5:3b` (1.9GB) as default local models, removing 0.5B model.
- [x] **Linked Process Lifecycle**: Registered `stop_ollama_server()` on application exit (`aboutToQuit`).
- [x] **Testing & Verification**: Verified via `pytest` (30/30 passed).
