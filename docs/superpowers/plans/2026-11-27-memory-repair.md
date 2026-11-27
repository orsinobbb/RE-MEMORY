# Memory repair implementation plan

> Execute inline with superpowers:executing-plans. The human approved implementation and requested continuation.

**Goal:** Make the existing memory evolution engine operable in Memory Explorer, with independently validated artifact revisions.

**Architecture:** Local owner-scoped FastAPI endpoints, existing SQLite transactions, immutable fact/artifact history, and native DOM forms. Artifact review checks current source-backed facts independently of invalidated artifacts; normal continuation still requires valid artifacts. Review requires an optimistic snapshot and explicit bounded-review acknowledgment. No model calls.

**Tech stack:** Python 3.12 / FastAPI / SQLite / pytest / vanilla JavaScript / Playwright.

**Spec:** `docs/project-v5.txt` sections Memory Explorer and Memory Evolution; project `AGENTS.md`; existing P0 design.

**Global Constraints:** Synthetic data only; preserve local .env and cumulative cost ledger; no paid calls, private imports, public deployment, or submission. Preserve CLAIM classification and completed task state. Only existing trusted source content can be offered as a verified fact revision. Do not provide a new source-import/trust interface in this phase.

**Review Focus:** Stale/concurrent edits; wrong-owner/project references; transaction rollback; artifacts superseded between review and save; active execution locks; unsupported source text; invalid current facts; stale browser context; revalidation metadata implying semantic truth or task execution.

## Task 1: Memory repair API and artifact revisions

Files: `app/engines/coverage.py`, `app/engines/artifact_revalidation.py`, `app/main.py`, `tests/test_memory_repair.py`.

Interfaces: `check_fact_coverage(store, pid, user, reference, dependency_ids=())`; `ArtifactRevalidation.review(user, artifact_id, reference)` and `.save(user, artifact_id, content, snapshot, acknowledged, reference)`. POST `/api/memory/aliases/{id}/confirm`, POST `/api/memory/facts/{id}/revise`, GET `/api/artifact/{id}/review`, POST `/api/artifact/{id}/revalidate`.

- [x] Write acceptance tests for source-supported fact revision, rejected edits, alias confirmation, current-fact coverage, stale review, ownership, invalid content, concurrent duplicate revision, execution locks, and atomic rollback.
- [x] Run `.venv/bin/python -m pytest -o addopts= -q tests/test_memory_repair.py`. Expected: missing API/engine failures.
- [x] Implement fact-only coverage, a same-transaction store reader, optimistic review snapshots, immutable artifact revision/provenance and pointer migrations. Explicit acknowledgment never promotes a CLAIM to a fact.
- [x] Run `.venv/bin/python -m pytest -o addopts= -q tests/test_memory_repair.py tests/test_evolution.py tests/test_context.py tests/test_tasks.py`. Expected: all pass.
- [x] Commit API and tests.

## Task 2: Operable Memory Explorer

Files: `frontend/app.js`, `frontend/style.css`, `tests/browser_memory_repair.mjs`.

Interfaces: Consume Task 1 endpoints; render forms with textContent; clear stale retrieval/context/recovery results after mutations; refresh memory/state.

- [x] Add a disposable, local, live-disabled browser fixture and Playwright workflow exercising alias confirmation, source-supported revision, failed unsupported revision, revalidation revision, and preserved history.
- [x] Run browser workflow. Expected: new controls absent before implementation.
- [x] Add accessible inline forms, source selection/preview, explicit invalidation notice, bounded artifact review acknowledgment, immutable revision badges, and errors.
- [x] Run browser workflow on desktop and mobile, then existing six-view smoke. Expected: pass, no overflow, zero paid calls.
- [x] Commit UI and browser verification.

## Task 3: Review, reports, and deliverable

Files: `reports/progress.md`, `reports/resources.json`, delivery documentation and generated source package.

Interfaces: Consume verified Tasks 1–2; preserve original P0 resource totals and report incremental elapsed/API usage.

- [x] Run full pytest suite and browser checks. Expected: all pass.
- [x] Request one fresh whole-change review; fix important findings with failing regression tests before code.
- [x] Refresh delivery documentation, stage timing, and cumulative resource report. Expected: added API calls/tokens/cost are zero.
- [x] Build and inspect source package; run source isolation verification. Expected: no keys, .env, runtime database, backups, or private screenshots.
- [x] Commit delivery updates, restart owned localhost preview, and report actual elapsed/resources and remaining public deployment/submission requirements.
