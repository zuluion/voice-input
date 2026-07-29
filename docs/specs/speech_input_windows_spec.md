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
- **全局长按热键触发**：按住指定热键（如 `Right Alt` 或 `Alt+Space`）即刻开始录音，松开按键自动精修并注入文本。支持交互式按键录制。
- **多 Provider ASR 架构**：深度接入小米 MiMo (`mimo-v2.5-asr` Base64 Audio API)、豆包 (Volcengine)、通义千问 (DashScope) 以及 OpenAI 兼容的 `/v1/audio/transcriptions` 接口。
- **三阶段视觉交互胶囊悬浮窗**：置顶无任务栏图标的胶囊浮窗，具备 **`Preparing...`** (缓冲扫频动画)、**`Listening...`** (亮白 + 🔴 REC 发光指示灯 + RMS 动态波形条)、**`Refining...`** (柔和紫光) 三阶段流畅状态转换。
- **智能 LLM 文本精修与口语清洗 (Refinement)**：通过 OpenAI 兼容接口接入 LLM，不仅修复谐音与术语，更能自动去除“呃”、“啊”、“那个”等口语冗余，转化为流畅书面语。支持在 UI 中自定义 System Prompt 并一键恢复默认。
- **无缝文本注入**：基于剪贴板备份与 Win32 `SendInput` 快捷键模拟，将最终文本安全注入到当前聚焦的任意输入框，并无感恢复原剪贴板内容。
- **现代暗黑风 Settings GUI 与硬件热插拔支持**：
  - 支持供应商参数全动态联动与官方 Base URL/Model 默认值自动填充。
  - 支持 `🔄 Fetch Models` 动态拉取服务商可用模型列表 (`/models` API)。
  - 支持 `Test Connection` 一键连通性测试。
  - 支持音频设备热插拔重新扫描与无设备双重弹窗/通知提醒。

---

## User Stories

1. As a Windows power user, I want to trigger voice recording by holding down a configurable global key (e.g. `Right Alt`), so that I can capture my spoken words instantly without focusing on a specific app window.
2. As a user, I want to interactively record my custom trigger hotkey inside the settings GUI using a keyboard keycap badge (e.g. `[ Right Alt ]`), so that I don't need to manually type raw key names.
3. As a developer, I want to connect the app to third-party ASR providers (Xiaomi MiMo `mimo-v2.5-asr`, Doubao, Qwen, OpenAI-compatible HTTP), so that I can leverage state-of-the-art speech recognition models.
4. As a user, I want a 3-stage floating capsule window (`Preparing...` -> `Listening...` with a glowing red 🔴 REC dot -> `Refining...`), so that I know precisely when the microphone is ready and capturing my voice.
5. As a user, I want the capsule window's 5 waveform bars to dynamically respond to my actual speaking volume level in real-time, so that I can intuitively verify audio input quality.
6. As a user, I want LLM refinement to automatically fix misrecognized technical jargon (e.g. "配森" -> "Python") AND clean speech dysfluencies (removing filler words like "呃", "那个"), so that the injected text is fluent written prose.
7. As a power user, I want to customize the LLM System Prompt in the Settings GUI, so that I can tailor the LLM polishing style to my personal workflow.
8. As a user, I want the settings GUI to dynamically fill default Base URLs, fetch available model lists from `/models` endpoints, and offer `Test Connection` buttons, so that setup is effortless and error-free.
9. As a user, I want the app to inject text via standard clipboard paste (`Ctrl+V`) and immediately restore my previous clipboard contents, so that my active clipboard data is never corrupted.
10. As a user, I want clear popup warnings and tray notifications if no microphone device is detected, and I want the system to auto-detect newly plugged-in USB/Bluetooth microphones on the next hotkey press without restarting the app.

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
| (pynput/Win32)| |(sounddevice)| | (Xiaomi MiMo/ | | (OpenAI   |
|               | | (RMS Calc)  | |  Qwen/Doubao) | |  Client)  |
+---------------+ +-----------+ +---------------+ +-----------+
        |               |               |               |
        +---------------+---------------+---------------+
                        |
                        v
        +-------------------------------+
        | UI Layer                      |
        | - Floating Capsule (3-Stage)  |
        | - System Tray (QSystemTrayIcon)|
        | - Settings Window (Dark QSS)  |
        +-------------------------------+
                        |
                        v
        +-------------------------------+
        | Text Injection Engine         |
        | (Clipboard Backup + SendInput)|
        +-------------------------------+
