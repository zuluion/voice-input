# Prompt: Windows 系统托盘语音输入法应用（Python + PySide6）

> 本提示词用于指导 AI 生成 Windows 平台的语音输入法应用。基于 Python 3.10+、PySide6 及第三方 ASR 模型（豆包、通义千问、小米等）与 OpenAI 兼容 LLM 精修。

---

```text
请实现一个 Windows 平台的系统托盘语音输入法应用（Python 3.10+，基于 PySide6），具体要求：

1. 全局按键触发：使用 pynput / Win32 API 监听全局按键。按住指定修饰键/组合键（如按住 Right Alt 或 Alt+Space）开始录音并实时转录，松开按键后结束录音并将转录/精修后的文字注入到当前聚焦的文本输入框中。按键在设置中可配置。

2. 多 Provider ASR (语音识别) 架构：
   - 默认识别语言为简体中文（zh-CN），开箱即用。同时提供识别语言切换选项（英语、简体中文、繁体中文、日语、韩语）。
   - 抽象出通用的 ASR Provider 接口，支持接入主流第三方语音服务：
     a) 实时流式 ASR (WebSocket 协议)：支持接入豆包 (Doubao / 火山引擎)、通义千问 (Qwen / 阿里云 SenseVoice) 及小米 (Xiaomi) 等实时语音推流接口。
     b) HTTP RESTful ASR (OpenAI 兼容 /v1/audio/transcriptions 格式)：支持上传音频切片/文件进行识别，方便对接 Whisper 及第三方代理服务。

3. 优雅的无边框胶囊悬浮窗 UI：
   - 录音时在屏幕底部居中显示一个优雅精致的无边框半透明胶囊状悬浮窗（窗口属性：Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool，无任务栏图标）。高度 56px，圆角半径 28px，背景采用深色/浅色半透明高斯模糊材质（Mica/Acrylic 或 RGBA 自绘半透明）。
   - 左侧 5 根竖条波形动画（44×32px）：由 sounddevice 实时捕获的麦克风音频 RMS 电平驱动（不要使用假动画），说话声音大波形就大、安静时变小。各竖条权重为 [0.5, 0.8, 1.0, 0.75, 0.55] 形成中间高两侧低效果，平滑包络（Attack 40%、Release 15%），每根竖条添加 ±4% 随机抖动增加有机感。
   - 右侧文字标签（弹性宽度 160-560px）：实时显示 ASR 转录文本或 LLM Refining... 状态，胶囊随文字变长平滑变宽。
   - 界面包含淡入弹簧/平滑缩放动画（0.35s）、文字宽度平滑过渡（0.25s）、退场淡出动画（0.22s）。

4. 文本注入策略：
   - 文本注入使用剪贴板备份 + 模拟 Ctrl+V 粘贴机制。
   - 注入流程：读取并备份当前系统剪贴板内容 -> 将转录/精修后的文本写入剪贴板 -> 使用 Win32 API (SendInput) 模拟按下并释放 Ctrl+V 粘贴快捷键 -> 延迟 100-200ms 确保目标输入框已接收粘贴 -> 恢复原剪贴板内容。

5. 接入 LLM 进行语音识别文本二次精修 (Refinement)：
   - 接入 OpenAI 兼容 API 对转录文本进行准确率提升（特别针对中英文混杂场景）。
   - LLM System Prompt 必须非常保守地纠错：只修复明显的语音识别错误（如中文谐音错误、英文技术术语被错误转为中文如「配森」→「Python」、「杰森」→「JSON」），绝对不要改写、润色或删除任何看起来正确的内容，如果输入看起来正确则必须原样返回。
   - 松开按键后，如果 LLM 精修已启用且配置完整，悬浮窗提示 Refining... 状态，待 LLM 返回后再执行文本注入。

6. 系统托盘与可视化配置界面：
   - 应用以后台托盘模式运行（QSystemTrayIcon），双击或右键菜单可打开【设置】窗口。
   - 设置窗口采用 Tab 标签页分割：
     - 【ASR 语音识别配置】：选择 Provider 类型（Doubao / Qwen / Xiaomi / OpenAI HTTP），配置各自对应的 API Key / AppID / Secret / WebSocket Endpoint，以及选择默认识别语言。
     - 【LLM 文本精修配置】：启用/禁用开关、API Base URL、API Key、Model Name 输入框（API Key 需支持完全清空），以及 Test (连通性测试) 与 Save 按钮。
   - 所有配置本地持久化保存（如 json 文件或 QSettings）。

7. 项目结构与打包分发：
   - 代码结构清晰、模块化（主入口 main.py、UI 悬浮窗 ui/capsule.py、录音与电平采样 audio/recorder.py、ASR 抽象层 asr/、LLM 精修 refine/、剪贴板与注入 utils/injector.py）。
   - 提供 requirements.txt（包含 PySide6, sounddevice, pynput, requests, websockets 等依赖）。
   - 提供 Python 构建脚本 (build.py) 或 Makefile，使用 PyInstaller 或 Nuitka 命令将项目编译打包为单文件/免安装的 Windows .exe 可执行文件。
```
