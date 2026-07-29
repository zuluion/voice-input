# voice-input

语音输入方案，暂时只支持 Windows 平台。

## 项目特点与设计
- **全局按键触发**：按住热键开始录音，松开自动转录并注入当前聚焦输入框。
- **多 Provider ASR 支持**：灵活接入豆包 (Doubao)、通义千问 (Qwen)、小米 (Xiaomi) 及 OpenAI 兼容语音识别 API。
- **动态胶囊悬浮窗**：无边框半透明置顶 UI，由真实音频 RMS 电平驱动 5 根动态波形动画。
- **LLM 保守智能纠错**：接入 OpenAI 兼容大模型修复语音识别中的中文谐音与技术术语错误，严格保护原意不修改正常内容。
- **无感文本注入**：基于剪贴板备份 + Win32 `SendInput` 模拟 `Ctrl+V`，注入完成后自动恢复原始剪贴板。

## 📚 文档列表
- 📋 [**需求规格说明书 (Spec / PRD)**](docs/specs/speech_input_windows_spec.md)
- 💡 [**Windows 提示词 (Prompt)**](docs/prompts/windows_voice_input_prompt.md)

## 🙏 致谢 (Acknowledgements)
本项目在产品理念与交互设计上，特别感谢开源项目 [yetone/voice-input-src](https://github.com/yetone/voice-input-src) 带来的灵感与启发！

