# 规格文档 (Spec / PRD): Windows 系统托盘语音输入法应用

## Problem Statement

在 Windows 操作系统下，用户在日常办公、代码编写和文档创作时面临以下文本输入痛点：
1. **键盘输入效率受限**：长文本或灵感记录时键盘打字速度有限，容易打断思考节奏。
2. **缺乏高质量与定制化语音输入工具**：系统自带语音识别准确率有限，无法直接接入豆包 (Doubao)、通义千问 (Qwen)、小米 (Xiaomi) 等高精度国内第三方语音大模型。
3. **专业术语与中英混杂识别率低**：传统 ASR（自动语音识别）容易产生中文谐音错误或将英文专业术语错写为中文（例如将 "Python" 误识别为 "配森"），缺乏大语言模型（LLM）的智能保守纠错机制。
4. **交互不够轻量无感**：缺少像 macOS 胶囊悬浮窗一样即按即用、平滑且不强占焦点的快捷语音输入体验。

---

## Solution

基于 Python 3.10+ 与 PySide6 开发一款 Windows 平台的系统托盘语音输入法应用。

该应用具备以下核心特性：
- **全局长按热键触发**：按住指定热键（如 `Right Alt` 或 `Alt+Space`）即刻开始录音并推流识别，松开按键自动精修并注入文本。
- **多 Provider ASR 架构**：灵活接入豆包、通义千问、小米等 WebSocket 实时流式 ASR 以及 OpenAI 兼容的 `/v1/audio/transcriptions` HTTP 接口。
- **优雅的无边框胶囊悬浮窗**：置顶显示无任务栏图标的胶囊窗口，包含根据实时音频 RMS 电平驱动的 5 根动态波形条、弹性转录文本展示及平滑入场/退场动画。
- **保守型 LLM 文本精修 (Refinement)**：通过 OpenAI 兼容接口接入 LLM，严格按照保守纠错 Prompt 修复谐音与技术术语错误，确保不改变原文意思。
- **无缝文本注入**：基于剪贴板备份与 Win32 `SendInput` 快捷键模拟，将最终文本安全注入到当前聚焦的任意输入框，并无感恢复原剪贴板内容。
- **系统托盘与模块化配置**：托盘后台运行，提供独立的 PySide6 配置界面与 PyInstaller/Nuitka 单文件打包发布支持。

---

## User Stories

1. As a Windows power user, I want to trigger voice recording by holding down a configurable global key combination (e.g. `Right Alt`), so that I can capture my spoken words instantly without focusing on a specific app window.
2. As a multilingual content creator, I want to switch the target ASR recognition language (Simplified Chinese, English, Traditional Chinese, Japanese, Korean) from the tray menu or settings, so that I can speak in different languages seamlessly.
3. As a developer, I want to connect the app to third-party ASR providers (Doubao, Qwen, Xiaomi, OpenAI-compatible HTTP), so that I can leverage state-of-the-art domain-specific speech recognition models.
4. As a user, I want to see a sleek, non-intrusive floating capsule window at the bottom of the screen while recording, so that I get visual feedback that my voice is being captured without losing focus on my active work.
5. As a user, I want the capsule window's waveform animation to dynamically respond to my actual speaking volume level in real-time, so that I can intuitively verify audio input quality.
6. As a user, I want the capsule to smoothly expand its width as live transcription text accumulates, so that I can preview the recognized text in real-time.
7. As a programmer, I want LLM refinement to automatically fix misrecognized technical jargon (e.g. converting "配森" to "Python" or "杰森" to "JSON"), so that I don't need to manually correct code-related voice entries.
8. As a user, I want the LLM refinement to strictly preserve correct phrasing without paraphrasing or rewriting my sentence structure, so that my original voice intent remains intact.
9. As a user, I want the app to inject text via standard clipboard paste (`Ctrl+V`) and immediately restore my previous clipboard contents, so that my active clipboard data is never lost or corrupted.
10. As a user, I want a "Refining..." indicator inside the floating capsule when LLM processing is active, so that I know the text is undergoing smart error correction before injection.
11. As a user, I want the app to run discretely in the Windows System Tray without clogging my Windows Taskbar, so that my workspace stays clean.
12. As a user, I want a clean settings GUI with tabs to test and configure API keys, endpoints, and model parameters for both ASR and LLM services, so that I can update configurations without editing raw code files.
13. As a system administrator, I want to build a standalone single-file `.exe` executable using PyInstaller or Nuitka, so that end users can run the application without installing a Python environment.

---

## Implementation Decisions

