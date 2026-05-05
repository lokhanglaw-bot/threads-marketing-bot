"""
Telegram 通知模組（增強版）
包含 Inline Keyboard 按鈕，實現「一鍵回覆」功能
"""

import requests
import json
import time
import os
from datetime import datetime


class TelegramSenderEnhanced:
    """Telegram 增強通知類"""

    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.api_url = f"https://api.telegram.org/bot{bot_token}"
        self.pending_replies_file = "pending_replies.json"

    def send_message(self, text: str, parse_mode: str = "HTML") -> bool:
        """發送普通消息"""
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }
        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            return result.get("ok", False)
        except Exception as e:
            print(f"[Telegram] 發送錯誤: {e}")
            return False

    def _escape_html(self, text: str) -> str:
        """轉義 HTML 特殊字符"""
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;'))

    def _clean_url(self, url: str) -> str:
        """清理 URL"""
        if url.startswith('http://'):
            url = url.replace('http://', 'https://')
        if url.endswith('/media'):
            url = url[:-6]
        if '?' in url:
            url = url.split('?')[0]
        return url

    def _make_link(self, url: str, text: str = None) -> str:
        """生成 HTML 連結"""
        if text is None:
            text = url
        safe_url = self._escape_html(url)
        safe_text = self._escape_html(text)
        return f'<a href="{safe_url}">{safe_text}</a>'

    def _save_pending_reply(self, reply_id: str, url: str, reply: str) -> None:
        """保存待回覆的資料"""
        pending = {}
        if os.path.exists(self.pending_replies_file):
            try:
                with open(self.pending_replies_file, 'r', encoding='utf-8') as f:
                    pending = json.load(f)
            except:
                pending = {}

        pending[reply_id] = {
            'url': url,
            'reply': reply,
            'timestamp': datetime.now().isoformat()
        }

        with open(self.pending_replies_file, 'w', encoding='utf-8') as f:
            json.dump(pending, f, ensure_ascii=False, indent=2)

    def _remove_pending_reply(self, reply_id: str) -> None:
        """刪除已回覆的資料"""
        if os.path.exists(self.pending_replies_file):
            try:
                with open(self.pending_replies_file, 'r', encoding='utf-8') as f:
                    pending = json.load(f)

                if reply_id in pending:
                    del pending[reply_id]

                with open(self.pending_replies_file, 'w', encoding='utf-8') as f:
                    json.dump(pending, f, ensure_ascii=False, indent=2)
            except:
                pass

    def send_post_with_buttons(self, post_data: dict, suggested_reply: str, post_number: int = 1) -> bool:
        """
        發送帖子通知 + Inline 按鈕

        Args:
            post_data: 帖子資料
            suggested_reply: AI 生成的回覆建議
            post_number: 帖子編號

        Returns:
            bool: 是否發送成功
        """
        raw_url = post_data.get('url', '')
        clean_url = self._clean_url(raw_url)
        author = self._escape_html(post_data.get('author', '未知用戶'))
        content = self._escape_html(post_data.get('content', '無法讀取內容'))
        suggested_reply_escaped = self._escape_html(suggested_reply)

        # 生成回覆 ID（使用時間戳確保唯一）
        reply_id = f"reply_{post_number}_{int(time.time())}"

        # 保存待回覆資料
        self._save_pending_reply(reply_id, clean_url, suggested_reply)
        print(f"[Telegram] 已保存回覆資料: {reply_id}")

        # 構建 Inline Keyboard
        inline_keyboard = {
            "inline_keyboard": [[
                {"text": "一鍵回覆", "callback_data": reply_id},
                {"text": "在瀏覽器開啟", "url": clean_url}
            ]]
        }

        # 構建訊息
        message = f"""━━━━━━━━━━━━━━━
帖子 #{post_number}

作者：{author}

內容：
{content[:600]}{'...' if len(content) > 600 else ''}

連結：{self._make_link(clean_url)}

回覆建議：
{suggested_reply_escaped}
━━━━━━━━━━━━━━━

點擊上方「一鍵回覆」按鈕
自動打開 Threads 並填寫回覆"""

        # 發送帶按鈕的訊息
        url = f"{self.api_url}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "reply_markup": json.dumps(inline_keyboard)
        }

        try:
            response = requests.post(url, json=payload, timeout=10)
            result = response.json()
            if result.get("ok"):
                print(f"[Telegram] 訊息發送成功（包含一鍵回覆按鈕）")
                return True
            else:
                print(f"[Telegram] 發送失敗: {result}")
                return False
        except Exception as e:
            print(f"[Telegram] 發送錯誤: {e}")
            return False

    def send_status_message(self, status: str, details: str = "") -> bool:
        """發送狀態消息"""
        status_icons = {
            "started": "🚀",
            "stopped": "⏹️",
            "error": "❌",
            "info": "ℹ️",
            "found": "✅"
        }
        icon = status_icons.get(status, "📌")
        message = f"{icon} 系統狀態\n\n{details}"
        return self.send_message(message)


# 保持向後兼容
class TelegramSender(TelegramSenderEnhanced):
    """向後兼容的 Telegram 通知類"""
    pass