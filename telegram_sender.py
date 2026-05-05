"""
Telegram 通知模組
負責發送消息到你的 Telegram
每個帖子獨立發送一條消息
使用 HTML 格式避免連結斜體問題
"""

import requests
import json
import time
import html
from datetime import datetime


class TelegramSender:
    """Telegram 通知類"""

    def __init__(self, bot_token: str, chat_id: str):
        """
        初始化 Telegram 發送器

        Args:
            bot_token: Telegram Bot Token
            chat_id: 你的 Chat ID
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """
        發送消息到 Telegram

        Args:
            text: 消息內容
            parse_mode: 格式化模式 (Markdown / HTML)

        Returns:
            bool: 是否發送成功
        """
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()

            if result.get("ok"):
                print(f"[Telegram] 消息發送成功")
                return True
            else:
                print(f"[Telegram] 發送失敗: {result}")
                return False

        except Exception as e:
            print(f"[Telegram] 發送錯誤: {e}")
            return False

    def _extract_post_id_from_url(self, url: str) -> str:
        """從 URL 提取帖子 ID"""
        try:
            # 例如: https://www.threads.net/@username/post/ABC123xyz
            if '/post/' in url:
                parts = url.split('/post/')
                if len(parts) > 1:
                    post_id = parts[1].split('/')[0].split('?')[0]
                    return post_id
            return ""
        except:
            return ""

    def _clean_url(self, url: str) -> str:
        """清理 URL，去除斜體格式問題"""
        # 確保使用 HTTPS
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        # 移除 /media 後綴（導致連結變成斜體不可點擊）
        if url.endswith('/media'):
            url = url[:-6]
        # 移除其他可能導致問題的後綴
        if '?' in url:
            url = url.split('?')[0]
        return url

    def _escape_html(self, text: str) -> str:
        """轉義 HTML 特殊字符"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

    def _make_link(self, url: str, text: str = None) -> str:
        """生成 HTML 連結格式"""
        if text is None:
            text = url
        # 確保 URL 是 https
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        # HTML 轉義
        safe_url = self._escape_html(url)
        safe_text = self._escape_html(text)
        return f'<a href="{safe_url}">{safe_text}</a>'

    def send_post_notification(self, post_data: dict, suggested_reply: str, post_number: int = 1) -> bool:
        """
        發送帖子通知到你 Telegram（每個帖子獨立一條消息）

        Args:
            post_data: 帖子資料
            suggested_reply: AI 生成的回覆建議
            post_number: 帖子編號（在本次掃描中的順序）

        Returns:
            bool: 是否發送成功
        """
        # 清理 URL
        raw_url = post_data.get('url', '')
        clean_url = self._clean_url(raw_url)
        author = self._escape_html(post_data.get('author', '未知用戶'))
        content = self._escape_html(post_data.get('content', '無法讀取內容'))
        suggested_reply_escaped = self._escape_html(suggested_reply)

        # 使用 HTML 格式，連結用 <a href> 標籤
        message = f"""━━━━━━━━━━━━━━━
🔍 帖子 #{post_number}

👤 作者：{author}

📝 內容：
{content[:800]}{'...' if len(content) > 800 else ''}

🔗 連結：{self._make_link(clean_url)}

💬 回覆建議：
{suggested_reply_escaped}
━━━━━━━━━━━━━━━"""

        return self.send_message(message)

    def send_status_message(self, status: str, details: str = "") -> bool:
        """
        發送狀態消息

        Args:
            status: 狀態類型 (started, stopped, error, etc.)
            details: 詳細信息
        """
        status_icons = {
            "started": "🚀",
            "stopped": "⏹️",
            "error": "❌",
            "info": "ℹ️",
            "found": "✅"
        }

        icon = status_icons.get(status, "📌")
        message = f"{icon} *系統狀態*\n\n{details}"

        return self.send_message(message)

    def send_daily_summary(self, stats: dict) -> bool:
        """
        發送每日摘要

        Args:
            stats: 統計數據字典
        """
        message = f"""
📊 *每日摘要報告*

🔍 掃描次數: {stats.get('scans', 0)}
📝 發現相關帖子: {stats.get('found', 0)}
✉️ 發送通知: {stats.get('sent', 0)}
⏱️ 運行時間: {stats.get('uptime', 'N/A')}

🤖 Bot 狀態: 正常運行中
"""

        return self.send_message(message)
