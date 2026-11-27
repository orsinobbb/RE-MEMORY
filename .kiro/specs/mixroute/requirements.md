# MixRoute 固定模型與自動路由：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **MIX-01**：使用已核實的 official endpoint 與 actual model ID；regular／Smart keys 只在本機後端設定，不進入 UI、Git、影片或公開紀錄。
- **MIX-02**：提供 FIXED 與 SMART，保留 requested／actual model、usage、request／response ID、latency 與 failure。
- **MIX-03**：未知價格、空授權池、未啟用 API、超 context limit／budget 時阻止付費執行；唯讀 catalogue 不等於 pool proof。
- **MIX-04**：最終必須驗證 FIXED requested model 與 SMART actual returned model 屬於核准模型池。
- **MIX-05**：逾時與 transient failure 只有有界 retry；未知 bill 不釋出保守 reservation，不自動儲值。
- **MIX-06**：真實連線、任務接續、跨模型交接與實驗效果分別驗證，單次 auto 探針不能代替任務成功。

## 驗證入口

- `tests/test_mixroute.py`
- `tests/test_api.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
