# Task Progress Log

## Session 2026-07-29

### Phase 1: 需求分析与方案设计
- 读取规格文档 `docs/specs/speech_input_windows_spec.md`。
- 完成总体实现方案设计，涵盖模块划分、关键算法、数据流向、UI 设计、测试策略及分阶段落地计划。
- 初始化 `task_plan.md`、`findings.md` 与 `progress.md`。

### Phase 2 ~ Phase 4: 代码实现与 UI/UX 深度升级
- 初始化并实现 `requirements.txt`。
- 实现配置持久化管理模块 [src/config.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/config.py)。
- 实现热键监听引擎 [src/core/hotkey.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/core/hotkey.py)。
- 实现音频录制与 5-Bar RMS 包络计算 [src/audio/recorder.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/audio/recorder.py)（支持硬件热插拔重扫描与首帧 `recording_ready` 信号）。
- 实现多 ASR 适配器群及小米 MiMo (`mimo-v2.5-asr`) 深入支持 [src/asr/xiaomi_mimo.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/asr/xiaomi_mimo.py)。
- 实现 LLM 精修与口语清洗引擎 [src/refine/llm.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/refine/llm.py)（支持口语冗余去除与自定义 System Prompt）。
- 实现剪贴板备份恢复与 Win32 `SendInput` 注入器 [src/utils/injector.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/utils/injector.py)。
- 实现 PySide6 动态无边框胶囊悬浮窗 [src/ui/capsule.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/ui/capsule.py)（具备 🔴 REC 录音指示灯与 `PREPARING` -> `LISTENING` -> `REFINING` 3 阶段 Visual State）。
- 实现系统托盘 [src/ui/tray.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/ui/tray.py) 与现代暗黑 Settings GUI [src/ui/settings.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/ui/settings.py)（支持 ASR 参数全联动、`🔄 Fetch Models` 动态模型拉取、`HotkeyRecorderWidget` 键帽录制、自定义 Prompt 编辑器及连通性测试）。
- 实现主入口与 Controller 控制器 [src/main.py](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/src/main.py)（`ASRProcessingWorker(QThread)` 线程隔离与设备缺失双重弹窗/通知提醒）。
- 编写并运行 seam 单元测试用例集 [tests/](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/tests)，100% 测试通过。

### Phase 5: 规格与项目文档全面更新
- 更新同步规格 PRD 文档 [docs/specs/speech_input_windows_spec.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/docs/specs/speech_input_windows_spec.md)（全面更新默认热键为 `Right Control` 与核心规则）。
- 更新同步 [README.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/README.md) 使用说明（全面更新推荐热键为 `Right Control` 示例）。
- 更新同步 [findings.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/findings.md) 与 [task_plan.md](file:///D:/AllProjects/OtherProjects_Workspace/voice-input/task_plan.md)。
