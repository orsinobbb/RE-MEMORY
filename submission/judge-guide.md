# 評審導覽

先看README.md啟動本機8791，再依demo-script.md操作。所有資料標DEMO；SIMULATION不消耗API；LIVE只在使用者按執行或明確CLI --run時呼叫。API金鑰只留本機.env，壓縮包不含金鑰。

1. Workspace：輸入「我要你繼續做昨天的音樂專案。」
2. Observatory：觀看LIVE SSE、L0–L5、候選與來源關係。不要把分數當機率。
3. Inspector：必要記憶、目標版本、來源、成果/任務依賴、硬性預算与缺失。
4. Recovery：新的raw_history_count=0 Session；完成任務返回既有成果并保留實際SIMULATION/FIXED/SMART模式。可選尚未完成的鋼琴專案生成新的清單。
5. Memory：查看版本、稱呼、多義關係與真實原文。
6. Benchmark：查看已保存LIVE矩陣或重新跑離線規模矩陣；匯出JSON/已產生的Markdown。

reports/evaluation-summary.md記錄完整比較與限制；reports/resources.json記錄每階段時間/用量，reports/code-review.md記錄獨立審查。最後測試證據在reports/final-verification.json。

reports/live-final-cross-first.json、live-final-cross-second.json、live-final-cross-summary.json是依最新規則驗證的實際成果交接，與只回OK的auto連通性探針區分。最初被阻擋的改寫限制pilot保留為失敗證據。

公开交付頁：https://orsinobbb.github.io/RE-MEMORY/；原始碼：https://github.com/orsinobbb/RE-MEMORY。正式本人旁白與成功投稿紀錄待完成。這是持久化記憶路由原型，交付物是接手清單，未宣稱把MIDI工作本身完成。


最終兩階段交接：Recovery Lab →「讀取已保存示範」，各卡片分別顯示SMART/auto Sonnet與固定DeepSeek、不同空白Session、实际用量及SHA；展開第二模型收到的前一成品可核對持久化交接。報告 reports/final-live-demo.json / final-live-summary.md 与 benchmarks/results/final-live.json 保留20新句型與6Sonnet案例的實際輸出。封裝給新的本機時，可「準備兩階段示範」，使用明確SIMULATION或自行設定MixRoute進行LIVE。
