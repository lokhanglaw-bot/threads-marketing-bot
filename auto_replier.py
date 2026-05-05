"""
自動化回覆腳本 v4
使用 Playwright + JavaScript 精確定位回覆按鈕
不受帖子長度影響
"""

import os
import time
import json
import webbrowser
import asyncio
from threading import Thread
from dataclasses import dataclass
from typing import Optional

# 嘗試導入 Playwright
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[AutoReplier] Playwright 不可用，請運行: pip install playwright && playwright install")

# 嘗試導入 pyautogui（用於備用方案）
try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False


@dataclass
class ReplyButtonResult:
    """回覆按鈕定位結果"""
    found: bool
    x: int = 0
    y: int = 0
    method: str = ""


class ThreadsAutoReplier:
    """Threads 智能回覆器"""

    def __init__(self, bot_token: str, pending_file: str = "pending_replies.json"):
        self.bot_token = bot_token
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.pending_file = pending_file
        self.update_offset = 0
        self.running = False

        # 瀏覽器視窗大小（用於備用座標方案）
        self.browser_viewport = {'width': 1280, 'height': 900}

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

    async def _find_reply_button_js(self, page) -> Optional[dict]:
        """
        使用 JavaScript 在 Threads 頁面中找到回覆按鈕
        返回按鈕的位置和尺寸
        """
        js_code = """
        async () => {
            // Threads 回覆按鈕的選擇器
            const selectors = [
                // 方法1: aria-label 包含"回覆"或"Reply"
                'button[aria-label*="回覆"]',
                'button[aria-label*="Reply"]',
                'button[aria-label*="replies"]',

                // 方法2: 找到回覆圖標（對話氣泡 SVG）
                'button svg path[d*="M20"]',
                'button svg path[d*="M2"]',
                'button:has(svg path[d*="M20 2"])',

                // 方法3: 找到 article 下的按鈕（回覆通常在第一個）
                'article button:not([aria-label*="like"]):not([aria-label*="vote"]):not([aria-label*="bookmark"])',
                'article button[aria-label*="回"]',

                // 方法4: 所有回覆相關的按鈕
                'button:has-text("回覆")',
                'button:has-text("回應")',
                'button:has-text("回")',

                // 方法5: 最後備用 - 找文章底部的小按鈕
                'main article button',
            ];

            for (const selector of selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        // 確保元素可見且在視窗內
                        if (rect.width > 0 && rect.height > 0 &&
                            rect.top >= 0 && rect.left >= 0) {

                            // 回覆按鈕通常是小的、方形的
                            // 寬度在 24-50px 之間
                            if (rect.width < 60 && rect.height < 60) {
                                return {
                                    found: true,
                                    x: rect.left + rect.width / 2,
                                    y: rect.top + rect.height / 2,
                                    width: rect.width,
                                    height: rect.height,
                                    selector: selector,
                                    text: el.getAttribute('aria-label') || el.textContent
                                };
                            }
                        }
                    }
                } catch (e) {}
            }

            // 找不到，回傳第一個可點擊的 article 按鈕
            const articleButtons = document.querySelectorAll('article button');
            for (const btn of articleButtons) {
                const rect = btn.getBoundingClientRect();
                if (rect.width > 20 && rect.height > 20) {
                    // 檢查是否是回覆相關
                    const label = btn.getAttribute('aria-label') || '';
                    if (!label.includes('like') && !label.includes('bookmark')) {
                        return {
                            found: true,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                            selector: 'article button (fallback)',
                            text: label
                        };
                    }
                }
            }

            return { found: false };
        }
        """

        try:
            result = await page.evaluate(js_code)
            return result if result else None
        except Exception as e:
            print(f"[AutoReplier] JavaScript 定位失敗: {e}")
            return None

    async def _find_reply_input_js(self, page) -> Optional[dict]:
        """
        使用 JavaScript 找到回覆輸入框
        """
        js_code = """
        async () => {
            const selectors = [
                // 主要選擇器
                'div[contenteditable="true"]',
                'div[role="textbox"]',
                'div[aria-label*="回覆"]',
                'div[aria-label*="Reply"]',
                'textarea',
                'input[type="text"]',

                // 包含回覆文字的
                'div:has-text("寫下回覆...")',
                'div:has-text("回覆...")',
                'div:has-text("添加回覆")',

                // 通用
                'div[data-pressable-container="true"]',
            ];

            for (const selector of selectors) {
                try {
                    const elements = document.querySelectorAll(selector);
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        // 確保元素可見
                        if (rect.width > 100 && rect.height > 30) {
                            return {
                                found: true,
                                x: rect.left,
                                y: rect.top,
                                width: rect.width,
                                height: rect.height,
                                selector: selector,
                                tag: el.tagName
                            };
                        }
                    }
                } catch (e) {}
            }

            return { found: false };
        }
        """

        try:
            result = await page.evaluate(js_code)
            return result if result else None
        except Exception as e:
            print(f"[AutoReplier] 輸入框定位失敗: {e}")
            return None

    async def _click_reply_and_type(self, page, reply_text: str) -> bool:
        """
        點擊回覆按鈕並輸入文字
        """
        # 步驟1: 找到回覆按鈕
        button_info = await self._find_reply_button_js(page)

        if button_info and button_info.get('found'):
            print(f"[AutoReplier] 找到回覆按鈕: ({button_info['x']:.0f}, {button_info['y']:.0f})")
            print(f"   按鈕大小: {button_info['width']:.0f}x{button_info['height']:.0f}")
            print(f"   按鈕文字: {button_info.get('text', 'N/A')}")

            # 點擊回覆按鈕
            await page.mouse.click(button_info['x'], button_info['y'])
            print("[AutoReplier] 已點擊回覆按鈕")
            await asyncio.sleep(1.5)

            # 步驟2: 找到輸入框
            input_info = await self._find_reply_input_js(page)

            if input_info and input_info.get('found'):
                print(f"[AutoReplier] 找到輸入框: {input_info['selector']}")

                # 點擊輸入框
                center_x = input_info['x'] + input_info['width'] / 2
                center_y = input_info['y'] + input_info['height'] / 2
                await page.mouse.click(center_x, center_y)
                await asyncio.sleep(0.3)
            else:
                print("[AutoReplier] 使用直接粘貼方式")

            # 步驟3: 輸入回覆
            # 使用 clipborad 粘貼（處理中文）
            import pyperclip
            pyperclip.copy(reply_text)

            await page.keyboard.press('Control+v')
            await asyncio.sleep(0.5)

            # 步驟4: 發送
            await page.keyboard.press('Enter')
            print("[AutoReplier] 回覆已發送！")
            return True
        else:
            print("[AutoReplier] 找不到回覆按鈕")
            return False

    def auto_reply(self, reply_id: str) -> bool:
        """執行自動回覆（非同步）"""
        pending = self._get_pending_replies()

        if reply_id not in pending:
            print(f"[AutoReplier] 未找到: {reply_id}")
            return False

        data = pending[reply_id]
        url = self._clean_url(data['url'])
        reply_text = data['reply']

        print(f"[AutoReplier] 開始自動回覆...")
        print(f"   URL: {url}")
        print(f"   回覆: {reply_text[:50]}...")

        # 創建新的事件循環來運行 async 代碼
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(self._auto_reply_async(url, reply_text))
        loop.close()

        # 刪除記錄
        if success:
            self._remove_pending_reply(reply_id)

        return success

    async def _auto_reply_async(self, url: str, reply_text: str) -> bool:
        """非同步執行回覆"""
        if not PLAYWRIGHT_AVAILABLE:
            print("[AutoReplier] Playwright 不可用")
            return False

        try:
            async with async_playwright() as p:
                # 啟動瀏覽器
                browser = await p.chromium.launch(headless=False)
                context = await browser.new_context(
                    viewport=self.browser_viewport
                )
                page = await context.new_page()

                # 訪問 Threads
                print(f"[AutoReplier] 訪問: {url}")
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")

                # 等待頁面加載
                await page.wait_for_load_state("networkidle", timeout=15000)
                await asyncio.sleep(3)

                # 滾動到頁面中央（讓帖子可見）
                await page.evaluate("window.scrollTo(0, window.innerHeight / 2)")
                await asyncio.sleep(1)

                # 執行回覆
                success = await self._click_reply_and_type(page, reply_text)

                # 等待確認
                await asyncio.sleep(2)

                await browser.close()
                return success

        except Exception as e:
            print(f"[AutoReplier] 執行失敗: {e}")
            return False

    def poll_callbacks(self) -> None:
        """輪詢 Telegram 回調"""
        import requests
        print("[AutoReplier] 開始監聽回覆按鈕...")
        print("等待 Telegram 回調...")

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
                            username = callback.get('from', {}).get('username', 'unknown')

                            print(f"[AutoReplier] 收到回覆請求: {data} (from @{username})")

                            if data.startswith('reply_'):
                                # 發送處理中信號
                                try:
                                    requests.post(
                                        f"{self.api_url}/answerCallbackQuery",
                                        json={
                                            'callback_query_id': callback['id'],
                                            'text': "正在處理，請稍候..."
                                        }
                                    )
                                except:
                                    pass

                                # 執行自動回覆
                                success = self.auto_reply(data)
                                if success:
                                    print("[AutoReplier] 回覆成功！")
                                else:
                                    print("[AutoReplier] 回覆失敗")

            except requests.exceptions.Timeout:
                continue
            except Exception as e:
                print(f"[AutoReplier] 輪詢錯誤: {e}")
                time.sleep(2)

    def start(self) -> None:
        self.running = True
        print("=" * 60)
        print("Threads 智能回覆器已啟動 (v4 - JavaScript 定位)")
        print("=" * 60)
        print("工作原理：")
        print("1. 打開 Threads 帖子")
        print("2. 使用 JavaScript 找到回覆按鈕（不受位置影響）")
        print("3. 點擊按鈕並填寫回覆")
        print("4. 按 Enter 發送")
        print("=" * 60)
        print("按 Ctrl+C 停止")
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
    """主函數"""
    from config import TELEGRAM_BOT_TOKEN

    if not PLAYWRIGHT_AVAILABLE:
        print("=" * 60)
        print("錯誤: Playwright 不可用")
        print("請運行以下命令安裝:")
        print("  pip install playwright")
        print("  playwright install chromium")
        print("=" * 60)
        return

    replier = ThreadsAutoReplier(TELEGRAM_BOT_TOKEN)
    replier.start()


if __name__ == "__main__":
    main()