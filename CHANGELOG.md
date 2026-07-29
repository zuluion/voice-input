# Changelog

All notable changes to this project will be documented in this file.

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
