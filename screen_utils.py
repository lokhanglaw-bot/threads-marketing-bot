"""
螢幕座標工具 - 處理 Windows DPI 縮放問題
（目前主要用於除錯和備用方案）
"""

import ctypes

# ── 告訴 Windows 這個程式自己處理 DPI ──
ctypes.windll.user32.SetProcessDPIAware()

print("[screen_utils] DPI 處理已啟用")

def to_click(x, y):
    """保留給 pyautogui 使用的座標轉換（目前主要用 Playwright）"""
    return int(x), int(y)