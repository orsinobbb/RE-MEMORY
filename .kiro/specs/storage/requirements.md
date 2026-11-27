# 版本化記憶儲存：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **STO-01**：所有資料存取以 user_id 篩選，專案記憶另以 project_id 篩選；同一 ID 不得跨使用者覆寫。
- **STO-02**：SQL 值採參數化；資料表名稱只能從白名單選取，任意輸入不得改寫查詢結構。
- **STO-03**：固定 seed 與日期基準可重現 10、100、1000 個合成專案；包含相似主題、歧義別名、舊版本、未完成工作與已存在的完成成果。
- **STO-04**：Fact Cell 保存類型、來源、有效時間、版本、驗證、信任、關聯、存取、superseded 與 conflict；查詢可區分目前版本與完整保存版本。
- **STO-05**：同一 alias 可連結多個專案；CONFIRMED／CANDIDATE 等狀態不得混同。
- **STO-06**：FTS5 支援中文 bigram 與英文詞；索引／資料庫不儲存 evaluator ground truth。
- **STO-07**：任務、成果、事件、快照與交付識別使用交易寫回；成本保留帳本能區分實際已結清值與未結清上界。

## 驗證入口

- `tests/test_storage.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
