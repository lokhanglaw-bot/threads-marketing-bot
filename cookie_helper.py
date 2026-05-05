"""
Threads Cookie 匯出工具
用於手動登入 Threads 並匯出 Cookies，绕过 OTP 驗證
"""

import asyncio
import json
from playwright.async_api import async_playwright


COOKIES_FILE = "threads_cookies.json"


async def main():
    print("=" * 60)
    print(" Threads Cookie 匯出工具")
    print("=" * 60)
    print()
    print("步驟:")
    print("1. 瀏覽器會打開 Threads 登入頁面")
    print("2. 手動輸入你的帳號密碼（可以輸入 OTP）")
    print("3. 登入成功後，在瀏覽器中隨便逛逛（刷新首頁等）")
    print("4. 回到這個終端，按 Enter 鍵匯出 Cookies")
    print()
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
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-HK',
            timezone_id='Asia/Hong_Kong'
        )

        page = await context.new_page()

        print("[1/3] 正在打開 Threads 登入頁面...")
        await page.goto("https://www.threads.net/login", timeout=30000)
        print("[2/3] 瀏覽器已打開！")
        print()
        print("=" * 60)
        print("⚠️  請在瀏覽器中完成登入（可以輸入 OTP）")
        print("⚠️  登入後，建議隨便點擊幾個帖子，確保頁面完全加載")
        print("=" * 60)
        print()

        input("完成登入後，按 Enter 鍵匯出 Cookies...")

        print()
        print("[3/3] 正在匯出 Cookies...")

        try:
            cookies = await context.cookies()

            cleaned_cookies = []
            for cookie in cookies:
                cleaned = {}
                for key in ['name', 'value', 'domain', 'path', 'expires']:
                    if key in cookie:
                        cleaned[key] = cookie[key]
                if 'name' in cleaned and 'value' in cleaned:
                    cleaned_cookies.append(cleaned)

            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cleaned_cookies, f, ensure_ascii=False, indent=2)

            print(f"✅ Cookies 已保存到: {COOKIES_FILE}")
            print(f"   共 {len(cleaned_cookies)} 個 Cookies")

            print()
            print("Cookies 概覽:")
            for i, cookie in enumerate(cleaned_cookies[:10], 1):
                print(f"  {i}. {cookie['name']}")

            if len(cleaned_cookies) > 10:
                print(f"  ... 還有 {len(cleaned_cookies) - 10} 個 Cookies")

        except Exception as e:
            print(f"❌ 匯出失敗: {e}")

        input("按 Enter 鍵關閉瀏覽器...")
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())