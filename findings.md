# Project Findings & Technical Context

## 1. 规格文档关键要点总结
- **操作系统与环境**: Windows 10/11, Python 3.10+, PySide6 UI.
- **触发机制**: 全局长按热键（如 `Right Alt` 或 `Alt+Space`）触发录音/推流，松开按键结束录音并精修注入。
- **ASR 适配层**: 抽象基类支持 WebSocket 实时流式 ASR（豆包/火山引擎、通义千问）与 HTTP RESTful / Base64 Audio API（小米 MiMo `mimo-v2.5-asr`、OpenAI `/v1/audio/transcriptions`）。
  - **小米 MiMo v2.5 ASR (`asr/xiaomi_mimo.py`)**:
    - **模型 ID**: `mimo-v2.5-asr`
    - **Endpoint**: `https://api.xiaomimimo.com/v1`
    - **调用协议**: 录音结束后将 PCM 封装为 WAV 数据流，转换为 Base64 `data:audio/wav;base64,...` 发送至开放平台 API。
- **三阶段动态胶囊悬浮窗 (`ui/capsule.py`)**:
  - `Preparing...` (琥珀黄 Loading 扫频脉冲动画) -> `Listening...` (亮白 + 🔴 高亮发光 REC 录音指示灯 + 5-Bar 音量波形) -> `Refining...` (紫色) -> 顺畅淡出隐退。
- **LLM 保守精修与口语清洗 (`refine/llm.py`)**:
  - OpenAI 兼容接口，支持去除“呃”、“啊”、“那个”等口语冗余、修复谐音与专业术语（如 "配森" -> "Python"），转化为流畅书面表达。支持设置页自定义 System Prompt 与一键恢复默认。
- **无感文本注入 (`utils/injector.py`)**:
  - 备份当前剪贴板 -> 写入精修文本 -> SendInput(`Ctrl+V`) -> 延迟 150ms 恢复原始剪贴板。
- **现代暗黑风 Settings GUI (`ui/settings.py`)**:
  - 供应商参数全动态联动、`🔄 Fetch Models` 动态拉取模型列表 (`/models` API)、交互式 `HotkeyRecorderWidget` 键帽录制、连通性测试。
- **硬件热插拔检测与 PySide6 线程隔离 (`main.py`)**:
  - `ASRProcessingWorker(QThread)` 解耦耗时网络请求与 Qt GUI 主线程。
  - `AudioRecorder` 每次 `start()` 重新检测 `sd.query_devices()` 与 PortAudio 刷新，无设备时触发双重弹窗/托盘警告。

## 2. 系统测试接缝 (Seams) 策略
- **ASR Adapter Seam**: 使用 Mock WebSocket / HTTP 服务校验解析与回调。
- **LLM Refine Seam**: Mock OpenAI 接口校验口语冗余清洗与术语修正逻辑。
- **Audio RMS Envelope**: 正弦波与静音输入测试 RMS 计算与包络衰减。
- **Clipboard Injection**: 测试前写入数据，验证 `SendInput` 触发后剪贴板完好恢复。
