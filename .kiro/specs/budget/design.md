# 情境 Token 與成本預算：design

## 實作來源

- `app/engines/budget.py`
- `app/engines/context_builder.py`
- `app/engines/mixroute.py`

## 資料流與決策

tokens() 優先使用 cl100k_base；失敗時使用 UTF-8 byte count。token_method() 明確傳回估算方式，並不聲稱適用所有提供者 tokenizer。

allocate() 計算 parts，增加 output_reserve 與 safety_margin；context_builder 另計 messages／JSON framing 開銷，再判定 feasible。

P0 預留輸出 384、安全餘裕 128，實際值由程式回傳而不是 UI 編造。必要內容即使超預算仍完整保留，任務被阻止。

provider 以 UTF-8 輸入上界與 max_tokens、定價上界計算每次 call reservation，SQLite BEGIN IMMEDIATE 原子檢查已有 committed／unsettled 成本。

開發上限 US$35，外部保留 US$15；目前初始包絡為 US$5。最終 billing 與所有索引／工具成本歸因尚待結算與驗證。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
