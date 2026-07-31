# Changelog

All notable changes to this project will be documented in this file.

## [2026.07.31.005] - 2026-07-31

### 🛠️ Fixed Single-Source VERSION File Packaging & Executable Size Reduction
- **Single-Source VERSION Asset Bundling**: Added `--add-data "VERSION;."` to PyInstaller build configuration in `.github/workflows/release.yml`, ensuring executable binaries dynamically read the latest single-source version number from the bundled `VERSION` asset at runtime.
- **Heavy Qt Module Exclusion**: Added `--exclude-module` for heavy unused Qt modules (`Qt3D`, `QtQml`, `QtQuick`, `QtPdf`, `QtVirtualKeyboard`, `QtWebEngineCore`, `QtDesigner`, `QtTest`) to PyInstaller build command, completely eliminating 15MB+ of redundant DLL binaries in GitHub Actions release builds (bringing CI/CD build size down to ~60MB).

## [2026.07.31.004] - 2026-07-31


### 🛠️ Fixed GBK UnicodeEncodeError & CI/CD Build Size Optimization
- **Non-blocking Audit Log Print**: Wrapped end-to-end execution trace print block in `_on_processing_finished()` within a `try...except` block in `src/main.py`, ensuring console print failures never prevent text injection or UI state transition.
- **UTF-8 Encoded Dummy Stream**: Updated `os.devnull` fallback stream initialization to explicitly specify `encoding='utf-8', errors='ignore'` in `src/main.py` and `src/backend/main_daemon.py`, preventing Windows GBK `UnicodeEncodeError` when writing Emoji characters (`🎤`, `🎙️`, `🤖`).
- **CI/CD Lightweight Build**: Refactored `.github/workflows/release.yml` to build inside an isolated `uv venv` environment instead of system Python, reducing GitHub Actions release executable size by ~15MB (down to ~60MB+, matching local builds) and accelerating PyInstaller packaging speed.


## [2026.07.31.003] - 2026-07-31


### 🛠️ PyInstaller --noconsole Mode Uvicorn Logging Crash Fix
- **Stdout & Stderr Null Safety Guard**: Added fallback dummy stream guards (`open(os.devnull, 'w')`) when `sys.stdout` or `sys.stderr` is `None` under PyInstaller `--noconsole` execution mode in `src/main.py` and `src/backend/main_daemon.py`.
- **Uvicorn Color Log Disabled**: Set `use_colors=False` in `uvicorn.run()` within `start_daemon()`, preventing `uvicorn.logging.DefaultFormatter` from invoking `sys.stdout.isatty()` and raising `AttributeError: 'NoneType' object has no attribute 'isatty'`.

## [2026.07.31.002] - 2026-07-31


### 🛠️ Frozen PyInstaller Executable Recursion Fix & CLI Entry Dispatch
- **Headless Daemon Dispatch in `src/main.py`**: Added `multiprocessing.freeze_support()` and `--headless-daemon` command-line argument handling in `main()`, directly invoking `start_daemon()` when spawned in headless mode. This completely fixes the recursive process creation bug in frozen PyInstaller single-file executables and restores the system tray icon rendering.
- **Unit Test Coverage**: Added `test_main_headless_daemon_dispatch` in `tests/test_thin_client.py` to ensure `--headless-daemon` flag dispatches daemon execution without initializing `QApplication`.

## [2026.07.31.001] - 2026-07-31

### 🚀 Decoupled Architecture & Full-Flow CLI Client (`voice-input-cli`)
- **Headless Core Daemon (FastAPI & WebSockets)**: Extracted core engine into a standalone headless daemon (`src/backend/main_daemon.py`), offering RESTful control plane APIs (`/api/v1/health`, `/api/v1/config`, `/api/v1/config/sync`) and bidirectional WebSocket stream channels (`/ws/v1/voice-session`).
- **Core Engine & Async EventBus**: Created `CoreEngine` (`src/core/engine.py`) and a lightweight Python `asyncio` Pub/Sub `EventBus` (`src/core/event_bus.py`), completely decoupling core business state machines from PySide6 GUI dependencies.
- **Full-Flow CLI Tool (`voice-input-cli`)**: Built a feature-complete terminal command-line tool (`src/cli/main.py`) powered by `Typer` and `Rich`:
  - `daemon`: Manage backend process lifecycle (`start`, `stop`, `status`).
  - `config`: View, quick-set, and trigger WebDAV sync (`show`, `set`, `sync`).
  - `interactive`: Rich TUI interactive console menu with ASR and 7 LLM provider management centers (local, ollama, deepseek, qwen, openai, xiaomi, custom).
  - `record`: Full-flow CLI voice recording session with real-time ASCII volume bar (`Audio Level: [ ▂▄...]`), ASR live preview, UNIX pipeline `--raw` stdout redirect, and automatic clipboard sync.
