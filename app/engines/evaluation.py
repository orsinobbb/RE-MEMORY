import json,time,uuid
from pathlib import Path
from app.storage.database import Store
from .retrieval import Router
from benchmarks.generators.synthetic import seed
from benchmarks.generators.truth import cases

def evaluate(count=10,budgets=None,strategies=None,directory=None,split="blind"):
    start=time.perf_counter();budgets=budgets or [4096];strategies=strategies or list("ABCDEF")
    directory=Path(directory or Path(__file__).resolve().parents[2]/"data/runtime/benchmark")
    directory.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid.uuid4());s=Store(directory/(run_id+".db"));seed(s,count,42,"2026-11-26")
    truth=cases(split);rows=[]
    for budget in budgets:
      for strategy in strategies:
        base={"strategy":strategy,"count":count,"budget":budget,"cases":len(truth),"task_success_rate":None,"api_cost_usd":None,"cost_per_success":None,"wrong_project_execution_rate":None,"duplicate_completed_rate":None}
        if strategy=="F":
            rows.append({**base,**{k:None for k in ("top1_accuracy","top3_accuracy","mrr","critical_memory_recall","memory_precision","critical_constraint_omission_rate","unnecessary_clarification_rate","mean_rounds","mean_retrieval_tokens","mean_e2e_tokens","mean_latency_ms")},"status":"NOT_RUN_REQUIRES_LIVE_SMART_ROUTING"});continue
        outputs=[Router(s).retrieve(t["query"],"demo",budget,"2026-11-26",strategy) for t in truth]
        correct=top3=mrr=recall=precision=omission=clarify=0;targeted=0
        for t,out in zip(truth,outputs):
            expected=t["project_id"];selected=out["project_id"]
            correct+=selected==expected
            ranking=[c["project_id"] for c in out.get("candidates",[])]
            top3+=expected in ranking[:3] if expected else selected is None
            mrr+=1/(ranking.index(expected)+1) if expected in ranking else (1 if expected is None and selected is None else 0)
            if expected:
                targeted+=1;ctx=out.get("context") or {};loaded={x["id"] for x in ctx.get("loaded",[]) if x.get("kind")}
                critical=set(t["critical_fact_ids"]);recall+=len(loaded&critical)/len(critical)
                precision+=len(loaded&critical)/len(loaded) if loaded else 0
                omission+=(expected+"-constraint-v2") not in loaded
                clarify+=out["status"]=="NEEDS_CONFIRMATION"
        n=len(truth)
        rows.append({**base,"top1_accuracy":correct/n,"top3_accuracy":top3/n,"mrr":mrr/n,"critical_memory_recall":recall/targeted if targeted else None,"memory_precision":precision/targeted if targeted else None,
          "critical_constraint_omission_rate":omission/targeted if targeted else None,"unnecessary_clarification_rate":clarify/targeted if targeted else None,
          "mean_rounds":sum(len(o["rounds"]) for o in outputs)/n,"mean_retrieval_tokens":sum(o["retrieval_tokens"] for o in outputs)/n,
          "mean_e2e_tokens":None,"mean_context_tokens_estimate":sum((o.get("context") or {}).get("token_breakdown",{}).get("total",0) for o in outputs)/n,
          "mean_latency_ms":sum(o["elapsed_ms"] for o in outputs)/n,"status":"MEASURED_LOCAL_RETRIEVAL","case_results":[{"case_id":t["id"],"selected_project":o["project_id"],"correct":o["project_id"]==t["project_id"],"status":o["status"],"stop_reason":o["stop_reason"]} for t,o in zip(truth,outputs)]})
    result={"id":run_id,"mode":"OFFLINE_RETRIEVAL","split":split,"ground_truth_isolated":True,"reference_date":"2026-11-26","results":rows,"elapsed_ms":round((time.perf_counter()-start)*1000,2),
      "limits":["Local reads and packed context are separate estimates; local reads do not incur API tokens. E2E API tokens are UNKNOWN offline.","Task success/execution cost are unmeasured offline, shown UNKNOWN.","Confidence has not been calibrated; synthetic fixtures are deliberately bounded.","A/B/C use recent history/frozen lossy summary/top-three facts, without memory supplementation; all strategies share a safety validator.","B deliberately omits current constraints; results do not generalize to every summary algorithm.","Semantic vectors use replaceable FTS fallback in P0."]}
    # Database was created solely for this evaluator run; no truth was stored in it.
    s.path.unlink(missing_ok=True)
    return result
