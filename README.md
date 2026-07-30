# voice-input

语音输入方案，暂时只支持 Windows 平台。

## 项目特点与设计
- **全局长按热键触发与交互录制**：按住热键开始录音，松开自动转录精修并注入文本。设置界面提供图形化交互式热键录制（推荐 `[ Right Control ]` / `[ Space ]` 键帽显示）。
- **多 Provider ASR 深度接入**：灵活接入小米 MiMo (`mimo-v2.5-asr`)、豆包 (Volcengine)、通义千问 (DashScope) 及 OpenAI 兼容语音识别 API。
- **7 大 LLM 供应商模式与口误中途改口处理**：支持 OpenAI, DeepSeek, Xiaomi, 阿里云通义千问, 本地 GGUF 模型, 本地 Ollama, Custom 自定义 7 大供应商。不仅自动擦除语气冗余与谐音错字，更可识别“不对”、“算了”、“改成”等改口信号，自动覆盖旧表述并完美保留句式主干。
- **本地 LLM 模型引擎与自动管理器 (`~/.voiceinput/models/`)**：新增 `local` 本地 GGUF 供应商模式，预设轻量 Qwen2.5 纠错模型，支持首次弹窗确认下载（含代理与进度条）、多型号选择与磁盘模型文件一键物理清理。
- **30 FPS 动态视觉交互与多位置悬浮窗**：无边框半透明置顶 UI，具备 30 FPS 呼吸脉冲与动态波形演进，支持 **`底部居中 (bottom_center)`**、**`顶部居中 (top_center)`**、**`屏幕中央 (center)`** 灵活摆放：
  - **`Preparing...`** (缓冲扫频动画)
  - **`Listening...`** (亮白文字 + 🔴 高亮发光呼吸 REC 红灯 + 5-Bar 音量扫频混合波形)
  - **`Refining...`** (柔和紫光)
- **WebDAV 路径精准拼接、自动父目录检查与最多 5 个备份自动循环清理**：
  - 支持坚果云与自定义 WebDAV 供应商，自动去重/规范 Path 路径层级（解决坚果云 `/dav/` 或 Nextcloud 子路径找不到问题）；
  - 下载/同步配置前自动补全本地目标目录，为上传历史生成年月日精准时间戳后缀（如 `config_20260730_101629.json`）；
  - 内置自动循环清理机制（默认最大保留 5 个备份），超过数量时自动物理删除最旧的历史文件。
- **全局网络代理与显式代理路由日志 (HTTP / SOCKS4 / SOCKS5)**：支持一键开关网络代理，配置 `127.0.0.1:7890` 提示主机与端口。开启调试模式时，全量显式输出 `[VIA PROXY: ...]` 代理路由日志。
- **调试模式与带时间戳日志写盘**：提供 `🐞 Debug` 调试设置页，开启时在本地 `logs/voice_input_YYYYMMDD.log` 生成带有毫秒级时间戳的 ASR 识别原始文本与 LLM 润色输出明文日志，关闭时全流程零日志保护隐私。
- **i18n 多语言引擎与 Windows 系统语言自动识别**：内置 **简体中文 (`zh_CN`)** 与 **English (`en_US`)** 完整国际化支持，启动时调用 `QLocale` 自动识别操作系统语言，支持在设置界面一键切换并即时动态刷新所有 Tab 标题与表单 Label。
- **模块化暗黑 Settings GUI & 软件信息页**：
  - 代码解耦重构拆分为 `src/ui/settings/` 模块包 (`asr_tab`, `llm_tab`, `webdav_tab`, `proxy_tab`, `hotkey_tab`, `debug_tab`, `about_tab`)。
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

### 2. 使用 uv 极速管理与运行（推荐 ⚡）
项目根目录内置 `.python-version` (锁死 Python 3.12)，通过 `uv` 即可无视宿主系统 Python 版本，100% 免编译直接使用预编译 Wheel：
```powershell
# 1. 自动下载 Python 3.12 解释器并创建隔离虚拟环境
uv venv

# 2. 一键秒级安装依赖与本地 GGUF 模型推理引擎 (llama-cpp-python)
uv pip install -r requirements.txt llama-cpp-python -i https://pypi.tuna.tsinghua.edu.cn/simple

# 3. 运行主程序
uv run python src/main.py
```

### 3. 传统 pip 源码运行
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
   - 在 **WebDAV Sync** 页中，选择 **`jianguoyun` (坚果云)** 或 **`custom` (自定义)** 供应商。
   - 填入服务器 URL（如坚果云 `https://dav.jianguoyun.com/dav/`）、账号、App 密码与远端目录（如 `/VoiceInput`）。
   - 可点击 **`📤 Upload Current Config`** 或 **`📋 View Remote Backups & Restore`** 查看历史备份恢复。系统将自动删除超过 5 个的最旧备份。
5. **设置代理 (Proxy)**：
   - 在 **Proxy** 页中，勾选 **Enable Global Network Proxy**，选择 `http`/`socks4`/`socks5` 协议并填入主机名（`127.0.0.1`）与端口（`7890`）。
6. **设置触发热键与显示语言 (Hotkey & General)**：
   - 在 **Language** 下拉框中选择 `Auto (跟随系统)`、`简体中文` 或 `English`。
   - 在 **Capsule Position** 下拉框中选择悬浮窗位置（`底部居中` / `顶部居中` / `屏幕中央`）。
   - 点击 **`🎙️ Click to Record`** 按钮，按键盘任意键（推荐右侧 **`Right Control`**）即可完成交互录制。
   - 点击 **`Save Config`** 保存设置。
7. **调试模式 (Debug)**：
   - 在 **Debug** 页勾选开启调试模式，即可在本地 `logs/` 查看带毫秒时间戳与代理路由标签的明文日志。

---

### 4. 快捷语音输入交互
1. 打开并聚焦到任意文本输入框（如 **VS Code**、**记事本**、**微信**、**浏览器** 等）。
2. **长按 `Right Control` 键**：
   - 屏幕上显示琥珀黄 **`Preparing...`** 缓冲动画。
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
