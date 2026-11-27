# RE:MEMORY — Adaptive Memory Router

AI 可以忘記，但人類的努力不能歸零。

OPEN LAB 2026 本機可操作原型。用低成本索引、個人語意字典、來源關係與必要記憶檢查，從空白 Session 找回工作；實際交付物為繁體中文 Markdown 驗收／接手清單，不宣稱已完成音訊轉換程式或清單中的測試。

## 公開交付

- 作品頁：https://orsinobbb.github.io/RE-MEMORY/
- 原始碼：https://github.com/orsinobbb/RE-MEMORY
- 下載：[完整原始碼](https://orsinobbb.github.io/RE-MEMORY/assets/RE-MEMORY-source.zip)／[實測證據](https://orsinobbb.github.io/RE-MEMORY/assets/RE-MEMORY-evidence.zip)

目前功能是「記憶找回與任務接續」：使用預載合成專案，找回當前目標與限制，確認後由 MixRoute 產出 Markdown 驗收／接續清單。尚未支援聊天式多輪追問、對話歷史累積或私人聊天匯入。作品頁提供保存實測與下載；互動原型需在本機啟動。

GitHub 與公開作品頁已準備。最新主要 Demo 約99.93秒，為參賽者重新錄製、包含本人聲音的三步驟操作影片；[播放／下載有聲 Demo](https://orsinobbb.github.io/RE-MEMORY/assets/participant-demo-voiced-20261128.mp4)。影片為原始錄影轉成 MP4，影音資料核對一致，沒有 AI 配音；先前[獨立旁白](https://orsinobbb.github.io/RE-MEMORY/assets/participant-voice.m4a)保留為備份。尚未取得競賽正式收件確認。

## 啟動

需要 Python 3.12 與 [uv](https://docs.astral.sh/uv/)。解壓來源包或 clone 儲存庫後，進入專案根目錄；macOS：

```sh
./start_mac.sh
```

Windows 執行 `start_windows.bat`。Windows 腳本已準備，尚未在 Windows 主機實測。瀏覽器開啟 `http://127.0.0.1:8791`；`.env` 的 `APP_PORT` 可改成本機未占用的埠。可執行原型只綁定 loopback；公開網站僅提供靜態實測與下載。

第一次將 `.env.example` 複製成 `.env`，金鑰只填入本機檔案。`MIXROUTE_ENABLED=false` 時可使用全部本機檢索與 SIMULATION。填好一般／Smart Key、價格上界、授權模型池後才啟用 LIVE。當前已驗證入口為 `https://api.mixroute.ai/v1/chat/completions`，Smart 的 model 為 `auto`；相容池為 Simple＝deepseek-v3.2、Complex／Ultra＝claude-sonnet-5-5。

## 使用

首頁現在只需三步：

1. 輸入「請接續鋼琴樂理教材，完成目前尚未完成的驗收清單。」並按「找回工作脈絡」。搜尋後留在首頁。
2. 確認顯示的專案、目標與限制，選 MixRoute 自動選模（SMART）或本機示範，再按確認接續。系統自動建立空白 Session。
3. 同一頁查看並下載 Markdown 成果。SMART 使用 model=auto；已完成任務讀取既有成果，不重複生成。

修改需求或預算後需重新搜尋。尚未辨識或必要記憶不足時不能接續。左側研究頁保留詳細記憶、檢索、完整性、兩階段示範與測試資料。

單頁真實驗收已由 SMART／auto 回傳 DeepSeek-V3.2，925Tokens，1次呼叫；空白 Session、下載 SHA、重播零追加呼叫及桌機／手機通過。詳見 [單頁實測](reports/quick-flow-live.json) 與 [審查](reports/quick-flow-review.md)。

## 驗證與實驗

```sh
.venv/bin/python -m pytest -q
REMEMORY_BASE_URL=http://127.0.0.1:8791 node tests/browser_smoke.mjs
.venv/bin/python -m benchmarks.run --count 10
.venv/bin/python -m benchmarks.run --count 100
.venv/bin/python -m benchmarks.run --count 1000
.venv/bin/python -m benchmarks.live --count 10 --budget 4096 --max-cases 10 --run
```

pytest 與瀏覽器 smoke 不呼叫真實模型。瀏覽器腳本使用 Playwright；此電腦已有 bundled runtime，其他電腦可安裝 Playwright 並設定 `PLAYWRIGHT_MODULE_PATH`／`PLAYWRIGHT_CHROMIUM_EXECUTABLE`。所有 paid trials 共用應用程式的 SQLite 預算帳本，不可另開帳本繞過上限。

離線矩陣包含 10／100／1,000 專案、1K／2K／4K／8K／16K。F 離線列保持 UNKNOWN。LIVE 已實測既有十個固定合成案例、六策略、4K；A–E 使用相同 DeepSeek，F 使用 auto，實際也全部路由到 DeepSeek。跨模型交接另外由 DeepSeek → Sonnet 實測，不能據此宣稱 Smart Routing 有模型品質提升。

結果見 [實驗摘要](reports/evaluation-summary.md)、[LIVE JSON](benchmarks/results/live-10-4096-blind.json)、[實際成果](benchmarks/results/artifacts/)、[資源紀錄](reports/resources.json)。初始失敗與第一輪結果保留；不預設新架構必定勝出。B 是刻意有損的凍結摘要，不代表所有摘要方法。

## 架構與限制

FastAPI + SQLite FTS5 + Pydantic + OpenAI 相容 SDK；前端原生 HTML／CSS／JS，SVG 圖表無外部資產。`FTSSearch` 是可替換介面，目前沒有下載 embedding 模型，不把 FTS 稱為向量檢索。

必要依賴和事實均驗證 owner、有效時間、信任、衝突、來源支持；來源或成果缺失會阻止呼叫。輸出驗證目前涵蓋 Markdown 結構、當前目標、逐字限制、三個未執行驗收項及 SHA。生成文字仍是 CLAIM，沒有全面事實查核。搜尋權重與信心未做真實使用者校準。

`MemoryEvolution` 的來源支持版本更新、稱呼確認及成果失效已接入 Memory Explorer。介面修正內容必須直接出現在所選既有可信來源；目前沒有新增來源或私人資料匯入功能。保存新記憶會保留歷史、使該專案成品失效，並清除畫面上過期脈絡。重新驗證會建立新 Markdown 成品與 SHA，保留原內容及工作完成狀態，更新目前成品指標；只驗證格式、目前目標與限制，仍為 CLAIM。過期審查、來源不足或執行中的專案會阻止儲存。舊 idempotency key 保留原交付紀錄，失效後需新請求，不自動重做已完成任務。工作／請求鎖有 300 秒租期；中斷結果先回報需明確重試，未知 API 保留額不自動歸零。

記憶修正的瀏覽器驗證使用獨立合成資料與停用付費設定：先執行 `.venv/bin/python -m tests.serve_memory_repair --port 8792`，再執行 `node tests/browser_memory_repair.mjs`。測試不修改原展示資料或共用費用帳本。

Token 索引／檢索／驗證在本機執行，不產生模型 Token。cl100k 為打包估算；完整 API Token 只用供應商回傳，任何未知／重試缺失都顯示 UNKNOWN，同時提供已知小計。控制台列示費用有四捨五入，精確帳單 UNKNOWN。當前執行額度閘門 US$5、常規硬上限 US$35，保留 US$15，不自動儲值。Codex 本身帳單無可用數據。

參閱 [本機部署／備份](DEPLOYMENT.md)、[評審導覽](submission/judge-guide.md)、[三分鐘 Demo](submission/demo-script.md)、[已知限制](submission/known-limits.md)。

測試檔名blind表示答案僅由evaluator讀取；這組案例已在開發迭代中檢視，並非封存的真正未見測試集。最終效果仍需獨立未見資料驗證。


## 11/27 最終兩階段示範

Recovery Lab新增「兩個模型，接續同一份努力」。新來源包可先準備合成專案；選SIMULATION測本機流程，或設定MixRoute後選LIVE：第一階段SMART／auto，第二階段要求另一授權模型。每階段使用新的空白Session，第二階段模型上下文包含完整前一成品。已完成階段讀取保存紀錄，不重設任務或費用。實際回傳同一模型會阻止第二階段完成。

已保存實測：auto選到Sonnet，再以固定DeepSeek接續；2,732Tokens。固定20新句型的E/F各16任務與4停止案例通過，另6個預選Sonnet案例通過。F在新案例實際生成全部選DeepSeek；結果不證明auto提升品質。新句型使用既有合成來源，沒有調整路由或答案，並非封存盲測。完整紀錄在 [最終實測報告](reports/final-live-summary.md) 與 [固定案例JSON](benchmarks/results/final-live.json)。

最終122項pytest通過；兩項獨立審查問題已以重現測試修正，詳見 [審查與修正](reports/final-code-review.md)。公開靜態交付頁與約99.93秒的本人有聲Demo已準備；[逐句稿](submission/voiceover-final-draft.md) 與 [投稿欄位草稿](submission/final-form-draft.md) 已備妥。GitHub 原始碼與靜態交付已獲本人授權公開；競賽正式收件狀態仍待主辦確認。

公開交付頁：[RE:MEMORY](https://orsinobbb.github.io/RE-MEMORY/)；公開原始碼：[GitHub](https://github.com/orsinobbb/RE-MEMORY)。提供保存實測、靜音影片預覽和來源包下載；可執行原型仍由來源包啟動本機 API。

最新驗收見 [60 項追溯與交付驗收](reports/acceptance.md)；本輪 122 pytest、記憶修正瀏覽器、備份還原與 macOS 解壓啟動通過。最新主要 Demo 已包含參賽者本人錄音。

瀏覽器工具可使用 `npm install --no-save playwright` 安裝，再執行 `npx playwright install chromium`；已有 Chrome 可透過 `PLAYWRIGHT_CHROMIUM_EXECUTABLE` 選擇執行檔。`PLAYWRIGHT_MODULE_PATH` 可指定本機已安裝模組，來源不包含個人電腦路徑。
