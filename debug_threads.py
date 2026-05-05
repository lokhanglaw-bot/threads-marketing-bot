"""
Threads 除錯工具
用於查看 Threads 頁面的實際結構，幫助找出為什麼找不到帖子
"""

import asyncio
import os
from playwright.async_api import async_playwright


# 嘗試讀取現有的 Cookies
COOKIES_FILE = "threads_cookies.json"


async def main():
    print("=" * 60)
    print(" Threads 除錯工具")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        # 啟動瀏覽器（非無頭模式）
        browser = await p.chromium.launch(
            headless=False,  # 顯示瀏覽器窗口
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-HK',
            timezone_id='Asia/Hong_Kong'
        )

        page = await context.new_page()

        # 嘗試載入 Cookies
        if os.path.exists(COOKIES_FILE):
            print(f"[1/4] 正在載入 Cookies...")
            try:
                import json
                with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)

                cleaned_cookies = []
                for cookie in cookies:
                    cleaned = {k: v for k, v in cookie.items()
                              if k not in ['sameSite', 'secure', 'httpOnly'] or k == 'value'}
                    if 'name' in cleaned and 'value' in cleaned:
                        cleaned_cookies.append(cleaned)

                await context.add_cookies(cleaned_cookies)
                print(f"    已載入 {len(cleaned_cookies)} 個 Cookies")
            except Exception as e:
                print(f"    載入 Cookies 失敗: {e}")

        # 訪問搜索頁面
        print("\n[2/4] 正在訪問 Threads 搜索頁面...")
        await page.goto("https://www.threads.net/search?q=%E5%81%9Cgym", timeout=30000)
        await asyncio.sleep(5)  # 等待頁面加載

        print("\n[3/4] 分析頁面結構...")

        # 獲取頁面標題
        title = await page.title()
        print(f"    頁面標題: {title}")

        # 檢查是否需要登入
        page_content = await page.content()
        if '登入' in page_content or '登入' in page_content:
            print("    ⚠️  檢測到需要登入！")
        else:
            print("    ✅ 已登入")

        # 嘗試找各種元素
        selectors_to_try = [
            ('article', '帖子文章'),
            ('div[dir="auto"]', '自動方向文字'),
            ('[role="article"]', '文章角色'),
            ('span[dir="auto"]', '自動方向span'),
            ('a[href*="/post/"]', '帖子連結'),
            ('main', '主內容'),
            ('div.x1iyjqo2', 'Threads類名'),
            ('div.x6s0dn4', 'Threads類名2'),
        ]

        print("\n    元素分析:")
        for selector, desc in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"    - {selector}: {len(elements)} 個")
            except:
                print(f"    - {selector}: 錯誤")

        # 嘗試點擊搜索框並輸入
        print("\n[4/4] 嘗試與頁面互動...")

        # 查找搜索框
        search_input = await page.query_selector('input[placeholder*="搜"]')
        if not search_input:
            search_input = await page.query_selector('input[type="search"]')
        if not search_input:
            search_input = await page.query_selector('input')

        if search_input:
            print("    ✅ 找到搜尋框，正在輸入關鍵詞...")
            await search_input.fill("健身")
            await asyncio.sleep(2)

            # 按 Enter
            await page.keyboard.press("Enter")
            await asyncio.sleep(3)
            print("    ✅ 已提交搜尋")
        else:
            print("    ❌ 找不到搜尋框")

        # 截圖
        print("\n    正在截圖...")
        await page.screenshot(path="debug_screenshot.png")
        print("    ✅ 截圖已保存: debug_screenshot.png")

        # 嘗試列出頁面上的文字
        print("\n    頁面文字預覽 (前100字):")
        body = await page.query_selector('body')
        if body:
            text = await body.inner_text()
            # 只顯示有內容的部分
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 3]
            preview = ' | '.join(lines[:10])
            print(f"    {preview[:200]}...")

        print("\n" + "=" * 60)
        print("完成！請查看 debug_screenshot.png 來了解頁面實際內容")
        print("=" * 60)

        # 等待用戶確認
        input("\n按 Enter 鍵關閉瀏覽器...")


if __name__ == "__main__":
    asyncio.run(main())