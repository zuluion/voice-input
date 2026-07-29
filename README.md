# voice-input

语音输入方案，暂时只支持 Windows 平台。

## 项目特点与设计
- **全局长按热键触发与交互录制**：按住热键开始录音，松开自动转录精修并注入文本。设置界面提供图形化交互式热键录制（推荐 `[ Right Control ]` / `[ Space ]` 键帽显示）。
- **多 Provider ASR 深度接入**：灵活接入小米 MiMo (`mimo-v2.5-asr`)、豆包 (Volcengine)、通义千问 (DashScope) 及 OpenAI 兼容语音识别 API。
- **三阶段视觉交互悬浮窗**：无边框半透明置顶 UI，包含 **`Preparing...`** (缓冲扫频动画)、**`Listening...`** (亮白文字 + 🔴 高亮发光 REC 录音指示灯 + 5-Bar RMS 动态波形) 与 **`Refining...`** (柔和紫光) 三阶段流畅转换。
- **LLM 保守智能纠错与口语清洗**：接入 OpenAI / DeepSeek / 通义千问 / 本地 Ollama 兼容大模型，不仅修复中文谐音与技术术语错误，更能自动清除“呃”、“啊”、“那个”等口语冗余，转化为流畅书面语。支持自定义 System Prompt。
- **无感文本注入**：基于剪贴板备份 + Win32 `SendInput` 模拟 `Ctrl+V`，注入完成后自动恢复原始剪贴板。
- **现代暗黑 Settings GUI & 硬件热插拔支持**：
  - 高质感 `#12151e` 暗黑护眼 UI 主题。
  - ASR 供应商全动态联动，官方 Base URL & Default Model 自动选择。
  - **`🔄 Fetch Models`** 按钮：动态拉取服务商可用模型列表 (`/models` API)，并将 Model Name 升级为下拉选择框。
  - **一键连通性测试**：`Test ASR Connection` 与 `Test LLM Connection`（模拟口语清洗测试）。
  - **硬件热插拔检测**：动态感应麦克风硬件接入，缺失时触发托盘气泡与警告弹窗提示。

---

## 🚀 快速上手使用指南

### 1. 使用 Scoop 安装（推荐）
```powershell
# 直接通过包管理器 Scoop 安装或更新
scoop install https://raw.githubusercontent.com/zuluion/voice-input/master/voice-input.json

# 或一键升级至最新滚动版本
scoop update voice-input
```

### 2. 源码开发环境运行
```powershell
# 安装依赖
pip install -r requirements.txt

# 运行主程序
python src/main.py
```
启动后，应用将在 **Windows 系统托盘（右下角任务栏）** 后台静默运行。

---

### 3. 配置 API Key 与热键（首次使用）
1. 右键点击系统托盘中的紫色小图标，选择 **`Settings...`** 打开现代暗黑设置界面。
2. **设置语音识别 (ASR)**：
   - 在 **ASR Settings** 页中，选择默认 Provider（如 **`xiaomi_mimo`**）。
   - 填入您的 **API Key**（如从 [小米开放平台](https://mimo.mi.com/) 获取）。
   - 可点击 **`🔄 Fetch Models`** 自动获取服务商模型列表，或点击 **`Test ASR Connection`** 一键测试连通性。
3. **设置 LLM 精修与口语清洗 (LLM Refinement)**：
   - 在 **LLM Refinement** 页中，勾选 **Enable LLM Refinement & Polishing**。
   - 填入 API Key、Base URL 与 Model Name（如 `gpt-4o-mini`、`deepseek-chat` 或本地 `http://localhost:11434/v1`）。
   - 可在 **System Prompt** 框中自定义整理规则，或点击 **`↺ Reset Prompt`** 恢复内置推荐规则。
   - 点击 **`Test LLM Connection`** 即可测试口语整理效果。
4. **设置触发热键 (Hotkey & General)**：
   - 点击 **`🎙️ Click to Record`** 按钮，按键盘任意键（推荐右侧 **`Right Control`**）即可完成交互录制。
   - 点击 **`Save Config`** 保存设置。

---

### 4. 快捷语音输入交互
1. 打开并聚焦到任意文本输入框（如 **VS Code**、**记事本**、**微信**、**浏览器** 等）。
2. **长按 `Right Control` 键**：
   - 屏幕底部中央立即弹起胶囊浮窗，显示琥珀黄 **`Preparing...`** 缓冲动画。
   - 麦克风成功捕获第一帧声音时，瞬间切换为 **亮白 `Listening...`** 并点亮 **高亮发光 REC 红灯 🔴**。
   - 说话时，5 根波形条随实际音量跳动。
3. **松开 `Right Control` 键**：
   - 悬浮窗显示紫色 **`Refining...`**。
   - 大模型完成口语清洗与术语修正后，自动注入当前输入框并无感还原剪贴板。

---

### 5. 常规控制与版本说明
- **滚动版本号**：项目版本统一记录在根目录 [VERSION](VERSION) 文件中（格式：`YYYY.MM.DD.xxx`）。
- **临时开关**：右键托盘图标取消勾选 **`Enabled`** 即可快捷禁用/启用。
- **退出应用**：右键托盘图标点击 **`Quit`**。

---

## 📚 文档列表
- 📋 [**需求规格说明书 (Spec / PRD)**](docs/specs/speech_input_windows_spec.md)
- 💡 [**Windows 提示词 (Prompt)**](docs/prompts/windows_voice_input_prompt.md)
- 🤖 [**项目 Agent 规范说明 (AGENTS.md)**](AGENTS.md)

---

## 🙏 致谢 (Acknowledgements)
本项目在产品理念与交互设计上，特别感谢开源项目 [yetone/voice-input-src](https://github.com/yetone/voice-input-src) 带来的灵感与启发！
