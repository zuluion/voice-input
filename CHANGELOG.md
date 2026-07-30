# Changelog

All notable changes to this project will be documented in this file.

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
