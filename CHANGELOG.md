# Changelog

All notable changes to this project will be documented in this file.

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
