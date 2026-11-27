# 聊天與記憶獨立審查

一次全分支唯讀審查：原判定 0 Critical、2 Important、1 Minor。兩項 Important 已修正；失敗呼叫的收據問題因使用者要求精確資源回報，提升為 Important 並修正。沒有待處理 Minor。

- 過時 scope 回應會把訊息送到舊專案：加入選擇 generation、回應範圍驗證、載入期間禁止送出、固定送出 conversation ID。`browser_chat_race.mjs` 先重現錯誤專案標題，再通過訊息送出範圍核對。
- 忘記後相同文字換 kind 可重建：依內容及歷史版本跨 kind 去重。`test_forgotten_content_not_recreated_under_another_kind` RED→GREEN。
- 付費失敗回傳 usage=null：採用 ProviderBlocked.record，清除前一回合費用顯示。`test_failed_paid_call_returns_its_own_receipt` RED→GREEN；瀏覽器合成503也顯示本輪 UNKNOWN Token 與保留上限。
- 共用頁首把使用者聊天標成合成資料：聊天頁改「本機聊天資料」。瀏覽器先重現 DEMO DATASET，再通過。

完整 142 項 pytest 通過；聊天操作、範圍倒序與原三步驟瀏覽器回歸通過。Starlette 的 httpx 相容性警告是既有依賴警告，未新增依賴或改動平台。

審查沒有判定的事項，後續另驗證本機與公開交付；漏驗可能造成交付失效。供應商實際帳單保持 UNKNOWN，保守上限沿用原帳本；實際費用仍需供應商帳單佐證。此次修正沒有新增付費呼叫。
