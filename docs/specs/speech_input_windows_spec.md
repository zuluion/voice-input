# 规格文档 (Spec / PRD): Windows 系统托盘语音输入法应用

## Problem Statement

在 Windows 操作系统下，用户在日常办公、代码编写和文档创作时面临以下文本输入痛点：
1. **键盘输入效率受限**：长文本或灵感记录时键盘打字速度有限，容易打断思考节奏。
2. **缺乏高质量与定制化语音输入工具**：系统自带语音识别准确率有限，无法直接接入豆包 (Doubao)、通义千问 (Qwen)、小米 (Xiaomi MiMo `mimo-v2.5-asr`) 等高精度国内第三方语音大模型。
3. **口语冗余与专业术语识别率低**：传统 ASR（自动语音识别）容易产生中文谐音错误、英文术语错写，且包含大量口语冗余（如“呃”、“啊”、“那个”、口吃与停顿），缺乏大语言模型（LLM）的智能精修与口语清洗机制。
4. **交互不够轻量无感**：缺少像 macOS 胶囊悬浮窗一样即按即用、平滑且不强占焦点的快捷语音输入体验。

---

## Solution

基于 Python 3.10+ 与 PySide6 开发一款 Windows 平台的系统托盘语音输入法应用。

该应用具备以下核心特性：
- **前后端分离架构与无头后端守护进程 (Headless Core Daemon)**：后端核心引擎下沉为独立无头守护进程 (`src/backend/main_daemon.py`)，基于 FastAPI + WebSockets 提供标准 RESTful 控制面 (`/api/v1/*`) 与双向实时 WebSocket 数据流 (`/ws/v1/voice-session`)。
- **全流程 CLI 命令行客户端 (`voice-input-cli`)**：提供无 GUI 环境下的终端全流程命令行工具 (`src/cli/main.py`)，支持 Daemon 生命周期管理 (`daemon start/stop/status`)、命令行语音录制与 UNIX 管道 (`record --raw`)，以及内建 ASR 与 7 大 LLM 供应商管理中心的 Rich TUI 交互式控制台。
- **全局长按热键触发**：按住指定热键（推荐 `Right Control` 或 `Alt+Space`）即刻开始录音，松开按键自动精修并注入文本。支持交互式按键录制。
- **多 Provider ASR 架构**：深度接入小米 MiMo (`mimo-v2.5-asr` Base64 Audio API)、豆包 (Volcengine)、通义千问 (DashScope) 以及 OpenAI 兼容的 `/v1/audio/transcriptions` 接口。
- **三阶段视觉交互与多位置胶囊悬浮窗**：置顶无任务栏图标的胶囊浮窗，具备 30 FPS 动态呼吸与波形演进，支持底部居中、顶部居中与屏幕中央定位：
  - **`Preparing...`**：琥珀黄缓冲扫频脉冲。
  - **`Listening...`**：亮白文字 + 🔴 高亮发光呼吸 REC 红灯 + 5-Bar 动态音量波形（无声间隙保持微弱呼吸扫频）。
  - **`Refining...`**：紫色柔和退场。
