# 持續聊天與 MixRoute 記憶實作計畫

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 由 MixRoute 實際協助開發，新增可保存多輪對話與可追溯記憶的本機入口。

**Architecture:** 獨立 ChatEngine 和 routes，不更動原有 Orchestrator。SQLite 新增表保存歷史、候選記憶與送出鎖；前端新聊天頁沿用本機 Origin/CSP。

**Tech Stack:** Python 3.12、FastAPI、SQLite、原有 MixRoute adapter、原生 JavaScript/CSS。

**Spec:** docs/superpowers/specs/2026-11-28-mixroute-chat-memory-design.md

## Global Constraints

- 介面全部繁體中文，動態資料用 textContent。
- 金鑰、私人回覆、真實聊天資料庫不提交；原 .env 與預算帳本不重設。
- 新記憶來源只限本次使用者訊息；來源引用為連續原文，最多四項、每項 500 字。
- system、本輪訊息與已確認 CONSTRAINT 不截斷。
- 預設 SMART/auto、4K context、1,536 輸出與 128 餘裕；聊天鎖 300 秒。
- 不改原三步驟、驗收/FACT/evaluator，不加入 shell 或私人檔案工具。

## Review Focus

- 逾時舊請求回來時不能覆寫新 owner 的聊天或記憶。
- 模型偽造其他訊息引用，不應造成候選記憶。
- 同 key 搭配改變模型、預算或內容，不應重用或重複付費。
- 刪去舊回合不能讓使用者訊息與錯誤助理答案配對。
- 忘記後新聊天不應載入該記憶，也不應從舊歷史重抽候選。

---

### Task 1: 聊天回覆、context 與持久化引擎

**Files:** Create app/engines/chat.py、app/engines/chat_context.py；Modify app/storage/database.py；Test tests/test_chat.py。
**Interfaces:** ChatEngine(store,provider).create(user,project_id)->dict；state(user,project_id)->dict；conversation(user,id)->dict；send(user,id,content,key,mode='SMART',model=None,budget=4096)->dict；mutate(user,id,action,content=None)->dict。parse_reply(record,source)->(reply,memories,warnings) 與 build_context(content,source_id,history,memories,budget)->(messages,metadata)。

- [ ] Step 1: tests/test_chat.py 建立 fixture 真實 SQLite + mock HTTP provider，撰寫 test_persistent_chat_and_cross_conversation_memory、test_rejects_forged_sources、test_scope_and_user_isolation、test_idempotency_and_conflict、test_concurrent_send、test_stale_memory、test_expired_owner_cannot_commit、test_context_budget_and_constraints、test_invalid_reply_and_partial_memory、test_forget_not_reextracted。驗收呼叫數以真實 model_calls/ledger 與保存訊息判斷。
- [ ] Step 2: Run `.venv/bin/python -m pytest tests/test_chat.py -q`，用原 repo 的 interpreter；Expected: 缺少 ChatEngine 的測試失敗。
- [ ] Step 3: 寫唯讀規格摘要並透過原 MixRoute 帳本取得 parse_reply 草稿，將回覆留私人目錄，檢視不可信內容後自行整合符合上述介面的引擎與 additive tables。Expected: key 未輸出；實際 call receipt 保存。
- [ ] Step 4: Run 同 Step 2；Expected: 全數通過。
- [ ] Step 5: Commit 引擎、測試與設計/計畫文件，排除任何 .env / 私人回覆。

### Task 2: API 與聊天入口

**Files:** Create app/chat_routes.py、frontend/chat.js；Modify app/main.py、frontend/index.html、frontend/app.js、frontend/style.css；Test tests/test_chat_api.py、tests/browser_chat.mjs。
**Interfaces:** mount_chat_routes(app,store,provider) 註冊 spec endpoints 與 /chat.js。前端使用現有 api/el/navigate；boot 後 initChat() 讀 project/model metadata 與保存資料。

- [ ] Step 1: 撰寫 test_chat_api_persistence_and_validation、test_chat_origin_and_private_data；瀏覽器案例驗證建聊天、送訊息、重載、換聊天接續、確認/修正/忘記與 textContent 防注入。
- [ ] Step 2: Run `.venv/bin/python -m pytest tests/test_chat_api.py -q`；Expected: 404/缺少路由。
- [ ] Step 3: 實作 POST 驗證、錯誤碼、7 個聊天 endpoints，預設 #chat 並保留 #workspace。送出期間停用範圍/聊天/模型/輸入，錯誤顯示原訊息 FAILED，不自動重試；client 保存 pending key，回應失聯時重送同 key。記憶卡顯示候選狀態、原引用、確認、文字編輯及忘記說明。所有文字用 textContent。
- [ ] Step 4: Run API 測試、瀏覽器案例，Expected: 介面持久化與隔離通過；Run 全 pytest，Expected: 原功能回歸通過。
- [ ] Step 5: Commit API/UI 與測試。

### Task 3: 真實 MixRoute 驗收、文件與交付

**Files:** Modify README.md、docs/api-contract.md、reports/progress.md、reports/resources.json；Create reports/chat-memory-acceptance.json。
**Interfaces:** 原 Settings/.env + 原 Store(data/runtime/rememory.db) 僅用於付費驗收；worktree 程式載入原帳本。報告只含合成資料與非機密用量。

- [ ] Step 1: 在原帳本建立合成專案/聊天，真實兩輪訊息及新聊天回想，最多三筆；Expected: 保存來源記憶、回應新聊天、模型實際名稱/Token/保守費用收據，不宣稱 billing 已知。
- [ ] Step 2: 若 live 未達標，先建立重現測試再修正；Expected: 沒有額度重設或盲目付費重試。
- [ ] Step 3: 更新使用說明、資源與限制；Run 全 pytest + browser syntax + secrets/繁體掃描；Expected: 通過且 private/.env 不在 diff。
- [ ] Step 4: Commit 驗收與文件，依 executing-plans 對整個分支做一次獨立 review，重要問題以 RED→GREEN 修正。
- [ ] Step 5: 將已驗證功能同步至原本機 RE:MEMORY，保留 .env / SQLite，啟動並用瀏覽器驗證；按既有公開交付授權更新 GitHub 原始碼/作品頁說明，公開匯出不含個人記憶。Expected: localhost8791 使用新入口、公開下載完整、個資金鑰掃描通過。
