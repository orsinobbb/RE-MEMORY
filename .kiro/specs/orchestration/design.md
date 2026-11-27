# Session 接續、驗證與交易式交付：design

## 實作來源

- `app/engines/task.py`
- `app/engines/validation.py`
- `app/governance/policy.py`

## 資料流與決策

new_session() 保存空 raw_history 與 previous_session_id 連結，但不讀取或傳入前一原始 buffer。API 不向前端回傳 raw_history。

run() 用 query／mode／model／project_id 做 request fingerprint，查 deliveries 去重，重新 Router 檢索與 build_context，拒絕未知 Session／專案與不完整記憶。

task_locks 以 user/task 唯一鎖及事務內再檢查 status 防止同任務並行交付。finally 釋放自身 lock；process crash 的 stale lock 恢復仍待補強。

SIMULATION 由本機白名單產生繁體中文驗收清單；LIVE 由 provider 生成。validate() 檢查非空、大小、目標／限制／下一步與硬性限制；final validator 正在加嚴，不假稱全面事實查核。

成功 artifact 保存 verification_scope、factual_status=CLAIM、mode 與 SHA256。transaction 同時更新任務、event、snapshot、delivery；ALREADY_COMPLETED 返回先前成果，不重新呼叫模型。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
