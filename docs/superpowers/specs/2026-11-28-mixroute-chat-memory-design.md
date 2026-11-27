# MixRoute 協助開發與持續聊天記憶

人類已明確要求：實際由 MixRoute 協助開發 RE:MEMORY 本身，以及在 RE:MEMORY 裡持續對話並產生記憶。以下架構與數值是實作者依現有程式決定的預設。

## 成果與邊界

新增「聊天與記憶」首頁；原有「接續工作」三步驟與所有檢索、驗收、去重契約保留。使用者選擇個人記憶或既有專案，建立聊天、持續送訊息、重新整理後讀回歷史；同範圍的新聊天能使用保存記憶。這次不新增程式檔案修改工具、shell、私人檔案掃描或自動部署。

MixRoute 已完成兩筆設計協助：第一筆 auto/Sonnet 截斷且內容空白（15,497 Token）；第二筆 DeepSeek 提供可用獨立聊天設計（906 Token）。後續請 DeepSeek 提供回覆驗證函式草稿，人工檢視後整合，不執行模型提供的命令。實測、開發皆沿用原有預算帳本、授權池、價格上限；不重設額度。

## 資料與 API

新增白名單 JSON 表 conversations、chat_messages、chat_memories、chat_requests，以及獨立 chat_locks。沿用 owner/project 分隔與 SQLite，新增表不修改原始事實、成果、任務與費用資料。個人範圍固定 PERSONAL；其他範圍必須是該本機使用者 demo 的既有專案。

GET /api/chat?project_id=PERSONAL 回傳該範圍聊天與記憶。POST /api/chat/conversations 建立聊天。GET /api/chat/conversations/{id} 回傳歷史與該範圍記憶。POST /api/chat/conversations/{id}/messages 接收 content、idempotency_key、mode（SMART 或 FIXED）、model、budget；預設 SMART/auto，4K context，輸出預留 1,536 Token。POST /api/chat/memories/{id} 接收 action（CONFIRM、EDIT、FORGET）及 EDIT 文字。

## 記憶來源

每次模型回覆使用 JSON {reply, memories:[{kind,content,source_message_id,source_quote}]}。新記憶來源只限本次使用者訊息；source_quote 必須是該訊息的連續原文片段。最多四項、每項最多 500 字，kind 為 GOAL、CONSTRAINT、DECISION、PREFERENCE、NOTE。

自動整理的項目是 CANDIDATE，不是已驗證事實；同專案新聊天可載入並明示候選狀態。使用者可確認、修正、忘記。修正保留版本歷史與原始引用，標示為使用者編輯，確認不改動原有 evaluator/FACT。忘記是 tombstone，不再載入；歷史不刪除，介面明說。候選不自動重新抽取舊歷史；完全相同內容去重，包含已忘記項目。

## 呼叫與一致性

一筆送出只做一筆應用層呼叫，provider 既有網路重試與費用保留規則不變。回覆空白、截斷或主 JSON 無效，不保存假的助理回覆；有效 reply 搭配無效記憶時保留 reply、略過無效記憶並警告，不額外付費重試。

同 key 同請求重播已保存結果，不多呼叫；同 key 不同內容阻擋。每個聊天鎖 300 秒，保存使用者訊息、request 與 lock 的交易不可分割；同時送出阻擋。失敗訊息保存 FAILED 狀態；人工再次送出是新的一輪，介面不自動重試。逾時鎖可接手，但舊 owner 永遠不能提交。模型呼叫中記憶若被確認、修正或忘記，提交前 snapshot 檢查阻擋過期結果，已產生費用仍保留。

## Context 與隱私

system、本輪訊息與已確認 CONSTRAINT 不截斷；超出 context 時先阻擋，沒有付費呼叫。其餘依相關性與確認狀態選最多 12 項記憶，加入最近完整成功聊天回合；超限時捨棄最舊回合。API 顯示載入記憶、歷史與本機 Token 估算。全訊息 + 1,536 輸出 + 128 餘裕不得超過所選 budget 或 provider context_limit。

介面全部繁體中文，動態資料用 textContent。提示「訊息會傳送至 MixRoute，並保存在這台電腦。」保留現有 loopback、Origin、CSP 與金鑰遮罩。聊天資料庫與私人開發回覆不放 GitHub。忘記不等於刪除本機歷史或撤回已傳送給供應商的資料。

## 驗收與資源

測試持久化、跨聊天記憶、owner/project 隔離、引用偽造、格式錯誤、空白截斷、同時送出、同 key 重播、過期鎖、記憶變更、context 上限與傳統流程回歸。獨立瀏覽器驗證送出、重載、確認、修正、忘記。使用原帳本做合成內容的兩輪對話與新聊天回想（至多三筆新呼叫）。估計剩餘 60–90 分鐘、MixRoute 額外保守上限 US$1；實際時間、已知 Token、費用 UNKNOWN 與保守上限分階段記錄。
