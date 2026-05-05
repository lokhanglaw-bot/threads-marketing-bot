# My Fit Monster - Threads Marketing Bot

## 🎯 使命宣言

**協助香港健身愛好者發現志同道合的社群，讓健身不再孤單。**

通過自動化工具，在 Threads 上發現正在尋找健身夥伴或感到健身無聊的用戶，以真實用戶的身份分享 My Fit Monster App，幫助更多人享受健身的樂趣。

---

## 📋 項目描述

這是一個專為 **My Fit Monster** App 設計的 Threads 自動化營銷工具。

### 核心功能

1. **🔍 智能監控** - 自動搜索 Threads 上包含健身相關關鍵詞的帖子
2. **🤖 AI 回覆生成** - 使用 DeepSeek AI 生成自然、友好的粵語回覆
3. **📱 Telegram 通知** - 發現相關帖子時即時通知，並附上一鍵回覆按鈕
4. **🖱️ 自動化點擊** - 透過圖像識別技術，自動點擊回覆按鈕

### 關鍵詞列表（85個）

```
操野, 操gym, 做gym, 健身, 好悶, 減肥, 一個人, 無聊, 孤獨,
訓練, 運動, 健身計劃, 減脂, 增肌, 健身目標, GymTime,
一個人做gym, 健身好悶, 操野好悶, 健身減肥, 想健身, 健身入門,
新手健身, 健身日記, 健身心得, 健身生活, 健身減肥...
```

---

## 🏗️ 系統架構

```
┌─────────────────────────────────────────────────────────────────┐
│                        系統架構圖                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐    │
│   │   Threads   │      │    AI      │      │  Telegram   │    │
│   │   Monitor   │─────▶│  Generator │─────▶│   Sender    │    │
│   │  (爬蟲)     │      │  (回覆)     │      │  (通知)     │    │
│   └─────────────┘      └─────────────┘      └─────────────┘    │
│         │                                           │           │
│         │                                           ▼           │
│         │              ┌─────────────────────────────────┐     │
│         │              │         User Decision           │     │
│         │              │  (人工確認 / 一鍵回覆)           │     │
│         │              └─────────────────────────────────┘     │
│         │                         │                           │
│         ▼                         ▼                           │
│   ┌─────────────┐      ┌─────────────────────────────┐        │
│   │    圖像     │◀─────│      Auto Replier          │        │
│   │    識別     │      │   (點擊回覆按鈕 + 填寫)     │        │
│   │  (找愛心)   │      └─────────────────────────────┘        │
│   └─────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔧 技術棧

| 技術 | 用途 |
|------|------|
| **Python 3.8+** | 主要程式語言 |
| **Playwright** | 瀏覽器自動化（爬蟲） |
| **OpenCV** | 圖像識別（找愛心按鈕） |
| **PyAutoGUI** | 滑鼠/鍵盤控制 |
| **DeepSeek API** | AI 回覆生成 |
| **Telegram Bot API** | 即時通知 |

---

## 📁 檔案結構

```
threads-marketing-bot/
├── config.py                    # 配置文件（API keys、關鍵詞等）
├── main.py                     # 主程式入口
├── threads_monitor.py          # Threads 爬蟲模組
├── reply_generator.py          # AI 回覆生成器
├── telegram_sender.py          # Telegram 通知（基本版）
├── telegram_sender_enhanced.py # Telegram 通知（增強版，帶按鈕）
├── auto_replier.py             # 自動化回覆器（圖像識別版）
├── cookie_helper.py            # Cookies 管理助手
├── debug.py                    # 調試工具
├── debug_threads.py            # Threads 調試腳本
├── auto_replier.ahk            # AHK 備用方案
├── requirements.txt            # Python 依賴列表
└── README.md                   # 本文件
```

---

## 🚀 快速開始

### 前置需求

```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 OpenCV（圖像識別）
pip install opencv-python

# 安裝 Playwright 瀏覽器
playwright install chromium

# 安裝 Pillow（修復相容性）
pip install Pillow==10.0.0
```

### 配置文件

編輯 `config.py`:

```python
# Telegram Bot Token
TELEGRAM_BOT_TOKEN = "your_bot_token"
TELEGRAM_CHAT_ID = "your_chat_id"

