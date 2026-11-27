import httpx,pytest
from app.engines.mixroute import MixRoute,ProviderBlocked
from app.engines.task import Orchestrator
from app.engines.validation import validate
from app.storage.database import Store
from app.engines.context_builder import build_context
from benchmarks.generators.synthetic import seed
from tests.test_mixroute import config

def test_unknown_fixed_model_never_reaches_network(tmp_path):
    calls=[]
    def handler(request):calls.append(1);return httpx.Response(500)
    provider=MixRoute(Store(tmp_path/'p.db'),config(),http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    with pytest.raises(ProviderBlocked,match='ALLOWLIST'):provider.call([{'role':'user','content':'hello'}],'FIXED','unpriced-model',16)
    assert not calls

def test_outside_smart_pool_retains_usage_but_never_delivers(tmp_path):
    s=Store(tmp_path/'p.db')
    def handler(request):
        return httpx.Response(200,json={'id':'r','object':'chat.completion','created':1,'model':'unpriced-model','choices':[{'index':0,'message':{'role':'assistant','content':'x'},'finish_reason':'stop'}],'usage':{'prompt_tokens':2,'completion_tokens':1,'total_tokens':3}})
    with pytest.raises(ProviderBlocked,match='ALLOWLIST'):
        MixRoute(s,config(),http_client=httpx.Client(transport=httpx.MockTransport(handler))).call([{'role':'user','content':'hi'}],'SMART',max_tokens=16)
    record=s.rows('model_calls','demo')[0]
    assert record['total_tokens']==3 and record['status']=='BLOCKED_UNAUTHORIZED_RESOLVED_MODEL'

def test_changed_source_during_call_cannot_write_completed_task(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    class MutatingProvider:
        def call(self,*args,**kwargs):
            e=s.get('evidence','evidence-PROJECT-028','demo');e['content']+='\nNew version';s.put('evidence',e)
            return {'content':'# 目標\n建立音檔轉 MIDI 與 PDF 的驗收計畫\n## 限制\n只使用合成音檔；不得上傳原始音訊到第三方；輸出使用繁體中文\n## 下一步\n- [ ] 一\n- [ ] 二\n- [ ] 三','finish_reason':'stop'}
    out=Orchestrator(s,MutatingProvider()).run({'query':'MIDI 專案','mode':'FIXED','budget':4096,'idempotency_key':'mutate'})
    assert out['reason']=='MEMORY_CHANGED_DURING_EXECUTION'
    assert s.get('tasks','task-PROJECT-028','demo')['status']=='PENDING'

def test_paraphrased_constraint_is_not_silently_accepted(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    ctx=build_context(s,'PROJECT-028','demo',4096,'MIDI 專案','2026-11-26')
    ok,reason=validate('# 目標\n建立音檔轉 MIDI 與 PDF 的驗收計畫\n## 限制\n只用資料\n## 下一步\n- [ ] 一\n- [ ] 二\n- [ ] 三',ctx)
    assert not ok and reason=='CRITICAL_CONSTRAINT_OMITTED'

def test_invalidated_delivery_cannot_be_replayed_as_verified(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26');o=Orchestrator(s)
    req={'query':'MIDI 專案','mode':'SIMULATION','budget':4096,'idempotency_key':'original'}
    out=o.run(req);a=out['artifact'];a['verified']=False;s.put('artifacts',a)
    assert o.run(req)['status']=='BLOCKED'
    assert o.run({**req,'idempotency_key':'another'})['status']=='BLOCKED'
    assert s.get('tasks','task-PROJECT-028','demo')['status']=='COMPLETED'

def test_nonmandatory_dependency_needs_full_current_proof_and_is_loaded(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    dependency={**s.get('facts','PROJECT-028-goal-v2','demo'),'id':'extra','kind':'FACT','mandatory':False,'content':'必要依賴測試','trust':'AI','conflict':True,'valid_from':'2027-01-01','evidence_ids':[]}
    s.put('facts',dependency);task=s.get('tasks','task-PROJECT-028','demo');task['dependency_ids'].append('extra');s.put('tasks',task)
    assert not build_context(s,'PROJECT-028','demo',4096,'MIDI 專案','2026-11-26')['feasible']
    dependency.update(trust='SOURCE',conflict=False,valid_from='2026-11-25',evidence_ids=['evidence-PROJECT-028']);s.put('facts',dependency)
    e=s.get('evidence','evidence-PROJECT-028','demo');e['content']+='\n必要依賴測試';s.put('evidence',e)
    ctx=build_context(s,'PROJECT-028','demo',4096,'MIDI 專案','2026-11-26')
    assert ctx['feasible'] and '必要依賴測試' in ctx['messages'][1]['content']

def test_unknown_longer_project_id_does_not_execute_prefix_project(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    out=Orchestrator(s).run({'query':'繼續 PROJECT-0280','mode':'SIMULATION','idempotency_key':'unknown'})
    assert out['status']=='BLOCKED'
    assert s.get('tasks','task-PROJECT-028','demo')['status']=='PENDING'
    assert Orchestrator(s).run({'query':'繼續 PROJECT-028 與 PROJECT-002 的 MIDI 專案','mode':'SIMULATION','idempotency_key':'multi'})['status']=='BLOCKED'

def test_reused_simulation_artifact_preserves_mode(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26');o=Orchestrator(s)
    req={'query':'MIDI 專案','mode':'SIMULATION','idempotency_key':'sim'}
    o.run(req);out=o.run({**req,'mode':'FIXED','idempotency_key':'fixed'})
    assert out['mode']=='SIMULATION' and out['requested_mode']=='FIXED'

def test_nonfinite_budget_cannot_bypass_hard_cap(tmp_path):
    p=MixRoute(Store(tmp_path/'p.db'),config(dev_budget=float('nan')))
    with pytest.raises(ProviderBlocked):p.reserve('over',36)
    with pytest.raises(ProviderBlocked):p.reserve('nan',float('nan'))

def test_concurrent_distinct_requests_with_same_key_never_both_call(tmp_path):
    from concurrent.futures import ThreadPoolExecutor
    import time
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26');calls=[]
    class Provider:
        def call(self,messages,*args,**kwargs):
            calls.append(1);time.sleep(.1)
            goal='完成鋼琴樂理教材的下一階段驗收計畫' if '鋼琴課' in messages[1]['content'] else '建立音檔轉 MIDI 與 PDF 的驗收計畫'
            return {'content':'# 目標\n'+goal+'\n## 限制\n只使用合成音檔；不得上傳原始音訊到第三方；輸出使用繁體中文\n只使用合成資料；輸出使用繁體中文\n## 下一步\n- [ ] 一\n- [ ] 二\n- [ ] 三','finish_reason':'stop'}
    o=Orchestrator(s,Provider())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results=list(pool.map(lambda q:o.run({'query':q,'mode':'FIXED','idempotency_key':'same'}),['MIDI 專案','鋼琴課']))
    assert len(calls)==1
    assert sum(r['status']=='COMPLETED' for r in results)==1

def test_stale_lock_is_reported_and_recoverable_without_silent_reexecution(tmp_path):
    import time
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    with s.connect() as db:db.execute('INSERT INTO task_locks VALUES (?,?,?,?)',('demo','task-PROJECT-028','dead-process',time.time()-86400))
    o=Orchestrator(s);req={'query':'MIDI 專案','mode':'SIMULATION','idempotency_key':'recover'}
    first=o.run(req)
    assert first['status']=='BLOCKED' and first['reason']=='INTERRUPTED_EXECUTION_REQUIRES_RETRY'
    assert o.run(req)['status']=='COMPLETED'

def test_wrong_goal_is_not_verified_even_with_exact_constraints(tmp_path):
    s=Store(tmp_path/'p.db');seed(s,10,42,'2026-11-26')
    ctx=build_context(s,'PROJECT-028','demo',4096,'MIDI 專案','2026-11-26')
    content='# 目標\n完成攝影照片上傳\n## 限制\n只使用合成音檔；不得上傳原始音訊到第三方；輸出使用繁體中文\n## 下一步\n- [ ] 一\n- [ ] 二\n- [ ] 三'
    assert validate(content,ctx)==(False,'CURRENT_GOAL_OMITTED')
