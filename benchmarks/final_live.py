"""Fixed prospective synthetic evaluation; labels stay in the evaluator."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time
import uuid
from app.engines.task import Orchestrator
from app.engines.mixroute import MixRoute, ProviderBlocked
from app.storage.database import Store
from benchmarks.generators.synthetic import seed

ROOT=Path(__file__).resolve().parents[1]
CASE_FILE=ROOT/'benchmarks/generators/final-cases.json'

def summarize(arm,records,budget):
    complete=stops=successful=stopped=wrong=duplicate=correct=0
    calls=[];outputs=[]
    for record in records:
        case=record['case'];out=record['output'];new_calls=record['calls']
        selected=out.get('project_id') or (out.get('retrieval') or {}).get('project_id')
        expected=case['expected_project'];delivered=out['status']=='COMPLETED'
        target_ok=delivered and selected==expected and out.get('artifact',{}).get('verified',False)
        stop_ok=out['status']=='BLOCKED' and selected is None and not new_calls
        if case['expected_outcome']=='COMPLETE':complete+=1;successful+=target_ok
        else:stops+=1;stopped+=stop_ok
        wrong+=delivered and selected!=expected
        duplicate+=record['duplicate_status']=='COMPLETED'
        correct+=selected==expected
        calls.extend(new_calls)
        outputs.append({**record,'outcome_success':bool(target_ok if expected else stop_ok)})
    n=len(records);unknown=sum(c.get('total_tokens') is None or c.get('retry_count',0)>0 for c in calls)
    known=sum(c.get('total_tokens') or 0 for c in calls)
    cost=sum(c['cost_usd'] for c in calls) if all(c.get('cost_usd') is not None for c in calls) else None
    return {'arm':arm,'budget':budget,'cases':n,'actionable_cases':complete,'expected_stop_cases':stops,
            'task_success_rate':successful/complete if complete else None,'stop_success_rate':stopped/stops if stops else None,
            'outcome_success_rate':(successful+stopped)/n if n else None,'top1_accuracy':correct/n if n else None,
            'wrong_project_execution_rate':wrong/n if n else None,'duplicate_completed_rate':duplicate/successful if successful else None,
            'api_calls':sum(c.get('attempts',c.get('retry_count',0)+1) for c in calls),'known_api_tokens':known,
            'api_tokens':None if unknown else known,'usage_unknown_calls':unknown,'api_cost_usd':cost,
            'actual_models':dict(Counter(c.get('model','UNKNOWN') for c in calls)),
            'cost_upper_bound_usd':sum(c.get('cost_upper_bound_usd',0) for c in calls),
            'case_results':outputs}

def evaluate_final(provider=None,directory=None,cases=None,arms=None,other_model=None,case_file=CASE_FILE,on_case=None,checkpoint=None):
    arms=arms or ['E','F']
    if any(arm not in ('E','F','OTHER') for arm in arms):raise ValueError('INVALID_ARM')
    if 'OTHER' in arms and not other_model:raise ValueError('OTHER_MODEL_REQUIRED')
    frozen=Path(case_file).read_bytes();digest=hashlib.sha256(frozen).hexdigest()
    if digest!=Path(case_file).with_suffix('.sha256').read_text().strip():raise ValueError('CASE_HASH_MISMATCH')
    cases=cases if cases is not None else json.loads(frozen)['cases']
    provider=provider or MixRoute(Store(ROOT/'data/runtime/rememory.db'))
    directory=Path(directory or ROOT/'data/runtime/final-benchmark');directory.mkdir(parents=True,exist_ok=True)
    run_id=str(uuid.uuid4());start=time.monotonic();rows=[]
    result={'id':run_id,'mode':'LIVE_END_TO_END','case_set_sha256':digest,'protocol':'NEW_FIXED_SYNTHETIC_NOT_SEALED_BLIND',
            'ground_truth_isolated':True,'reference_date':'2026-11-26','results':rows,'complete':False,
            'limits':['Twenty synthetic queries reuse bounded source fixtures; no generalization to real users.',
                      'Outcome and artifact validation do not certify semantic truth; artifacts remain CLAIM.',
                      'Actual model, retries and unknown billing are retained; no tuning after freeze.',
                      'OTHER is a six-case subset and cannot be compared as an aggregate against the full set.']}
    for arm in arms:
        records=[]
        selection=cases if arm!='OTHER' else [c for i,c in enumerate(cases) if i in (0,4,8,12,2,10)]
        for case in selection:
            s=Store(directory/(run_id+'-'+arm+'-'+case['id']+'.db'));seed(s,10,42,'2026-11-26')
            orchestrator=Orchestrator(s,provider);session=orchestrator.new_session()
            request={'query':case['query'],'mode':'SMART' if arm=='F' else 'FIXED','strategy':'F' if arm=='F' else 'E',
                     'model':other_model if arm=='OTHER' else None,'budget':4096,'session_id':session['id'],
                     'idempotency_key':run_id+arm+case['id']}
            # No target override or evaluator labels enter the request/model context.
            out=orchestrator.run(request);calls=[out['model_call']] if out.get('model_call') else []
            duplicate_status=None
            if out['status']=='COMPLETED':
                replay=orchestrator.run({**request,'session_id':orchestrator.new_session()['id'],'idempotency_key':request['idempotency_key']+'-new-session'})
                duplicate_status=replay['status']
                if replay.get('model_call') and replay['model_call']['id'] not in {c['id'] for c in calls}:calls.append(replay['model_call'])
            record={'case':case,'output':out,'calls':calls,'duplicate_status':duplicate_status,'raw_history_count':session['raw_history_count']}
            records.append(record)
            partial=summarize(arm,records,4096)
            result['results']=rows+[partial];result['elapsed_seconds']=round(time.monotonic()-start,3)
            if checkpoint:Path(checkpoint).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
            if on_case:on_case(arm,partial['case_results'][-1])
            # Only the evaluator-created memory fixture is removed; the shared paid ledger persists.
            s.path.unlink(missing_ok=True)
        rows.append(summarize(arm,records,4096))
    result.update(results=rows,complete=True,elapsed_seconds=round(time.monotonic()-start,3))
    if checkpoint:Path(checkpoint).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    return result

class FinalWindowProvider:
    def __init__(self,provider,baseline=77,max_attempts=60):self.provider=provider;self.baseline=baseline;self.max_attempts=max_attempts
    def call(self,*args,**kwargs):
        attempts=sum(c.get('attempts',c.get('retry_count',0)+1) for c in self.provider.store.rows('model_calls','demo'))
        if attempts-self.baseline+self.provider.settings.max_retries+1>self.max_attempts:raise ProviderBlocked('FINAL_ATTEMPT_LIMIT_REACHED')
        return self.provider.call(*args,**kwargs)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
    if not args.run:parser.error('Explicit --run is required for bounded paid evaluation.')
    ledger=Store(ROOT/'data/runtime/rememory.db');ledger.start_budget_window('submission-2026-11-27',3)
    provider=FinalWindowProvider(MixRoute(ledger));path=ROOT/'benchmarks/results/final-live.json'
    if path.exists():parser.error('A checkpoint exists; preserve it rather than silently repeating paid calls.')
    def progress(arm,row):
        print(json.dumps({'arm':arm,'case_id':row['case']['id'],'status':row['output']['status'],'success':row['outcome_success'],
                          'models':[c.get('model') for c in row['calls']],'tokens':sum(c.get('total_tokens') or 0 for c in row['calls'])},ensure_ascii=False),flush=True)
    out=evaluate_final(provider=provider,arms=['E','F','OTHER'],other_model='claude-sonnet-5-5',on_case=progress,checkpoint=path)
    print(json.dumps({'saved':str(path),'elapsed_seconds':out['elapsed_seconds'],'results':[{k:v for k,v in row.items() if k!='case_results'} for row in out['results']]},ensure_ascii=False))

if __name__=='__main__':main()
