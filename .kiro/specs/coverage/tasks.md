# 必要記憶與完整性：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入 coverage、manifest、snapshot 與 source／artifact integrity 檢查。
- [x] 已寫入缺失來源、CLAIM／AI trust、衝突、有效期、缺失依賴與篡改成果測試。

## 最終驗收與待補強

- [x] 最終重跑 coverage/context/task 測試並保存實際 fault 原因。
- [x] 非 mandatory 的直接依賴有效期、信任、來源、完整內容已由 test_hardening 驗證。
- [ ] 任意遞迴依賴圖的完整閉包仍未完成。
- [x] 確認介面覆蓋率措辭與 validator 範圍，避免將 structure verified 說成事實正確。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_context.py`、`tests/test_tasks.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、兩階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
