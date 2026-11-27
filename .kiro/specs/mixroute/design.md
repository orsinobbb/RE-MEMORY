# MixRoute 固定模型與自動路由：design

## 實作來源

- `app/engines/mixroute.py`
- `app/main.py`

## 資料流與決策

Settings 從本機後端設定讀取。OpenAI-compatible SDK 使用 raw response，取得 provider usage、response ID、x-request-id 與 actual model；SDK 自帶 retry 關閉，模組自己做有限 transient retry。

call() 檢查模式、啟用、價格、池設定、context 與 output limit。成本保留與 model_calls 保存由 Store 管理；錯誤文字與內容中的金鑰字串會遮蔽。

實際 cost_usd 在帳務核對前為 null，cost_source 為 UNKNOWN_PENDING_BILLING_RECONCILIATION；cost_upper_bound 是保守上界，不能當作 billed cost。

人工核准池改為 Simple deepseek-v3.2、Complex／Ultra claude-sonnet-5-5 後，一次 auto 回傳 DeepSeek-V3.2：9 input、2 output、11 total tokens、870.91 ms。這是主代理提供的真實探針紀錄，精確 billing pending。

首次 auto HTTP 400 與舊 OpenAI 模型類型設定不相容；目前池為配置替代方案，官方原因／全部池可用性仍需核驗。

LIVE FIXED 接續 pilot 曾因生成內容改寫必要限制而正確 BLOCKED；prompt／validator 正在補強，不放寬限制。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
