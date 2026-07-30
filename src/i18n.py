from PySide6.QtCore import QLocale

TRANSLATIONS = {
    "zh_CN": {
        # General & Tray
        "app_title": "语音输入法",
        "tray_enabled": "启用语音输入",
        "tray_settings": "设置...",
        "tray_quit": "退出",

        # Floating Capsule
        "capsule_preparing": "准备中...",
        "capsule_listening": "正在聆听...",
        "capsule_refining": "智能润色中...",

        # Settings Tabs
        "tab_asr": "🎙️ 语音识别",
        "tab_llm": "🤖 大模型润色",
        "tab_webdav": "☁️ WebDAV 同步",
        "tab_proxy": "🌐 网络代理",
        "tab_hotkey": "⌨️ 热键与常规",
        "tab_debug": "🐞 调试模式",
        "tab_about": "ℹ️ 关于软件",

        # Buttons
        "btn_save": "保存设置",
        "btn_cancel": "取消",
        "btn_fetch_models": "🔄 获取模型列表",
        "btn_test_asr": "测试 ASR 连通性",
        "btn_test_llm": "测试 LLM 连通性",
        "btn_test_proxy": "测试代理连通性",
        "btn_record_hotkey": "🎙️ 点击开始录制",
        "btn_reset_hotkey": "↺ 重置",
        "btn_reset_prompt": "↺ 恢复默认提示词",
        "btn_upload_webdav": "📤 上传当前配置",
        "btn_download_webdav": "📥 下载最新配置",
        "btn_history_webdav": "📋 查看远端备份并恢复",
        "btn_download_local_model": "📥 下载本地模型",
        "btn_delete_local_model": "🗑️ 删除本地模型",
        "lbl_local_model_status": "本地模型状态:",
        "local_model_ready": "✅ 已就绪 (存储在 ~/.voiceinput/models/)",
        "local_model_missing": "⚠️ 未下载",
        "confirm_download_model_title": "确认下载本地模型",
        "confirm_download_model_msg": "是否确认下载以下本地 LLM 模型？\n\n模型 ID: {model_id}\n文件大小: {size_str}\n保存目录: ~/.voiceinput/models/\n\n(若在设置中开启了代理，将自动通过代理下载)",
        "confirm_delete_model_title": "确认删除本地模型",
        "confirm_delete_model_msg": "确定要删除本地模型 [{model_id}] 吗？\n此操作将清理本地 GGUF 文件并释放空间。",
        "btn_open_config_dir": "📂 打开配置文件夹",
        "btn_open_logs_dir": "📂 打开日志文件夹",
        "btn_check_update": "🚀 检查版本更新",

        # Form Labels & Common
        "lbl_language": "显示语言:",
        "lbl_lang_auto": "跟随系统 (Auto)",
        "lbl_lang_zh": "简体中文 (Chinese)",
        "lbl_lang_en": "English",
        "lbl_provider": "供应商模式:",
        "lbl_api_key": "API 密钥 (Key):",
        "lbl_base_url": "服务地址 (Base URL):",
        "lbl_model_name": "模型名称:",
        "lbl_hotkey": "触发热键:",
        "lbl_position": "悬浮窗位置:",

        # Capsule Positions
        "pos_bottom_center": "底部居中",
        "pos_top_center": "顶部居中",
        "pos_center": "屏幕中央",

        # ASR Tab
        "asr_provider": "ASR 供应商:",
        "asr_doubao_app_id": "豆包 App ID:",
        "asr_doubao_token": "访问令牌 (Access Token):",
        "asr_doubao_cluster": "业务集群 (Cluster):",
        "asr_qwen_api_key": "通义千问 API 密钥:",
        "asr_qwen_app_key": "通义千问 App 密钥:",
        "asr_mimo_api_key": "小米 MiMo API 密钥:",
        "asr_mimo_base_url": "小米 MiMo 服务地址:",
        "asr_mimo_model": "小米 MiMo 模型名称:",
        "asr_openai_api_key": "Whisper API 密钥:",
        "asr_openai_base_url": "Whisper 服务地址:",
        "asr_openai_model": "Whisper 模型名称:",

        # LLM Tab
        "llm_enable": "启用 LLM 智能精修与口语纠错",
        "llm_provider": "LLM 供应商:",
        "llm_system_prompt": "系统提示词 (System Prompt):",

        # WebDAV Tab
        "webdav_enable": "启用 WebDAV 配置文件同步",
        "webdav_provider": "WebDAV 供应商:",
        "webdav_server_url": "WebDAV 服务器 URL:",
        "webdav_username": "账号 / 用户名:",
        "webdav_password": "应用密码 / 密钥:",
        "webdav_remote_dir": "远端保存目录:",
        "webdav_max_backups": "最多保留备份数:",
        "webdav_auto_sync": "启动应用时自动从 WebDAV 下载最新配置",
        "webdav_history_title": "📋 选择需恢复的 WebDAV 备份",
        "webdav_history_label": "找到的远端 WebDAV 备份文件:",

        # Proxy Tab
        "proxy_enable": "启用全局网络代理",
        "proxy_protocol": "代理协议:",
        "proxy_host": "代理主机:",
        "proxy_port": "代理端口:",

        # Hotkey & General Tab
        "hotkey_trigger": "触发热键:",
        "hotkey_position": "悬浮窗位置:",
        "hotkey_recording": "🔴 请按下任意热键...",
        "hotkey_waiting": "[ 等待按键中... ]",

        # Debug Tab
        "debug_enable": "启用调试日志模式 (写入日志文件)",
        "debug_desc": "<b>注意:</b> 开启调试模式后，应用会在本地 <code>logs/</code> 目录下生成格式化日志（包含 ASR 识别原始文本与 LLM 润色输出）。<br>日常使用建议关闭调试模式以保护个人隐私。",

        # About Tab
        "about_title": "🎙️ Voice Input (语音输入法)",
        "about_subtitle": "Windows 系统托盘语音输入法应用 · PySide6 & 多 Provider ASR/LLM 精修",
        "about_author": "开发者:",
        "about_version": "当前版本:",
        "about_repo": "官方 GitHub 仓库:",
        "about_license": "开源协议:"
    },
    "en_US": {
        # General & Tray
        "app_title": "Voice Input",
        "tray_enabled": "Enabled",
        "tray_settings": "Settings...",
        "tray_quit": "Quit",

        # Floating Capsule
        "capsule_preparing": "Preparing...",
        "capsule_listening": "Listening...",
        "capsule_refining": "Refining...",

        # Settings Tabs
        "tab_asr": "🎙️ ASR",
        "tab_llm": "🤖 LLM Refine",
        "tab_webdav": "☁️ WebDAV Sync",
        "tab_proxy": "🌐 Proxy",
        "tab_hotkey": "⌨️ Hotkey & General",
        "tab_debug": "🐞 Debug",
        "tab_about": "ℹ️ About",

        # Buttons
        "btn_save": "Save Config",
        "btn_cancel": "Cancel",
        "btn_fetch_models": "🔄 Fetch Models",
        "btn_test_asr": "Test ASR Connection",
        "btn_test_llm": "Test LLM Connection",
        "btn_test_proxy": "Test Proxy Connection",
        "btn_record_hotkey": "🎙️ Click to Record",
        "btn_reset_hotkey": "↺ Reset",
        "btn_reset_prompt": "↺ Reset Prompt",
        "btn_upload_webdav": "📤 Upload Current Config",
        "btn_download_webdav": "📥 Download Latest Config",
        "btn_history_webdav": "📋 View Remote Backups & Restore",
        "btn_download_local_model": "📥 Download Local Model",
        "btn_delete_local_model": "🗑️ Delete Local Model",
        "lbl_local_model_status": "Local Model Status:",
        "local_model_ready": "✅ Ready (Stored in ~/.voiceinput/models/)",
        "local_model_missing": "⚠️ Not Downloaded",
        "confirm_download_model_title": "Confirm Download Local Model",
        "confirm_download_model_msg": "Are you sure you want to download the following local model?\n\nModel ID: {model_id}\nSize: {size_str}\nTarget Dir: ~/.voiceinput/models/\n\n(Proxy settings will be used automatically if enabled)",
        "confirm_delete_model_title": "Confirm Delete Local Model",
        "confirm_delete_model_msg": "Are you sure you want to delete local model [{model_id}]?\nThis will remove the GGUF file and free disk space.",
        "btn_open_config_dir": "📂 Open Config Location",
        "btn_open_logs_dir": "📂 Open Logs Directory",
        "btn_check_update": "🚀 Check for Updates",

        # Form Labels & Common
        "lbl_language": "Language:",
        "lbl_lang_auto": "Auto (System Default)",
        "lbl_lang_zh": "简体中文 (Chinese)",
        "lbl_lang_en": "English",
        "lbl_provider": "Provider Mode:",
        "lbl_api_key": "API Key:",
        "lbl_base_url": "Base URL:",
        "lbl_model_name": "Model Name:",
        "lbl_hotkey": "Trigger Hotkey:",
        "lbl_position": "Capsule Position:",

        # Capsule Positions
        "pos_bottom_center": "Bottom Center",
        "pos_top_center": "Top Center",
        "pos_center": "Center",

        # ASR Tab
        "asr_provider": "ASR Provider:",
        "asr_doubao_app_id": "Doubao App ID:",
        "asr_doubao_token": "Access Token:",
        "asr_doubao_cluster": "Cluster:",
        "asr_qwen_api_key": "Qwen API Key:",
        "asr_qwen_app_key": "Qwen App Key:",
        "asr_mimo_api_key": "MiMo API Key:",
        "asr_mimo_base_url": "MiMo Base URL:",
        "asr_mimo_model": "MiMo Model:",
        "asr_openai_api_key": "Whisper API Key:",
        "asr_openai_base_url": "Whisper Base URL:",
        "asr_openai_model": "Whisper Model:",

        # LLM Tab
        "llm_enable": "Enable LLM Refinement & Speech Cleaning",
        "llm_provider": "LLM Provider:",
        "llm_system_prompt": "System Prompt:",

        # WebDAV Tab
        "webdav_enable": "Enable WebDAV Configuration Sync",
        "webdav_provider": "WebDAV Provider:",
        "webdav_server_url": "WebDAV Server URL:",
        "webdav_username": "Username / Account:",
        "webdav_password": "Password / Secret:",
        "webdav_remote_dir": "Remote Directory:",
        "webdav_max_backups": "Max Backups Retention:",
        "webdav_auto_sync": "Auto-sync from WebDAV on application startup",
        "webdav_history_title": "📋 Select WebDAV Backup to Restore",
        "webdav_history_label": "Remote WebDAV Backups Found:",

        # Proxy Tab
        "proxy_enable": "Enable Global Network Proxy",
        "proxy_protocol": "Proxy Protocol:",
        "proxy_host": "Proxy Host:",
        "proxy_port": "Proxy Port:",

        # Hotkey & General Tab
        "hotkey_trigger": "Trigger Hotkey:",
        "hotkey_position": "Capsule Position:",
        "hotkey_recording": "🔴 Press any key...",
        "hotkey_waiting": "[ Waiting key... ]",

        # Debug Tab
        "debug_enable": "Enable Debug Logging Mode (Log to File)",
        "debug_desc": "<b>Note:</b> When Debug Mode is enabled, the app writes timestamped plaintext logs (including ASR recognized text & LLM refined output) to a local <code>logs/</code> directory.<br>Turn OFF Debug Mode during normal usage to protect user privacy.",

        # About Tab
        "about_title": "🎙️ Voice Input",
        "about_subtitle": "Windows System Tray Voice Input App · PySide6 & Multi-Provider ASR/LLM",
        "about_author": "Author:",
        "about_version": "Current Version:",
        "about_repo": "GitHub Repository:",
        "about_license": "License:"
    }
}

class I18nManager:
    _instance = None

    def __init__(self) -> None:
        self.current_lang = "zh_CN"

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = I18nManager()
        return cls._instance

    def detect_system_language(self) -> str:
        try:
            sys_locale = QLocale.system().name()
            if sys_locale.startswith("zh"):
                return "zh_CN"
        except Exception:
            pass
        return "en_US"

    def set_language(self, lang_setting: str) -> None:
        if lang_setting == "auto" or not lang_setting:
            self.current_lang = self.detect_system_language()
        elif lang_setting in TRANSLATIONS:
            self.current_lang = lang_setting
        else:
            self.current_lang = "en_US"

    def t(self, key: str, default: str = "") -> str:
        lang_dict = TRANSLATIONS.get(self.current_lang, TRANSLATIONS["en_US"])
        if key in lang_dict:
            return lang_dict[key]
        return TRANSLATIONS["en_US"].get(key, default or key)

i18n = I18nManager.get_instance()
