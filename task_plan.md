# Task Plan: Windows 系统托盘语音输入法应用

## 目标 (Goal)
基于 `docs/specs/speech_input_windows_spec.md` 规格文档，开发并验证一款基于 Python 3.10+ 与 PySide6 的 Windows 平台系统托盘语音输入法应用。

---

## 阶段规划 (Phases)

### Phase 1: 需求分析与方案设计 (Complete)
- [x] 读取分析 `docs/specs/speech_input_windows_spec.md`
- [x] 制定详细的项目模块架构与实现方案（补充小米 MiMo `mimo-v2.5-asr` 接入）
- [x] 初始化项目规划文件 (`task_plan.md`, `findings.md`, `progress.md`)

### Phase 2: 基础架构与配置/日志模块搭建 (Complete)
- [x] 初始化 Python 项目结构与依赖文件 (`requirements.txt` / `pyproject.toml`)
- [x] 实现配置持久化管理模块 (`src/config.py`)，支持保存/加载 ASR、LLM、热键及 UI 偏好
- [x] 创建全局常量与数据模型类型定义

### Phase 3: 核心逻辑模块实现 (Audio, Hotkey, ASR, Refine, Injector) (Complete)
- [x] 实现 Audio 录音与 RMS 电平包络引擎 (`src/audio/recorder.py`)，集成硬件热插拔重扫描
- [x] 实现 Win32/pynput 热键监听引擎 (`src/core/hotkey.py`)
- [x] 实现 ASR 抽象基类及适配器群 (`src/asr/base.py`, `src/asr/doubao.py`, `src/asr/qwen.py`, `src/asr/xiaomi_mimo.py`, `src/asr/openai_http.py`)
- [x] 实现 LLM 保守纠错与口语清洗精修引擎 (`src/refine/llm.py`)，支持自定义 System Prompt
- [x] 实现剪贴板备份与 `SendInput` 文本注入引擎 (`src/utils/injector.py`)

### Phase 4: PySide6 UI 界面与系统托盘 (Complete)
- [x] 实现无边框胶囊悬浮窗 (`src/ui/capsule.py`)，包含 🔴 REC 录音指示灯与 3-Stage 视觉状态
- [x] 实现系统托盘 `QSystemTrayIcon` 与主控逻辑 (`src/ui/tray.py`, `src/main.py`)，集成 QThread 线程隔离
- [x] 实现现代暗黑设置界面 (`src/ui/settings.py`)，提供供应商参数全动态联动、`🔄 Fetch Models` 动态模型拉取、`HotkeyRecorderWidget` 键帽录制、自定义 Prompt 编辑器及连通性测试

### Phase 5: 测试、调试与文档完善 (Complete)
- [x] 编写并执行单元测试/集成测试 (ASR Seam, LLM Refine, Audio RMS, Clipboard Injection)
- [x] 端到端功能验证与边界条件测试 (DPI 缩放、长按/松开防抖、恢复剪贴板、设备缺失提醒)
- [x] 更新同步规格文档 `docs/specs/speech_input_windows_spec.md` 与 `README.md`