- **Thin PySide6 Desktop Client**: Converted `VoiceInputController` into a thin WebSocket client with automatic daemon process lifecycle management (`DaemonProcessManager`).
- **Proxy Bypass for Local IPC**: Updated proxy utilities to automatically bypass system HTTP proxies for internal `127.0.0.1` IPC calls, preventing proxy loopbacks or connection refusals.

## [2026.07.30.018] - 2026-07-30

### 🛡️ Offline Model Detection & Win32 Job Process Tree Teardown
- **Offline Disk Model Probe**: Enhanced `is_model_downloaded` with offline manifest inspection (`~/.voiceinput/models/manifests/`), ensuring instant model status detection on application startup even when Ollama HTTP service is silent.
- **Win32 Job Object & Tree Teardown**: Bound Ollama process to Win32 Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) and added `taskkill /F /T` for `ollama.exe` and `ollama_llama_server.exe` tree termination, completely preventing orphan background processes.

## [2026.07.30.017] - 2026-07-30

### 🛠️ CI/CD Release Build Fix
- **Windows Executable Icon Fix**: Generated multi-resolution `assets/logo.ico` and added `pillow` dependency to GitHub Release workflow, fixing PyInstaller icon format error on Windows Server.

## [2026.07.30.016] - 2026-07-30

### 🚀 Zero-Compiler Local Engine, Decoupled Prompts & Final Polish
- **Stand-alone Zero-Build Engine**: Successfully migrated local LLM execution to a standalone Ollama binary (`~/.voiceinput/bin/ollama.exe`), completely fixing Python 3.14 and Windows C++ compiler errors.
- **Provider-Decoupled System Prompts**: Introduced `DEFAULT_LOCAL_SYSTEM_PROMPT` for local models with UI real-time prompt sync, ensuring unedited context retention and prohibiting artificial outer quote wrappers (`""`).
- **Model Preset Refinement**: Standardized on `Qwen2.5-1.5B` and `Qwen2.5-3B`, removing low-quality 0.5B model.
- **Linked Engine Lifecycle Teardown**: Automatically shuts down background Ollama processes on application exit to free system RAM and CPU.

## [2026.07.30.015] - 2026-07-30

### 🚀 Standalone Ollama Local LLM Engine & Prompt Optimization
- **Zero-Build Ollama Migration**: Replaced complex `llama-cpp-python` compilation with a 100% standalone, zero-compiler Ollama binary engine (`~/.voiceinput/bin/ollama.exe`), fixing Python 3.14/Windows C++ compiler errors completely.
- **Provider-Decoupled System Prompts**: Introduced provider-specific System Prompts (`DEFAULT_LOCAL_SYSTEM_PROMPT`) with UI sync, preserving full unedited context, preventing prompt example leaks, and prohibiting artificial quote wrappers.
- **Linked Engine Lifecycle Teardown**: Automatically shuts down background Ollama processes on application exit to save CPU and RAM.

## [2026.07.30.014] - 2026-07-30

### ⚡ Standardized uv Package Management Workflow
- **Pinned Python Version (.python-version)**: Added `.python-version` locking project runtime to Python 3.12, enabling seamless Wheel downloads without requiring local C++ compilation tools.
- **Modern uv Workflow Guide**: Updated `README.md` with official `uv` installation and environment setup instructions (`uv venv`, `uv pip install`, `uv run`).

## [2026.07.30.013] - 2026-07-30

### ⚡ Auto Local Inference Engine Installer (llama-cpp-python)
- **Automatic Framework Detection & One-Click Installer**: Added `is_llama_cpp_installed()` and `install_llama_cpp()` in `src/utils/model_downloader.py`. Automatically detects if the GGUF C/C++ inference binding library `llama-cpp-python` is present in the Python runtime.
- **Interactive UI Framework Installation**: Added `⚡ 自动安装推理依赖` (Auto Install Engine) button and status label in `LLMSettingsTab`. Automatically prompts user with confirmation dialogs to perform a background async `pip install` when using or downloading local models without requiring manual command-line execution.

## [2026.07.30.012] - 2026-07-30

