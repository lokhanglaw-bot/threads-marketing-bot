# My Fit Monster - Threads Marketing Bot

一個智慧型的 Threads 監控營銷工具，幫助你發現相關帖子並生成自然的回覆建議。

## 功能特點

- 🔍 **自動監控** - 監控 Threads 上包含健身、無聊、減肥等關鍵詞的帖子
- 🤖 **智能回覆** - AI 生成符合你個人風格的自然回覆
- 📱 **Telegram 通知** - 發現相關帖子時立即發送到你的 Telegram
- ✅ **人工確認** - 所有回覆都需要你確認才執行，確保內容符合你的意圖
- 🛡️ **防偵測設計** - 模擬人類行為，減少被 Threads 偵測的風險

## 工作流程

```
Threads 監控 → 發現相關帖子 → AI 生成回覆建議
                                      ↓
                              📱 Telegram 通知你
                                      ↓
                              ✅ 你確認後手動回覆
```

## 安裝步驟

### 1. 安裝 Python（如果是 Mac）

```bash
# 使用 Homebrew 安裝 Python
brew install python3
```

### 2. 創建虛擬環境（推薦）

```bash
cd threads-marketing-bot
python3 -m venv venv

# 激活虛擬環境
source venv/bin/activate  # Mac/Linux
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

### 4. 安裝 Playwright 瀏覽器

```bash
playwright install chromium
```

## 配置

### 編輯 `config.py`

```python
# Telegram 配置（已填好）
TELEGRAM_BOT_TOKEN = "8209819396:AAHW0CXKW1uc-lO8m31H0R3lYQKYpzLXuss"
TELEGRAM_CHAT_ID = "504271612"

# App 推廣連結
APP_LINK = "https://apps.apple.com/hk/app/my-fit-monster/id6759150998"

# 監控關鍵詞（可以根據需要添加更多）
KEYWORDS = [
    "操野", "做gym", "健身好悶", "一個人做gym",
    "好悶", "一個人", "減肥", "瘦身", ...
]

# 你的個人背景（用於生成更真實的回覆）
YOUR_PROFILE = "..."

# 你對 App 的真實體驗
YOUR_APP_EXPERIENCE = "..."
```

### 定制回覆風格

在 `reply_generator.py` 中可以修改回覆模板，使回覆更符合你的風格。

## 使用方法

### 測試連接

```bash
python main.py test
```

這個命令會：
1. 嘗試連接到 Threads
2. 測試 Telegram 發送功能
3. 顯示結果

### 執行一次掃描

```bash
python main.py once
```

這個命令會：
1. 掃描 Threads 首頁和搜索結果
2. 找到包含關鍵詞的帖子
3. 為每個帖子生成回覆建議
4. 發送到你的 Telegram

### 循環運行

```bash
# 每 5 分鐘掃描一次（默認）
python main.py loop

# 每 10 分鐘掃描一次
python main.py loop 600
```

Bot 會一直運行直到你按 `Ctrl+C` 停止。

## Telegram 通知格式

當 Bot 發現相關帖子時，你會收到這樣的消息：

```
🔍 *新發現相關帖子*

⏰ 時間: 14:30:25

📝 *帖子內容:*
我最近健身好無聊，一個人去gym又冇動力，有冇人介紹下...

👤 *作者:*
@fitness_hk

🔗 *連結:*
https://www.threads.net/@fitness_hk/post/xxx

━━━━━━━━━━━━━━━━━━━━

💬 *AI 回覆建議:*

我都試過咁！後來我開始用 My Fit Monster 做運動，發覺幾好堅持，你可以試下 😊

━━━━━━━━━━━━━━━━━━━━

⚠️ *請確認後手動回覆*
回复鏈接: https://www.threads.net/@fitness_hk/post/xxx

✅ 已確認後，請複製上方的回覆建議到 Threads 回覆
```

## 風險提示

⚠️ **重要**：
- Threads 可能會偵測自動化行為
- 建議適度使用，不要過於頻繁
- 建議只在必要時運行
- 系統只是輔助工具，最終回覆由你決定

## 疑難解答

### Q: 為什麼 Bot 找不到帖子？
A:
- Threads 頁面結構可能變化，需要更新選擇器
- 嘗試運行 `python main.py test` 檢查連接
- 檢查關鍵詞是否與帖子內容匹配

### Q: Telegram 沒有收到通知？
A:
- 檢查 Bot Token 和 Chat ID 是否正確
- 確保 Bot 已經 start 了（給 Bot 發送 /start）
- 檢查網絡連接

### Q: 如何停止 Bot？
A:
- 在運行 `python main.py loop` 的終端中按 `Ctrl+C`

## 文件結構

```
threads-marketing-bot/
├── config.py           # 配置文件
├── main.py            # 主程序入口
├── threads_monitor.py # Threads 監控模組
├── telegram_sender.py # Telegram 通知模組
├── reply_generator.py # 回覆生成模組
├── requirements.txt    # Python 依賴列表
└── README.md          # 本文件
```

## 技術棧

- **Python 3.8+**
- **Playwright** - 瀏覽器自動化
- **Telegram Bot API** - 消息推送

## License

MIT License

---

🤖 Made with ❤️ for My Fit Monster
