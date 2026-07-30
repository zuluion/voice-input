import unittest
from src.i18n import i18n, I18nManager

class TestI18nManager(unittest.TestCase):
    def test_translation_zh(self):
        i18n.set_language("zh_CN")
        self.assertEqual(i18n.t("app_title"), "语音输入法")
        self.assertEqual(i18n.t("btn_save"), "保存设置")

    def test_translation_en(self):
        i18n.set_language("en_US")
        self.assertEqual(i18n.t("app_title"), "Voice Input")
        self.assertEqual(i18n.t("btn_save"), "Save Config")

    def test_translation_auto(self):
        i18n.set_language("auto")
        self.assertIn(i18n.current_lang, ["zh_CN", "en_US"])
        title = i18n.t("app_title")
        self.assertTrue(title in ["语音输入法", "Voice Input"])

if __name__ == "__main__":
    unittest.main()
