import unittest
from unittest.mock import MagicMock
from pynput.keyboard import Key, KeyCode
from src.core.hotkey import HotkeyListener

class TestHotkeyMatching(unittest.TestCase):
    def setUp(self):
        self.listener = HotkeyListener(target_key_str="Key.ctrl_r")

    def test_match_right_control(self):
        # VK 163 is Right Control in Win32
        key_rctrl = KeyCode.from_vk(163)
        self.assertTrue(self.listener._match_key(key_rctrl))

        # VK 162 is Left Control in Win32
        key_lctrl = KeyCode.from_vk(162)
        self.assertFalse(self.listener._match_key(key_lctrl))

    def test_match_right_alt(self):
        listener_alt = HotkeyListener(target_key_str="Key.alt_r")
        # VK 165 is Right Alt
        key_ralt = KeyCode.from_vk(165)
        self.assertTrue(listener_alt._match_key(key_ralt))

        # VK 164 is Left Alt
        key_lalt = KeyCode.from_vk(164)
        self.assertFalse(listener_alt._match_key(key_lalt))

    def test_match_space_key(self):
        listener_space = HotkeyListener(target_key_str="Key.space")
        self.assertTrue(listener_space._match_key(Key.space))
        self.assertFalse(listener_space._match_key(Key.ctrl_r))

if __name__ == "__main__":
    unittest.main()
