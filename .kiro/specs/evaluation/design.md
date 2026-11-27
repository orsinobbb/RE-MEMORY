# 可重現對照評估：design

## 實作來源

- `app/engines/evaluation.py`
- `benchmarks/generators/synthetic.py`
- `benchmarks/generators/truth.py`

## 資料流與決策

evaluate() 以 UUID 建臨時 Store，呼叫 synthetic seed；只有 evaluator 導入 cases(split)。輸出每個策略／預算的 row 與可核對 case_results，memory 資料庫不持有答案。

offline 通過 Router 回傳候選、選擇與 context，計算身份辨識與已知 critical facts 覆蓋；計數的是固定合成案例，專案數增加不表示案例數同倍增加。

離線 mean_e2e_tokens 是本機邏輯估算，不是 LLM 實際端到端 billing。wrong project execution／duplicate completion 等執行結果不從檢索推測。

F 在離線直接標未執行。結果使用 UNKNOWN／null 和 limits 傳達未量測專案，不自填零或成功率。

主代理正在實作／執行完整離線與有界 live runner。A–E 共用必要驗證的範圍、完整 baseline payload 及 graph 補強須在 final report 說明；嚴格消融仍待驗證。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
