# MixRoute public documentation research

Updated **2026-11-26, 23:10 Asia/Taipei**. Researcher scope: official public documentation and unauthenticated public status only. This researcher read no secrets and made no authenticated/inference calls, key changes, payments, installations, or deployments. The actual account pool below is attributed separately to the root agent's authorized read-only console observation.

## Confirmed API and routing contract

The homepage's **Docs** link now opens [Introduction](https://mixroute.ai/docs/introduction); discovery index: [llms.txt](https://mixroute.ai/docs/llms.txt). Inference base URL is `https://api.mixroute.ai/v1`. Exact IDs must match the Model Marketplace. Documentation distinguishes ordinary inference keys from account-management credentials. [Introduction](https://mixroute.ai/docs/introduction), [Authentication and Quota](https://mixroute.ai/docs/api-reference/system-api/authentication-and-quota)

| Question | Confirmed public contract |
| --- | --- |
| Smart request model | `auto`, using the route's inference key at `POST /v1/chat/completions` |
| Regular versus Smart key | Smart keys have `smart_routing: true`; a regular key calls a named model directly. A named model request with a Smart key is **not documented as bypassing its router**. |
| Authorized pool | Key setting `smart_route_tiers` is a **JSON-encoded string**, with `simple`, `reasoning`, `complex`, `super`. Console Ultra maps to `super`; current console sets `reasoning = simple`. |
| Pool/key readback | Documented `GET /api/token/<id>`, list and search require **system access token** plus `New-Api-User`, not merely an inference `sk-` key. |
| Routing statistics | Protected `GET /api/token/smart_route/stats`; fields include `requests`, `actual_quota`, `saved_quota`, `daily` baseline/actual, `tier_dist`, `trial_start_ts`. |

