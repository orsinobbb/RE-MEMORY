# 版本化記憶儲存：tasks

最終狀態由根代理核對；實際測試輸出、UI、API、矩陣及備份證據見 reports/acceptance.md、reports/acceptance.json 與 reports/resources.json。

## 已寫入

- [x] 已建立 SQLite Store、資料表白名單、參數化查詢及使用者／專案篩選。
- [x] 已寫入合成資料生成、版本／來源／歧義別名與完成成果測試。

## 最終驗收與待補強

- [x] 重新執行最終 storage 測試，保存實際輸出與 10／100／1000 規模紀錄。
- [x] 核驗備份／還原、交易故障與交付／成本帳本保留。
- [x] 索引／更新在本機執行、零模型 Token；macOS 解壓後實際一鍵啟動驗證。
- [ ] Windows 原生主機啟動尚未實測。

## 依賴與證據

需求：本目錄 requirements.md；設計：design.md。測試：`tests/test_storage.py`。測試命令與實際輸出、elapsed time、API usage／保留額與最終驗收狀態寫入根目錄 reports，不在本文件編造測量。

未執行公開部署或競賽投稿。

## 2026-11-27 驗收補記

全套 122 項 pytest、六視圖、两階段及記憶修正實際瀏覽器檢查通過。記憶修正／再驗證 UI 已完成；備份還原及 macOS 解壓一鍵啟動通過。逐項需求／證據／範圍見 [驗收表](../../../reports/acceptance.md)。私人交付已準備；本人旁白依使用者安排延後，公開與投稿未執行。
