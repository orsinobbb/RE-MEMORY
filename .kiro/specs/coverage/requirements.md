# 必要記憶與完整性：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **COV-01**：接續工作必須有目前 GOAL、CONSTRAINT、DECISION、未完成任務及其依賴。
- **COV-02**：必要記憶須在有效時間、非 superseded、無衝突、具驗證／可信狀態與同專案可信來源。
- **COV-03**：已完成任務與 required_artifact_ids 指向的成果必須存在、屬於同專案、具有驗證狀態與正確 SHA256。
- **COV-04**：產生含專案、目標版本、active task、mandatory memory、依賴、來源、缺失、衝突、snapshot 與預算的 manifest。
- **COV-05**：缺失、未核實來源、衝突或有效期錯誤要產生 Semantic Page Fault／阻擋原因，不得默認可執行。
- **COV-06**：覆蓋率只描述已知必要記憶；不能宣稱知道全部歷史，生成 CLAIM 不能代替已驗證限制。

## 驗證入口

- `tests/test_context.py`
- `tests/test_tasks.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
