"""
自動化回覆腳本 v10
添加調試功能，幫助找到正確的回覆按鈕位置
"""

import os
import time
import json
import webbrowser
from threading import Thread
from PIL import Image, ImageGrab
import numpy as np

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[AutoReplier] pyautogui 不可用")

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[AutoReplier] OpenCV 不可用")


def take_screenshot():
    """截圖"""
    try:
        img = ImageGrab.grab()
        return np.array(img)
    except Exception as e:
        print(f"[AutoReplier] 截圖失敗: {e}")
        return None


class SmartButtonFinder:
    """智能按鈕定位器"""

    @staticmethod
    def find_heart_button(screenshot):
        """找愛心按鈕"""
        hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)

        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([160, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
        mask = mask1 + mask2

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        best = None
        best_score = 0

        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            if 300 < area < 2500:
                aspect = min(w, h) / max(w, h) if max(w, h) > 0 else 0
                if aspect > 0.6:
                    screen_h = screenshot.shape[0]
                    if y > screen_h * 0.3:
                        score = area * aspect
                        if score > best_score:
                            best_score = score
                            best = (x + w // 2, y + h // 2)

        return best

    @staticmethod
    def find_buttons_near_heart(screenshot, heart_pos, distance_range=(50, 150)):
        """
        在愛心周圍找到所有小按鈕
        返回按鈕列表及其與愛心的距離
        """
        if heart_pos is None:
            return []

        hx, hy = heart_pos
        gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)

        # 閾值化
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        buttons = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = w * h

            # 按鈕大小
            if 200 < area < 2000:
                aspect = min(w, h) / max(w, h) if max(w, h) > 0 else 0
                if aspect > 0.5:
                    cx, cy = x + w // 2, y + h // 2

                    # 計算與愛心的距離
                    dist = abs(cx - hx)  # 只考慮水平距離

                    # 在距離範圍內的按鈕
                    if distance_range[0] <= dist <= distance_range[1]:
                        buttons.append({
                            'pos': (cx, cy),
                            'dist': dist,
                            'area': area,
                            'label': 'right' if cx > hx else 'left'
                        })

        return buttons


class BrowserAutoReplier:
    """自動回覆器"""

    def __init__(self, bot_token: str, pending_file: str = "pending_replies.json"):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.pending_file = pending_file
        self.update_offset = 0
        self.running = False

    def _get_pending_replies(self) -> dict:
        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _remove_pending_reply(self, reply_id: str) -> None:
        pending = self._get_pending_replies()
        if reply_id in pending:
            del pending[reply_id]
            with open(self.pending_file, 'w', encoding='utf-8') as f:
                json.dump(pending, f, ensure_ascii=False, indent=2)

    def _clean_url(self, url: str) -> str:
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        if url.endswith('/media'):
            url = url[:-6]
        if '?' in url:
            url = url.split('?')[0]
        return url

    def open_url_in_existing_browser(self, url: str) -> bool:
        try:
            webbrowser.open(url)
            print(f"[AutoReplier] 已打開: {url}")
            return True
        except Exception as e:
            print(f"[AutoReplier] 打開失敗: {e}")
            return False

    def wait_for_page_load(self):
        print("[AutoReplier] 等待頁面加載...")
        time.sleep(5)

    def scroll_to_bottom(self):
        if PYAUTOGUI_AVAILABLE:
            print("[AutoReplier] 滾動頁面...")
            pyautogui.press('end')
            time.sleep(0.5)
            pyautogui.press('end')
            time.sleep(0.5)

    def find_reply_button_position(self) -> tuple:
        """找到回覆按鈕位置 - 使用調試模式"""
        if not CV2_AVAILABLE:
            print("[AutoReplier] OpenCV 不可用")
            return None

        print("[AutoReplier] 截圖並識別按鈕...")

        try:
            screenshot = take_screenshot()
            if screenshot is None:
                return None

            # 找愛心按鈕
            heart_pos = SmartButtonFinder.find_heart_button(screenshot)

            if heart_pos:
                print(f"[AutoReplier] 找到愛心按鈕: {heart_pos}")

                # 找愛心周圍的按鈕
                buttons = SmartButtonFinder.find_buttons_near_heart(screenshot, heart_pos)

                if buttons:
                    print(f"[AutoReplier] 愛心周圍找到 {len(buttons)} 個按鈕:")
                    for i, btn in enumerate(buttons):
                        print(f"  按鈕 {i+1}: 位置={btn['pos']}, 距離={btn['dist']}px, 方向={btn['label']}")

                    # 找右邊最近的按鈕（這應該是回覆）
                    right_buttons = [b for b in buttons if b['label'] == 'right']
                    if right_buttons:
                        # 選擇距離 50-100 像素的
                        for btn in sorted(right_buttons, key=lambda b: b['dist']):
                            if 50 <= btn['dist'] <= 100:
                                print(f"[AutoReplier] 選擇回覆按鈕: {btn['pos']}")
                                return btn['pos']

                        # 如果找不到，選擇第一個右邊的按鈕
                        reply_btn = min(right_buttons, key=lambda b: b['dist'])
                        print(f"[AutoReplier] 選擇第一個右邊按鈕: {reply_btn['pos']} (距離: {reply_btn['dist']}px)")
                        return reply_btn['pos']

                # 沒有找到周圍按鈕，使用預設偏移
                reply_pos = (heart_pos[0] + 70, heart_pos[1])
                print(f"[AutoReplier] 使用預設位置: {reply_pos}")
                return reply_pos

            print("[AutoReplier] 找不到愛心按鈕")
            return None

        except Exception as e:
            print(f"[AutoReplier] 識別失敗: {e}")
            return None

    def click_at_position(self, x, y):
        if PYAUTOGUI_AVAILABLE:
            print(f"[AutoReplier] 點擊位置: ({x}, {y})")
            pyautogui.click(x, y)
            time.sleep(1.5)  # 增加等待時間

    def type_reply(self, text: str) -> bool:
        if PYAUTOGUI_AVAILABLE:
            try:
                import pyperclip
                pyperclip.copy(text)
                time.sleep(0.3)

                pyautogui.hotkey('ctrl', 'v')
                print("[AutoReplier] 已粘貼回覆內容")
                time.sleep(0.5)

                pyautogui.press('enter')
                print("[AutoReplier] 回覆已發送！")

                return True
            except Exception as e:
                print(f"[AutoReplier] 輸入失敗: {e}")
                return False

    def auto_reply(self, reply_id: str) -> bool:
        pending = self._get_pending_replies()

        if reply_id not in pending:
            print(f"[AutoReplier] 未找到: {reply_id}")
            return False

        data = pending[reply_id]
        url = self._clean_url(data['url'])
        reply_text = data['reply']

        print(f"[AutoReplier] 開始自動回覆...")

        self.open_url_in_existing_browser(url)
        self.wait_for_page_load()
        self.scroll_to_bottom()

        position = self.find_reply_button_position()

        if position:
            x, y = position
            self.click_at_position(x, y)

            time.sleep(1)
            self.type_reply(reply_text)
        else:
            print("[AutoReplier] 無法找到回覆按鈕")
            return False

        self._remove_pending_reply(reply_id)
        print("[AutoReplier] 完成！")

        return True

    def poll_callbacks(self) -> None:
        import requests
        print("[AutoReplier] 開始監聽回覆按鈕...")

        while self.running:
            try:
                url = f"{self.api_url}/getUpdates"
                params = {'offset': self.update_offset, 'timeout': 5}

                response = requests.get(url, params=params, timeout=10)
                result = response.json()

                if result.get('ok'):
                    for update in result.get('result', []):
                        self.update_offset = update['update_id'] + 1

                        if 'callback_query' in update:
                            callback = update['callback_query']
                            data = callback.get('data', '')

                            print(f"[AutoReplier] 收到: {data}")

                            if data.startswith('reply_'):
                                try:
                                    requests.post(
                                        f"{self.api_url}/answerCallbackQuery",
                                        json={'callback_query_id': callback['id'], 'text': "正在處理，請稍候..."}
                                    )
                                except:
                                    pass

                                success = self.auto_reply(data)
                                print(f"[AutoReplier] 回覆{'成功！' if success else '失敗'}")

            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                print(f"[AutoReplier] 輪詢錯誤: {e}")
                time.sleep(2)

    def start(self) -> None:
        self.running = True
        print("=" * 60)
        print("自動化回覆器已啟動 (v10 - 調試模式)")
        print("=" * 60)
        print("-" * 60)

        thread = Thread(target=self.poll_callbacks)
        thread.daemon = True
        thread.start()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self) -> None:
        self.running = False
        print("\n[AutoReplier] 已停止")


def main():
    from config import TELEGRAM_BOT_TOKEN

    if not CV2_AVAILABLE:
        print("請運行: pip install opencv-python")
        return

    if not PYAUTOGUI_AVAILABLE:
        print("請運行: pip install pyautogui")
        return

    replier = BrowserAutoReplier(TELEGRAM_BOT_TOKEN)
    replier.start()


if __name__ == "__main__":
    main()