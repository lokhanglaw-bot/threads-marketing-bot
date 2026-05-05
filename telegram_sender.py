"""
Telegram 通知模組
支援「一鍵回覆」按鈕功能
"""

import requests
import json
import time
import os
from datetime import datetime


class TelegramSender:
    """Telegram 通知類（支援按鈕）"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.pending_file = "pending_replies.json"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json().get("ok", False)
        except:
            return False

    def _escape_html(self, text: str) -> str:
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

    def _clean_url(self, url: str) -> str:
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        if url.endswith('/media'):
            url = url[:-6]
        if '?' in url:
            url = url.split('?')[0]
        return url

    def _make_link(self, url: str, text: str = None) -> str:
        if text is None:
            text = url
        return f'<a href="{self._escape_html(url)}">{self._escape_html(text)}</a>'

    def _save_pending(self, reply_id: str, url: str, reply: str):
        """保存待回覆資料"""
        pending = {}
        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                pending = json.load(f)
        pending[reply_id] = {'url': url, 'reply': reply}
        with open(self.pending_file, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)

    def _remove_pending(self, reply_id: str):
        """刪除已回覆"""
        if os.path.exists(self.pending_file):
            with open(self.pending_file, 'r', encoding='utf-8') as f:
                pending = json.load(f)
            if reply_id in pending:
                del pending[reply_id]
                with open(self.pending_file, 'w', encoding='utf-8') as f:
                    json.dump(pending, f, ensure_ascii=False, indent=2)

    def send_post_notification(self, post_data: dict, suggested_reply: str, post_number: int = 1) -> bool:
        raw_url = post_data.get('url', '')
        clean_url = self._clean_url(raw_url)
        author = self._escape_html(post_data.get('author', '未知用戶'))
        content = self._escape_html(post_data.get('content', '無法讀取內容'))
        suggested_reply_escaped = self._escape_html(suggested_reply)

        # 生成回覆 ID
        reply_id = f"reply_{post_number}_{int(time.time())}"

        # 保存待回覆
        self._save_pending(reply_id, clean_url, suggested_reply)

        # Inline 按鈕
        inline_keyboard = {
            "inline_keyboard": [[
                {"text": "✅ 一鍵回覆", "callback_data": reply_id},
                {"text": "🔗 在瀏覽器開啟", "url": clean_url}
            ]]
        }

        message = f"""━━━━━━━━━━━━━━━
🔍 帖子 #{post_number}

👤 作者：{author}

📝 內容：
{content[:600]}{'...' if len(content) > 600 else ''}

🔗 連結：{self._make_link(clean_url)}

💬 回覆建議：
{suggested_reply_escaped}
━━━━━━━━━━━━━━━

👆 點擊上方「一鍵回覆」按鈕"""

        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(inline_keyboard)
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.json().get("ok", False)
        except:
            return False

    def send_status_message(self, status: str, details: str = "") -> bool:
        icons = {"started": "🚀", "stopped": "⏹️", "error": "❌", "info": "ℹ️", "found": "✅"}
        return self.send_message(f"{icons.get(status, '📌')} 系統狀態\n\n{details}")