### 1. High-Level Architecture & Module Boundaries
应用采用基于 Python 3.10+ 与 PySide6 的分层事件驱动架构，拆分为 6 个自治模块：

```
+-----------------------------------------------------------------------+
|                             Main App                                  |
|                 (main.py / Event Loop / Controller)                   |
+-------+---------------+---------------+---------------+---------------+
        |               |               |               |
        v               v               v               v
+---------------+ +-----------+ +---------------+ +-----------+
| Hotkey Engine | | Audio Engine| | ASR Adapter   | | LLM Engine|
| (pynput/Win32)| |(sounddevice)| | (WebSocket/   | | (OpenAI   |
|               | | (RMS Calc)  | |  HTTP REST)   | |  Client)  |
+---------------+ +-----------+ +---------------+ +-----------+
        |               |               |               |
        +---------------+---------------+---------------+
                        |
                        v
        +-------------------------------+
        | UI Layer                      |
        | - Floating Capsule Window     |
        | - System Tray (QSystemTrayIcon)|
        | - Settings Window (Tabbed GUI)|
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
- 维持热键防抖逻辑，当检测到指定热键按下时触发 `recording_started` 信号；当按键松开时触发 `recording_stopped` 信号。

#### B. Audio & Waveform Level Engine (`audio/recorder.py`)
- 基于 `sounddevice.InputStream` 异步捕获默认麦克风音频数据（采样率 16000Hz, 16bit, 单声道 PCM）。
- 实时计算每一个 Buffer 帧的均方根电平（RMS）：
  $$\text{RMS} = \sqrt{\frac{1}{N}\sum_{i=1}^{N} x_i^2}$$
- 将 RMS 值经过 Attack 40%、Release 15% 的包络平滑算法处理，并加上 `[0.5, 0.8, 1.0, 0.75, 0.55]` 权重分配及 $\pm 4\%$ 动态随机抖动，实时发射 `volume_changed(list)` 信号供 UI 刷新波形。

#### C. Multi-Provider ASR Engine (`asr/base.py`, `asr/doubao.py`, `asr/qwen.py`, `asr/openai_http.py`)
- 定义抽象基类 `BaseASRProvider`，暴露统一的方法接口：
  - `connect()`
  - `send_audio_chunk(data: bytes)`
  - `finish()`
  - `on_text_updated(callback)`
- **WebSocket 流式 Adapter**：专门针对豆包 / 火山引擎和通义千问的实时语音推流协议进行二进制/JSON 数据包封包。
- **HTTP RESTful Adapter**：录音结束时将 PCM 编码为 WAV 文件，发送 POST 请求至 `/v1/audio/transcriptions`。

#### D. Floating Capsule Window (`ui/capsule.py`)
- 使用 `QWidget`，窗口标志设为 `Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool`，且 `setAttribute(Qt.WA_TranslucentBackground)` 启用透明度。
- 固定高度 56px，动态宽度 160px ~ 560px。
- 使用 `QPainter` 绘制抗锯齿圆角矩形背景（深色半透明带有微弱边框 Glow 特效）。
- 左侧区域（44×32px）绘制 5 根根据 RMS 电平平滑过渡的圆角矩形竖条。
- 右侧使用 `QLabel` 或 `QStaticText` 渲染转录文本/状态。
- 使用 `QPropertyAnimation` 实现入场淡入、宽度平滑缩放和退场淡出效果。

#### E. LLM Refinement Module (`refine/llm.py`)
- 通过 `requests` / `httpx` 发起 OpenAI 兼容接口请求。
- 构造系统提示词 (System Prompt)：
  ```text
  You are an expert voice-recognition error correction assistant. Your task is to fix speech recognition errors in the user's transcript.
  Strict Rules:
  1. Fix ONLY clear speech recognition mistakes (e.g., Chinese homophone errors, wrongly translated English technical terms like "配森" -> "Python", "杰森" -> "JSON").
  2. DO NOT rewrite, paraphrase, polish, reformat, or delete any correct words.
  3. If the input transcript appears correct, return it EXACTLY as-is.
  4. Output ONLY the refined final text, with no explanations or preamble.
  ```

#### F. Text Injection Engine (`utils/injector.py`)
- 使用 `win32clipboard` (或 `pyperclip`) 备份当前的剪贴板内容（包括文本/格式/HTML 等类型数据）。
- 将精修文本置入系统剪贴板。
- 调用 `ctypes.windll.user32.SendInput` 模拟键盘事件：按住 `VK_CONTROL` -> 按下 `V` -> 松开 `V` -> 松开 `VK_CONTROL`。
- 开启 `QTimer.singleShot(150)` 异步延迟后，恢复原始剪贴板数据。

#### G. System Tray & Settings Window (`ui/tray.py`, `ui/settings.py`)
- `QSystemTrayIcon` 提供图标、主开关勾选框、设置窗口人口及退出选项。
- `SettingsWindow` 提供 PySide6 选项页：
  - ASR 配置页：Provider 选择下拉框、Endpoint、AppID/Key/Secret 配置框。
  - LLM 配置页：Enable 开关、Base URL、API Key、Model Name、Test Connection 按钮。
  - 热键设置页：录音触发按键绑定。

---

## Testing Decisions

### 1. Seam Selection & Strategy
为了保证代码的可维护性与测试稳健度，测试策略聚焦于外部行为与关键模块边界（Seams），避免测试细枝末节的 UI 绘制像素：

```
                    +--------------------------------+
                    |  System Test (End-to-End Seam) |
                    +---------------+----------------+
                                    |
            +-----------------------+-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
