# Project Findings & Technical Context

## 1. 规格文档关键要点总结
- **操作系统与环境**: Windows 10/11, Python 3.10+, PySide6 UI.
- **触发机制**: 全局长按热键（如 `Right Alt` 或 `Alt+Space`）触发录音/推流，松开按键结束录音并精修注入。
- **ASR 适配层**: 抽象基类支持 WebSocket 实时流式 ASR（豆包/火山引擎、通义千问）与 HTTP RESTful / Base64 Audio API（小米 MiMo `mimo-v2.5-asr`、OpenAI `/v1/audio/transcriptions`）。
  - **小米 MiMo v2.5 ASR (`asr/xiaomi_mimo.py`)**:
    - **模型 ID**: `mimo-v2.5-asr`
    - **Endpoint**: `https://api.xiaomimimo.com/v1`
    - **调用协议**: 录音结束后将 PCM 封装为 WAV 数据流，转换为 Base64 `data:audio/wav;base64,...` 发送至 OpenAI 兼容补全/转录接口，解析中英混杂及标点符号。
- **动态胶囊悬浮窗**: 无边框、置顶、半透明、无任务栏图标、5 根 RMS 包络驱动的动态圆角波形条、自适应文本宽度（160px ~ 560px）、`QPropertyAnimation` 淡入淡出。
- **LLM 保守精修**: OpenAI 兼容接口，严格保守纠错 System Prompt，修复谐音与专业术语（如 "配森" -> "Python"），原样返回无误文本。
- **无感文本注入**: 备份当前剪贴板 -> 写入精修文本 -> SendInput(`Ctrl+V`) -> 延迟 150ms 恢复原始剪贴板。

## 2. 系统测试接缝 (Seams) 策略
- **ASR Adapter Seam**: 使用 Mock WebSocket / HTTP 服务校验解析与回调。
- **LLM Refine Seam**: Mock OpenAI 接口校验错误修复与非纠错原样返回逻辑。
- **Audio RMS Envelope**: 正弦波与静音输入测试 RMS 计算与包络衰减。
- **Clipboard Injection**: 测试前写入数据，验证 `SendInput` 触发后剪贴板完好恢复。
