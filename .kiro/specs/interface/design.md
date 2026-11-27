# 六視圖可觀察介面與 API：design

## 實作來源

- `app/main.py`
- `frontend/index.html`
- `frontend/style.css`
- `frontend/app.js`
- `docs/api-contract.md`

## 資料流與決策

FastAPI 同源服務 index.html、style.css、app.js 與 /api/*，提供 local-origin／TrustedHost 防護與 CSP。公開部署身份、跨主機設置不是目前驗收。

原生 HTML/CSS/JS 不使用外部網路資產；圖表／關係圖用 native SVG。DOM helper 全程以 textContent 處理 imported values。

Workspace 的 query／budget 驅動檢索。fetch streaming 解析 round／result，最終結果共享給 Context；fallback 明確 SAVED REPLAY。

Recovery建立session後再execute，前端只使用已回傳模型目錄與設定。模型目錄不證明授權池；provider最終阻擋理由要如實顯示。

Benchmark POST live:false，結果 table／bars 來自response；導出路徑只指向 backend 保存的 result／artifact。Null成本與成功指標保留UNKNOWN。

browser_smoke.mjs 用已有Playwright／browser，不自起服務器或付費。最初RED停在8000健康檢查非本服務；actual integration pending final run。

## 實作依據與限制

以目前原始碼與對應測試為準。完整實驗、提供者回傳、帳務與介面證據須由最終實測補齊；未量測值保留 UNKNOWN。參閱 submission/known-limits.md。
