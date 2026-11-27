# 意圖與專案辨識：design

## 實作來源

- `app/engines/intent.py`
- `app/engines/entity_resolution.py`
- `app/engines/semantic_dictionary.py`
- `app/engines/scoring.py`

## 資料流與決策

parse_intent() 使用本機規則辨識昨天／ISO 日期、有限主題詞與 CONTINUE／RETRIEVE。它不消耗模型 API，也不是通用語言理解服務。

explicit_target() 先找唯一專案 ID／名稱，再由 confirmed_target() 判定唯一已確認稱呼。matching_aliases() 保留多對多對應，不強制替使用者選擇歧義稱呼。

alias_evidence() 依稱呼狀態與 strength 提供分數；已確認與推論稱呼不同。score_candidate() 隨層級增加可用維度，使用當輪可用權重的正規化值。

候選包括來源文字與負向日期／未完成工作證據。初始權重與閾值為啟發式，尚未取得 dev 調參與嚴格信心校準證據。

辨識輸出只是 Router 的候選與身份關卡；即使明確指向專案，仍需後續必要記憶與預算檢查。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
