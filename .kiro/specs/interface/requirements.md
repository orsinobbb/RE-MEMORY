# 六視圖可觀察介面與 API：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **IFR-01**：提供 Workspace、Memory Explorer、Retrieval Observatory、Context Inspector、Recovery Lab、Benchmark Lab 六個可操作視圖。
- **IFR-02**：所有資料來自 same-origin backend，憑證不得進入前端；導入文本通過 textContent／DOM API 呈現，不執行不可信 HTML。
- **IFR-03**：Observatory 呈現真實輪次／候選／證據／Tokens／停止原因；SSE優先，回退回放標示 SAVED REPLAY。
- **IFR-04**：Context 顯示 manifest、必要內容、未載入、缺失、衝突、fault 與八類預算；未知測量為 UNKNOWN。
- **IFR-05**：Recovery 使用真實新 Session、唯一 idempotency key、使用者選擇模式／catalogue model，顯示實際 artifact 與下載。
- **IFR-06**：Benchmark 只通過 UI 執行 offline，顯示 actual rows 與 JSON export；未量測 live 指標不能填示意成績。
- **IFR-07**：深藍／青綠／白色，body 16px、常用labels 14px；桌面／手機無頁面水平溢位，具基本鍵盤與狀態可讀性。
- **IFR-08**：actual browser integration 與最終畫面必須驗證，靜態語法檢查不能代替 six-view end-to-end。

## 驗證入口

- `tests/test_api.py`
- `tests/browser_smoke.mjs`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
