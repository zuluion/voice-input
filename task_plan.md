# Task Plan: Windows 系统托盘语音输入法应用

## 目标 (Goal)
基于 `docs/specs/speech_input_windows_spec.md` 规格文档，开发并验证一款基于 Python 3.10+ 与 PySide6 的 Windows 平台系统托盘语音输入法应用。

---

## 阶段规划 (Phases)

### Phase 1: 需求分析与方案设计 (Current)
- [x] 读取分析 `docs/specs/speech_input_windows_spec.md`
- [x] 制定详细的项目模块架构与实现方案
- [x] 初始化项目规划文件 (`task_plan.md`, `findings.md`, `progress.md`)

### Phase 2: 基础架构与配置/日志模块搭建
- [ ] 初始化 Python 项目结构与依赖文件 (`requirements.txt` / `pyproject.toml`)
- [ ] 实现配置持久化管理模块 (`config.py`)，支持保存/加载 ASR、LLM、热键及 UI 偏好
- [ ] 创建全局常量与数据模型类型定义

### Phase 3: 核心逻辑模块实现 (Audio, Hotkey, ASR, Refine, Injector)
- [ ] 实现 Audio 录音与 RMS 电平包络引擎 (`audio/recorder.py`)
- [ ] 实现 Win32/pynput 热键监听引擎 (`core/hotkey.py`)
- [ ] 实现 ASR 抽象基类及适配器群 (`asr/base.py`, `asr/doubao.py`, `asr/qwen.py`, `asr/xiaomi_mimo.py`, `asr/openai_http.py`)
- [ ] 实现 LLM 保守纠错精修引擎 (`refine/llm.py`)
- [ ] 实现剪贴板备份与 `SendInput` 文本注入引擎 (`utils/injector.py`)

### Phase 4: PySide6 UI 界面与系统托盘
- [ ] 实现无边框胶囊悬浮窗及 5 根动态波形条动画 (`ui/capsule.py`)
- [ ] 实现系统托盘 `QSystemTrayIcon` 与主控逻辑 (`ui/tray.py`, `main.py`)
- [ ] 实现多 Tab 设置界面 (`ui/settings.py`)，提供 ASR、LLM、热键配置与连通性测试

### Phase 5: 测试、调试与打包准备
- [ ] 编写并执行单元测试/集成测试 (ASR Seam, LLM Refine, Audio RMS, Clipboard Injection)
- [ ] 端到端功能验证与边界条件测试 (DPI 缩放、长按/松开防抖、恢复剪贴板)
- [ ] 配置 PyInstaller/Nuitka 打包脚本
