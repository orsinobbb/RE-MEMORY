import json
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.storage.database import Store
from app.engines.mixroute import MixRoute, Settings, ProviderBlocked
from app.engines.task import Orchestrator
from app.main import create_app


class FixtureProvider:
    """Explicit test double; no network, real credentials, or invented billing."""
    settings = Settings(enabled=False, fixed_model='deepseek-v3.2', authorized_models=['deepseek-v3.2', 'claude-sonnet-5-5'])
    def __init__(self): self.calls = []
    def call(self, messages, mode, model=None, *args, **kwargs):
        self.calls.append({'messages': messages, 'mode': mode, 'model': model})
        raw = messages[1]['content'].split('CURRENT_MANDATORY_MEMORY\n', 1)[1].split('\nWORK_STATE', 1)[0]
        facts = json.loads(raw)
        goal = '\n'.join(f['content'] for f in facts if f['kind'] == 'GOAL')
        constraints = '\n'.join(f['content'] for f in facts if f['kind'] == 'CONSTRAINT')
        content = f'## 目標\n{goal}\n## 限制\n{constraints}\n## 下一步\n- [ ] 核對來源\n- [ ] 核對交接\n- [ ] 保存驗收\n'
        return {'id': f'test-double-{len(self.calls)}', 'status': 'TEST_DOUBLE', 'model': model or 'DeepSeek-V3.2', 'requested_model': model or 'auto', 'content': content, 'total_tokens': None, 'request_id': None, 'mode': mode}


def demo(store, provider=None):
    from app.engines.live_demo import LiveDemo
    return LiveDemo(store, provider or FixtureProvider())


def test_budget_window_persists_and_cannot_be_reset(tmp_path):
    store = Store(tmp_path/'budget.db'); p = MixRoute(store, Settings())
    p.reserve('prior', .5)
    first = store.start_budget_window('final', .6)
    p.reserve('new', .4)
    assert Store(store.path).start_budget_window('final', .6) == first
    with pytest.raises(ProviderBlocked, match='BUDGET_LIMIT_REACHED'):
        MixRoute(Store(store.path), Settings()).reserve('blocked', .25)
    assert store.spend()['committed'] == pytest.approx(.9)
    with pytest.raises(ValueError): store.start_budget_window('final', 3)


def test_budget_window_concurrent_reservations_are_atomic(tmp_path):
    store = Store(tmp_path/'budget.db'); store.start_budget_window('final', .5)
    def attempt(i):
        try: MixRoute(Store(store.path), Settings()).reserve(str(i), .35); return True
        except ProviderBlocked: return False
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(attempt, [1,2]))
    assert sum(results) == 1


def test_prepare_preserves_other_data_and_never_resets_completed_stages(tmp_path):
    store = Store(tmp_path/'demo.db'); provider = FixtureProvider(); d = demo(store, provider)
    store.put('projects', {'id':'unrelated','user_id':'demo','project_id':'unrelated','name':'existing','topic':'unrelated','description':'preserve','last_active':'2026-11-25'})
    before = store.get('projects','unrelated','demo')
    state = d.prepare(); assert len(state['stages']) == 2
    first = d.run(1, 'SMART', 'first')
    assert first['status'] == 'COMPLETED'
    again = d.prepare()
    assert again['stages'][0]['status'] == 'COMPLETED'
    assert store.get('projects','unrelated','demo') == before
    assert len(provider.calls) == 1


def test_two_models_empty_sessions_and_exact_prior_artifact_consumption(tmp_path):
    store = Store(tmp_path/'demo.db'); provider = FixtureProvider(); d = demo(store, provider); d.prepare()
    blocked = d.run(2,'FIXED','premature')
    assert blocked['status'] == 'BLOCKED' and not provider.calls
    first = d.run(1,'SMART','first'); second = d.run(2,'FIXED','second')
    assert first['status'] == second['status'] == 'COMPLETED'
    assert first['session_id'] != second['session_id']
    assert all(store.get('sessions', out['session_id'], 'demo')['raw_history_count'] == 0 for out in [first,second])
    assert provider.calls[0]['mode'] == 'SMART' and provider.calls[1]['model'] == 'claude-sonnet-5-5'
    work=json.loads(provider.calls[1]['messages'][1]['content'].split('WORK_STATE\n',1)[1].split('\nSOURCE_EVIDENCE_DATA',1)[0])
    prior=next(a for a in work['artifacts'] if a['id']==first['artifact']['id'])
    assert prior['content']==first['artifact']['content'] and prior['sha256']==first['artifact']['sha256']
    assert second['handoff_proof']['prior_artifact_loaded'] is True
    assert second['artifact']['factual_status']=='CLAIM'


def test_completed_stage_replay_does_not_run_the_next_stage(tmp_path):
    store=Store(tmp_path/'demo.db'); provider=FixtureProvider(); d=demo(store,provider);d.prepare()
    first=d.run(1,'SMART','first'); replay=d.run(1,'SMART','different-key')
    assert replay['status']=='ALREADY_COMPLETED' and replay['artifact']['id']==first['artifact']['id']
    assert replay['api_call_made'] is False and len(provider.calls)==1
    assert d.state()['stages'][1]['status']=='PENDING'


