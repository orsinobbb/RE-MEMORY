# 情境 Token 與成本預算：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **BUD-01**：計算 system、user、mandatory、work、evidence、tools、output reserve、safety margin 與 total。
- **BUD-02**：將最終 messages framing 開銷算入 packing，支援 1K、2K、4K、8K、16K 展示預算與模型 context limit。
- **BUD-03**：必要限制不可截斷；total 超出預算必須標記 INFEASIBLE／阻止執行。
- **BUD-04**：本機 Token 估算與 actual provider usage 分開；未知實際值保持 null／UNKNOWN。
- **BUD-05**：付費呼叫前以保守輸入／輸出與有限 retry 上界做交易式成本保留，不能超過開發包絡。
- **BUD-06**：精確帳單尚未核對時，保留上界與未結清 reservation，不假報已測零成本。

## 驗證入口

- `tests/test_context.py`
- `tests/test_mixroute.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
