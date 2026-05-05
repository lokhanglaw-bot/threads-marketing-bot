import asyncio
from playwright.async_api import async_playwright

async def debug():
    print("正在初始化瀏覽器...")
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()

    # 所有關鍵詞
    keywords = [
        "操野", "操gym", "做gym", "健身", "健身好悶",
        "一個人做gym", "去gym好悶", "好悶", "好無聊",
        "一個人", "冇人陪", "孤獨", "減肥", "瘦身",
        "減脂", "肥咗", "想瘦", "keep fit",
        "gym貴", "三分鐘熱度", "懶", "home workout"
    ]

    all_results = []

    for keyword in keywords:
        print(f"\n搜索關鍵詞: {keyword}")

        # URL 編碼關鍵詞
        encoded_keyword = keyword.replace(" ", "%20")
        search_url = f"https://www.threads.net/search?q={encoded_keyword}"

        try:
            await page.goto(search_url, timeout=30000)
            await asyncio.sleep(3)

            # 滾動頁面
            for i in range(5):
                await page.evaluate('window.scrollBy(0, 500)')
                await asyncio.sleep(0.5)

            # 提取中文內容
            texts = await page.evaluate('''() => {
                const lines = document.body.innerText.split('\\n');
                return [...new Set(lines)]
                    .filter(line => line.trim().length > 15 && /[\\u4e00-\\u9fff]/.test(line))
                    .slice(0, 5);
            }''')

            if texts:
                print(f"  ✅ 找到 {len(texts)} 段中文內容")
                for text in texts[:2]:
                    print(f"     - {text[:80]}...")
                all_results.append({
                    'keyword': keyword,
                    'count': len(texts),
                    'samples': texts
                })
            else:
                print(f"  ❌ 沒有找到中文內容")

        except Exception as e:
            print(f"  ❌ 錯誤: {e}")

    # 總結
    print("\n" + "=" * 60)
    print("📊 搜索結果總結")
    print("=" * 60)

    found_keywords = [r for r in all_results if r['count'] > 0]
    print(f"\n有結果的關鍵詞: {len(found_keywords)}/{len(keywords)}")

    if found_keywords:
        print("\n有效關鍵詞列表:")
        for r in found_keywords:
            print(f"  ✅ {r['keyword']} ({r['count']} 段內容)")

    await browser.close()
    print("\n完成！")

asyncio.run(debug())
