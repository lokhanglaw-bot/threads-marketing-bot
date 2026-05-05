"""
回覆生成模組
使用 DeepSeek AI 根據帖子內容生成自然的個人回覆
"""

import requests
import random
from typing import Dict, List, Optional


class ReplyGenerator:
    """使用 DeepSeek AI 的回覆生成器"""

    def __init__(self, app_link: str, app_experience: str, profile: str, api_key: str = None, api_url: str = None):
        """
        初始化回覆生成器

        Args:
            app_link: App 下載連結
            app_experience: 你對 App 的真實體驗
            profile: 你的個人背景描述
            api_key: DeepSeek API Key
            api_url: DeepSeek API URL
        """
        self.app_link = app_link
        self.app_experience = app_experience
        self.profile = profile
        self.api_key = api_key or "sk-8fd8bfd7288d4192811bafec7d920f7f"
        self.api_url = api_url or "https://api.deepseek.com/v1/chat/completions"
        self.cache = {}  # 簡單的回复緩存

    def _build_prompt(self, post_content: str, matched_keywords: List[str]) -> str:
        """構建給 DeepSeek 的提示"""
        keyword_str = ", ".join(matched_keywords) if matched_keywords else "健身相關"

        prompt = f"""你係一個香港健身愛好者，用口語化嘅方式同人傾偈。

【你的背景】
{self.profile}

【你對 My Fit Monster 的使用體驗】
{self.app_experience}

【帖子內容】
{post_content}

【匹配關鍵詞】
{keyword_str}

【要求】
1. 用第一人身廣東話回覆，自然、口語化
2. 先對帖子的內容作出共鳴或回應，然後自然帶到 My Fit Monster
3. 唔好 hard sell，要係真實用家角度分享
4. 回覆長度：50-100字
5. 唔好加 emoji，但可以加適當的香港口語

【輸出格式】
直接輸出回覆內容，唔好加任何標題或解釋
"""

        return prompt

    def generate_reply(self, post_content: str, matched_keywords: List[str]) -> str:
        """根據帖子內容生成回覆（使用 DeepSeek AI）"""
        # 檢查緩存
        cache_key = f"{post_content[:100]}_{matched_keywords}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        try:
            prompt = self._build_prompt(post_content, matched_keywords)

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.8,
                "max_tokens": 200,
                "stream": False
            }

            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                reply = result["choices"][0]["message"]["content"].strip()

                # 確保回覆包含 app 連結
                if self.app_link not in reply:
                    reply = f"{reply}\n{self.app_link}"

                self.cache[cache_key] = reply
                return reply
            else:
                print(f"[ReplyGenerator] DeepSeek API 錯誤: {response.status_code}")
                return self._fallback_reply(post_content, matched_keywords)

        except requests.exceptions.Timeout:
            print("[ReplyGenerator] API 請求超時")
            return self._fallback_reply(post_content, matched_keywords)

        except Exception as e:
            print(f"[ReplyGenerator] 生成回覆失敗: {e}")
            return self._fallback_reply(post_content, matched_keywords)

    def _fallback_reply(self, post_content: str, matched_keywords: List[str]) -> str:
        """當 API 失敗時的後備回覆"""
        content_lower = post_content.lower()

        # 分析帖子類型
        if any(k in content_lower for k in ["悶", "無聊", "冇動力"]):
            openings = [
                "我明，全部人都試過咁",
                "係呀，健身最難係keep住有動力",
                "我識，我之前都係咁",
            ]
        elif any(k in content_lower for k in ["肥", "減", "瘦身"]):
            openings = [
                "減肥係需要時間，唔好俾自己太大壓力",
                "我最近都在減，但慢慢來先最緊要",
                "我明，慢慢黎就得",
            ]
        elif any(k in content_lower for k in ["gym", "健身", "操"]):
            openings = [
                "我成日去gym，明白你",
                "健身真係要堅持",
                "我都有去gym",
            ]
        else:
            openings = [
                "我明你",
                "有道理",
                "我都試過咁諗",
            ]

        opening = random.choice(openings)
        return f"{opening}！你有興趣可以試下 My Fit Monster，幾幫到手\n{self.app_link}"

    def should_reply(self, post_content: str) -> tuple[bool, str]:
        """判斷是否應該回覆這條帖子"""
        content_lower = post_content.lower()

        # 檢查是否有負面關鍵詞
        negative_keywords = [
            "減肥藥", "瘦身產品", "極端減肥", "催吐",
            "已經放棄", "算啦", "無所謂",
            "減肥產品", "減肥門", "減肥診所"
        ]

        for keyword in negative_keywords:
            if keyword in content_lower:
                return False, f"包含負面關鍵詞: {keyword}"

        # 檢查是否太短
        if len(post_content) < 20:
            return False, "帖子太短"

        # 檢查是否太長
        if len(post_content) > 5000:
            return False, "帖子太長"

        return True, "適合回覆"

    def clear_cache(self):
        """清除回覆緩存"""
        self.cache.clear()