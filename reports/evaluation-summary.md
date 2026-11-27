# 實驗摘要

實測日期：2026-11-26，固定種子42，合成十個盲測案例；8個有明確目標、2個應停止。A–E固定deepseek-v3.2；F以auto呼叫，實際也都是DeepSeek-V3.2。

| 策略 | Top-1 | 任務成功／8目標 | 實際生成請求 | 已知API Tokens | 錯誤／重複執行 |
|---|---:|---:|---:|---:|---:|
| A | 90% | 75.0% | 7 | 21,468 | 0 / 0 |
| B | 90% | 0.0% | 7 | 3,848 | 0 / 0 |
| C | 90% | 87.5% | 7 | 6,025 | 0 / 0 |
| D | 90% | 87.5% | 7 | 6,561 | 0 / 0 |
| E | 100% | 100.0% | 8 | 7,555 | 0 / 0 |
| F | 100% | 100.0% | 8 | 7,546 | 0 / 0 |

E/F均為8/8成功；F未觀察到模型多樣性或品質收益。A用更多Tokens仍有目標缺失；B省Token但必要限制遺漏，被共同安全驗證器阻止。C/D使用較少Token但會漏掉需要個人稱呼的核心案例。B是刻意有損凍結摘要，不能推論所有壓縮方法。

離線矩陣有三種規模×五種預算×六策略，共90列；F的離線列未呼叫模型，指標UNKNOWN。E在10/100/1000專案4K的Top-1均為100%，僅限這組合成辨識案例，不代表真實使用者準確率。

最終LIVE輸出36個實際Markdown成果，SHA與當前目標/限制驗證通過，檔案在benchmarks/results/artifacts/。任務成果是未執行的驗收／接手清單，生成內容仍為CLAIM。

完整API Tokens只來自provider usage；本機檢索估算另列，未重複計入API。LIVE最終矩陣沒有重試或未知usage；整段開發早期兩次400未返回用量，因此全程總量UNKNOWN、已知小計87,333。

MixRoute控制台75筆列示費用小計US$0.035152（6位小數顯示，有四捨五入）；精確invoice UNKNOWN。全程77次請求，保守帳本占用US$0.93813。Codex本身帳單UNKNOWN。

原始資料：[LIVE JSON](../benchmarks/results/live-10-4096-blind.json)、[第一輪](../benchmarks/results/live-10-4096-first-run.json)、[資源](resources.json)、[控制台觀察](billing-observation.json)。

測試檔名blind表示答案僅由evaluator讀取；這組案例已在開發迭代中檢視，並非封存的真正未見測試集。最終效果仍需獨立未見資料驗證。

最終規則重新驗證的跨模型交接：[summary](live-final-cross-summary.json)，auto實際DeepSeek→Fixed Sonnet，新Session原始歷史均0，第二模型收到第一成果內容。兩次usage共3,105 Tokens，精確目標/限制/3項未執行驗收及SHA通過。早期pilot保留原驗證範圍與失敗紀錄。
