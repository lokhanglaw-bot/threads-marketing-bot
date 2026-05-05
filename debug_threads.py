"""
Threads 除錯工具
用於查看 Threads 頁面的實際結構
"""

import asyncio
import os
from playwright.async_api import async_playwright


COOKIES_FILE = "threads_cookies.json"


async def main():
    print("=" * 60)
    print(" Threads 除錯工具")
    print("=" * 60)
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
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
            print("[1/4] 正在載入 Cookies...")
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
        await asyncio.sleep(5)

        print("\n[3/4] 分析頁面結構...")

        title = await page.title()
        print(f"    頁面標題: {title}")

        page_content = await page.content()
        if '登入' in page_content or 'login' in page_content.lower():
            print("    ⚠️  需要登入！")
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
            ('div.x6s0dn4', 'Threads類名'),
        ]

        print("\n    元素分析:")
        for selector, desc in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"    - {selector}: {len(elements)} 個")
            except:
                print(f"    - {selector}: 錯誤")

        # 滾動頁面
        print("\n    滾動頁面...")
        for i in range(5):
            await page.evaluate("window.scrollBy(0, 600)")
            await asyncio.sleep(1)

        # 再次統計元素
        print("\n    滾動後元素統計:")
        for selector, desc in selectors_to_try:
            try:
                elements = await page.query_selector_all(selector)
                print(f"    - {selector}: {len(elements)} 個")
            except:
                pass

        # 截圖
        print("\n[4/4] 截圖...")
        await page.screenshot(path="debug_screenshot.png")
        print("    ✅ 截圖已保存: debug_screenshot.png")

        print("\n" + "=" * 60)
        print("完成！請查看 debug_screenshot.png")
        print("=" * 60)

        input("\n按 Enter 鍵關閉瀏覽器...")


if __name__ == "__main__":
    asyncio.run(main())