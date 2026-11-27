# 可重現對照評估：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已寫入 evaluator、獨立 synthetic DB、dev／blind cases 與 offline metrics。
- [x] 已寫入 truth 隔離、不同策略輸出與不造 live success／cost 測試。

## 最終驗收與待補強

- [x] 保存完整規模／預算／策略矩陣 JSON 與實際執行時間。
- [x] 完成同固定模型 A–E 與 F routing 的 fresh LIVE task trials，核對 artifact 與 usage。
- [x] 核對 A／B／C 具體 payload、F 實際模型及成功／失敗輸出；標示案例已見過和新固定句型。
- [ ] 真正封存盲測、每個元件增益的完整消融及正式帳單尚未完成。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_evaluation.py`、`tests/test_storage.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、两階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
