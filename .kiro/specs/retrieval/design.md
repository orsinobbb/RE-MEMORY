# 有界漸進式檢索：design

## 實作來源

- `app/engines/retrieval.py`
- `app/engines/exploration.py`
- `app/engines/scoring.py`

## 資料流與決策

SearchState 保存 budget、read_versions、clues、rounds 與 spent；observe() 對相同版本回傳零新增成本。Router 儲存完成 trace，並可透過 on_round 發送 SSE。

P0 初始 D／E／F 使用 L0–L2；A／B／C 使用不同有界單層基線。L2 使用候選稱呼與全文索引補充中斷活動、待辦線索，候選分數與差距決定是否辨識。

context_builder 在辨識後完成必要記憶檢查，Router 以 L3–L5 trace 顯示相關資訊讀取。這不是把高分當作全面理解。

目前 FTS FALLBACK 沒有向量校準；搜尋上限與成本以目前本機估算為準。任意歷史、跨外部來源與動態任務拆分並不在本輪已驗收範圍。

主代理正在補強實際 relation traversal 與 recent-history／fixed-summary 基線 payload；在最終測試與矩陣完成前，這些驗收維持 pending。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
