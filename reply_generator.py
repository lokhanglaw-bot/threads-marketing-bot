"""
回覆生成模組
根據帖子內容，生成自然的個人回覆
"""

import random
import re
from typing import Dict, List


class ReplyGenerator:
    """回覆生成器"""

    def __init__(self, app_link: str, app_experience: str, profile: str):
        """
        初始化回覆生成器

        Args:
            app_link: App 下載連結
            app_experience: 你對 App 的真實體驗
            profile: 你的個人背景描述
        """
        self.app_link = app_link
        self.app_experience = app_experience
        self.profile = profile

    def generate_reply(self, post_content: str, keywords_found: List[str]) -> str:
        """
        根據帖子內容生成回覆

        Args:
            post_content: 帖子原文
            keywords_found: 匹配到的關鍵詞列表

        Returns:
            str: 生成的回覆
        """
        # 分析帖子類型，選擇合適的回覆模板
        post_type = self._analyze_post_type(post_content, keywords_found)

        # 根據類型生成回覆
        if "健身無聊" in post_type:
            return self._generate_fitness_boring_reply(post_content, keywords_found)
        elif "孤獨無聊" in post_type:
            return self._generate_lonely_boring_reply(post_content, keywords_found)
        elif "減肥" in post_type:
            return self._generate_weight_loss_reply(post_content, keywords_found)
        else:
            return self._generate_general_reply(post_content, keywords_found)

    def _analyze_post_type(self, content: str, keywords: List[str]) -> str:
        """分析帖子類型"""
        content_lower = content.lower()

        # 健身相關關鍵詞
        fitness_keywords = ["gym", "健身", "操", "訓練", "運動"]
        # 無聊相關關鍵詞
        boring_keywords = ["悶", "無聊", "冇動力", "懶"]
        # 減肥相關關鍵詞
        weight_keywords = ["肥", "減", "瘦身", "減脂"]

        has_fitness = any(k in content_lower for k in fitness_keywords)
        has_boring = any(k in content_lower for k in boring_keywords)
        has_weight = any(k in content_lower for k in weight_keywords)

        if has_fitness and has_boring:
            return "健身無聊"
        elif has_weight:
            return "減肥"
        elif has_boring:
            return "孤獨無聊"
        else:
            return "一般"

    def _generate_fitness_boring_reply(self, post: str, keywords: List[str]) -> str:
        """生成健身無聊類型的回覆"""
        templates = [
            "我都試過咁！一個人做gym真係幾悶，不過而家用開個 app 叫 My Fit Monster，幾好用，可以追蹤進度，做完夠數會有成就感，慢慢就冇咁悶了 😄",

            "明白！操野最難係堅持，我有試過下載 My Fit Monster，佢有啲幾正嘅功能，跟住做又幾有動力，推介你試下！",

            "係呀係呀！一個人做gym真係好易放棄，我有個 tip 就係用 My Fit Monster 記錄低每次訓練，見到自己進步會開心啲 💪",

            "我都係！後來發現有個 app 可以跟住訓練計劃，唔使自己想做咩，慢慢就堅持多咗。你可以試下 My Fit Monster，入面有好多動作教學！",

            "完全明白你！我之前都係咁，後來朋友介紹我用 My Fit Monster，有訓練計劃又可以打卡，慢慢就變成習慣了 👍",
        ]

        return random.choice(templates)

    def _generate_lonely_boring_reply(self, post: str, keywords: List[str]) -> str:
        """生成孤獨無聊類型的回覆"""
        templates = [
            "香港人係咁，上班已經冇咩精力，我懂！我最近就用 My Fit Monster 做運動，唔使去 gym，一個人喺屋企都得，跟住 app 做又唔使諗嘢",

            "我都係咁！不過最近試咗 My Fit Monster，發覺做運動係幾舒服嘅，唔使諗嘢，又可以keep fit，一舉兩得！",

            "哈哈我可以幫到你！我用 My Fit Monster 一段時間了，入面有啲訓練好短，10分鐘就搞得掂，喺屋企就得，幾適合我哋呢啲懶人 🏃",

            "明嘅！不過與其發愁，不如郁下？我最近用 My Fit Monster，發覺幾適合我呢啲唔想去 gym 但又想運動嘅人，推介你試下 😊",

            "我都試過咁！不過後來發現做gym可以舒壓，我而家用 My Fit Monster 跟住做，幾方便，唔使plan 做咩野，推介試下 💪",
        ]

        return random.choice(templates)

    def _generate_weight_loss_reply(self, post: str, keywords: List[str]) -> str:
        """生成減肥類型的回覆"""
        templates = [
            "我都係想減肥嗰個！有試過 My Fit Monster，入面有啲訓練plan 唔錯，跟住做幾有效，堅持咗兩個月有啲成效，可以試下！",

            "減肥係一場持久戰！我最近用 My Fit Monster 幫我tracking，佢會提醒我每日要做幾多分鐘，慢慢就變成習慣了，推介你試下 😊",

            "我之前都係咁諗，但試咗 My Fit Monster 之後發覺原來可以幾簡單，入面有啲動作好basic，但幾有效，你可以試下！",

            "減肥最緊要係揾到適合自己嘅方法，我有朋友推介 My Fit Monster，我試完覺得幾好，佢有啲short workout 適合香港人 👍",

            "我都想減！不過要約定自己，我用 My Fit Monster 幫我 set goal，每日打卡，慢慢就有動力了，你可以試下 💪",
        ]

        return random.choice(templates)

    def _generate_general_reply(self, post: str, keywords: List[str]) -> str:
        """生成一般類型的回覆"""
        templates = [
            "我都試過咁！後來我開始用 My Fit Monster 做運動，發覺幾好堅持，你可以試下 😊",

            "明白！我之前都有呢個問題，後來發現 My Fit Monster 幾適合我哋香港人，訓練唔長但幾有效，推介你試下！",

            "我懂你！我最近用 My Fit Monster 跟住做，唔使自己想做咩，跟住做就得，幾方便 👍",

            "係呀！我最近試咗 My Fit Monster，幾適合懶人，動作又唔難，你可以試下 💪",

            "我都有類似經歷！不過我揾到個幾好嘅 app 叫 My Fit Monster，做完有成就感，慢慢就堅持多咗 😄",
        ]

        return random.choice(templates)

    def format_reply_for_copy(self, reply: str) -> str:
        """
        格式化回覆，便於複製粘貼
        這個方法可以添加一些額外的說明或者調整格式
        """
        return reply.strip()

    def should_reply(self, post_content: str) -> tuple[bool, str]:
        """
        判斷是否應該回覆這條帖子

        Args:
            post_content: 帖子內容

        Returns:
            tuple: (是否回覆, 原因)
        """
        content_lower = post_content.lower()

        # 檢查是否有負面關鍵詞（不適合推廣的帖子）
        negative_keywords = [
            "減肥藥", "瘦身產品", "極端減肥", "催吐",
            "已經放棄", "算啦", "無所謂"
        ]

        for keyword in negative_keywords:
            if keyword in content_lower:
                return False, f"包含負面關鍵詞: {keyword}"

        # 檢查是否太短（可能係廣告或無意義帖子）
        if len(post_content) < 20:
            return False, "帖子太短"

        # 檢查是否太長（可能係長文分享，不適合快速回覆）
        if len(post_content) > 5000:
            return False, "帖子太長"

        return True, "適合回覆"
