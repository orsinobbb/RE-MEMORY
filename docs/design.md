# RE:MEMORY — executable P0 design
User-approved direction: local build → real MixRoute integration → experiment
→ competition materials → deployment package for a host to be specified.

Implementation call: one FastAPI process serving static frontend and JSON API,
SQLite persistence with user/project filtering and FTS5 Chinese bigram terms.
The prescribed local stack fits P0; distributed services add no benefit and
browser-only storage cannot demonstrate independent recovery with backend keys.

Each fact carries kind, version, validity, trust, provenance, conflict and ACL.
Aliases are many-to-many and user confirmation is distinct from inference.
The router maintains bounded search state with read-version deduplication,
score/margin/negative evidence, dynamically normalized weights and iterative
low-cost distinguishing clues. L3–L5 enforce mandatory memory even after a high
identity score. Coverage faults supplement retrieval or block task execution.

Packed context includes current goal, hard constraints, decisions, task state,
verified prior artifacts and dependency evidence. It never truncates constraints.
Token categories include system/user/mandatory/work/evidence/tools/output reserve
and safety margin. Local tokenizer estimates and actual API usage are separate.

MixRoute regular and Smart keys stay in .env. Only verified official endpoints
are called. Model pool/prices/context limits are verified before paid tests.
Worst-case request cost including bounded retry is reserved transactionally;
timeouts/unknown billing retain a conservative reservation. No auto top-ups.
Provider model ID, usage, latency, response/request IDs and failures are recorded.

Task execution allows only markdown_handoff: produce a real Markdown artifact,
verify required goal/constraint/next-step headings and preserved constraints,
write a hash, mark completion and event in one transaction. No arbitrary shell.
Offline execution is SIMULATION. Provider generated content is not automatically
verified truth. Fresh sessions receive no previous raw conversation buffer.

Benchmarks A–F use separate evaluator truth, fresh databases for task trials,
same fixed model for A–E; F differs only in provider routing. Offline retrieval
results do not stand in for live LLM task success. Weight tuning uses dev only;
blind evaluation remains held out. Unknown metrics stay null with a reason.

Scope limits: synthetic local single-user competition prototype; embeddings are
replaceable adapters with FTS fallback, semantic calibration is not pre-claimed.
Public host/domain are unspecified; prepare deployment instructions and rollback,
do not publish. Deadline in supplied spec: 2026-11-27 23:59 Asia/Taipei.
