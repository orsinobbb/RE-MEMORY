# 版本化記憶儲存：design

## 實作來源

- `app/storage/database.py`
- `app/schemas/models.py`
- `benchmarks/generators/synthetic.py`

## 資料流與決策

Store 為 SQLite 封裝。資料以 id、user_id、project_id 與 JSON data 保存，主鍵為 (user_id,id)，並設 owner 索引。連線 context manager 負責交易提交與關閉。

TABLES 白名單控制允許的資料物件。模型提供 FactCell、Alias、Task、Artifact 等 Pydantic 型別；其他事件／實驗物件在 P0 以 JSON 保存。

terms() 產生英文詞與中文連續雙字，去重後用 FTS5 搜尋。reindex() 目前將專案名稱、主題與描述建索引；別名另由辨識引擎比對。這是 FTS FALLBACK，不是已校準語意向量索引。

seed() 僅生成合成資料；音訊轉換、鋼琴教材、遊戲與工作管理構成展示情境。舊版目標設 superseded，已完成任務附內容與 SHA256 以供完整性檢查。

deliveries、task_locks 與 cost_ledger 使用獨立 SQLite 表協調交付與成本。spend() 對未知實際費用使用保留上界；它不能把 pending billing 當成已知零。

P0 是單使用者本機原型。長期 migration、外部匯入、多人認證、崩潰後 lock 清理與完整索引成本歸因仍屬後續驗收。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