@pytest.mark.parametrize('case',['missing','tampered','unverified_fact'])
def test_second_stage_blocks_unsafe_prior_or_source(tmp_path,case):
    store=Store(tmp_path/'demo.db'); provider=FixtureProvider();d=demo(store,provider);state=d.prepare()
    first=d.run(1,'SMART','first')
    if case=='missing':
        with store.connect() as db:db.execute('DELETE FROM artifacts WHERE id=?',(first['artifact']['id'],))
    elif case=='tampered':
        row=store.get('artifacts',first['artifact']['id'],'demo');row['content']+='tamper';store.put('artifacts',row)
    else:
        f=store.facts(state['project_id'],'demo')[0];f['verification']='UNVERIFIED';store.put('facts',f)
    result=d.run(2,'FIXED','second')
    assert result['status']=='BLOCKED' and len(provider.calls)==1


def test_expected_task_id_cannot_execute_a_different_active_task(tmp_path):
    store=Store(tmp_path/'demo.db');provider=FixtureProvider();d=demo(store,provider);state=d.prepare()
    out=Orchestrator(store,provider).run({'query':state['query'],'project_id':state['project_id'],'task_id':state['stages'][1]['id'],'mode':'FIXED','model':'claude-sonnet-5-5','budget':4096,'idempotency_key':'wrong-stage'})
    assert out['status']=='BLOCKED' and not provider.calls


def test_demo_api_simulation_order_replay_and_origin(tmp_path):
    store=Store(tmp_path/'demo.db');client=TestClient(create_app(store,Settings(enabled=False)))
    prepared=client.post('/api/demo/prepare',json={});assert prepared.status_code==200
    body={'stage':1,'mode':'SIMULATION','idempotency_key':'one'}
    first=client.post('/api/demo/run',json=body).json(); assert first['status']=='COMPLETED'
    replay=client.post('/api/demo/run',json={**body,'idempotency_key':'repeat'}).json(); assert replay['status']=='ALREADY_COMPLETED'
    second=client.post('/api/demo/run',json={'stage':2,'mode':'SIMULATION','idempotency_key':'two'}).json()
    assert second['status']=='COMPLETED' and second['handoff_proof']['prior_artifact_loaded']
    assert not store.rows('model_calls','demo')
    assert client.post('/api/demo/prepare',json={},headers={'Origin':'https://evil.invalid'}).status_code==403


def test_legacy_idempotency_fingerprint_remains_valid(tmp_path):
    import hashlib
    store=Store(tmp_path/'demo.db');d=demo(store);state=d.prepare()
    request={'query':state['query'],'project_id':state['project_id'],'mode':'SIMULATION','budget':4096,'idempotency_key':'legacy'}
    out=Orchestrator(store).run(request)
    old_hash=hashlib.sha256(json.dumps({'query':request['query'],'mode':'SIMULATION','model':None,'project_id':state['project_id'],'strategy':'E'},sort_keys=True).encode()).hexdigest()
    with store.connect() as db:db.execute('UPDATE deliveries SET request_hash=? WHERE key=?',(old_hash,'legacy'))
    replay=Orchestrator(store).run(request)
    assert replay['artifact']['id']==out['artifact']['id'] and replay.get('stored_replay') is True


def test_second_stage_rejects_same_actual_model_and_retains_usage(tmp_path):
    store=Store(tmp_path/'demo.db')
    class Substitution(FixtureProvider):
        def call(self,*args,**kwargs):
            record={**super().call(*args,**kwargs),'model':'claude-sonnet-5-5','user_id':'demo','project_id':''}
            store.put('model_calls',record)
            return record
    provider=Substitution();d=demo(store,provider);d.prepare()
    first=d.run(1,'SMART','first');out=d.run(2,'FIXED','second')
    assert provider.calls[1]['model']=='deepseek-v3.2'
    assert out['status']=='BLOCKED' and out['reason']=='CROSS_MODEL_RESOLVED_TO_PRIOR_MODEL'
    assert d.state()['stages'][1]['status']=='PENDING'
    assert len(store.rows('model_calls','demo'))==2 and out['model_call']['model']==first['model_call']['model']
    assert len(store.rows('artifacts','demo',d.state()['project_id']))==1


def test_concurrent_completed_stages_return_requested_stage_and_replay_label(tmp_path,monkeypatch):
    store=Store(tmp_path/'demo.db');provider=FixtureProvider();d=demo(store,provider);d.prepare()
    original=d.orchestrator.run;completed={}
    def concurrent_completion(request,user='demo'):
        other=demo(store,provider)
        completed[1]=other.run(1,'SMART','other-first')
        completed[2]=other.run(2,'FIXED','other-second')
        return original(request,user)
    monkeypatch.setattr(d.orchestrator,'run',concurrent_completion)
    replay=d.run(1,'SMART','racing-first')
    assert replay['artifact']['id']==completed[1]['artifact']['id']
    assert replay['artifact']['id']!=completed[2]['artifact']['id']
    assert replay['stored_replay'] is True and replay['api_call_made'] is False
    assert len(provider.calls)==2
