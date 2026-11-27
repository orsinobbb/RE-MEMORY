# 可重現對照評估：requirements

依據：docs/project-v5.txt（V5）與 docs/design.md。此模組文件提供可執行驗收規則，不減少完整規格。

## 需求與驗收

- **EVA-01**：每輪評估使用獨立合成資料庫，不把 ground truth 保存於 memory 或交給 retrieval／task runner。
- **EVA-02**：dev 與 blind 分開，權重調整只使用 dev；report 標記 split、seed／日期與策略配置。
- **EVA-03**：比較 A–F、10／100／1000 與 1K／2K／4K／8K／16K，不預先假設新策略勝出。
- **EVA-04**：輸出 top1／top3／MRR／critical recall／precision／constraint omission／clarification／rounds／tokens／latency 等實測值與 case results。
- **EVA-05**：離線任務成功、wrong execution、duplicate delivery、API cost、cost per success 維持 null；F 離線為 NOT_RUN_REQUIRES_LIVE_SMART_ROUTING。
- **EVA-06**：LIVE A–E 使用相同固定模型；F 只改 provider routing，fresh trials 與真實 artifact／usage 才能支持 task success。
- **EVA-07**：完整矩陣、LIVE 比較、元件消融與 billed cost 應逐項報告實測狀態，不能由測試存在推論成績。

## 驗證入口

- `tests/test_evaluation.py`
- `tests/test_storage.py`

2026-11-27 最新驗收：全套 122 項 pytest 通過，實際瀏覽器與交付檢查見 [驗收表](../../../reports/acceptance.md)。逐項範圍及未完成研究驗證均在表內；不能把測試通過等同全部 V5 研究需求完成。