### 🤖 Local LLM Provider, WebDAV Path Precision, Logo & Dynamic Versioning
- **Local GGUF LLM Provider**: Added `local` LLM provider support in `src/refine/llm.py` and `src/ui/settings/llm_tab.py`. Supports running GGUF models locally with automatic fallback.
- **Model Downloader & Manager**: Implemented `src/utils/model_downloader.py` storing models in `~/.voiceinput/models/`. Features model selection (Qwen2.5-0.5B/1.5B), confirmation popups with model ID and file size, progress dialog, proxy support via `src/utils/proxy.py`, and a "Delete Local Model" button with confirmation.
- **WebDAV Path Resolution Fix**: Refactored `WebDAVSync._get_url_for_path()` in `src/utils/webdav.py` with standard `urllib.parse` path splitting and subpath deduplication. Ensures subpaths (e.g. `/dav/`, `/remote.php/webdav/`) are correctly preserved and automatically creates local destination directories.
- **Single-Source Versioning**: Created `src/utils/version.py` (`get_app_version()`, `get_logo_path()`) to dynamically read the single-source `VERSION` file in both development and PyInstaller frozen environments.
- **Transparent Vector Logo**: Created and integrated a clean transparent background PNG logo (`assets/logo.png`) displayed in the About tab and header.

## [2026.07.30.011] - 2026-07-30

### 🚀 CI/CD Cumulative Release Changelog Extraction
- **Cumulative GitHub Release Notes Algorithm**: Upgraded `.github/workflows/release.yml` to automatically parse and extract all cumulative changelog entries spanning between the previous GitHub Release tag and the current target version (`$lastTag` to `$ver`). Ensures that when multiple local releases are pushed together, the release notes on GitHub encompass all version changes since the last release.

## [2026.07.30.010] - 2026-07-30

### 🌐 Capsule Position Dropdown i18n Fix
- **Capsule Position ComboBox i18n Localization**: Added i18n translations for Capsule Position options (`pos_bottom_center`, `pos_top_center`, `pos_center`), displaying `底部居中`, `顶部居中`, `屏幕中央` in Chinese and `Bottom Center`, `Top Center`, `Center` in English, while preserving exact configuration string compatibility (`bottom_center`, `top_center`, `center`).

## [2026.07.30.009] - 2026-07-30

### 🐛 Hotkey Tab i18n Refresh Fix
- **Hotkey & General Tab i18n Retranslation Fix**: Fixed missing dynamic i18n label and button updates in `HotkeySettingsTab` (`src/ui/settings/hotkey_tab.py`). Added explicit label references (`lbl_language`, `lbl_hotkey`, `lbl_position`), dropdown item re-population (`_populate_languages`), and recorder widget retranslation (`HotkeyRecorderWidget.retranslate_ui`).

## [2026.07.30.008] - 2026-07-30

### 🌐 Comprehensive 100% i18n Sub-Page Coverage & Dynamic Retranslation
- **100% Sub-Page i18n Localization**: Fully refactored all 7 settings sub-tabs (`asr_tab`, `llm_tab`, `webdav_tab`, `proxy_tab`, `hotkey_tab`, `debug_tab`, `about_tab`), dialogs, and form labels to retrieve text dynamically from `i18n.t(...)`.
- **Dynamic Real-Time UI Retranslation**: Implemented `retranslate_ui()` in `SettingsWindow` so that saving or changing language preferences instantly refreshes all Tab headers, window titles, and action button labels without restarting the app.
- **Key Parity Verification**: Added key parity test (`test_translation_keys_parity`) ensuring 100% symmetric key coverage between Chinese (`zh_CN`) and English (`en_US`).

## [2026.07.30.007] - 2026-07-30

### 🌐 i18n Internationalization & Auto System Language
- **i18n Multi-Language Engine**: Added `src/i18n.py` supporting English (`en_US`) and Simplified Chinese (`zh_CN`).
- **Auto OS Language Detection**: Automatically detects Windows OS system locale (`QLocale.system().name()`), defaulting to Simplified Chinese on Chinese systems and English on international systems.
- **Language Switcher UI**: Added Language selector (`Auto`, `简体中文`, `English`) in Hotkey & General Settings Tab.
- **UI Localization**: Fully localized Settings window, Floating Capsule, and System Tray Menu items.

## [2026.07.30.006] - 2026-07-30