# App 推廣連結
APP_LINK = "https://apps.apple.com/hk/app/my-fit-monster/id6759150998"

# 監控關鍵詞（已預設85個）
KEYWORDS = ["操野", "做gym", "健身好悶", ...]
```

### 運行

```bash
# 終端 1：監控 Threads 並發送到 Telegram
python main.py loop

# 終端 2：監聽一鍵回覆按鈕（需要同時運行）
python auto_replier.py
```

---

## 🎮 工作流程

```
1. main.py loop        →  每12小時自動掃描 Threads
        ↓
   發現相關帖子         →  使用 DeepSeek AI 生成回覆
        ↓
   發送到 Telegram     →  附帶「一鍵回覆」按鈕
        ↓
   用戶點擊按鈕        →  auto_replier.py 監聽到
        ↓
   圖像識別定位        →  找愛心 ♥ 按鈕 → 點擊右邊的回覆 💬
        ↓
   自動化回覆          →  填寫內容 → 發送
```

---

## 🔍 圖像識別原理

### 核心邏輯

```
1. 截圖整個螢幕
2. 使用 OpenCV 找紅色/粉色的愛心 ♥ 按鈕
3. 回覆 💬 按鈕位於愛心的右邊（約 50-70 像素）
4. 點擊該位置打開回覆框
5. 使用剪貼板粘貼回覆內容
6. 按 Enter 發送
```

### 關鍵代碼邏輯

```python
# 找愛心按鈕
heart_pos = find_heart_button(screenshot)  # 返回 (x, y) 座標

# 回覆按鈕在愛心右邊
reply_pos = (heart_pos[0] + 70, heart_pos[1])

# 點擊
pyautogui.click(reply_pos)
```

---

## ⚙️ 命令詳解

| 命令 | 功能 |
|------|------|
| `python main.py test` | 測試 Threads 和 Telegram 連接 |
| `python main.py once` | 執行一次掃描 |
| `python main.py loop` | 循環運行（每12小時掃描一次） |
| `python main.py loop 600` | 循環運行（每10分鐘掃描一次） |
| `python auto_replier.py` | 啟動自動化回覆監聽 |

---

## ⚠️ 風險提示

1. ** Threads 可能偵測自動化行為**，建議適度使用
2. **自動回覆功能仍在調試中**，可能需要手動調整
3. **所有回覆都需要人工確認**，確保內容符合預期
4. **遵守 Threads 服務條款**，合理使用自動化工具

---

## 🔧 故障排除

### 問題：圖像識別找不到按鈕

```
[AutoReplier] 圖像識別失敗: PyAutoGUI was unable to import pyscreeze
```

**解決方案：**
```bash
pip uninstall Pillow
pip install Pillow==10.0.0
```

### 問題：點擊位置不準確

確保：
1. Threads 瀏覽器窗口是**窗口模式**（非全屏）
2. 窗口位置相對固定
3. 頁面已滾動到可以看到回覆按鈕的位置

### 問題：回覆沒有發送

1. 檢查點擊後回覆框是否打開
2. 檢查文字是否成功粘貼
3. 檢查 Enter 鍵是否生效

---

## 📝 開發日誌

### v11 (最新)
- 添加點擊驗證功能
- 優化圖像識別邏輯
- 增加調試輸出

### v10
- 添加調試模式
- 顯示愛心周圍所有按鈕
- 幫助定位正確的回覆按鈕

### v9
- 修復 Pillow/pyscreeze 相容性問題
- 使用 PIL 直接截圖

### v8
- 智能按鈕定位
- 找愛心 ♥ → 點擊右邊 💬

### v7
- OpenCV 圖像識別基礎版

### v6
- 固定座標點擊（已棄用）

---

## 🤝 貢獻指南

歡迎提交 Issue 或 Pull Request！

---

## 📄 License

MIT License

---

## 👤 作者

**My Fit Monster Team**

- App Store: https://apps.apple.com/hk/app/my-fit-monster/id6759150998
- 官網: https://www.myfitmonster.com

---

## 🙏 致謝

- [DeepSeek](https://deepseek.com) - AI 回覆生成
- [Playwright](https://playwright.dev) - 瀏覽器自動化
- [OpenCV](https://opencv.org) - 圖像識別