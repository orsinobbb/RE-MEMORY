# 本機部署、備份與回復

已驗證 macOS／Python3.12；現行埠8791，不能停止其他專案占用的8000服務。啟動腳本只綁127.0.0.1。`uv sync --frozen --python 3.12` 會按鎖定版本建立環境。

資料庫在 `data/runtime/rememory.db`，模型與應用程式共用預算帳本。切換開發副本時必須沿用帳本，不能將新的零額度檔當成重設成本的方法。`.env` 由使用者本機管理，備份程式不包含金鑰。

```sh
.venv/bin/python scripts/backup.py
```

這會透過 SQLite backup API 產生一致快照到 `data/backups/`。回復前先停止自己的 RE:MEMORY 服務，保存當前資料庫，將指定快照複製到 runtime 原檔名後重新啟動；不得覆蓋唯一備份。正在執行的未知請求需查核供應商紀錄，不能自行將 cost_ledger 清空。

```sh
.venv/bin/python scripts/package.py
```

封裝只包含原始碼、鎖定依賴、規格、測試、合成結果與提交文件；排除 .env、金鑰、runtime／備份、private 截圖、虛擬環境與cache，並對封裝內容做金鑰字串掃描。壓縮包在 `dist/`，不會自動上傳。

可執行原型只綁本機loopback，尚未提供多使用者登入或對外API服務。另已準備HTTPS私人靜態交付頁，提供實測回放與來源包下載。公開部署與投稿依 V5 §20 需要使用者另行指定與授權，尚未執行。本機API若要對外服務，需另外配置認證、TLS、host/origin、防濫用、備份保存政策與合成資料外的資料匯入審查。
