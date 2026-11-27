# Final independent review

Reviewer: fresh-context GPT-6-astra, read-only; no credentials or paid calls. Reviewed 2dfb2e5..7202a7b plus private static Site source. Critical: none. Initial verdict WITH FIXES; two Important findings reproduced and fixed in one pass, no second reviewer run.

## Verified fixes

- Actual returned model must differ from stage1 before committing stage2. `test_second_stage_rejects_same_actual_model_and_retains_usage` failed when the substituted model was saved COMPLETED, then passed with BLOCKED, stage2 PENDING, paid-call record retained and no second artifact.
- Concurrent completion must return the requested stage's artifact and label saved replay. `test_concurrent_completed_stages_return_requested_stage_and_replay_label` failed with the stage2 artifact for a stage1 request, then passed with the stage1 artifact, stored_replay and api_call_made=false.
- Full suite after both fixes:122 tests pass. Existing real records already use distinct models; no new paid experiment was needed.

## Deferred minor

Source bundle contains workstation-specific paths in development scripts and test logs; the macOS recorder has no portable Playwright fallback. They contain no API credentials. Deferred as development-environment metadata; app startup instructions remain provided for macOS/Windows.

## Rulings on the reviewer's declined items

- Human narration/synchronization: pending actual supplied audio; direct final playback check required. Cost if wrong: video could fail competition voice/length requirements.
- Public hosting and submission rights: remain pending explicit human approval, private preparation is authorized. Cost if wrong: unintended disclosure or rights acceptance; no such action taken.
- Provider invoice/early unknown usage: retain UNKNOWN and conservative commitments in shared budget. Cost if wrong: reported invoice would be inaccurate; no invoice claim made.
- Real-user generalization/semantic truth: preserve bounded synthetic protocol and CLAIM labels. Cost if wrong: readers could mistake structural success for general correctness.
- Multi-tenant/private-data hardening: retain local prototype and static evidence-only delivery scope. Cost if wrong: unsuitable for an exposed paid backend, which is not deployed.
- Independent paid rerun: not required for this code fix; reuse actual provider records and author-side fixture regressions. Cost if wrong: unobserved provider changes remain outside the snapshot.
- Independent suite/browser rerun: reviewer inspected read-only sources/evidence; implementer ran and read122 tests plus actual browser checks. Cost if wrong: independent reproduction is weaker than author verification.
- Model-ID aliases: normalize case and reject the same known actual ID; do not claim unknown aliases are distinct models. Cost if wrong: unrecognized aliases could represent the same underlying model. Current actual IDs are known Sonnet/DeepSeek.

## GitHub publication follow-up

The workstation path finding was resolved for the public snapshot: browser scripts and the recorder now resolve installed Playwright or explicit environment configuration, and the saved test log uses a workspace placeholder. Current publication verification includes the full suite, three actual browser flows, and a clean-history credential/privacy scan. No production authentication or full semantic validation claim is added.