### 🚀 Debug Logging & Proxy Visibility
- **Explicit Proxy Logging**: Updated `src/utils/proxy.py`, `src/refine/llm.py`, and `src/asr/xiaomi_mimo.py` to output explicit log tags (`[PROXY ENABLED: socks5://127.0.0.1:7890]`, `[VIA PROXY: ...]`, `[DIRECT]`) when global proxy is active, making network routing 100% visible in debug logs.

## [2026.07.30.005] - 2026-07-30

### 🚀 Features & Debug Logging
- **WebDAV Provider Mode**: Added provider mode support to WebDAV Settings (`src/ui/settings/webdav_tab.py`), defaulting to `jianguoyun` (坚果云) while supporting `custom` WebDAV providers.
- **Timestamped Debug Logging Mode**: Added Debug Settings Tab (`src/ui/settings/debug_tab.py`) and `AppLogger` (`src/utils/logger.py`). When Debug Mode is ON, writes timestamped plaintext ASR & LLM recognition logs to `<app_dir>/logs/voice_input_YYYYMMDD.log` for troubleshooting. When OFF, zero logging occurs to preserve privacy.
- **Default Hotkey Verification**: Verified and enforced `Key.ctrl_r` (`Right Control`) as the default trigger hotkey across configuration and recorder settings.

## [2026.07.30.004] - 2026-07-30

### 🚀 WebDAV Backup Rotation & Dir Simplification
- **Remote Directory Simplification**: Updated WebDAV config to specify remote directory (`remote_dir`, default `/VoiceInput`) while maintaining `config.json` as the primary configuration file.
- **Timestamped History Backups**: Enhanced upload history backups with timestamp suffix (e.g. `config_20260730_101629.json`).
- **Max 5 Backups Auto-Retention Cleanup**: Implemented automatic backup rotation with default `max_backups = 5` retention. When backup files exceed 5, oldest history files are automatically deleted via WebDAV `DELETE` API.

## [2026.07.30.003] - 2026-07-30

### 🧪 Testing & E2E Integration Suite
- **Comprehensive Unit & Integration Test Suite**: Expanded `tests/` directory with 19 comprehensive unit and E2E integration tests:
  - `tests/test_config_manager.py`: Configuration loading, portable mode, AppData resolution, and directory anomaly fallback.
  - `tests/test_webdav_sync.py`: WebDAV upload, download, and history backup PROPFIND XML response parsing.
  - `tests/test_proxy.py`: Environment proxy injection and network connection testing.
  - `tests/test_hotkey.py`: Strict VK matching for Left vs Right Control/Alt.
  - `tests/test_llm_providers.py`: 6-provider configuration and spoken self-correction prompt logic.
  - `tests/test_e2e_pipeline.py`: Full end-to-end integration test (Floating capsule -> ASR -> LLM refinement -> Injector).

## [2026.07.30.002] - 2026-07-30

### 🚀 Features & Architecture Refactoring
- **6-Provider LLM Refinement**: Refactored LLM Settings to provider mode supporting OpenAI, DeepSeek, Xiaomi, Qwen, Ollama, and Custom providers.
- **WebDAV Configuration Sync**: Added WebDAV sync tab (`src/ui/settings/webdav_tab.py`) supporting upload, download, remote backup history browser dialog (`WebDAVHistoryDialog`), and startup auto-sync.
- **Global Network Proxy Support**: Added proxy settings tab (`src/ui/settings/proxy_tab.py`) supporting HTTP/SOCKS4/SOCKS5, default placeholders (`127.0.0.1:7890`), and connection testing.
- **Software Info & About Tab**: Added About tab (`src/ui/settings/about_tab.py`) showcasing app title, author (`Zuluion`), current version (`VERSION`), repo link, and update checker.
- **Floating Capsule 30 FPS Animation**: Enhanced floating capsule UI (`src/ui/capsule.py`) with 30 FPS timer, breathing REC dot glow, and dynamic wave animation.
- **Settings Architecture Modularization**: Refactored `src/ui/settings.py` into a modular package `src/ui/settings/` (`asr_tab`, `llm_tab`, `webdav_tab`, `proxy_tab`, `hotkey_tab`, `about_tab`, `window.py`).

## [2026.07.30.001] - 2026-07-30

### 🚀 LLM Refinement Prompt Enhancement
- **Speech Self-Correction & Mid-Sentence Revision**: Upgraded default LLM System Prompt in `src/refine/llm.py`, `src/config.py`, and `docs/specs/speech_input_windows_spec.md` to intelligently handle spoken self-corrections (e.g., "A, wait, change to B", "xxx, then aaa, nevermind, bbb" -> "xxx, bbb"), preserving context while replacing discarded intent.

