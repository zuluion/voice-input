# 需求规格说明书 (Spec): 前后端分离架构与全流程 CLI 支持

## 问题陈述 (Problem Statement)

当前 `voice-input` 系统是一个标准的单体桌面应用 (Monolithic Application)，其核心业务逻辑（包括音频采集、ASR 流式识别、LLM 文本精修、配置管理、WebDAV 同步以及文本注入）高度耦合在 PySide6 GUI 框架与 Windows 宿主环境的 `VoiceInputController` 中。

这种高度耦合带来了以下核心痛点：
1. **缺乏无头/服务端模式 (Lack of Headless Mode)**：核心引擎无法在无 GUI 环境（如 Linux/Windows 无头服务器、SSH 远程终端、Docker 容器）中独立运行。
2. **多平台扩展受限 (Limited Multi-Platform Extensibility)**：无法在不重复编写代码的前提下，将核心 ASR 与 LLM 业务逻辑复用于未来的移动端 App (Android/iOS IME 输入法)、浏览器扩展 (Chrome Extension) 或 CLI 终端工具。
3. **状态管理脆弱**：GUI 界面的重绘或窗口事件直接影响进程内的音频数据流传输与 LLM 精修任务。

---

## 解决方案 (Solution)

将 `voice-input` 系统重构为**前后端分离架构**：
1. **无头核心守护进程 (Headless Core Daemon)**：构建基于 `asyncio` 和 `FastAPI` / `WebSockets` 的独立无头后端服务，负责管理 Session 状态机、流式处理管道 (Audio -> ASR -> LLM)、配置中心及 WebDAV 同步。
2. **标准 API 网关**：暴露用于控制面 (Control Plane) 的 RESTful API（配置查改、健康检查、WebDAV 同步）与用于数据面 (Data Plane) 的双向 WebSocket 实时通道（PCM/Opus 音频流推送、ASR 实时预览、状态变更通知与最终精修文本输出）。
3. **全流程 CLI 终端客户端 (`voice-input-cli`)**：提供极轻量的命令行工具，支持后台服务生命周期管理 (start/stop/status)、终端 TUI 配置菜单，以及支持 ANSI 波形渲染、流式识别预览与 UNIX 管道 (`stdout`/剪贴板) 的**全流程命令行语音输入体验**。
4. **瘦桌面客户端 (Thin Desktop Client)**：将现有的 PySide6 悬浮胶囊和托盘程序改造为瘦客户端，通过本地 WebSocket (`127.0.0.1`) 与后端守护进程通信。

---

## 用户故事 (User Stories)

1. 作为一名桌面端用户，我希望悬浮胶囊在进行复杂的 LLM 文本精修时保持界面极速响应，从而避免桌面操作出现任何卡顿。
2. As a 无头服务器 (Headless Server) 用户，我希望在没有图形界面的情况下在后台启动语音输入守护进程，以便能够远程使用高性能 ASR 与 LLM 服务。
3. As a 命令行终端极客，我希望通过一条简单的 CLI 命令 (`voice-input-cli record`) 触发语音输入，以便无需离开终端即可完成文字录入。
4. As a 命令行终端极客，我希望在控制台中看到实时的 ASCII 音量波形与 ASR 流式识别预览，以便确认麦克风与 ASR 服务正常工作。
5. As a 自动化脚本开发者，我希望可以通过 `--raw` 参数将精修后的最终文本直接输出到标准输出 (`stdout`)，以便将语音输入管道重定向至其他 CLI 工具或文件 (`voice-input-cli record --raw >> notes.md`)。
6. As a 终端管理员，我希望能够使用简单的 CLI 指令 (`voice-input-cli daemon start/stop/status`) 管理后端守护进程的生命周期，以便轻松控制后台服务。
7. As a 无 GUI 环境下的用户，我希望使用终端交互菜单 (`voice-input-cli config tui`) 切换 ASR/LLM 供应商和更新 API Key，以便无需手动编辑 JSON 配置文件。
8. As a 多设备用户，我希望将后端守护进程部署在局域网 NAS 服务器上，以便我所有的本地电脑与设备共享统一的 ASR/LLM 配置与 WebDAV 同步状态。
9. As a 移动端开发者，我希望拥有定义明确的 WebSocket 通信协议，以便快速开发能够连接至核心引擎的 Android 原生输入法 (IME) 客户端。
10. As a 浏览器扩展开发者，我希望通过 RESTful 和 WebSocket 接口直接接收文本，以便将语音识别结果注入到网页输入框中。
11. As a 注重隐私的用户，我希望客户端与守护进程之间的所有本地 IPC 通信均绑定在 `127.0.0.1`，以便防止音频数据泄露到未授权的网络接口。
12. As a 软件开发者，我希望 ASR 与 LLM 供应商通过标准的异步 Protocol 接口定义，以便在添加新的 ASR 或 LLM 供应商时无需修改任何 UI 或守护进程核心逻辑。