```

### 2. Module Specifications

#### A. Hotkey & Event Hook (`core/hotkey.py`)
- 使用 `pynput.keyboard` 全局 Hook 捕获修饰键/组合键状态（`on_press` / `on_release`）。
- 增强 `Right Alt` (AltGr) 与 Win32 `VK_RMENU (165)` / `VK_LMENU (164)` 的匹配识别，排除 Windows 系统的伴随信号干扰。
- 维持按键防抖逻辑，触发 `recording_started` 与 `recording_stopped` 信号。

#### B. Audio & Waveform Level Engine (`audio/recorder.py`)
- 基于 `sounddevice.InputStream` 异步捕获默认麦克风音频数据（采样率 16000Hz, 16bit, 单声道 PCM）。
- **设备热插拔重扫描**：每次 `start()` 触发时自动调用 `sd._terminate()` 与 `sd._initialize()` 重新感应当年前后接入的麦克风硬件。若无可用设备，发射 `error_occurred` 触发 `QMessageBox` 与系统托盘气泡警报。
- 捕获首帧音频时发射 `recording_ready` 信号，指示胶囊进入 `LISTENING` 阶段。
- 实时计算 RMS 包络并经过 Attack 40%/Release 15% 平滑算法分配 5 根竖条高度标度。

#### C. Multi-Provider ASR Engine (`asr/base.py`, `asr/xiaomi_mimo.py`, `asr/doubao.py`, `asr/qwen.py`, `asr/openai_http.py`)
- 定义抽象基类 `BaseASRProvider`。
- **小米 MiMo ASR (`mimo-v2.5-asr`)**：PCM 转内存 WAV 字节流，转换为 Base64 `data:audio/wav;base64,...` 发送至开放平台 API。
- **通义千问 DashScope / 豆包 / OpenAI**：封装各平台官方 HTTP RESTful 与音频转录端点，全员具备控制台日志与 `error_occurred` 错误响应。

#### D. Floating Capsule Window (`ui/capsule.py`)
- `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool` + `Qt.WA_TranslucentBackground`。
- **三阶段视觉交互**：
  - `PREPARING`：琥珀黄文字 `Preparing...` + 5-Bar Loading 扫频脉冲动画。
  - `LISTENING`：亮白文字 `Listening...` + 🔴 高亮发光 REC 录音指示灯 + 音量驱动波形。
  - `REFINING`：紫色文字 `Refining...` + 柔和退场。

#### E. LLM Refinement & Dysfluency Cleaning (`refine/llm.py`)
- 通过 `requests` 发起 OpenAI 兼容接口请求（支持任意标准 API 或本地 Ollama/vLLM 服务）。
- **内置默认提示词 (Default System Prompt)**：
  ```text
  你是一个专业的语音输入文本精修与整理助手。请对输入的语音识别文本进行智能润色与纠错，严格遵循以下规则：
  1. 移除口语冗余：自动删除语气词（如“呃”、“啊”、“那个”、“就是”）、口吃重叠字及不连贯的语气停顿。
  2. 语音识别纠错：自动修复谐音错别字、中文拼音误写，以及英文/技术术语（例如将“配森”修正为“Python”，“杰森”修正为“JSON”）。
  3. 语句顺畅化：在不改变用户原意的前提下，适当优化句式与标点符号，使口语转为流畅、通顺的书面表达。
  4. 输出要求：仅输出精修与整理后的最终文本，不要包含任何解释、前言或总结说明。
  ```

#### F. Text Injection Engine (`utils/injector.py`)
- 备份剪贴板内容 -> 写入精修文本 -> Win32 `SendInput(Ctrl+V)` -> `QTimer.singleShot(150)` 还原剪贴板。

#### G. System Tray & Modern Settings Window (`ui/tray.py`, `ui/settings.py`)
- 高质感 `#12151e` 暗黑护眼主题（QSS）。
- **ASR 供应商全联动**：切换供应商自动更新 Key 标签、App ID 显隐、Base URL & Default Model。
- **动态获取可用模型**：`🔄 Fetch Models` 按钮请求 `{base_url}/models` 并将 Model Name 升级为下拉选择框。
- **交互式热键录制器 (`HotkeyRecorderWidget`)**：基于同源 `pynput` 监听捕获，键盘键帽徽章展示（如 `[ Right Alt ]`），带 `↺ Reset` 按钮。
- **自定义 Prompt 编辑器**：支持多行自定义 System Prompt 编辑与一键恢复默认。
- **一键连通性测试**：`Test ASR Connection` 与 `Test LLM Connection` 按钮。

---

## Testing Decisions

### 1. Seam Selection & Strategy
测试策略聚焦于外部行为与关键 Seam 隔离：
- **ASR Adapter Seam** (`tests/test_asr_adapter.py`)：校验 `mimo-v2.5-asr` WAV 数据流 Payload 组装与 Base64 请求格式。
- **LLM Refine Seam** (`tests/test_llm_refine.py`)：校验口语冗余清洗与术语纠错逻辑。
- **Audio RMS Envelope Seam** (`tests/test_audio_rms.py`)：校验正弦波音量平滑包络与 Mock InputStream。
- **Clipboard Injection Seam** (`tests/test_injector.py`)：校验 SendInput 与剪贴板延迟还原。

---

## Out of Scope

1. **macOS / Linux 平台支持**：本 Spec 仅针对 Windows 10/11 平台。
2. **离线本地大模型推理引擎**：不内置本地 llama.cpp 依赖，依赖在线 API 或本地 Ollama/vLLM HTTP 服务。
3. **自定义 Windows 内核键盘驱动**：仅使用 Win32 API / `pynput` 进行热键 Hook。

---

## Further Notes

1. **管理员权限 (UAC) 提示**：高权限窗口（如管理员 CMD/PowerShell）可能被 Windows UIPI 隔离，需在文档中提示建议权限。
2. **多显示器 DPI 缩放**：PySide6 悬浮窗自适应 High-DPI，居中于屏幕底部。
