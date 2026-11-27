# Session 接續、驗證與交易式交付：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入空 Session、模式切換、白名單、task lock、idempotency 與原子交付。
- [x] 已寫入 SIMULATION 實體成果、重複請求、歧義／缺失記憶與未知 Session 測試。

## 最終驗收與待補強

- [x] 驗證加嚴後的 heading／constraint validator，保持 paraphrase omission 阻擋。
- [x] 完成真實 FIXED／SMART 產物與跨模型 fresh-session 接續驗收。
- [x] 補充並發交付、交易失敗／process crash lock 恢復與 key fingerprint 邊界測試。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_tasks.py`、`tests/test_context.py`、`tests/test_mixroute.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、兩階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