- **智能 LLM 文本精修、口误中途改口覆盖与口语清洗 (Refinement)**：支持 **7 大 LLM 供应商模式**（OpenAI, DeepSeek, Xiaomi, 阿里云通义千问, 本地 Ollama, Custom 自定义, 本地免编译 GGUF）。不仅修复谐音与术语，更可自动识别“不对”、“算了”、“改成”等改口信号并替换废弃表达，本地模式通过免 C++ 编译的独立 Ollama 引擎（`~/.voiceinput/bin/ollama.exe`）托管，具备离线磁盘清单探针与 Win32 Job Object (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`) 及 `taskkill /F /T` 进程树同生共死联动销毁。
- **单源真实版本控制与透明矢量 Icon 整合**：以根目录 `VERSION` 文件作为 Single Source of Truth，系统托盘、任务栏 AppUserModelID、关于窗口全量绑定统一高质感透明背景 Logo (`assets/logo.png`)。
- **WebDAV 供应商模式、全量配置同步与最多 5 个备份循环清理**：支持坚果云与自定义 WebDAV 供应商，远端目录简化为保存路径（如 `/VoiceInput`），自动为上传历史生成年月日时间戳后缀（如 `config_20260730_101629.json`），并在超过 5 个备份时自动物理删除最旧的历史文件。
- **全局网络代理支持 (HTTP / SOCKS4 / SOCKS5)**：支持一键开关代理、配置主机名（默认提示 `127.0.0.1`）与端口号（默认提示 `7890`），全量注入环境变量驱动 API、WebSocket 与网络请求走代理。
- **带时间戳调试日志模式 (Debug Logging Mode)**：提供独立 `🐞 Debug` 调试设置页，开启时在本地 `logs/voice_input_YYYYMMDD.log` 生成带有毫秒级时间戳及 `[VIA PROXY: ...]` 路由标签的 ASR/LLM 明文日志，关闭时全流程零磁盘日志以保护隐私。
- **i18n 多语言引擎与 Windows 系统语言自动检测**：内置 **简体中文 (`zh_CN`)** 与 **English (`en_US`)** 完整国际化支持，自动识别操作系统语言，且支持在设置界面一键切换并即时动态重绘全软件所有 Tab 与 Label。
- **软件信息与一键版本更新**：提供独立 About 页展示作者（`Zuluion`）、当前滚动版本号、GitHub 官方仓库链接及一键检查最新 Release 更新。
- **无缝文本注入**：基于剪贴板备份与 Win32 `SendInput` 快捷键模拟，将最终文本安全注入到当前聚焦的任意输入框，并无感恢复原剪贴板内容。
- **模块化设计的暗黑 Settings GUI 与硬件热插拔支持**：
  - 重构拆分为 `src/ui/settings/` 模块包（`asr_tab`, `llm_tab`, `webdav_tab`, `proxy_tab`, `hotkey_tab`, `debug_tab`, `about_tab`）。
  - 支持 `🔄 Fetch Models` 动态拉取服务商可用模型列表 (`/models` API)。
  - 支持一键连通性测试。

---

## User Stories

1. As a Windows power user, I want to trigger voice recording by holding down a configurable global key (e.g. `Right Control`), so that I can capture my spoken words instantly without focusing on a specific app window or losing menu focus.
2. As a user, I want to interactively record my custom trigger hotkey inside the settings GUI using a keyboard keycap badge (e.g. `[ Right Control ]`), so that I don't need to manually type raw key names.
3. As a developer, I want to connect the app to third-party ASR providers (Xiaomi MiMo `mimo-v2.5-asr`, Doubao, Qwen, OpenAI-compatible HTTP), so that I can leverage state-of-the-art speech recognition models.
4. As a user, I want a 3-stage floating capsule window (`Preparing...` -> `Listening...` with a breathing red 🔴 REC dot -> `Refining...`), so that I know precisely when the microphone is ready and capturing my voice.
5. As a user, I want the capsule window's 5 waveform bars to dynamically respond to my actual speaking volume level in real-time while maintaining a subtle breathing motion during quiet pauses, so that the interface feels alive.
6. As a user, I want LLM refinement to select from 6 major providers (OpenAI, DeepSeek, Xiaomi, Qwen, Ollama, Custom), automatically fix technical jargon, clean filler words, AND handle mid-sentence self-corrections ("A, wait, change to B" -> "B"), so that injected text is accurate and polished.
7. As a user, I want to sync my `config.json` to my Jianguoyun/custom WebDAV server, auto-rotate up to 5 timestamped backups, view remote backup history, restore previous configs, or auto-sync on startup, so that my settings are never lost across devices.
8. As a user behind a network proxy, I want to enable HTTP/SOCKS proxy (e.g. `127.0.0.1:7890`) in settings so that all network requests route through my local proxy seamlessly with explicit proxy tags in debug logs.
9. As an international user, I want the app to automatically adapt to my system language (Simplified Chinese or English) and allow instant real-time switching without restarting.
10. As a user, I want an About tab displaying app info, author (`Zuluion`), current version, and an option to check for GitHub updates.

---

## Implementation Decisions

### 1. High-Level Architecture & Module Boundaries
应用采用基于 Python 3.10+ 与 PySide6 的分层事件驱动架构，使用 `QThread` 实现耗时任务与主 GUI 线程解耦：

```
+-----------------------------------------------------------------------+
|                             Main App                                  |
|                 (main.py / Controller / QThread Worker)               |
+-------+---------------+---------------+---------------+---------------+
        |               |               |               |
        v               v               v               v
+---------------+ +-----------+ +---------------+ +-----------+
| Hotkey Engine | | Audio Engine| | ASR Adapter   | | LLM Engine|
| (pynput/Win32)| |(sounddevice)| | (Xiaomi MiMo/ | | (6-Provider|
|               | | (RMS Calc)  | |  Qwen/Doubao) | |  Support) |
+---------------+ +-----------+ +---------------+ +-----------+
        |               |               |               |
        +---------------+---------------+---------------+
                        |
                        v
        +-------------------------------+
        | UI Layer                      |
        | - Floating Capsule (30 FPS)   |
        | - System Tray                 |
        | - Modular Settings (src/ui/   |
        |   settings/ subpackage)       |
        | - i18n Internationalization   |
        +-------------------------------+
                        |
                        v
        +-------------------------------+
        | Utils Layer                   |
        | - Text Injector (SendInput)   |
        | - WebDAV Sync (Max 5 Clean)   |
        | - Network Proxy Engine        |
        | - AppLogger (Debug Mode)      |
        +-------------------------------+
```

### 2. Module Specifications

#### A. Hotkey & Event Hook (`core/hotkey.py`)
- 使用 `pynput.keyboard` 全局 Hook 捕获修饰键/组合键状态（`on_press` / `on_release`）。
- 精确匹配 `Right Control` (VK 163) 与 `Right Alt` (VK 165)，严格隔离左侧修饰键。

#### B. Audio & Waveform Level Engine (`audio/recorder.py`)
- 基于 `sounddevice.InputStream` 异步捕获默认麦克风音频数据（采样率 16000Hz, 16bit, 单声道 PCM）。

#### C. Multi-Provider ASR Engine (`asr/base.py`, `asr/xiaomi_mimo.py`, `asr/doubao.py`, `asr/qwen.py`, `asr/openai_http.py`)
- 接入 Xiaomi MiMo (`mimo-v2.5-asr`), Doubao, Qwen, OpenAI-compatible HTTP.

#### D. Floating Capsule Window (`ui/capsule.py`)
- 30 FPS `QTimer` 动效驱动，支持 `bottom_center` / `top_center` / `center` 灵活屏幕定位：
  - `PREPARING`：琥珀黄扫频。
  - `LISTENING`：🔴 REC 红色指示灯呼吸脉冲 + 5-Bar 音量与扫频无缝混合波形。
  - `REFINING`：紫色柔和退场。

#### E. 6-Provider LLM Refinement (`refine/llm.py`)
- 支持 `openai`, `deepseek`, `xiaomi`, `qwen`, `ollama`, `custom` 供应商模式。
- 系统提示词全面覆盖语气词清洗、术语修正、口误改口覆盖与标点整理。

#### F. WebDAV Sync Engine (`utils/webdav.py`)
- 支持 `jianguoyun` 与 `custom` 供应商，支持 `PUT` 上传、`GET` 下载、`PROPFIND` 列出远端备份文件、时间戳历史命名、最多 5 个备份自动物理清理，支持浏览远端历史备份文件并一键恢复至本地。

#### G. Network Proxy Manager (`utils/proxy.py`)
- 支持 `http`, `socks4`, `socks5` 协议，统一注入 `HTTP_PROXY` / `HTTPS_PROXY` / `ALL_PROXY` 环境变量。

#### H. AppLogger Debug Engine (`utils/logger.py`)
- 开关式日志管理器，开启时在本地 `logs/voice_input_YYYYMMDD.log` 生成带有毫秒级时间戳及 `[VIA PROXY: ...]` 路由标签的 ASR/LLM 明文日志。

#### I. i18n Internationalization Engine (`i18n.py`)
- 支持 `zh_CN` 与 `en_US` 完整词条映射，调用 `QLocale` 自动适配系统语言。

#### J. Modular Settings Package (`src/ui/settings/`)
- 拆分为子包：`window.py`, `asr_tab.py`, `llm_tab.py`, `webdav_tab.py`, `proxy_tab.py`, `hotkey_tab.py`, `debug_tab.py`, `about_tab.py`。

---

## Out of Scope

1. **macOS / Linux 平台支持**：本 Spec 仅针对 Windows 10/11 平台。
2. **离线本地大模型推理引擎**：不内置本地 llama.cpp 依赖，依赖在线 API 或本地 Ollama/vLLM HTTP 服务。
