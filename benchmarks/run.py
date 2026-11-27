import argparse,json
from pathlib import Path
from app.engines.evaluation import evaluate
p=argparse.ArgumentParser();p.add_argument('--count',type=int,choices=(10,100,1000),default=10);p.add_argument('--split',choices=('dev','blind'),default='blind');p.add_argument('--budgets',nargs='+',type=int,default=[1024,2048,4096,8192,16384]);a=p.parse_args()
result=evaluate(a.count,a.budgets,list('ABCDEF'),split=a.split)
root=Path(__file__).resolve().parent/'results';root.mkdir(parents=True,exist_ok=True);path=root/f'offline-{a.count}-{a.split}.json';path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'path':str(path),'elapsed_ms':result['elapsed_ms'],'rows':len(result['results']),'E_4K':next((r['top1_accuracy'] for r in result['results'] if r['strategy']=='E' and r['budget']==4096),None)},ensure_ascii=False))
