# Security scope

RE:MEMORY is a local prototype with synthetic retrieval examples and user-entered chat. The public delivery page serves saved demonstration records, video and source downloads; it has no paid inference endpoint or personal-data upload form.

The FastAPI prototype uses one local demo identity and is not a production authentication system. Keep its binding at `127.0.0.1`; do not expose it with a public proxy or change it to `0.0.0.0` without adding authentication, access control, rate limits and an independent deployment review.

MixRoute credentials belong only in the local ignored `.env`. Source archives exclude `.env`, runtime databases, backups and private attachments. New records intended for publication must contain synthetic data and pass credential and privacy checks.

Model-generated artifacts remain CLAIM. Source/constraint checks, cost reservations and task idempotency are safeguards within the documented prototype scope, not a claim of complete semantic validation or penetration-test certification.

Do not post credentials or private user data in public issues.

聊天訊息會傳送至 MixRoute，並保存在本機 SQLite；公開網站不提供聊天後端。候選記憶僅驗證來源引用，不代表外部事實已查核。「忘記」停止載入該筆記，本機歷史與版本仍保留。原始聊天、執行資料庫與私人開發回覆不公開。
