# Final LIVE submission implementation plan

> Execute inline using superpowers:executing-plans; one fresh whole-change review at the end. Human approved the assessed scope and requested continuous completion.

**Goal:** Deliver an operable MixRoute two-stage handoff, fixed prospective evaluation, and reviewable competition materials with human narration.

**Architecture:** Keep the existing FastAPI/SQLite/vanilla UI. Add one independent synthetic two-task project; preserve all old tasks and artifacts. All paid providers share the original ledger and a persistent extra-US$3 window. Stage 2 consumes a verified stage-1 artifact in a new session, using an actual different authorized model. Static delivery contains sanitized evidence/source downloads and an actual recording, without a paid backend.

**Tech Stack:** Python3.12, FastAPI, SQLite, pytest, Playwright, static HTML/CSS/JS, native Sites hosting when prepared and authorized.

**Spec:** reports/final-version-assessment.md; docs/project-v5.txt; AGENTS.md; official 2026-11-25 competition rules. Current start16:19 Asia/Taipei leaves7h40; prioritize core/recording and freeze behavior by18:00.

## Global constraints

Synthetic data only; do not print .env/keys or change its credentials. Existing data and completions persist. Initial total gateUS$5; new windowUS$3; hardUS$35 and outside reserveUS$15 remain. Unknown billing stays UNKNOWN. No new zero-budget ledger. No private imports, arbitrary shell tools, broad features, public paid backend, automatic submission or publicity without final explicit approval. Human real voice is required; never synthesize or clone it.

## Review focus

- Concurrent stage clicks must not execute the wrong next task or duplicate a completed stage.
- Budget window remains effective across provider instances/processes and preserves unknown reservations.
- Stage2 refuses missing/tampered/stale prior artifact or unverified current facts.
- UI distinguishes fresh LIVE generation, stored LIVE replay and SIMULATION; actual model may differ from requested auto.
- Static delivery excludes keys, runtime/session/private data and does not overstate scope/results.

## Task 1: Persistent paid window and operable handoff

Files: app/storage/database.py, app/engines/mixroute.py, app/engines/task.py, app/engines/coverage.py, app/engines/live_demo.py, app/main.py, frontend/index.html, frontend/app.js, frontend/style.css, tests/test_live_demo.py, tests/browser_live_demo.mjs.

Interfaces: Store.start_budget_window(id, extra_limit=3); reservation uses the active ceiling atomically. LiveDemo.prepare(user='demo') and run(stage, mode, idempotency_key, user='demo') reuse one synthetic project and always fresh sessions. GET /api/demo; POST /api/demo/prepare; POST /api/demo/run. Stage1 SMART/auto, stage2 FIXED an authorized model different from stage1 actual response; SIMULATION available only as clearly labeled local testing. Orchestrator request task_id constrains expected active task. Context covers depends_on_task_ids and prior artifact.

- [x] Write and run failing tests for window persistence/concurrency, non-resetting prepare, ordered stage dependency, duplicate stage clicks, wrong-task requests, source/prior-artifact rejection and actual prior content in stage2 messages. Expected: missing feature failures.
- [x] Implement bounded window, demo engine and APIs, preserving original storage/ledger.
- [x] Run targeted/full pytest. Expected: pass; no paid calls.
- [x] Add accessible Recovery Lab demo panel showing real returned model/usage, prior content/hash and stored versus new generation. Test two stages with SIMULATION and no overflow.
- [x] Activate persistent final window on original ledger and run actual SMART→different FIXED demo. Expected: current goals/constraints/checklist/hash pass, two empty sessions, prior content included, no duplicate call on replay. Save actual outputs.
- [x] Commit implementation and evidence.

## Task 2: Fixed prospective evaluation and bounded LIVE comparison

Files: benchmarks/generators/final-cases.json, benchmarks/final_live.py, tests/test_final_live.py, benchmarks/results/final-live.json, reports/final-live-summary.md.

Interfaces: Freeze20 newly written cases before tuning or live execution. Each case has id/query/expected_project/expected_outcome, evaluator-only. Same synthetic source setup and4K budget for E/F;16 actionable cases plus4 expected stops, plus up to6 authorized Fixed-other-model comparisons. Shared provider/paid window; cap60 attempts overall and retain failures. Persist result/artifacts and immutable case-set hash. No genuine sealed-blind claim.

- [x] Create/hash fixed20 cases and meaningful evaluator tests; run failing tests before implementation.
- [x] Implement evaluator with target/stop success, unknown usage accounting, replay duplicate checks, reserved-cost window and no truth in messages.
- [x] Run local fixture tests, then real E/F and limited second-model comparisons. Expected: measured results, not assumed improvement; stop when time/attempt/window ceiling reached.
- [x] Save exported actual Markdown and concise comparative report; commit.

## Task 3: Review, recording, delivery, and final external approval

Files: reports/progress.md, reports/resources.json, reports/final-verification.json, submission docs/narration, submission recording assets (ignored/private until approved), delivery-site static sources/build and source package.

Interfaces: Consume actual Tasks1–2 records. Read-only whole-change reviewer; fix important findings with regression tests. Browser capture genuine UI/actual results, edit to1–3 minutes with user-supplied real narration; no fake voice. Static landing has source/evidence downloads, honest limits and usable playback; no private keys. Public visibility and competition rights/submission are explicit final user decisions.

- [x] Run full tests/browser checks; one fresh independent review. Expected: verified required fixes, no unsupported success claims.
- [x] Produce real screen recording and updated line-by-line narration; request human audio/path once materials are ready, continue independent work while waiting.
- [x] Build/visually verify static delivery and source archive; prepare hosting privately if supported. Expected: no secrets/runtime in download, genuine artifacts and transparent modes.
- [ ] Receive human narration, assemble/playback-check1–3-minute final video and source/evidence links.
- [ ] Present concrete public/submission material for final authorization; once approved complete hosting/submission and verify success. If permission/assets missing, keep request pending and report exactly what is ready, without calling the whole submission complete.
- [ ] Update actual phase times/API resources, package and final links. Preserve branch; no remote merge required.

## 18:15 驗收續行

使用者指示「先不錄其他的先完成驗收」：本人錄音／影片合成延後，先完成程式、備份、解壓啟動、文件與私人交付驗收。最新 60 項追溯與研究缺口見 reports/acceptance.md；不新增付費重跑，不改成公開權限，不投稿。
