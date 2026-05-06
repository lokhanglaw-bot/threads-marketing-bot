"""
Threads 監控模組
使用 Playwright 自動化瀏覽 Threads，搜索相關帖子
支援 Cookie 登入，绕过 OTP 驗證
"""

import asyncio
import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass

from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# Cookies 檔案路徑
COOKIES_FILE = "threads_cookies.json"


@dataclass
class Post:
    """帖子資料類"""
    post_id: str
    content: str
    author: str
    url: str
    likes: int
    timestamp: datetime
    post_time: str = ""  # 帖子的實際發布時間（如 "2小時前"）


class ThreadsMonitor:
    """Threads 監控器"""

    def __init__(self, keywords: List[str], headless: bool = True):
        """
        初始化 Threads 監控器

        Args:
            keywords: 監控的關鍵詞列表
            headless: 是否以無頭模式運行（True = 看不見瀏覽器）
        """
        self.keywords = keywords
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.processed_posts = set()  # 追蹤已處理的帖子

    async def initialize(self):
        """初始化瀏覽器"""
        print("[Threads Monitor] 初始化瀏覽器...")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-infobars',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-gpu'
            ]
        )

        # 創建上下文（類似於新的瀏覽器配置）
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            locale='zh-HK',
            timezone_id='Asia/Hong_Kong'
        )

        # 設置指紋隨機化（減少被偵測）
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        self.page = await self.context.new_page()
        print("[Threads Monitor] 瀏覽器初始化完成")

    async def close(self):
        """關閉瀏覽器"""
        if self.browser:
            await self.browser.close()
            print("[Threads Monitor] 瀏覽器已關閉")

    async def _human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """模擬人類延遲（防偵測）"""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def _random_scroll(self, times: int = 3):
        """隨機滾動頁面（模擬人類瀏覽）"""
        for _ in range(times):
            scroll_amount = random.randint(300, 800)
            await self.page.evaluate(f"window.scrollBy(0, {scroll_amount})")
            await self._human_delay(0.5, 1.5)

    async def save_cookies(self):
        """保存當前瀏覽器會話的 Cookies 到檔案"""
        try:
            cookies = await self.context.cookies()
            # 清理不支援的屬性
            cleaned_cookies = []
            for cookie in cookies:
                cleaned = {k: v for k, v in cookie.items()
                          if k not in ['sameSite', 'secure', 'httpOnly'] or k == 'value'}
                # 確保必要的欄位
                if 'name' in cleaned and 'value' in cleaned:
                    cleaned_cookies.append(cleaned)

            with open(COOKIES_FILE, 'w', encoding='utf-8') as f:
                json.dump(cleaned_cookies, f, ensure_ascii=False, indent=2)

            print(f"[Threads Monitor] Cookies 已保存到 {COOKIES_FILE}")
            return True
        except Exception as e:
            print(f"[Threads Monitor] 保存 Cookies 失敗: {e}")
            return False

    async def load_cookies(self) -> bool:
        """從檔案載入 Cookies"""
        if not os.path.exists(COOKIES_FILE):
            print(f"[Threads Monitor] 找不到 Cookies 檔案: {COOKIES_FILE}")
            return False

        try:
            with open(COOKIES_FILE, 'r', encoding='utf-8') as f:
                cookies = json.load(f)

            if not cookies:
                print("[Threads Monitor] Cookies 檔案為空")
                return False

            # 清理並添加 Cookies
            cleaned_cookies = []
            for cookie in cookies:
                cleaned = {k: v for k, v in cookie.items()
                          if k not in ['sameSite', 'secure', 'httpOnly'] or k == 'value'}
                if 'name' in cleaned and 'value' in cleaned:
                    cleaned_cookies.append(cleaned)

            await self.context.add_cookies(cleaned_cookies)
            print(f"[Threads Monitor] 已載入 {len(cleaned_cookies)} 個 Cookies")
            return True
        except Exception as e:
            print(f"[Threads Monitor] 載入 Cookies 失敗: {e}")
            return False

    def has_cookies(self) -> bool:
        """檢查是否存在有效的 Cookies 檔案"""
        return os.path.exists(COOKIES_FILE)

    async def login_with_cookies(self) -> bool:
        """
        使用 Cookies 登入
        如果 Cookies 無效或不存在，返回 False

        Returns:
            bool: 是否成功使用 Cookies 登入
        """
        if not self.has_cookies():
            print("[Threads Monitor] 沒有找到 Cookies，需要手動登入一次")
            return False

        # 先嘗試載入 Cookies
        if not await self.load_cookies():
            return False

        # 訪問 Threads 測試是否仍然登入
        try:
            await self.page.goto("https://www.threads.net/", timeout=15000)
            await self._human_delay(2, 3)

            # 檢查是否仍然登入（檢查頁面是否有登入狀態的元素）
            page_content = await self.page.content()

            # 如果頁面包含 "登入" 或 "登入" 按鈕，說明 Cookies 已過期
            if '登入' in page_content or 'login' in page_content.lower():
                print("[Threads Monitor] Cookies 已過期，需要重新登入")
                return False

            print("[Threads Monitor] 使用 Cookies 登入成功")
            return True

        except Exception as e:
            print(f"[Threads Monitor] 測試 Cookies 失敗: {e}")
            return False

    async def _get_page_html_for_debug(self, label: str = ""):
        """除錯用：獲取頁面 HTML 的關鍵部分"""
        try:
            html = await self.page.content()
            # 只取 body 的前 2000 字符
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.DOTALL | re.IGNORECASE)
            if body_match:
                body_content = body_match.group(1)[:3000]
                print(f"[Debug] {label} - 頁面內容預覽:")
                print(body_content[:1500])
                return True
        except Exception as e:
            print(f"[Debug] 獲取頁面失敗: {e}")
        return False

    async def _find_all_posts_on_page(self) -> List[Dict]:
        """
        在當前頁面查找所有帖子元素

        Returns:
            List[Dict]: 帖子元素列表，每個包含元素和URL
        """
        posts = []

        # Threads 的選擇器可能會變化，嘗試多個版本
        selector_strategies = [
            # 新版 Threads 選擇器
            ('article', 'div[dir="auto"]'),
            ('div[data-pressable-container="true"]', 'span[dir="auto"]'),
            # 備用選擇器
            ('[role="article"]', '[dir="auto"]'),
            ('article[role="article"]', 'div[dir="auto"]'),
            # 通用選擇器
            ('div.x1iyjqo2', 'div[dir="auto"]'),
            ('main div', 'span'),
        ]

        for container_sel, text_sel in selector_strategies:
            try:
                # 等待頁面加載
                await self.page.wait_for_load_state("domcontentloaded", timeout=5000)
                await self._human_delay(0.5, 1)

                # 查找所有容器
                containers = await self.page.query_selector_all(container_sel)

                if len(containers) > 5:  # 只處理找到多個元素的情況
                    print(f"[Threads Monitor] 選擇器 {container_sel} 找到 {len(containers)} 個元素")

                    for i, container in enumerate(containers):
                        try:
                            # 嘗試提取文本
                            text_elements = await container.query_selector_all(text_sel)
                            for text_el in text_elements:
                                text = await text_el.inner_text()
                                if text and len(text) > 20:  # 過濾太短的內容
                                    # 嘗試獲取 URL
                                    links = await container.query_selector_all('a[href*="/post/"]')
                                    url = ""
                                    for link in links:
                                        href = await link.get_attribute('href')
                                        if href and '/post/' in href:
                                            # 清理 URL：移除 /media 後綴
                                            if href.startswith('http'):
                                                url = href.split('/media')[0] if '/media' in href else href
                                            else:
                                                clean_href = href.split('/media')[0] if '/media' in href else href
                                                url = f"https://www.threads.net{clean_href}"
                                            break

                                    # 如果沒找到 /post/ 連結，嘗試其他連結
                                    if not url:
                                        all_links = await container.query_selector_all('a[href*="/@"]')
                                        for link in all_links:
                                            href = await link.get_attribute('href')
                                            if href and '/post/' in href:
                                                # 清理 URL：移除 /media 後綴
                                                if href.startswith('http'):
                                                    url = href.split('/media')[0] if '/media' in href else href
                                                else:
                                                    clean_href = href.split('/media')[0] if '/media' in href else href
                                                    url = f"https://www.threads.net{clean_href}"
                                                break

                                    if text and url:
                                        posts.append({
                                            'content': text.strip(),
                                            'url': url,
                                            'container': container
                                        })
                                        break
                        except Exception:
                            continue

                    if len(posts) > 0:
                        break

            except Exception:
                continue

        return posts

    async def _extract_post_content(self, element) -> str:
        """從元素中提取帖子內容"""
        try:
            # 嘗試不同的文本選擇器
            text_selectors = [
                'div[dir="auto"]',
                'span.x1lliihq',
                'div.x1iorvi4',
                'p',
                'span'
            ]

            for selector in text_selectors:
                text = await element.query_selector(selector)
                if text:
                    content = await text.inner_text()
                    if content and len(content) > 10:
                        return content.strip()

            return ""

        except Exception:
            return ""

    async def _extract_post_url(self, element) -> str:
        """提取帖子 URL"""
        try:
            # 查找包含 /post/ 的連結
            links = await element.query_selector_all('a[href*="/post/"]')
            for link in links:
                href = await link.get_attribute('href')
                if href:
                    if href.startswith('http'):
                        return href
                    return f"https://www.threads.net{href}"

            # 嘗試其他格式的連結
            article_links = await element.query_selector_all('a')
            for link in article_links:
                href = await link.get_attribute('href')
                if href and '/@' in href and '/post/' in href:
                    if href.startswith('http'):
                        return href
                    return f"https://www.threads.net{href}"

            return ""

        except Exception:
            return ""

    async def _extract_author(self, element) -> str:
        """提取作者名稱"""
        try:
            author_selectors = [
                'strong',
                'span[dir="auto"]',
                'a[role="link"]',
                'div[dir="auto"]:first-child'
            ]

            for selector in author_selectors:
                author = await element.query_selector(selector)
                if author:
                    name = await author.inner_text()
                    if name and '@' not in name and len(name) < 30 and len(name) > 0:
                        return name.strip()

            return "未知用戶"

        except Exception:
            return "未知用戶"

    async def _extract_post_time(self, element) -> str:
        """提取帖子的發布時間（如 '2小時前', '昨天'）"""
        try:
            # 常見的時間選擇器
            time_selectors = [
                'span[dir="ltr"]',
                'span[dir="auto"]',
                'time',
                'abbr[title]',
                'span.x4pmi6',
                'span.x1lliihq'
            ]

            for selector in time_selectors:
                time_el = await element.query_selector(selector)
                if time_el:
                    time_text = await time_el.inner_text()
                    # 檢查是否像時間格式
                    if any(keyword in time_text.lower() for keyword in ['秒', '分', '小時', '小時前', '小時', '天', '週', '月', '年', '前', 'ago', 'ago']):
                        return time_text.strip()

                    # 嘗試獲取 datetime 屬性
                    datetime_attr = await time_el.get_attribute('datetime')
                    if datetime_attr:
                        return datetime_attr[:16] if len(datetime_attr) > 16 else datetime_attr

            return "未知時間"

        except Exception:
            return "未知時間"

    def _is_recent_post(self, time_text: str) -> bool:
        """
        檢查帖子是否是新發布的（24小時內）

        Args:
            time_text: 時間文字（如 "2小時前"、"昨天"）

        Returns:
            bool: 是否是近期帖子
        """
        time_text_lower = time_text.lower()

        # 跳過已處理的標記
        if '已處理' in time_text or 'processed' in time_text_lower:
            return False

        # 檢查常見的時間模式
        recent_patterns = [
            '秒', '分鐘', '分鐘前', '小時', '小時前',
            '今天', '今日', 'day', 'hour', 'minute',
            '小時前', '分鐘前'
        ]

        for pattern in recent_patterns:
            if pattern in time_text_lower:
                return True

        # 檢查 "昨天"
        if '昨天' in time_text or 'yesterday' in time_text_lower:
            return True

        # 檢查數字 + 小時/天/週
        time_numbers = re.findall(r'(\d+)', time_text)
        if time_numbers:
            num = int(time_numbers[0])
            if any(x in time_text_lower for x in ['小時', '小時前', 'hour', 'h']):
                return num <= 24  # 24小時內
            if any(x in time_text_lower for x in ['天', 'day', 'd']):
                return num <= 1  # 1天內
            if any(x in time_text_lower for x in ['週', 'week', 'w']):
                return False  # 超過一週
            if any(x in time_text_lower for x in ['月', 'month', 'm']):
                return False  # 超過一個月
            if any(x in time_text_lower for x in ['年', 'year', 'y']):
                return False  # 超過一年

        return False  # 無法判斷時間，保守起見跳過

    def _check_keywords(self, content: str) -> List[str]:
        """
        檢查內容是否包含關鍵詞

        Args:
            content: 帖子內容

        Returns:
            List[str]: 匹配的關鍵詞列表
        """
        content_lower = content.lower()
        matched = []

        for keyword in self.keywords:
            if keyword.lower() in content_lower:
                matched.append(keyword)

        return matched

    async def search_by_keyword(self, keyword: str) -> List[Post]:
        """
        搜索包含特定關鍵詞的帖子

        Args:
            keyword: 搜索關鍵詞

        Returns:
            List[Post]: 匹配的帖子列表
        """
        posts = []
        seen_urls_this_search = set()  # 單次搜索內去重

        try:
            # ── 策略 1: 搜索「最新」排序 ──
            print(f"[Threads Monitor] 搜索關鍵詞: {keyword} (最新)")

            # 構建搜索 URL - 使用 search 頁面，強制排序為最新
            search_url = f"https://www.threads.net/search?q={keyword}&mode=latest"

            await self.page.goto(search_url, timeout=30000)
            await self._human_delay(3, 5)

            # 等待頁面加載完成
            try:
                await self.page.wait_for_load_state("networkidle", timeout=15000)
            except:
                print("[Threads Monitor] 等待 networkidle 超時，繼續...")

            await self._human_delay(1, 2)

            # 滾動頁面多次，加載所有內容（只滾動少量，避免載入太多舊帖子）
            print("[Threads Monitor] 滾動頁面（淺層滾動，只看最新）...")
            for i in range(3):  # 減少滾動次數
                await self.page.evaluate("window.scrollBy(0, 400)")
                await self._human_delay(0.8, 1.2)

            # 提取所有帖子
            print("[Threads Monitor] 提取內容...")
            raw_posts = await self._find_all_posts_on_page()
            print(f"[Threads Monitor] 找到 {len(raw_posts)} 個帖子元素")

            # 過濾並創建 Post 對象
            for i, raw_post in enumerate(raw_posts):
                content = raw_post['content']
                url = raw_post['url']
                container = raw_post.get('container')

                # 跳過太短的內容
                if len(content) < 15:
                    continue

                # 跳過沒有 URL 的內容
                if not url or '/post/' not in url:
                    continue

                # 清理 URL（移除 /media 後綴）
                clean_url = url.replace('/media', '')

                # 單次搜索內去重
                if clean_url in seen_urls_this_search:
                    continue
                seen_urls_this_search.add(clean_url)

                # 全局去重
                if clean_url in self.processed_posts:
                    continue

                # ── 提取並檢查發布時間 ──
                post_time = "未知時間"
                if container:
                    try:
                        post_time = await self._extract_post_time(container)
                    except:
                        pass

                # 只處理 24 小時內的帖子
                if post_time != "未知時間" and not self._is_recent_post(post_time):
                    print(f"[Threads Monitor] ⏭️ 太舊 ({post_time}): {content[:40]}...")
                    continue

                # 檢查關鍵詞
                matched_keywords = self._check_keywords(content)

                if matched_keywords:
                    post = Post(
                        post_id=clean_url,
                        content=content,
                        author="未知用戶",
                        url=clean_url,
                        likes=0,
                        timestamp=datetime.now(),
                        post_time=post_time
                    )

                    posts.append(post)
                    self.processed_posts.add(clean_url)
                    print(f"[Threads Monitor] ✅ 匹配 ({post_time}): {content[:60]}...")

            # ── 策略 2: 如果找到的帖子太少，嘗試搜索 Trending ──
            if len(posts) < 2:
                print(f"[Threads Monitor] 找到的帖子太少 ({len(posts)})，嘗試 Trending...")
                trending_url = f"https://www.threads.net/search?q={keyword}&mode=trending"
                await self.page.goto(trending_url, timeout=30000)
                await self._human_delay(2, 4)

                await self.page.evaluate("window.scrollBy(0, 300)")
                await self._human_delay(0.5, 1)

                raw_posts_2 = await self._find_all_posts_on_page()
                for raw_post in raw_posts_2:
                    content = raw_post['content']
                    url = raw_post['url']
                    clean_url = url.replace('/media', '')

                    if len(content) < 15 or not url or '/post/' not in url:
                        continue
                    if clean_url in seen_urls_this_search or clean_url in self.processed_posts:
                        continue

                    matched_keywords = self._check_keywords(content)
                    if matched_keywords:
                        post = Post(
                            post_id=clean_url,
                            content=content,
                            author="未知用戶",
                            url=clean_url,
                            likes=0,
                            timestamp=datetime.now(),
                            post_time="熱門"
                        )
                        posts.append(post)
                        self.processed_posts.add(clean_url)
                        print(f"[Threads Monitor] ✅ 熱門匹配: {content[:60]}...")

        except Exception as e:
            print(f"[Threads Monitor] 搜索時出錯: {e}")

        print(f"[Threads Monitor] 關鍵詞 '{keyword}' 找到 {len(posts)} 個相關帖子")
        return posts

    async def run_scan(self) -> List[Post]:
        """
        執行一次完整掃描

        Returns:
            List[Post]: 發現的匹配帖子
        """
        all_posts = []

        try:
            # 1. 首先嘗試使用 Cookies 登入
            print("[Threads Monitor] 嘗試使用 Cookies 登入...")
            if not await self.login_with_cookies():
                print("[Threads Monitor] Cookies 登入失敗，需要手動登入")
                print("[Threads Monitor] 請運行 python cookie_helper.py 來匯出 Cookies")

            # 2. 然後搜索每個關鍵詞
            for keyword in self.keywords[:8]:  # 限制關鍵詞數量
                try:
                    keyword_posts = await self.search_by_keyword(keyword)
                    all_posts.extend(keyword_posts)
                    await asyncio.sleep(3)  # 避免請求太快
                except Exception as e:
                    print(f"[Threads Monitor] 關鍵詞 '{keyword}' 搜索失敗: {e}")
                    continue

            # 去重（使用清理後的 URL）
            unique_posts = []
            seen_urls = set()
            for post in all_posts:
                # 清理 URL
                clean_url = post.url.replace('/media', '')
                if clean_url not in seen_urls and '/post/' in clean_url:
                    post.url = clean_url  # 更新為清理後的 URL
                    unique_posts.append(post)
                    seen_urls.add(clean_url)

            print(f"[Threads Monitor] 掃描完成，共發現 {len(unique_posts)} 個匹配帖子")

            # 3. 保存 Cookies 以備下次使用
            await self.save_cookies()

        except Exception as e:
            print(f"[Threads Monitor] 掃描時出錯: {e}")

        return unique_posts

    async def test_connection(self) -> bool:
        """
        測試 Threads 連接

        Returns:
            bool: 是否連接成功
        """
        try:
            print("[Threads Monitor] 測試 Threads 連接...")
            await self.page.goto("https://www.threads.net/", timeout=15000)
            await self._human_delay(2, 3)

            title = await self.page.title()
            print(f"[Threads Monitor] 頁面標題: {title}")

            return True

        except Exception as e:
            print(f"[Threads Monitor] 連接測試失敗: {e}")
            return False


# 同步包裝器（方便非 async 代碼調用）
class ThreadsMonitorSync:
    """同步版本的 Threads 監控器"""

    def __init__(self, keywords: List[str], headless: bool = True):
        self.keywords = keywords
        self.headless = headless
        self.monitor = ThreadsMonitor(keywords, headless)

    def run_scan(self) -> List[Dict]:
        """同步執行掃描"""
        return asyncio.run(self.monitor.run_scan())

    def test_connection(self) -> bool:
        """同步測試連接"""
        return asyncio.run(self.monitor.test_connection())