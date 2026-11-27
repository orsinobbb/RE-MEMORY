# Session 接續、驗證與交易式交付：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **ORC-01**：新 Session 的 raw_history_count=0，沒有前一 Session 原始對話，接續只使用目前需求與持久化記憶。
- **ORC-02**：接續前必須辨識目標、重建 feasible context，並驗證任務工具在白名單。
- **ORC-03**：P0 僅允許 markdown_handoff，不能執行任意 shell、其他私人專案讀取、上傳或外部變更。
- **ORC-04**：SIMULATION／FIXED／SMART 標記清楚；成果必須非空、有目標／限制／下一步、保存目前硬性限制與 SHA256。
- **ORC-05**：同 idempotency key 的不同請求被阻止；同任務不得重複完成，執行中回傳 IN_PROGRESS。
- **ORC-06**：成果、任務完成、事件、快照與 delivery 在同一交易寫回；生成文字仍為 CLAIM，驗證範圍受限。
- **ORC-07**：live 生成內容改寫必要限制時必須 BLOCKED，不能為了展示成功放寬驗證。

## 驗證入口

- `tests/test_tasks.py`
- `tests/test_context.py`
- `tests/test_mixroute.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
