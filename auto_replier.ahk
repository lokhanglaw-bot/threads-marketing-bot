;========================================
; My Fit Monster - Threads 自動化回覆
; AutoHotkey 腳本
;========================================
; 按下 Ctrl+Shift+R 開始自動回覆流程

#SingleInstance Force
#Persistent

; 監控是否在運行
global g_Running := False

; 回覆檔案路徑
global PENDING_FILE := "pending_replies.json"
global REPLY_TEMP_FILE := "current_reply.txt"

;========================================
; 熱鍵：Ctrl+Shift+R 啟動自動回覆
;========================================
^Space::
    RunAutoReply()
Return

;========================================
; 主動回覆流程
;========================================
RunAutoReply() {
    global PENDING_FILE, REPLY_TEMP_FILE

    ; 檢查是否有待回覆
    if (!FileExist(PENDING_FILE)) {
        MsgBox, 48, 錯誤, 找不到待回覆檔案！`n請確保 Threads Monitor Bot 正在運行。
        return
    }

    ; 讀取 JSON
    FileRead, content, %PENDING_FILE%

    ; 解析第一個待回覆
    ; 這裡需要正則表達式提取
    ; 格式: {"reply_XYZ": {"url": "...", "reply": "..."}}

    ; 簡化版本：從檔案中讀取最新的一條
    loop, parse, content, `n
    {
        if (A_LoopField ~= "reply_") {
            ; 找到回覆 ID
            line := A_LoopField

            ; 提取 URL 和回覆內容
            ; 使用正則表達式
            if (RegExMatch(line, """url"":\s*""([^""]+)""", url_match)) {
                url := url_match1
            }
            if (RegExMatch(line, """reply"":\s*""([^""]+)""", reply_match)) {
                reply := reply_match1
            }
            if (RegExMatch(line, """([reply_][^""]+)""", id_match)) {
                ; 提取 key 名稱
                StringTrimLeft, reply_id, id_match1, 1
                StringTrimRight, reply_id, reply_id, 1
            }

            if (url && reply) {
                break
            }
        }
    }

    if (!url || !reply) {
        MsgBox, 48, 錯誤, 無法解析回覆資料！
        return
    }

    ; 保存回覆到臨時檔案
    FileDelete, %REPLY_TEMP_FILE%
    FileAppend, %reply%, %REPLY_TEMP_FILE%

    ; 複製回覆到剪貼板
    Clipboard := reply

    ; 打開瀏覽器
    Run, msedge.exe "%url%", , Hide
    ; 或者使用 Chrome
    ; Run, chrome.exe "%url%", , Hide

    ; 等待瀏覽器啟動
    Sleep, 3000

    ; 激活瀏覽器視窗
    WinWait, ahk_class Chrome_WidgetWin_1, , 10
    if (ErrorLevel) {
        WinWait, ahk_class MozillaWindowClass, , 10
    }

    ; 等待頁面加載
    Sleep, 3000

    ; 按 Tab 跳到回覆框
    Send, {Tab 5}
    Sleep, 500

    ; 粘貼回覆
    Send, ^v
    Sleep, 1000

    ; 發送（按 Enter）
    Send, {Enter}

    ; 刪除臨時檔案
    Sleep, 1000
    FileDelete, %REPLY_TEMP_FILE%

    ; 刪除已回覆的項目（需要 Python 來更新 JSON）
    ; 這裡我們簡化為標記已處理
    MsgBox, 64, 完成, 回覆已發送！`n`n請手動更新 pending_replies.json`n刪除已回覆的項目。
}

;========================================
; 熱鍵：Ctrl+Shift+S 停止 Bot
;========================================
^s::
    Suspend
    if (A_IsSuspended) {
        MsgBox, 64, 提示, 腳本已暫停`n按 Ctrl+Shift+S 恢復
    } else {
        MsgBox, 64, 提示, 腳本已恢復
    }
Return

;========================================
; 最小化到系統托盤
;========================================
#z::  ; 按 Win+Z 隱藏
    Gui, Hide
    TrayTip, Threads AutoReplier, 已隱藏到系統托盤`n按 Ctrl+Shift+R 啟動回覆, 5
Return

; 雙擊托盤圖標恢復
GuiClose:
    ; 不關閉，只是隱藏
Return