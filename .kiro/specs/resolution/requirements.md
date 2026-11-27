# 意圖與專案辨識：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **RES-01**：解析目前需求的時間、主題與接續行為；日期以明確 reference_date 計算。
- **RES-02**：唯一明確專案 ID／完整名稱可辨識目標，且只能在目前使用者資料範圍搜尋。
- **RES-03**：唯一 CONFIRMED alias 與 CANDIDATE／歧義 alias 分開處理；REJECTED／DEPRECATED 不得作為已確認指令。
- **RES-04**：同一稱呼對應多個專案且無足夠區別線索時，回傳澄清，不執行錯誤專案。
- **RES-05**：候選分數顯示 time、topic、alias、behavior、content、unfinished、frequency 與正反證據；缺失構面重新正規化。
- **RES-06**：吻合分數與校準信心機率分離；未校準 confidence_probability 保持 null／UNKNOWN。

## 驗證入口

- `tests/test_retrieval.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
