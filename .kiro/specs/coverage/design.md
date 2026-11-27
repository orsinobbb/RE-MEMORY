# 必要記憶與完整性：design

## 實作來源

- `app/engines/coverage.py`
- `app/engines/context_builder.py`

## 資料流與決策

check_coverage() 讀目前 facts 與 tasks，檢查必要類型、有效時間、verification、trust 與 evidence。coverage 為已覆蓋必要專案／required 清單，不是搜尋命中率。

task dependency 及 completed task artifact 列入 required。先前成果以內容 SHA256 比對並檢查同專案與 verified 狀態。

build_context() 產生 manifest、loaded／not_loaded、missing／conflicts／faults 與 memory snapshot 雜湊。缺失檢查後仍未解決的 fault 標記 resolved=false。

情境包含目前必要 facts、任務／完成狀態與來源。SYSTEM 指令把來源視為資料，禁止來源改變權限；未核實來源使 context 不可行。

P0 supplement 是現有持久化資料的必要讀取與檢查。跨外部原始文件補讀、一般化依賴閉包與獨立外部真實性查核尚未全面驗證。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