Sources: [Smart Routing guide](https://mixroute.ai/docs/api-reference/smart-routing), [Smart Routing System API](https://mixroute.ai/docs/api-reference/system-api/smart-routing), [API Key Management](https://mixroute.ai/docs/api-reference/system-api/api-key-management). MixRoute explicitly recommends a separate regular key for traffic that must hit one model. [Smart Routing product FAQ](https://mixroute.ai/smart-routing/)

### Public status observed; not account-specific

Unauthenticated [GET /api/status](https://api.mixroute.ai/api/status) returned `success: true`, `quota_per_unit: 500000`, `smart_routing_enabled: true`, and `smart_routing_model_aliases: ["auto"]`. Public presets included:

| Preset/group | Simple (and reasoning) | Complex | Ultra |
| --- | --- | --- | --- |
| Default / blank group | `deepseek-flash` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| Recommend / blank group | `gemini-3.8-flash` | `claude-sonnet-5-5` | `claude-opus-5-5` |
| Super Money-Saving / blank group | `deepseek-flash` | `claude-sonnet-5-5` | `qwen3.8-max` |
| Default / free | `deepseek-v4-flash` | `deepseek-v4-pro` | `gpt-6-sol` |

These are deployment presets, **not evidence of this application's key pool**. Docs tell clients to fetch presets/exclusions instead of copying screenshots. `smart_routing_free_trial_days` and `smart_routing_service_fee_percent` were absent in this response; the product FAQ describes routing as free, but the current status response does not independently supply a fee value. [Smart Routing System API](https://mixroute.ai/docs/api-reference/system-api/smart-routing), [Smart Routing FAQ](https://mixroute.ai/smart-routing/)

## Cost, request ID, and wallet visibility

The [Chat Completions response](https://mixroute.ai/docs/api-reference/endpoint/chat-openai) documents `id`, `model`, and `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`. The `id` example is a completion ID (`chatcmpl-...`); its equivalence to the gateway log's request ID is **UNKNOWN**. The [billing FAQ](https://mixroute.ai/docs/faq/billing-and-uasge) promises real-time token usage in `usage`, not a billed-dollar field.

**Direct actual billed cost/quota in chat body or headers: UNKNOWN / no documented field contract found.** No named `x-request-id` or cost response header contract was found in the relevant official API docs. Some model-page prose says to monitor usage headers without naming them; this is insufficient for a parser or spending guarantee.

[User Logs & Usage Statistics](https://mixroute.ai/docs/api-reference/endpoint/user-logs) documents protected `GET /api/log/self`, with per-request `quota`, `model_name`, `prompt_tokens`, `completion_tokens`, `request_id`, `token_id`, and `other` (JSON string). `other` may contain `billing_source`, `model_price`, model/cache/completion/group ratios, `cache_tokens`, `reasoning_effort`, conversion/path, and first-token latency. Compute billed USD from `quota / quota_per_unit`; current public conversion is 500,000 units/USD. `GET /api/log/self/stat` reports **cumulative consumed quota**, not wallet balance. The log guide uses the console hostname; newer System API docs use `https://api.mixroute.ai` as management base. Host equivalence is not authenticated here.

Wallet balance is officially documented: protected `GET /api/user/self`, field `data.quota`, divided by current `quota_per_unit`. Credentials are a **system access token** and numeric account `New-Api-User`. Account wallet balance and key `remain_quota` are separate; key quota is a ceiling, not a wallet transfer. Some auth failures return HTTP 200 with `success: false`. Do **not** call `GET /api/user/token` as an inspection step: docs say it rotates and invalidates the previous system token. [Authentication and Quota](https://mixroute.ai/docs/api-reference/system-api/authentication-and-quota)

**Inference-key-only self-inspection: UNKNOWN / no documented endpoint found** to obtain the key's Smart flag, actual tier pool, key ceiling, or wallet. Reviewed docs index, key management, routing, list-models, SDK and billing/usage guides; no `sk-`-only pool introspection contract was located. `/v1/models` availability does not establish authorized router tiers, prices, or a maximum bill.

## Actual pool confirmed by console; current maximum rate

The root agent reports read-only CUA verification of **Smart-Route-API-1** in the user's logged-in dashboard: Simple `gpt-5.4-nano`, Complex `claude-sonnet-5-5`, Ultra `gpt-6.2-astra`. Pre-probe account balance was **US$55.00**, historical consumption/request count zero. These are account observations, not public preset assumptions. A nonzero wallet does not alter the independent authorized US$35 total / US$5 initial-test limits.

USD per **1M tokens**, Standard processing, text messages. MixRoute and fetched official OpenAI model pages agree on the two GPT rates/specs below:

| Actual tier / exact ID | Context / max output | Input / output | Cached input | Other billing details |
| --- | --- | --- | --- | --- |
| Simple `gpt-5.4-nano` | 400,000 / 128,000 | $0.20 / $1.25 | $0.02 | MixRoute pricing updated 2026-03; OpenAI supports reasoning and text/image input. |
| Complex `claude-sonnet-5-5` | 1,000,000 / 128,000 | $2 / $10 | $0.10 | MixRoute base tier, updated 2026-09; cache write $2.50 (5m) / $4 (1h). |
| Ultra `gpt-6.2-astra`, input ≤272K | 1,050,000 / 128,000 | **$8 / $40** | $0.40 | Cache write $10 (30m) / $20 (12h). |
| Ultra `gpt-6.2-astra`, input >272K | 1,050,000 / 128,000 | **$16 / $60** | $0.80 | Cache write $20 (30m) / $40 (12h); long-context rates apply to the entire request. |

Sources: [MixRoute Nano](https://mixroute.ai/models/gpt-5-4-nano/), [OpenAI Nano](https://developers.openai.com/api/docs/models/gpt-5.4-nano), [MixRoute Sonnet](https://mixroute.ai/models/claude-sonnet-5-5/), [MixRoute Astra](https://mixroute.ai/models/gpt-6-2-astra/) (pricing updated 2026-11), [OpenAI Astra](https://developers.openai.com/api/docs/models/gpt-6.2-astra). OpenAI separately caps Astra input at **922,000** tokens. Astra rejects reasoning effort `none`. Fast processing costs 2× Standard; Ultrafast costs 3× through 2027-02-28 and 6× from 2027-03-01. These premium processing modes and explicit cache-write features should remain outside the tiny probe's request configuration. The model names alone do not prove an account's processing mode or discounts.

**Conservative rate across this exact pool for Standard text requests without tools or explicit cache writes: US$16 input / US$60 completion per 1M.** If the full model input is enforced ≤272K, US$8/$40 is sufficient under the same assumptions. Reserving `($16 × bounded_input_tokens + $60 × bounded_completion_tokens) / 1,000,000` covers the listed uncached model rates even if the router chooses Ultra. For example, a conservative 1,000-input-token allowance and **16 total generated tokens** reserves **US$0.01696** (short-context rates yield US$0.00864). This is a rate-based reservation, not observed billed cost; input limits must include message overhead and any transmitted context. Reconcile with the console usage log after the one authorized probe; no retry.

OpenAI `max_completion_tokens` bounds **visible output plus reasoning**, and the [token-counting guide](https://developers.openai.com/api/docs/guides/token-counting) confirms non-visible formatting tokens are also included. A prompt asking for 16 visible tokens is insufficient. [Chat Completions parameter reference](https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create) deprecates `max_tokens` in favor of this field. MixRoute's chat documentation explicitly lists `max_tokens`; router propagation of `max_completion_tokens` to all three targets is **not documented here**. Treat parameter rejection as a failed single probe, not grounds for automatic retry or dropping the limit.

OpenAI marks Nano deprecated with an announced **2027-04-01 shutdown** (notice 2026-10-01); this is a future retirement, not proof it is currently unavailable. MixRoute's longer-term replacement/alias behavior remains unknown. [OpenAI deprecations](https://developers.openai.com/api/docs/deprecations)

## Low-cost named text candidates and price caveats

USD per **1M tokens**. These are official published observations, not independently verified account prices or proof of a pinned underlying snapshot.

| Exact MixRoute request ID | MixRoute context / max output | MixRoute published input / output / cache read | Price page date | Qualification |
| --- | --- | --- | --- | --- |
| `deepseek-v3.2` | 163,840 / 65,536 | $0.28 / $0.42 / $0.028 | 2025-12 | Page explicitly lists text→text and Chat Completions. Suitable named baseline candidate; actual key access and underlying serving revision unverified. |
| `deepseek-v4-flash` | 1,000,000 / 384,000 | $0.14 / $0.28 / $0.0028 | 2026-04 | MixRoute page lists text→text, but current upstream documents retirement/alias substitution. Do not claim pinned V4 or rely on this old price. |
| `gemini-3.5-flash-lite` | 1,048,576 / 65,536 | $0.30 / $1.20 / $0.03 | 2026-07 | Text output; multimedia input capability. Google current standard output price is $2.50, conflicting with MixRoute page. |
| `deepseek-flash` | 1,000,000 / 384,000 | $0.30 / $1.20 / $0.006 | 2026-09 | Text/image input, text output. Current alias, not pinned snapshot. MixRoute listed rates match upstream peak rates. |

Sources: [V3.2](https://mixroute.ai/models/deepseek-v3-2/), [V4 Flash](https://mixroute.ai/models/deepseek-v4-flash/), [Gemini Flash-Lite](https://mixroute.ai/models/gemini-3-5-flash-lite/), [DeepSeek Flash](https://mixroute.ai/models/deepseek-flash/). Official MixRoute per-model docs also show exact request IDs: [V3.2 request example](https://mixroute.ai/docs/model-api/deepseek/deepseek-v3.2), [V4 Flash example](https://mixroute.ai/docs/model-api/deepseek/deepseek-v4-flash).

Current [DeepSeek Models & Pricing](https://api-docs.deepseek.com/quick_start/pricing/) identifies `deepseek-flash` as **DeepSeek-V4.1-Flash-1017** and says legacy `deepseek-v4-flash` requests are served by it. Context/output remain 1M/384K; vision is supported. Upstream peak input/output/cache hit: **$0.30/$1.20/$0.006**; off-peak: **$0.15/$0.60/$0.003**. Whether MixRoute follows upstream time-based discounts or keeps its stated flat rate is **UNKNOWN**. Current [Google standard pricing](https://aistudio.google.com/docs/pricing#gemini-3.5-flash-lite) is **$0.30 input / $2.50 output including thinking**, cache $0.03; therefore $1.20 is not a defensible current upper-bound estimate for Gemini.

### Public preset expensive targets

Public default preset includes [Sonnet 5.5](https://mixroute.ai/models/claude-sonnet-5-5/): base $2 input/$10 output, and [Opus 5.5](https://mixroute.ai/models/claude-opus-5-5/): base **$4 input/$20 output**, both updated 2026-09. Opus also lists cache write $5 (5m)/$8 (1h); each has 1M context/128K output. The free preset's [GPT-6 Sol](https://mixroute.ai/models/gpt-6-sol/) lists $2/$10 up to 272K input, then $4/$15 above it. These public presets differ from the actual console-confirmed pool above and must not replace it in cost calculations.

## Actionable implementation recommendation (inference)

1. The root agent's read-only console observation now supplies the actual pool for the explicitly authorized single tiny `auto` probe. Reserve against Astra's rates above and verify its billed log before additional calls. For continued testing, refresh pool/rate evidence if settings change; public presets or the 270-ID model list cannot prove the actual pool.
2. For a regular-key named-model baseline, prefer `deepseek-v3.2` if confirmed available. Use only text messages, no provider search/tools, non-streaming usage, a tight output cap (e.g. 512), short bounded input, concurrency 1, and no automatic retry. At its published $0.28/$0.42 rates, 4,000 input + 512 output estimates $0.00133504; this is an estimate, not confirmed billing.
3. Preserve `response.id`, returned `model`, token usage, status and any actual request ID header **if present**, without inventing fields or calling estimated spend actual spend. A response model is useful retrospective evidence; it does not establish the pool before the next call.
4. Use the authorized read-only console to reconcile billed cost after the pilot; System API is optional if suitable management credentials already exist. Reserve the worst approved pool charge before sending and fail closed when prices, pool, or usage are missing. Keep independent total US$35 and initial-test US$5 ceilings. No credential writes/rotation or automatic recharge are needed for these read checks.

Budget enforcement without either exact billing access or a verified complete pool/rate bound cannot be described as a guaranteed US$35 cap. Unknown costs must remain visible as unknown.
