# save_templates.py
# 執行方式：python save_templates.py
# 只需要跑一次，用來截取回覆按鈕的圖片

import time
import os
import pyautogui
import ctypes
from PIL import ImageGrab

ctypes.windll.user32.SetProcessDPIAware()

os.makedirs('templates', exist_ok=True)

print("=" * 40)
print("回覆按鈕模板截圖工具")
print("=" * 40)
print()
print("步驟：")
print("1. 請先打開 Threads 網頁，找到任意一個帖子")
print("2. 把滑鼠移到【回覆按鈕】上（不要點）")
print("3. 切換回這個視窗，按 Enter")
print()
input("準備好後按 Enter...")

print("3 秒後截取滑鼠位置...")
for i in range(3, 0, -1):
    print(f"  {i}...")
    time.sleep(1)

x, y = pyautogui.position()
print(f"滑鼠位置: ({x}, {y})")

# 截取按鈕周圍 60x40 的區域
region = (x - 30, y - 20, x + 30, y + 20)
img = ImageGrab.grab(bbox=region)
img.save('templates/reply_button.png')

print()
print("✅ 已儲存到 templates/reply_button.png")
print("正在預覽...")
img = img.resize((180, 120))  # 放大方便查看
img.show()
print()
print("如果預覽圖片看起來正確（是回覆按鈕），就完成了。")
print("如果截錯了，重新執行這個腳本。")
