import unittest
from src.i18n import i18n, TRANSLATIONS

class TestI18nManager(unittest.TestCase):
    def test_translation_zh(self):
        i18n.set_language("zh_CN")
        self.assertEqual(i18n.t("app_title"), "语音输入法")
        self.assertEqual(i18n.t("btn_save"), "保存设置")
        self.assertEqual(i18n.t("tab_asr"), "🎙️ 语音识别")
        self.assertEqual(i18n.t("tab_llm"), "🤖 大模型润色")
        self.assertEqual(i18n.t("tab_webdav"), "☁️ WebDAV 同步")
        self.assertEqual(i18n.t("tab_proxy"), "🌐 网络代理")
        self.assertEqual(i18n.t("tab_hotkey"), "⌨️ 热键与常规")
        self.assertEqual(i18n.t("tab_debug"), "🐞 调试模式")
        self.assertEqual(i18n.t("tab_about"), "ℹ️ 关于软件")
        self.assertEqual(i18n.t("asr_provider"), "ASR 供应商:")
        self.assertEqual(i18n.t("webdav_provider"), "WebDAV 供应商:")

    def test_translation_en(self):
        i18n.set_language("en_US")
        self.assertEqual(i18n.t("app_title"), "Voice Input")
        self.assertEqual(i18n.t("btn_save"), "Save Config")
        self.assertEqual(i18n.t("tab_asr"), "🎙️ ASR")
        self.assertEqual(i18n.t("tab_llm"), "🤖 LLM Refine")
        self.assertEqual(i18n.t("tab_webdav"), "☁️ WebDAV Sync")
        self.assertEqual(i18n.t("tab_proxy"), "🌐 Proxy")
        self.assertEqual(i18n.t("tab_hotkey"), "⌨️ Hotkey & General")
        self.assertEqual(i18n.t("tab_debug"), "🐞 Debug")
        self.assertEqual(i18n.t("tab_about"), "ℹ️ About")
        self.assertEqual(i18n.t("asr_provider"), "ASR Provider:")
        self.assertEqual(i18n.t("webdav_provider"), "WebDAV Provider:")

    def test_translation_keys_parity(self):
        zh_keys = set(TRANSLATIONS["zh_CN"].keys())
        en_keys = set(TRANSLATIONS["en_US"].keys())
        self.assertEqual(zh_keys, en_keys, f"Missing keys in translations: {zh_keys ^ en_keys}")

if __name__ == "__main__":
    unittest.main()
