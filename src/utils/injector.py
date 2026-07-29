import ctypes
import time
import win32clipboard
import win32con
from PySide6.QtCore import QTimer

# Win32 SendInput constants & structs
PUL = ctypes.POINTER(ctypes.c_ulong)

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.c_ulong),
        ("wParamL", ctypes.c_ushort),
        ("wParamH", ctypes.c_ushort)
    ]

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", PUL)
    ]

class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("ki", KEYBDINPUT),
        ("mi", MOUSEINPUT),
        ("hi", HARDWAREINPUT)
    ]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("ii", INPUT_UNION)
    ]

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL = 0x11
VK_V = 0x56

def send_key_event(vk_code: int, flags: int = 0) -> None:
    extra = ctypes.c_ulong(0)
    ii_ = INPUT_UNION()
    ii_.ki = KEYBDINPUT(vk_code, 0, flags, 0, ctypes.pointer(extra))
    input_struct = INPUT(ctypes.c_ulong(INPUT_KEYBOARD), ii_)
    ctypes.windll.user32.SendInput(1, ctypes.pointer(input_struct), ctypes.sizeof(input_struct))

def send_ctrl_v() -> None:
    send_key_event(VK_CONTROL, 0)
    send_key_event(VK_V, 0)
    send_key_event(VK_V, KEYEVENTF_KEYUP)
    send_key_event(VK_CONTROL, KEYEVENTF_KEYUP)

def get_clipboard_text() -> str:
    try:
        win32clipboard.OpenClipboard()
        if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
            data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
        else:
            data = ""
        win32clipboard.CloseClipboard()
        return data
    except Exception:
        return ""

def set_clipboard_text(text: str) -> None:
    try:
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
        win32clipboard.CloseClipboard()
    except Exception:
        pass

class TextInjector:
    def __init__(self, restore_delay_ms: int = 150) -> None:
        self.restore_delay_ms = restore_delay_ms

    def inject(self, text: str) -> None:
        if not text:
            return

        # 1. Backup original clipboard
        old_text = get_clipboard_text()

        # 2. Put text into clipboard
        set_clipboard_text(text)

        # 3. Simulate Ctrl + V
        send_ctrl_v()

        # 4. Restore original clipboard asynchronously after delay
        def restore():
            set_clipboard_text(old_text)

        QTimer.singleShot(self.restore_delay_ms, restore)
