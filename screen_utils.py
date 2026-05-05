"""
螢幕座標工具 - 處理 Windows DPI 縮放問題
所有截圖座標都需要經過這裡轉換才能正確點擊
"""

import ctypes
import pyautogui
from PIL import ImageGrab

# ── 告訴 Windows 這個程式自己處理 DPI，必須在最頂部執行 ──
ctypes.windll.user32.SetProcessDPIAware()

# ── 啟動時計算一次縮放比 ──
def _calc_scale():
    sw, sh = pyautogui.size()
    img = ImageGrab.grab()
    return img.width / sw, img.height / sh

SCALE_X, SCALE_Y = _calc_scale()
print(f"[screen_utils] DPI 縮放比: {SCALE_X:.2f}x / {SCALE_Y:.2f}y")


def to_click(screenshot_x, screenshot_y):
    """
    把截圖圖像識別返回的座標，轉成 pyautogui.click() 可以正確使用的座標。
    所有 pyautogui.click() 前都要先經過這個函數。
    """
    return int(screenshot_x / SCALE_X), int(screenshot_y / SCALE_Y)


def find_on_screen(template_path, region=None, confidence=0.7):
    """
    在螢幕上找模板圖片，返回中心點的【可點擊座標】。
    找不到返回 None。
    """
    try:
        location = pyautogui.locateOnScreen(
            template_path,
            region=region,
            confidence=confidence,
            grayscale=False
        )
        if location:
            cx = location.left + location.width // 2
            cy = location.top + location.height // 2
            # 轉換成實際螢幕座標
            return to_click(cx, cy)
    except Exception as e:
        print(f"[find_on_screen] 失敗: {e}")
    return None


def find_reply_button(heart_x_screenshot, heart_y_screenshot):
    """
    在愛心按鈕附近找回覆按鈕。
    heart_x_screenshot, heart_y_screenshot 是圖像識別返回的截圖座標（未縮放）。
    返回可以直接傳給 pyautogui.click() 的座標。
    """
    # 先把愛心座標轉成可點擊座標
    heart_cx, heart_cy = to_click(heart_x_screenshot, heart_y_screenshot)

    # 在愛心右邊區域搜尋回覆按鈕（使用截圖座標範圍）
    search_region = (
        heart_x_screenshot - 20,
        heart_y_screenshot - 25,
        300,   # 寬度
        50     # 高度
    )

    # 嘗試用模板圖片識別
    result = find_on_screen('templates/reply_button.png', region=search_region, confidence=0.65)
    if result:
        print(f"[find_reply_button] 找到回覆按鈕: {result}")
        return result

    # 找不到模板時的備用方案：偏移量 + DPI 校正
    print("[find_reply_button] 模板找不到，使用偏移量備用")
    return to_click(heart_x_screenshot + 70, heart_y_screenshot)
