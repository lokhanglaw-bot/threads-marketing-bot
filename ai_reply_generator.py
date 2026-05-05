"""
AI 回覆生成模組
使用 DeepSeek AI 根據帖子內容智能生成回覆
"""

import requests
import json
from config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, APP_LINK, YOUR_PROFILE, YOUR_APP_EXPERIENCE


class AIReplyGenerator:
    """使用 DeepSeek AI 生成智能回覆"""

    def __init__(self):
        self.api_key = DEEPSEEK_API_KEY
        self.api_url = DEEPSEEK_API_URL
        self.app_link = APP_LINK

    def generate_reply(self, post_content: str) -> str:
        """
        使用 DeepSeek AI 根據帖子內容生成回覆
        
        Args:
            post_content: 帖子的完整內容
            
        Returns:
            str: AI 生成的回覆
        """
        
        # 構建 prompt
        prompt = f"""你是一個香港健身愛好者，正在用個人身份回覆 Threads 上的帖子。

你的背景：
{YOUR_PROFILE}

你對 My Fit Monster 的使用體驗：
{YOUR_APP_EXPERIENCE}

帖子內容：
「{post_content}」

請根據這個帖子的內容，生成一個自然的、像真實用家一樣的回覆。

要求：
1. 用廣東話口語風格（香港人嘅方式傾偈）
2. 自然分享你對 My Fit Monster 的使用感受
3. 唔好 hard sell，要自然
4. 回覆長度：20-30字左右
5. 可以提及 My Fit Monster 的功能，但唔好太刻意
6. 最後要加入下載連結：{self.app_link}

請直接給我回覆內容，唔好加其他說明。
"""

        try:
            # 調用 DeepSeek API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.8,  # 有一點隨機性，但唔會太飄
                "max_tokens": 500
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                reply = result['choices'][0]['message']['content'].strip()
                
                # 確保回覆包含下載連結
                if self.app_link not in reply:
                    reply = f"{reply}\n\n📱 {self.app_link}"
                
                return reply
            else:
                print(f"[AI] API 錯誤: {response.status_code}")
                return self._fallback_reply(post_content)

        except Exception as e:
            print(f"[AI] 生成回覆時出錯: {e}")
            return self._fallback_reply(post_content)

    def _fallback_reply(self, post_content: str) -> str:
        """如果 AI 生成失敗，使用簡單的回覆"""
        return f"我最近試咗 My Fit Monster，覺得幾好用，幫到我堅持健身，你可以試下 😊\n📱 {self.app_link}"

    def should_reply(self, content: str) -> tuple[bool, str]:
        """判斷是否應該回覆"""
        negative_keywords = ["減肥藥", "瘦身產品", "極端減肥", "已經放棄", "算啦", "唔減啦"]

        for keyword in negative_keywords:
            if keyword in content:
                return False, f"包含負面關鍵詞: {keyword}"

        if len(content) < 20:
            return False, "帖子太短"
        if len(content) > 500:
            return False, "帖子太長"

        return True, "適合回覆"