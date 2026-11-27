# MixRoute 固定模型與自動路由：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入 SDK、raw usage／IDs／latency、finite retry、reservation 與 redaction。
- [x] 已寫入未知價格／空池、SDK response 解析、retry 與 concurrent cap 測試。
- [x] 主代理已提供一次真實 auto connectivity 探針紀錄；不是端到端任務驗收。

## 最終驗收與待補強

- [x] 驗證 requested／returned model 授權池檢查與預算防護。
- [x] 完成 FIXED／SMART 真實接續 artifact、同模型比較與跨模型交接實測。
- [ ] 核對 balance／expiry／pricing／帳單與上界 reservation，保存非敏感證據。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_mixroute.py`、`tests/test_api.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、两階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
