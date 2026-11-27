# 有界漸進式檢索：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入 SearchState、版本去重、候選探索、有限輪次與可保存 trace。
- [x] 已寫入 progressive retrieval、歧義、未知、budget 及 SSE 路由測試。

## 最終驗收與待補強

- [x] 驗證主代理補強的關係探索與具體 A／B baseline payload，記錄對照差異。
- [x] 最終測試每輪原因／新資訊／成本與 regular、SSE 結果一致。
- [x] 驗證過小預算、停止界限與完整矩陣；不得把未量測策略寫成勝出。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_retrieval.py`、`tests/test_api.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、两階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