## [2026.07.29.007] - 2026-07-29

### 🐛 Bug Fixes & Scoop Persistence
- **Scoop Config Directory Fix**: Added `pre_install` hook to `voice-input.json` to pre-create `config.json` as a file before Scoop links persistence, preventing Scoop from miscreating `config.json` as a directory.
- **ConfigManager AppData Fallback**: Added `resolve_config_path()` in `src/config.py` with AppData directory fallback (`%APPDATA%\VoiceInput\config.json`) if local `config.json` is a directory or missing, providing robust native Windows persistence across upgrades.

## [2026.07.29.006] - 2026-07-29

### 🚀 Packaging & Scoop
- **Scoop Config Persistence**: Added `"persist": "config.json"` to `voice-input.json` Scoop manifest so user configurations (API keys, endpoints, prompts, hotkeys) are automatically preserved across `scoop update` application upgrades.

## [2026.07.29.005] - 2026-07-29

### 📝 Documentation
- **Hotkey Documentation Sync**: Updated [README.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/README.md) and [docs/specs/speech_input_windows_spec.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/docs/specs/speech_input_windows_spec.md) examples and setup instructions to use `Right Control` (`Key.ctrl_r`) as the default recommended trigger hotkey.

## [2026.07.29.004] - 2026-07-29

### 🐛 Bug Fixes
- **UTF-8 Emoji Encoding in Release Changelog**: Fixed corrupted emoji characters (`ðŸš€`, `ðŸ›`) in GitHub Release notes by switching workflow shell to `pwsh` (PowerShell 7) and explicitly enforcing `-Encoding utf8` on all `Get-Content` calls in `.github/workflows/release.yml`.

## [2026.07.29.003] - 2026-07-29

### 🚀 Features & UX
- **Default Hotkey Update**: Changed default recommended trigger hotkey to `Right Control` (`Key.ctrl_r`) to avoid Windows system menu focus stealing issues caused by `Alt` keys.

### 🐛 Bug Fixes
- **Strict Hotkey Matching**: Refactored `_match_key()` in `src/core/hotkey.py` to strictly distinguish `Right Alt` (VK 165) from `Left Alt` (VK 164) and `Right Control` (VK 163) from `Left Control` (VK 162), preventing `Left Alt` from accidentally triggering recording when set to `Right Alt`.

## [2026.07.29.002] - 2026-07-29

### 🐛 Bug Fixes
- **PyInstaller Frozen Bundle Module Import**: Fixed `ModuleNotFoundError: No module named 'src'` when launching standalone compiled `VoiceInput.exe` by supporting `sys._MEIPASS` path resolution in `src/main.py` and adding `--paths "."` to PyInstaller build flags.

## [2026.07.29.001] - 2026-07-29

### 🚀 Features
- **Xiaomi MiMo ASR**: Added integration for Xiaomi MiMo `mimo-v2.5-asr` Base64 Audio API (`src/asr/xiaomi_mimo.py`).
- **3-Stage Floating Capsule**: Implemented `PREPARING` amber loading pulse, `LISTENING` bright white with glowing 🔴 REC dot, and `REFINING` purple state animations.
- **Interactive Hotkey Recorder**: Added `HotkeyRecorderWidget` with mechanical keyboard keycap badge (`[ Right Alt ]`) and direct `pynput` key capture.
- **Dynamic Model Fetching**: Added `🔄 Fetch Models` button to dynamically fetch provider models via `/models` API and populate `QComboBox`.
- **LLM Refinement & Speech Cleaning**: Added prompt-based removal of speech dysfluencies ("呃", "啊", "那个") and customizable System Prompt editor with `↺ Reset Prompt`.
- **Audio Hotplugging**: Added PortAudio re-scanning on every hotkey trigger to support USB/Bluetooth mic hotplugging without restarting app.
- **Connection Testing**: Added `Test ASR Connection` and `Test LLM Connection` buttons in settings GUI.
- **Automated CI/CD**: Added GitHub Actions workflow for automated PyInstaller builds and Scoop manifest updates.

### 🐛 Bug Fixes
- Fixed `Right Alt` (AltGr) key recording issue where Windows `VK_RMENU` was misidentified as `Left Alt` in Qt event layer.
- Fixed `QCheckBox` dark theme visibility issue in settings GUI.
- Fixed Qt thread safety issues by decoupling ASR/LLM network calls using `ASRProcessingWorker(QThread)`.
