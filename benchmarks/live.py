import argparse,json
from pathlib import Path
from app.engines.evaluation_live import evaluate_live
from app.storage.database import Store
from datetime import datetime,timezone

def main():
    p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=(10,100,1000),default=10);p.add_argument('--budget',type=int,choices=(1024,2048,4096,8192,16384),default=4096);p.add_argument('--max-cases',type=int,default=10);p.add_argument('--split',choices=('dev','blind'),default='blind');p.add_argument('--strategies',default='ABCDEF');p.add_argument('--run',action='store_true');a=p.parse_args()
    if not a.run:p.error('Paid trials require explicit --run; protected by the shared cost ledger.')
    if not 1<=a.max_cases<=10 or not a.strategies or any(s not in 'ABCDEF' for s in a.strategies):p.error('Invalid bounded trial selection')
    result=evaluate_live(a.count,a.budget,list(dict.fromkeys(a.strategies)),max_cases=a.max_cases,split=a.split,on_case=lambda strategy,row:print(json.dumps({'strategy':strategy,**row},ensure_ascii=False),flush=True))
    root=Path(__file__).resolve().parents[1];path=root/'benchmarks/results'/f'live-{a.count}-{a.budget}-{a.split}.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    Store(root/'data/runtime/rememory.db').put('evaluations',{'id':result['id'],'user_id':'demo','project_id':'','created_at':datetime.now(timezone.utc).isoformat(),'result':result})
    print(json.dumps({'saved':str(path),'elapsed_ms':result['elapsed_ms'],'results':[{k:r[k] for k in ('strategy','task_success_rate','api_calls','known_api_tokens','api_cost_usd')} for r in result['results']]},ensure_ascii=False))

if __name__=='__main__':main()
