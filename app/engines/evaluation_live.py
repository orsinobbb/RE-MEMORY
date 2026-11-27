"""Evaluator-only measured end-to-end trials. Truth never enters model inputs."""
import time,uuid
from pathlib import Path
from app.storage.database import Store
from .task import Orchestrator
from .mixroute import MixRoute
from benchmarks.generators.synthetic import seed
from benchmarks.generators.truth import cases

def evaluate_live(count=10,budget=4096,strategies=None,provider=None,directory=None,max_cases=10,split='blind',on_case=None):
    start=time.perf_counter();run_id=str(uuid.uuid4())
    directory=Path(directory or Path(__file__).resolve().parents[2]/'data/runtime/live-benchmark')
    directory.mkdir(parents=True,exist_ok=True)
    provider=provider or MixRoute(Store(Path(__file__).resolve().parents[2]/'data/runtime/rememory.db'))
    truth=cases(split)[:max_cases];rows=[]
    for strategy in strategies or list('ABCDEF'):
        correct=top3=mrr=recall=precision=clarify=success=wrong=duplicate=targeted=generated=omissions=0
        outputs=[];calls=[];rounds=[];local_tokens=[];latencies=[]
        for case in truth:
            s=Store(directory/(run_id+'-'+strategy+'-'+case['id']+'.db'));seed(s,count,42,'2026-11-26')
            o=Orchestrator(s,provider);session=o.new_session()
            req={'query':case['query'],'mode':'SMART' if strategy=='F' else 'FIXED','strategy':strategy,'budget':budget,'session_id':session['id'],'idempotency_key':run_id+strategy+case['id']}
            case_start=time.perf_counter();out=o.run(req)
            new_calls=[out['model_call']] if out.get('model_call') else []
            ret=out.get('retrieval') or {};ctx=ret.get('context') or {}
            selected=out.get('project_id') or ret.get('project_id');expected=case['project_id']
            correct+=selected==expected;ranking=[c['project_id'] for c in ret.get('candidates',[])]
            top3+=expected in ranking[:3] if expected else selected is None
            mrr+=1/(ranking.index(expected)+1) if expected in ranking else (1 if expected is None and selected is None else 0)
            delivered=out['status']=='COMPLETED'
            wrong+=delivered and selected!=expected
            if expected:
                targeted+=1;critical=set(case['critical_fact_ids']);loaded={f['id'] for f in ctx.get('loaded',[]) if f.get('kind')}
                recall+=len(critical&loaded)/len(critical);precision+=len(critical&loaded)/len(loaded) if loaded else 0
                clarify+=ret.get('status')=='NEEDS_CONFIRMATION'
                success+=delivered and selected==expected and out.get('artifact',{}).get('verified',False)
                if (out.get('model_call') or {}).get('content'):
                    generated+=1;constraint=s.get('facts',expected+'-constraint-v2','demo')['content']
                    omissions+=''.join(constraint.split()) not in ''.join(out['model_call']['content'].split())
            duplicate_status=None
            if delivered:
                replay=o.run({**req,'idempotency_key':req['idempotency_key']+'-fresh-session','session_id':o.new_session()['id']})
                duplicate_status=replay['status'];duplicate+=replay['status']=='COMPLETED'
                if replay.get('model_call') and replay['model_call']['id'] not in {c['id'] for c in new_calls}:new_calls.append(replay['model_call'])
            calls.extend(new_calls)
            incomplete=sum(c.get('total_tokens') is None or c.get('retry_count',0)>0 for c in new_calls)
            known_usage=sum(c.get('total_tokens') or 0 for c in new_calls)
            result={'case_id':case['id'],'selected_project':selected,'correct':selected==expected,'status':out['status'],'reason':out.get('reason'),'actual_models':[c.get('model') for c in new_calls],'usage_tokens':None if incomplete else known_usage,'known_usage_tokens':known_usage,'usage_unknown_calls':incomplete,'raw_history_count':session['raw_history_count'],'duplicate_check_status':duplicate_status,'artifact_id':out.get('artifact',{}).get('id'),'artifact':out.get('artifact')}
            outputs.append(result);rounds.append(len(ret.get('rounds',[])));local_tokens.append(ret.get('retrieval_tokens',0));latencies.append((time.perf_counter()-case_start)*1000)
            if on_case:on_case(strategy,result)
            s.path.unlink(missing_ok=True)
        n=len(truth);cost_known=all(c.get('cost_usd') is not None for c in calls);usage_known=all(c.get('total_tokens') is not None and c.get('retry_count',0)==0 for c in calls)
        cost=sum(c['cost_usd'] for c in calls) if cost_known else None
        rows.append({'strategy':strategy,'count':count,'budget':budget,'cases':n,'status':'MEASURED_LIVE_END_TO_END','top1_accuracy':correct/n,'top3_accuracy':top3/n,'mrr':mrr/n,'critical_memory_recall':recall/targeted if targeted else None,'memory_precision':precision/targeted if targeted else None,'task_success_rate':success/targeted if targeted else None,'critical_constraint_omission_rate':omissions/generated if generated else None,'wrong_project_execution_rate':wrong/n,'duplicate_completed_rate':duplicate/success if success else None,'unnecessary_clarification_rate':clarify/targeted if targeted else None,'mean_rounds':sum(rounds)/n,'mean_retrieval_tokens':sum(local_tokens)/n,'mean_e2e_tokens':sum(c['total_tokens'] for c in calls)/n if usage_known else None,'known_api_tokens':sum(c.get('total_tokens') or 0 for c in calls),'api_calls':sum(c.get('attempts',c.get('retry_count',0)+1) for c in calls),'api_cost_usd':cost,'cost_per_success':cost/success if cost is not None and success else None,'mean_latency_ms':sum(latencies)/n,'case_results':outputs,'model_calls':calls})
    return {'id':run_id,'mode':'LIVE_END_TO_END','split':split,'ground_truth_isolated':True,'reference_date':'2026-11-26','results':rows,'elapsed_ms':round((time.perf_counter()-start)*1000,2),'limits':['Ten bounded synthetic queries are not a real-user evaluation.','A–E share fixed model; F requests auto. Actual resolved models are recorded.','A/B/C use different memory payloads; all share the current-source safety validator.','B is deliberately lossy, not a claim about every compression method.','Indexing/retrieval/validation are local: zero model tokens; their CPU latency is measured separately from API usage.','Provider billing remains UNKNOWN until exact reconciliation; upper bounds are reservations, not invoices.']}
