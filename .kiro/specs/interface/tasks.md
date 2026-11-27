# 六視圖可觀察介面與 API：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入六視圖、原生回傳式樣式、native SVG、SSE／回放與實際API路由。
- [x] 已寫入先行 smoke test，完成 JS語法、DOM ID、同源資產與文字渲染靜態檢查。
- [x] 已寫入 API endpoint／SSE／downloads／origin／key absence 測試。

## 最終驗收與待補強

- [x] 後端啟動後實際跑smoke，驗證query／六導航／context／SIMULATION artifact／benchmark輸出。
- [x] 用支持的瀏覽器工具觀察桌面與手機、overflow／狀態／下載與錯誤處理。
- [x] 確認SSE／SAVED REPLAY、DEMO／SIMULATION／LIVE與actualresults一致，保存最終證據。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_api.py`、`tests/browser_smoke.mjs`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、两階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
