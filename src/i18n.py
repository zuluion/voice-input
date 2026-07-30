import locale
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
        "btn_open_config_dir": "📂 打开配置文件夹",
        "btn_open_logs_dir": "📂 打开日志文件夹",
        "btn_check_update": "🚀 检查版本更新",

        # Form Labels
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

        # WebDAV
        "lbl_enable_webdav": "启用 WebDAV 配置文件同步",
        "lbl_webdav_url": "WebDAV 服务器 URL:",
        "lbl_webdav_user": "账号 / 用户名:",
        "lbl_webdav_pwd": "应用密码 / 密钥:",
        "lbl_remote_dir": "远端保存目录:",
        "lbl_max_backups": "最多保留备份数:",
        "lbl_auto_sync": "启动应用时自动从 WebDAV 下载最新配置",

        # Proxy
        "lbl_enable_proxy": "启用全局网络代理",
        "lbl_proxy_protocol": "代理协议:",
        "lbl_proxy_host": "代理主机:",
        "lbl_proxy_port": "代理端口:",

        # Debug
        "lbl_enable_debug": "启用调试日志模式 (写入日志文件)",
        "lbl_debug_desc": "<b>注意:</b> 开启调试模式后，应用会在本地 <code>logs/</code> 目录下生成格式化日志（包含 ASR 识别原始文本与 LLM 润色输出）。<br>日常使用建议关闭调试模式以保护个人隐私。",

        # About
        "lbl_about_subtitle": "Windows 系统托盘语音输入法应用 · PySide6 & 多 Provider ASR/LLM 精修",
        "lbl_author": "开发者:",
        "lbl_current_ver": "当前版本:",
        "lbl_repo": "官方 GitHub 仓库:",
        "lbl_license": "开源协议:"
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
        "btn_open_config_dir": "📂 Open Config Location",
        "btn_open_logs_dir": "📂 Open Logs Directory",
        "btn_check_update": "🚀 Check for Updates",

        # Form Labels
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

        # WebDAV
        "lbl_enable_webdav": "Enable WebDAV Configuration Sync",
        "lbl_webdav_url": "WebDAV Server URL:",
        "lbl_webdav_user": "Username / Account:",
        "lbl_webdav_pwd": "Password / Secret:",
        "lbl_remote_dir": "Remote Directory:",
        "lbl_max_backups": "Max Backups Retention:",
        "lbl_auto_sync": "Auto-sync from WebDAV on application startup",

        # Proxy
        "lbl_enable_proxy": "Enable Global Network Proxy",
        "lbl_proxy_protocol": "Proxy Protocol:",
        "lbl_proxy_host": "Proxy Host:",
        "lbl_proxy_port": "Proxy Port:",

        # Debug
        "lbl_enable_debug": "Enable Debug Logging Mode (Log to File)",
        "lbl_debug_desc": "<b>Note:</b> When Debug Mode is enabled, the app writes timestamped plaintext logs (including ASR recognized text & LLM refined output) to a local <code>logs/</code> directory.<br>Turn OFF Debug Mode during normal usage to protect user privacy.",

        # About
        "lbl_about_subtitle": "Windows System Tray Voice Input App · PySide6 & Multi-Provider ASR/LLM",
        "lbl_author": "Author:",
        "lbl_current_ver": "Current Version:",
        "lbl_repo": "GitHub Repository:",
        "lbl_license": "License:"
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
        # Fallback to English
        return TRANSLATIONS["en_US"].get(key, default or key)

i18n = I18nManager.get_instance()
