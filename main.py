"""
My Fit Monster - Threads Marketing Bot
主程序入口
"""

import asyncio
import sys
import time
from datetime import datetime

# 導入自定義模組
from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    KEYWORDS,
    SCAN_INTERVAL,
    APP_LINK,
    APP_NAME,
    YOUR_PROFILE,
    YOUR_APP_EXPERIENCE
)
from threads_monitor import ThreadsMonitor
from telegram_sender_enhanced import TelegramSenderEnhanced
from reply_generator import ReplyGenerator


class MarketingBot:
    """My Fit Monster 營銷 Bot"""

    def __init__(self):
        """初始化 Bot"""
        print("=" * 50)
        print(f"My Fit Monster Marketing Bot")
        print(f"App: {APP_NAME}")
        print(f"Link: {APP_LINK}")
        print("=" * 50)

        # 初始化各模組（使用增強版 Telegram 發送器，支援一鍵回覆）
        self.telegram = TelegramSenderEnhanced(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID)
        self.reply_gen = ReplyGenerator(APP_LINK, YOUR_APP_EXPERIENCE, YOUR_PROFILE)
        self.threads = ThreadsMonitor(KEYWORDS, headless=True)

        # 統計數據
        self.stats = {
            'scans': 0,
            'found': 0,
            'sent': 0,
            'start_time': datetime.now()
        }

    async def initialize(self):
        """初始化瀏覽器"""
        await self.threads.initialize()

    async def close(self):
        """關閉資源"""
        await self.threads.close()

    def get_uptime(self) -> str:
        """獲取運行時間"""
        delta = datetime.now() - self.stats['start_time']
        hours = int(delta.total_seconds() // 3600)
        minutes = int((delta.total_seconds() % 3600) // 60)
        return f"{hours}h {minutes}m"

    async def process_posts(self):
        """處理發現的帖子"""
        print("\n" + "=" * 50)
        print("開始掃描 Threads...")
        print("=" * 50)

        try:
            # 執行掃描
            posts = await self.threads.run_scan()
            self.stats['scans'] += 1
            self.stats['found'] += len(posts)

            print(f"\n掃描 #{self.stats['scans']}")
            print(f"運行時間: {self.get_uptime()}")
            print(f"發現匹配帖子: {len(posts)}")

            # 處理每個帖子
            for i, post in enumerate(posts):
                post_number = i + 1
                print(f"\n處理帖子 {post_number}/{len(posts)}")

                # 檢查是否應該回覆
                should_reply, reason = self.reply_gen.should_reply(post.content)

                if should_reply:
                    # 生成回覆
                    matched_keywords = []
                    for keyword in KEYWORDS:
                        if keyword.lower() in post.content.lower():
                            matched_keywords.append(keyword)

                    reply = self.reply_gen.generate_reply(post.content, matched_keywords)

                    # 準備帖子資料
                    post_data = {
                        'content': post.content,
                        'author': post.author,
                        'url': post.url,
                        'keywords': matched_keywords,
                        'timestamp': post.timestamp.isoformat()
                    }

                    # 發送到 Telegram（使用增強版，帶有一鍵回覆按鈕）
                    success = self.telegram.send_post_with_buttons(post_data, reply, post_number)

                    if success:
                        self.stats['sent'] += 1
                        print(f"已發送到 Telegram (帖子 #{post_number})")
                        print(f"連結: {post.url}")
                        print(f"回覆: {reply[:50]}...")
                    else:
                        print(f"發送到 Telegram 失敗")

                else:
                    print(f"跳過: {reason}")

            # 顯示統計
            print("\n" + "=" * 50)
            print("當前統計:")
            print(f"   掃描次數: {self.stats['scans']}")
            print(f"   發現帖子: {self.stats['found']}")
            print(f"   發送通知: {self.stats['sent']}")
            print("=" * 50)

        except Exception as e:
            print(f"處理時出錯: {e}")
            self.telegram.send_status_message("error", f"錯誤: {str(e)}")

    async def run_once(self):
        """執行一次掃描"""
        print("\n執行單次掃描...")

        await self.initialize()

        try:
            # 先測試連接
            if await self.threads.test_connection():
                print("Threads 連接測試成功")
                await self.process_posts()
            else:
                print("Threads 連接測試失敗")

        except Exception as e:
            print(f"運行時出錯: {e}")

        finally:
            await self.close()

    async def run_loop(self, interval: int = None):
        """
        循環運行 Bot

        Args:
            interval: 掃描間隔（秒），None 則使用配置文件中的值
        """
        if interval is None:
            interval = SCAN_INTERVAL

        print(f"\n開始循環模式（每隔 {interval} 秒掃描一次）")
        print("按 Ctrl+C 停止\n")

        # 發送啟動通知
        self.telegram.send_status_message(
            "started",
            f"My Fit Monster Marketing Bot 已啟動！\n"
            f"App: {APP_NAME}\n"
            f"掃描間隔: {interval} 秒\n"
            f"關鍵詞數量: {len(KEYWORDS)}"
        )

        await self.initialize()

        try:
            while True:
                await self.process_posts()

                print(f"\n等待 {interval} 秒後進行下一次掃描...")
                await asyncio.sleep(interval)

        except KeyboardInterrupt:
            print("\n\n收到停止信號，正在關閉...")
            self.telegram.send_status_message(
                "stopped",
                f"Bot 已停止\n"
                f"統計: {self.stats['scans']} 次掃描，"
                f"{self.stats['sent']} 個通知發送"
            )

        finally:
            await self.close()
            print("Bot 已關閉")


async def main():
    """主函數"""
    bot = MarketingBot()

    # 檢查命令行參數
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()

        if command == 'once':
            # 執行一次
            await bot.run_once()

        elif command == 'test':
            # 測試模式（只測試連接）
            print("測試模式...")
            await bot.initialize()
            success = await bot.threads.test_connection()
            await bot.close()

            if success:
                print("\nThreads 連接測試成功！")
                print("Telegram 發送測試...")
                bot.telegram.send_status_message("info", "測試成功！Bot 準備就緒")
            else:
                print("\nThreads 連接測試失敗")
                sys.exit(1)

        elif command == 'loop':
            # 循環模式
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else None
            await bot.run_loop(interval)

        else:
            print_help()

    else:
        # 默認：執行一次
        print("提示：使用以下命令")
        print("   python main.py once   - 執行一次掃描")
        print("   python main.py test   - 測試連接")
        print("   python main.py loop   - 循環運行")
        print("   python main.py loop 300  - 循環運行（每5分鐘）")
        print()
        await bot.run_once()


def print_help():
    """打印幫助信息"""
    print("""
My Fit Monster Marketing Bot - 幫助
================================================================================
用法:
    python main.py [command] [options]

命令:
    once           執行一次掃描（默認）
    test           測試 Threads 和 Telegram 連接
    loop [秒數]    循環運行（可指定間隔，默認300秒）

示例:
    python main.py once           # 執行一次
    python main.py test            # 測試連接
    python main.py loop            # 每5分鐘循環
    python main.py loop 600       # 每10分鐘循環

功能說明:
    - 自動搜索 Threads 相關帖子
    - 使用 DeepSeek AI 生成自然回覆
    - 發送到 Telegram 通知
    - 支援「一鍵回覆」按鈕（需要同時運行 auto_replier.py）
    """)


if __name__ == "__main__":
    asyncio.run(main())