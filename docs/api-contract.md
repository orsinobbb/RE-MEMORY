# Frontend API v0.1
All same-origin JSON; no credentials enter frontend. Any response may contain
{error:string}. Render all imported text using textContent, never untrusted HTML.

GET /api/state -> {dataset:"DEMO", reference_date, projects:[{id,name,topic,description,last_active}], tasks:[{id,project_id,title,status}], events:[{id,project_id,type,detail,date}], resources:{api_calls,api_tokens,api_cost_usd,api_reserved_usd}, settings:{fixed_model,smart_model,enabled,configured}, stats:{projects,facts,aliases,artifacts}}
GET /api/memory?project_id=...&q=... -> {project,facts:[{id,kind,content,version,verification,trust,evidence_ids,superseded,conflict}], aliases:[{id,alias,status,uses,strength,ambiguous}], evidence:[{id,source,content,version,trusted}], relations:[{from,to,type}], tasks,artifacts:[{id,content,sha256,verified}]}
POST /api/retrieve JSON {query,budget:4096,strategy:"E",reference_date?} -> {id,status:"RESOLVED"|"NEEDS_CONFIRMATION"|"NOT_FOUND"|"BUDGET_EXCEEDED",project_id|null,query,intent:{time,topic,action},rounds:[{round,layer,reason,search_terms:[],candidates:[{project_id,name,score,dimensions:{time,topic,alias,behavior,content,unfinished,frequency},positive_evidence:[],negative_evidence:[]}],new_clues:[],new_information:[],tokens,cumulative_tokens}],retrieval_tokens,stop_reason,clarification|null,confidence_probability:null,context:{feasible,coverage,missing:[],conflicts:[],faults:[],manifest:{active_task,mandatory_memory,required_dependencies,evidence_references,missing_information,memory_snapshot},loaded:[],not_loaded:[],token_breakdown:{system,user,mandatory,work,evidence,tools,output_reserve,safety_margin,total},budget_status},elapsed_ms}
POST /api/retrieve/stream same body -> SSE event: round (round object), event: result (full result). UI may use regular endpoint and show saved rounds, but must label replay if not streamed.
POST /api/session {previous_session_id?} -> {id,raw_history_count:0,created_at}; no prior conversation passed.
POST /api/execute {query,budget:4096,mode:"SIMULATION"|"FIXED"|"SMART",model?:string,idempotency_key:string,session_id?:string,project_id?:string} -> {status:"COMPLETED"|"BLOCKED"|"ALREADY_COMPLETED"|"IN_PROGRESS",mode,session_id,project_id,reason?,retrieval?,artifact?:{id,content,sha256,verified},model_call?:{model,requested_model,input_tokens,output_tokens,total_tokens,cost_usd,cost_source,latency_ms,request_id},elapsed_ms}
GET /api/models -> {fixed:[],smart:[],configured,enabled,error?}; model entries {id}; read-only catalogue; never proves authorized routing pool.
POST /api/benchmark {count:10|100|1000,budgets:[1024,2048,4096,8192,16384],strategies:["A","B","C","D","E","F"],live:false} -> {id,mode:"OFFLINE_RETRIEVAL"|"LIVE",results:[{strategy,count,budget,cases,top1_accuracy,top3_accuracy,mrr,critical_memory_recall,memory_precision,task_success_rate,critical_constraint_omission_rate,wrong_project_execution_rate,unnecessary_clarification_rate,duplicate_completed_rate,mean_rounds,mean_retrieval_tokens,mean_e2e_tokens,api_cost_usd,mean_latency_ms,cost_per_success,status}],elapsed_ms,limits:[]}
GET /api/benchmark/latest -> benchmark object or {results:[]}
GET /api/export/{result_id} -> saved benchmark JSON download
GET /api/artifact/{artifact_id} -> Markdown download
POST /api/memory/aliases/{alias_id}/confirm {reference_date?} -> confirmed alias; explicit owner confirmation, no fact promotion.
POST /api/memory/facts/{fact_id}/revise {content,evidence_id,reference_date?} -> new source-backed current fact version. Existing trusted same-project evidence must support the exact content and original fact must already be verified. Rejects unsupported text, superseded fact IDs and active project execution. Invalidates project artifacts, preserves completed milestones.
GET /api/artifact/{artifact_id}/review?reference_date=YYYY-MM-DD -> {artifact,facts,evidence,snapshot,draft,verification_scope,factual_status:"CLAIM"}. Current completed-task artifact must require revalidation. Checks current source-backed memory in a consistent read transaction; normal continuation still requires valid artifacts.
POST /api/artifact/{artifact_id}/revalidate {content,snapshot,acknowledged:true,reference_date?} -> new artifact revision {id,parent_artifact_id,version,sha256,verified:true,factual_status:"CLAIM",verification_scope:"STRUCTURE_CURRENT_GOAL_AND_CONSTRAINTS",revision_method:"USER_REVIEW"}. Atomic optimistic snapshot validation; preserves old content/hash and completed state, migrates current task/required artifact pointers. Cached deliveries remain historical and invalidated cached content is rejected.
Memory repair failures return HTTP 409 {detail:code}; malformed request fields return HTTP 422. Repair endpoints are synthetic owner-scoped local prototype operations, never model calls. UI repair dates use Asia/Taipei and UI retrieval/execution uses /api/state reference_date, which advances with current fact revisions.
GET /api/health -> {status:"ok",dataset:"DEMO"}
For offline F return status:"NOT_RUN_REQUIRES_LIVE_SMART_ROUTING" with null outcomes.
Null API costs/metrics are UNKNOWN, never show as measured zero. Offline local
tokenizer measurements are estimates, not billed API tokens. Use no canned scores.


## 聊天與候選記憶（11/28）

- GET `/api/chat?project_id=PERSONAL`：列出範圍內聊天與未忘記記憶。
- POST `/api/chat/conversations`：`{project_id}`；PERSONAL 或既有專案。
- GET `/api/chat/conversations/{id}`：按順序讀回保存訊息與候選記憶。
- POST `/api/chat/conversations/{id}/messages`：`{content,idempotency_key,mode,model,budget}`；SMART/auto、4096 預設，輸出預留 1536。COMPLETED 含 reply/new_memories/context/usage；FAILED 保存原使用者訊息與錯誤，不自動付費重試。
- POST `/api/chat/memories/{id}`：`{action:CONFIRM|EDIT|FORGET,content?}`。確認／修正為使用者接受的筆記，不改原 FACT/evaluator。忘記保留原聊天與版本，停止載入。

每個聊天有 300 秒鎖，同 key 不同請求回 409；已保存結果可重播而不新增 API。引用只能來自當輪使用者訊息；主回答無效或截斷會失敗，無效候選略過而保留有效回答。所有模型呼叫共用原 SQLite 費用帳本與授權池；金鑰不返回前端。
