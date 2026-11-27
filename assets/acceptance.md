# RE:MEMORY 最終版本驗收

程式與私人交付的本輪驗收通過。範圍是合成資料、本機單使用者原型、持久化記憶與 Markdown 接手清單。最新主要 Demo 已包含參賽者本人錄音；公開評審入口已上線，尚未取得競賽投稿成功回條。此結論不代表全部 V5 研究驗證完成。

## 公開交付狀態

作品頁：[RE:MEMORY](https://orsinobbb.github.io/RE-MEMORY/)；原始碼：[GitHub](https://github.com/orsinobbb/RE-MEMORY)。目前為記憶找回與任務接續，尚未支援聊天式多輪對話。最新單頁 SMART／auto 實測回傳 DeepSeek-V3.2，新增1次呼叫／925Token，成果下載 SHA、空白 Session、桌機／手機與重播零追加呼叫通過；累計118次生成嘗試／129,955已知Token，仍有2次早期用量未知。詳見 [單頁實測](quick-flow-live.json)、[審查](quick-flow-review.md) 與 [資源紀錄](resources.json)。下方保留18:15開始的歷史驗收與當時用量。

## 本輪實際驗證

- `.venv/bin/python -m pytest -q -rA`：122 passed，1 項上游 Starlette/httpx 警告。
- 在獨立停用 LIVE 的合成資料庫，重跑六視圖 smoke、兩階段交接與記憶修正 Playwright 流程；桌面 1440／手機 390 通過，沒有新增 API 呼叫。
- SQLite 在線備份到獨立還原庫，`integrity_check=ok`，呼叫／費用／預算窗口紀錄相符。
- 來源 ZIP 解壓到暫存資料夾，用 `.env.example` 和本機依賴快取實際執行 `./start_mac.sh`；獨立 8795 埠健康檢查、LIVE 停用／零呼叫通過。原 `.env` 與原資料庫未替換。
- 已保存 LIVE 證據：Sonnet → DeepSeek，兩個空白 Session；前一成品完整內容與 SHA 進入下一模型上下文。固定 20 句型 E/F 各 16 成品與 4 停止案例；6 個 Sonnet 子集成品。38 份成品 SHA 及 8 次預期停止核對通過。
- 私人靜態交付：兩階段切換、完整前件、3 列比較、下載、149.84 秒影片 seek／播放及桌面／手機無水平溢位通過。新的 IAB 本機頁已顯示連線正常。

## MixRoute 用量與時間

本輪驗收新增 0 呼叫、0 模型 Token、US$0 新增模型費用。原帳本仍為 117 次生成嘗試、129,030 已知 Token、2 次早期未知用量、US$1.35510 未結清保守保留額。Codex 的精確 Token／帳單沒有可用數據，保持 UNKNOWN。

最後 LIVE 開發的 40 次呼叫（41,697 Token）已與 MixRoute 控制台模型／input／output 多重集合逐筆相符。控制台參考小計 US$0.038070，單列四捨五入且不是正式發票，未用此數字釋出原保留額。[核對紀錄](console-final-live-reconciliation.json)。

驗收開始 2026-11-27 18:15:47（台北），本輪各階段實際時間及累計主動工作時間見 [resources.json](resources.json)，等待使用者錄音的時間不納入主動工作。

## 60 項規格追溯

PASS 為上述原型範圍內已驗證；PARTIAL 直接列出尚未完成的部分。每項可對應本輪重跑的測試入口與保存證據。過往 reports 留存當時的歷史結果，最新狀態以本表為準。

| 需求 | 狀態 | 驗收範圍／證據 |
|---|---|---|
| BUD-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| BUD-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| BUD-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| BUD-04 | PASS | 最後40次 usage與控制台逐筆模型／輸入／輸出多重集合相符；累計兩筆早期用量仍未知。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| BUD-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| BUD-06 | PASS | 控制台參考小計 US$0.038070 不作發票；原帳本 US$1.35510 未結清保留額不釋出。 [test_context.py](../tests/test_context.py)、[test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| COV-01 | PARTIAL | 已核驗宣告的直接 fact／task／artifact 依賴；任意遞迴依賴圖的完整閉包未完成。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| COV-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| COV-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| COV-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| COV-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| COV-06 | PASS | 只覆蓋已知必要記憶；生成成果仍為 CLAIM。 [test_context.py](../tests/test_context.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py) |
| EVA-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-02 | PARTIAL | dev／blind 標籤與 evaluator 答案隔離已驗證，但舊案例已參與迭代，沒有真正封存盲測。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-03 | PASS | 已保存 3 規模 × 5 預算 × 6 策略＝90 離線列；F 離線不執行模型。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-06 | PASS | 既有 A–E 同固定 DeepSeek、F auto；最後新增 E/F 固定20句型和6個 Sonnet 子集。F 實際均為 DeepSeek，無品質提升結論。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| EVA-07 | PARTIAL | 矩陣與 LIVE 已測；完整元件消融、獨立未見資料和正式 billed cost 尚未完成。 [test_evaluation.py](../tests/test_evaluation.py)、[test_baselines.py](../tests/test_baselines.py)、[test_live_evaluation.py](../tests/test_live_evaluation.py)、[test_final_live.py](../tests/test_final_live.py)、[final-live.json](../benchmarks/results/final-live.json)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| IFR-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-06 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-07 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| IFR-08 | PASS | 本輪重跑六視圖、兩階段和記憶修正，桌面1440／手機390；IAB 新頁已確認本機連線。 [test_api.py](../tests/test_api.py)、[browser_smoke.mjs](../tests/browser_smoke.mjs)、[browser_live_demo.mjs](../tests/browser_live_demo.mjs)、[browser_memory_repair.mjs](../tests/browser_memory_repair.mjs)、[delivery-verification.json](../reports/delivery-verification.json) |
| MIX-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| MIX-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| MIX-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| MIX-04 | PASS | requested／returned allowlist 與 stage2 不同實際模型驗證已通過。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| MIX-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| MIX-06 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_mixroute.py](../tests/test_mixroute.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[final-live-demo.json](../reports/final-live-demo.json)、[console-final-live-reconciliation.json](../reports/console-final-live-reconciliation.json) |
| STO-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-06 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| STO-07 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_storage.py](../tests/test_storage.py)、[test_evolution.py](../tests/test_evolution.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[DEPLOYMENT.md](../DEPLOYMENT.md) |
| RES-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RES-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RES-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RES-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RES-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RES-06 | PASS | 未校準信心保持 UNKNOWN；沒有真實使用者校準。 [test_retrieval.py](../tests/test_retrieval.py)、[test_evolution.py](../tests/test_evolution.py)、[final-live.json](../benchmarks/results/final-live.json) |
| RET-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-06 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| RET-07 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_retrieval.py](../tests/test_retrieval.py)、[test_graph.py](../tests/test_graph.py)、[test_baselines.py](../tests/test_baselines.py)、[test_api.py](../tests/test_api.py)、[evaluation-summary.md](../reports/evaluation-summary.md) |
| ORC-01 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-02 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-03 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-04 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-05 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-06 | PASS | 交易及 SHA／目標／逐字限制／3項清單驗證，不代表語意全部正確或清單已執行。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |
| ORC-07 | PASS | 合成資料、本機單使用者原型；依本輪重跑測試及已保存 LIVE 證據驗證。 [test_tasks.py](../tests/test_tasks.py)、[test_hardening.py](../tests/test_hardening.py)、[test_live_demo.py](../tests/test_live_demo.py)、[test_memory_repair.py](../tests/test_memory_repair.py)、[final-live-demo.json](../reports/final-live-demo.json) |

## 交付物

| 項目 | 驗收 |
|---|---|
| 原始碼、鎖定依賴 | 已準備；來源 ZIP 另附 SHA256SUMS |
| 一鍵啟動 | macOS 實際解壓啟動通過；Windows 腳本未原生實測 |
| 六視圖本機 UI | 實際瀏覽器流程通過 |
| MixRoute FIXED／auto | 真實生成、授權池、預算、重播與跨模型交接通過 |
| 合成資料／版本／稱呼／來源 | 10／100／1000 專案及記憶修正通過 |
| A–F 對照 | 90 離線列、既有六策略 LIVE；完整元件消融待做 |
| Token／費用紀錄 | 已知小計與 UNKNOWN 分開；正式帳單待核對 |
| 測試與結果 | 122 pytest＋真實瀏覽器＋保存 LIVE JSON／MD |
| 架構說明 | [design.md](../docs/design.md) |
| 作品說明 | [project-description.md](../submission/project-description.md) |
| Demo 腳本／本人逐句稿 | 已準備；最新約99.93秒影片已包含本人錄音 |
| 評審導覽 | [judge-guide.md](../submission/judge-guide.md) |
| 已知限制 | [known-limits.md](../submission/known-limits.md) 及本表 PARTIAL |
| 秘密排除／私人交付 | 來源／證據包排除 .env、runtime、backups；GitHub Pages 靜態作品頁已公開 |

最新主要 Demo 為約99.93秒的參賽者重新錄製操作影片，已包含本人聲音，具有 H.264 影像與 AAC 音軌。轉成 MP4 後影音資料核對一致；正式競賽收件狀態仍待主辦確認。公開作品頁：[RE:MEMORY](https://orsinobbb.github.io/RE-MEMORY/)。程式使用 loopback，沒有部署公開付費後端。
