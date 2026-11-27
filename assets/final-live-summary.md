# Final LIVE handoff — measured records

Executed 2026-11-27T16:32:49.608827+08:00 using synthetic data only. Stage1 requested `auto`, returned `claude-sonnet-5-5` (1,396 Tokens); stage2 requested `deepseek-v3.2`, returned `DeepSeek-V3.2` (1,336 Tokens). Both artifacts passed current-source/structure/checklist/hash validation; both remain CLAIM for real-world semantic truth.

Distinct persisted Sessions each have zero raw history. The stage2 packed model context contains the exact stage1 artifact content and SHA-256. A completed-stage replay made zero additional API calls. These checks prove persisted handoff and validation boundaries, not superior reasoning quality.

Task1 wall time: 13.6 minutes. New known API Tokens: 2,732; two generation attempts. Exact billing UNKNOWN. Shared ledger conservative commitments: US$0.96545; the persistent final window ceiling is US$3.93813, preserving prior US$0.93813 and limiting new reservations to US$3.

## Fixed prospective evaluation

Case-set SHA-256: `08e2e855e0a0756de0ba47e379deac381a6e7c8cad91381998eec4cacaa76fd0`. Frozen new wording before execution; no routing/source/output tuning after freeze. It reuses ten bounded synthetic source projects and is not a sealed blind or real-user trial.

| Arm | Cases | Valid task artifacts | Expected stops without API | Actual models | Known Tokens |
|---|---:|---:|---:|---|---:|
| E | 20 | 16/16 | 4/4 | {"DeepSeek-V3.2": 16} | 14,917 |
| F | 20 | 16/16 | 4/4 | {"DeepSeek-V3.2": 16} | 14,938 |
| OTHER | 6 | 6/6 | 0/0 | {"claude-sonnet-5-5": 6} | 9,110 |

E and F each passed 16/16 artifact-boundary checks and 4/4 expected stops. Zero wrong-project execution or repeated completion in these cases. Both E and F returned DeepSeek throughout this set; these results do not establish an auto quality improvement. OTHER is the preselected six-case Sonnet subset, not an aggregate comparison against all twenty. All generated artifacts remain CLAIM.

Actual benchmark wall time: 51.31 seconds; 38 generation attempts; 38,965 known Tokens; no unknown new usage. Conservative price-bound commitments US$0.38965, exact invoice UNKNOWN.

## 18:15 final acceptance continuation

122 pytest checks, three actual browser workflows, isolated SQLite restore, fresh extracted macOS one-click startup and private static playback/download acceptance passed. This continuation added zero MixRoute calls. Human narration is deferred by the user. Full requirement trace and declared research gaps: [acceptance.md](acceptance.md).

The final40 calls (41,697 Tokens) match the console model/input/output multiset. Displayed reference subtotal US$0.038070 is rounded and is not a definitive invoice; the original conservative ledger is unchanged. See [console reconciliation](console-final-live-reconciliation.json).