|  ASR Adapter Seam     |                       |  LLM Refine Seam      |
| (Mock WS/HTTP Server) |                       |  (Mock OpenAI Server) |
+-----------------------+                       +-----------------------+
            |                                               |
            v                                               v
+-----------------------+                       +-----------------------+
| Audio RMS Envelope    |                       | Clipboard Backup Seam |
| (Pure Math Function)  |                       | (Win32 Clipboard API) |
+-----------------------+                       +-----------------------+
```

### 2. Tested Modules & Criteria

- **ASR Adapter Seam**:
  - *测试方法*：使用 `unittest.mock` 或搭建本地 Mock WebSocket/HTTP 服务，向 ASR Adapter 灌入模拟音频 Byte 流。
  - *验证标准*：验证 Adapter 是否能正确解析服务端返回的 JSON/流式帧，并精准触发 `on_text_updated` 回调。

- **LLM Refine Module Seam**:
  - *测试方法*：对 `refine/llm.py` 进行单元测试，传入包含典型错误的转录文本（如包含 "配森"、"杰森" 的字符串）。
  - *验证标准*：使用 Mock HTTP 响应，验证 Prompt 格式、Header 携带的 API Key 格式以及无错误文本的“原样返回”逻辑。

- **Audio RMS Envelope Seam**:
  - *测试方法*：向 RMS 平滑包络函数输入已知振幅的正弦波/静音 NumPy 数组。
  - *验证标准*：计算返回的 5 根竖条高度标度值，验证是否在 `[0, 1.0]` 范围内，且包络在静音时平滑衰减至接近 0。

- **Clipboard Backup & Restore Seam**:
  - *测试方法*：在测试开始前向剪贴板写入预设测试数据，调用 `inject_text("Transcribed text")` 模拟注入流程。
  - *验证标准*：验证 `SendInput` 事件触发后，剪贴板在延迟时间过后恢复为预设测试数据。

---

## Out of Scope

以下内容不在本次规格说明书及首次实施范围之内：
1. **macOS / Linux 平台支持**：本 Spec 仅针对 Windows 10/11 平台。
2. **离线本地大模型推理引擎**：不内置本地 llama.cpp 或 Whisper.cpp 推理依赖，所有 ASR 与 LLM 功能均依赖在线 API。
3. **自定义 Windows 内核键盘驱动**：不编写 Ring 0 级别的键盘驱动，仅使用标准的 Win32 API / `pynput` 进行热键 Hook。
4. **语音合成 (TTS) 反向朗读**：本应用专注语音到文本输入，不提供语音合成播报功能。

---

## Further Notes

1. **管理员权限 (UAC) 提示**：当目标聚焦软件（如以管理员身份运行的 CMD/PowerShell）处于高权限模式时，低权限的 Win32 `SendInput` 或 Keyboard Hook 可能会被 Windows UIPI (User Interface Privilege Isolation) 隔离。应用打包时需在 manifest 中标注建议的权限级别或在文档中提醒用户。
2. **多显示器 DPI 缩放**：PySide6 悬浮窗需开启 High-DPI 自适应（`QGuiApplication.setHighDpiScaleFactorRoundingPolicy`），保证在 100%、125%、150% 等不同 Windows 屏幕缩放比例下胶囊无变形、无模糊。
3. **音视频采样设备选择**：默认绑定 Windows 系统默认默认麦克风输入设备，若设备断开（如拔出蓝牙耳机），`sounddevice` 应具备自动重连机制。