---

## 实施决策 (Implementation Decisions)

### 切缝选择 (Architectural Seams)
本项目选定的核心测试与解耦切缝为 **网络与事件网关切缝 (Network & Event Gateway Seam)**（即 `ws://127.0.0.1:28080/ws/v1/voice-session` 和 `/api/v1/*`）。所有客户端（PySide6 瘦客户端、CLI 客户端、移动端及 Web 扩展）均仅通过此切缝与核心引擎交互。

### 核心架构决策
1. **核心逻辑剥离**：
   - 从 `VoiceInputController` 中提取 Session 状态机、ASR 调度、LLM 精修及 WebDAV 同步，封装为独立的 `CoreEngine` 类。
   - 用轻量级 Python 原生 `asyncio` EventBus 替换 PySide6 的 `Signal/Slot` 和 `QThread`。
2. **服务网关**：
   - 使用 `FastAPI` / `ASGI` 框架暴露 RESTful 控制面接口。
   - 通过 WebSockets 提供实时双向流传输接口 (`/ws/v1/voice-session`)。
3. **全流程 CLI 客户端实现**：
   - 使用 `typer` 库处理命令行参数，使用 `rich` 库构建终端 UI 动画、ASCII 音频波形以及实时流式文本渲染。
   - 在 CLI 客户端集成基于 `sounddevice`/`PyAudio` 的音频采集 HAL。
   - 提供支持纯文本输出 (`--raw`) 的 UNIX 管道交互模式。
4. **客户端硬件抽象层 (Client HAL)**：
   - 将硬件绑定操作（音频采集、热键监听、文本注入）彻底移至客户端实现。
   - 在无头或缺乏声卡/剪贴板的环境中，提供优雅的降级处理机制。

---

## 测试决策 (Testing Decisions)

### 优质测试原则 (Good Test Principles)
- 测试必须严格验证**外部行为**（如 API 契约、WebSocket 消息流、CLI 退出码和输出流），严禁测试内部私有实现细节。
- 避免 Mock 内部 Python 类；在执行自动化 CI 流水线时，仅在网络边界 Mock 外部三方 ASR/LLM HTTP/WS 接口。

### 受测模块
1. **守护进程 REST API**：使用 `httpx.AsyncClient` 或 FastAPI `TestClient` 测试 `/api/v1/health`、`/api/v1/config`、`/api/v1/providers`。
2. **WebSocket Session 协议**：自动化测试完整会话生命周期（`session_start` -> 音频帧 -> `asr_partial_result` -> `session_stop` -> `session_complete`）。
3. **CLI 命令行工具**：使用 CLI 测试框架测试命令调用 (`voice-input-cli status`、`config set`、`daemon start/stop`)。
4. **Provider 抽象 Protocol**：针对 Mock WebSocket/REST 服务器，对 ASR 和 LLM 供应商抽象接口进行单元测试。

### 项目现有参考 (Prior Art)
- 参考项目现有的 [`tests/`](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/tests) 目录下的配置加载与测试模式。

---

## 范围外事项 (Out of Scope)

1. **原生移动端 App 代码开发**：编写 Android Java/Kotlin 原生 IME 代码或 iOS Swift 代码不在本 Spec 范围之内（仅提供通信协议定义）。
2. **浏览器扩展打包**：编写 Chrome/Edge 扩展的 Manifest 文件与前端 JS Bundle 不在本 Spec 范围之内。
3. **三方 ASR/LLM SDK 变动**：不会修改三方 ASR (Doubao, Qwen, Xiaomi) 和 LLM 的底层 API 契约。

---

## 补充说明 (Further Notes)

- **进程隔离策略**：对于 PySide6 桌面前端，建议将其与 Backend Daemon 运行在不同的操作系统进程中，以防止 Qt 事件循环与 `asyncio` 事件循环产生锁冲突。
- **默认端口分配**：后端守护进程默认端口为 `28080`，若被占用则自动寻找可用端口。
