# voice-input

语音输入方案，暂时只支持 Windows 平台。

## 项目特点与设计
- **全局长按热键触发与交互录制**：按住热键开始录音，松开自动转录精修并注入文本。设置界面提供图形化交互式热键录制（推荐 `[ Right Control ]` / `[ Space ]` 键帽显示）。
- **多 Provider ASR 深度接入**：灵活接入小米 MiMo (`mimo-v2.5-asr`)、豆包 (Volcengine)、通义千问 (DashScope) 及 OpenAI 兼容语音识别 API。
- **6 大 LLM 供应商模式与口误中途改口处理**：支持 OpenAI, DeepSeek, Xiaomi, 阿里云通义千问, 本地 Ollama, Custom 自定义 6 大供应商。不仅自动擦除语气冗余与谐音错字，更可识别“不对”、“算了”、“改成”等改口信号，自动覆盖旧表述并完美保留句式主干。
- **30 FPS 动态视觉交互悬浮窗**：无边框半透明置顶 UI，具备 30 FPS 呼吸脉冲与动态波形演进：
  - **`Preparing...`** (缓冲扫频动画)
  - **`Listening...`** (亮白文字 + 🔴 高亮发光呼吸 REC 红灯 + 5-Bar 音量扫频混合波形)
  - **`Refining...`** (柔和紫光)
- **WebDAV 全量配置同步与历史备份恢复**：支持坚果云与自定义 WebDAV 服务器（URL、账号、应用密码），提供手动上传/下载、**远端历史备份浏览与选择恢复**，以及应用启动时自动下载同步。
- **全局网络代理支持 (HTTP / SOCKS4 / SOCKS5)**：支持一键开关网络代理，配置 `127.0.0.1:7890` 提示主机与端口，全量注入环境变量驱动所有网络请求走代理。
- **模块化暗黑 Settings GUI & 软件信息页**：
  - 代码解耦重构拆分为 `src/ui/settings/` 模块包 (`asr_tab`, `llm_tab`, `webdav_tab`, `proxy_tab`, `hotkey_tab`, `about_tab`)。
  - 高质感 `#12151e` 暗黑护眼 UI 主题。
  - **`🔄 Fetch Models`** 按钮：动态拉取服务商可用模型列表 (`/models` API)。
  - **一键连通性测试**：支持 ASR、LLM、WebDAV、代理连通性测试。
  - **软件信息页 (About Tab)**：展示作者（`Zuluion`）、当前版本、官方 GitHub 仓库链接，支持一键检查最新 Release 更新。
- **无感文本注入**：基于剪贴板备份 + Win32 `SendInput` 模拟 `Ctrl+V`，注入完成后自动恢复原始剪贴板。

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
   - 在 **LLM Refinement** 页中，选择 6 大供应商（**OpenAI**, **DeepSeek**, **Xiaomi**, **Qwen**, **Ollama**, **Custom**）。
   - 填入 API Key、Base URL 与 Model Name。
   - 可在 **System Prompt** 框中自定义整理规则，或点击 **`↺ Reset Prompt`** 恢复内置推荐规则。
   - 点击 **`Test LLM Connection`** 即可测试口语整理与改口覆盖效果。
4. **设置 WebDAV 同步 (WebDAV Sync)**：
   - 在 **WebDAV Sync** 页中，填入服务器 URL（如坚果云 `https://dav.jianguoyun.com/dav/`）、账号与 App 密码。
   - 可点击 **`📤 Upload Current Config`** 或 **`📋 View Remote Backups & Restore`** 查看历史备份恢复。
5. **设置代理 (Proxy)**：
   - 在 **Proxy** 页中，勾选 **Enable Global Network Proxy**，选择 `http`/`socks4`/`socks5` 协议并填入主机名（`127.0.0.1`）与端口（`7890`）。
6. **设置触发热键 (Hotkey & General)**：
   - 点击 **`🎙️ Click to Record`** 按钮，按键盘任意键（推荐右侧 **`Right Control`**）即可完成交互录制。
   - 点击 **`Save Config`** 保存设置。

---

### 4. 快捷语音输入交互
1. 打开并聚焦到任意文本输入框（如 **VS Code**、**记事本**、**微信**、**浏览器** 等）。
2. **长按 `Right Control` 键**：
   - 屏幕底部中央立即弹起胶囊浮窗，显示琥珀黄 **`Preparing...`** 缓冲动画。
   - 麦克风成功捕获第一帧声音时，瞬间切换为 **亮白 `Listening...`** 并点亮 **高亮发光呼吸 REC 红灯 🔴**。
   - 说话时，5 根波形条随实际音量与扫频跳动。
3. **松开 `Right Control` 键**：
   - 悬浮窗显示紫色 **`Refining...`**。
   - 大模型完成口语清洗、改口覆盖与术语修正后，自动注入当前输入框并无感还原剪贴板。

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
本项目在产品理念与交互设计上，特别感谢开源项目 [yetone/voice-input-src](https://github.com/yetone/voice-input-src) 来的灵感与启发！
