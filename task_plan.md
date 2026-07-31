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
- [x] **Decoupled Architecture & Spec Design**: Authored decoupled architecture design ([optimization_decoupled_architecture_design_2026-07-31.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/docs/specs/optimization_decoupled_architecture_design_2026-07-31.md)) and full-flow CLI spec ([spec_decoupled_architecture_and_cli.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/docs/specs/spec_decoupled_architecture_and_cli.md)).

## Completed Refactoring & Full Testing Tasks (Phases 1 to 3)
- [x] **Phase 1: In-Memory CoreEngine Extraction & Async EventBus**
  - [x] Extracted `CoreEngine` from `VoiceInputController`, replacing Qt `Signal/Slot` with async EventBus (`src/core/event_bus.py`, `src/core/engine.py`).
  - [x] Unit tests passed (`tests/test_event_bus.py`, `tests/test_core_engine.py`).
- [x] **Phase 2: Headless Daemon (FastAPI/WebSockets) & HAL Separation**
  - [x] Implemented `src/backend/main_daemon.py` with RESTful `/api/v1` and WebSocket `/ws/v1/voice-session`.
  - [x] API integration & WebSocket stream tests passed (`tests/test_backend_daemon.py`).
- [x] **Phase 3: Full-Flow CLI Tool (`voice-input-cli`) & E2E Testing**
  - [x] Implemented `voice-input-cli` (daemon lifecycle, TUI config, record command with Rich ASCII wave and stdout/clipboard outputs in `src/cli/main.py`).
  - [x] CLI integration & end-to-end full-flow tests passed (`tests/test_cli.py`).
- [x] **Phase 4: PySide6 Thin Client Adapter**
  - [x] Refactored `src/main.py` (`VoiceInputController`) into Thin Desktop Client with `DaemonProcessManager` auto-托管 lifecycle.
  - [x] Bound GUI capsule, audio recorder, and settings window to Daemon via WebSocket and REST APIs.
  - [x] Added `tests/test_thin_client.py` and passed full regression suite (47/47 passed).
- [x] **Phase 5: PyTest Execution Freeze & Async WebSocket Stability Fix**
  - [x] Fixed `llm_model` `MagicMock` JSON serialization in `last_trace_meta`.
  - [x] Added UTF-8 / GBK encoding fallback protection to `AppLogger`.
  - [x] Optimized `EventBus.emit()` for same-loop `create_task` dispatch.
  - [x] Configured `NO_PROXY` / `no_proxy` loopback bypass in `apply_proxy_config()`.
  - [x] Full regression test suite passed (48/48 passed).
- [x] **Phase 6: CLI Daemon Stop Command & Comprehensive Doc Sync**
  - [x] Added `voice-input-cli daemon stop` command with cross-platform PID termination.
  - [x] Verified full regression test suite (49/49 passed).
  - [x] Synchronized all project documentation (README, Spec, Changelog, Version).


