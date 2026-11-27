"""Catch lost persistence, cross-scope recall, paid duplicates and fabricated memory."""
import json, threading, time
from concurrent.futures import ThreadPoolExecutor
import httpx, pytest
from app.storage.database import Store
from app.engines.mixroute import MixRoute, Settings

@pytest.fixture
def setup(tmp_path):
    store=Store(tmp_path/'chat.db')
    store.put('projects',{'id':'p1','user_id':'demo','name':'合成行程'})
    store.put('projects',{'id':'p2','user_id':'demo','name':'合成音樂'})
    seen=[]
    def handler(request):
        payload=json.loads(request.content);seen.append(payload)
        current=json.loads(payload['messages'][-1]['content'])
        body={'reply':'記住了，接下來一起規劃。','memories':[{'kind':'CONSTRAINT','content':'請使用繁體中文','source_message_id':current['source_message_id'],'source_quote':'請使用繁體中文'}]}
        return response(body)
    settings=Settings(api_key='not-real-key',smart_key='not-real-smart',fixed_model='test-model',smart_model='auto',authorized_models=['test-model'],max_price=.42,enabled=True,max_retries=0)
    provider=MixRoute(store,settings,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    from app.engines.chat import ChatEngine
    return store,ChatEngine(store,provider),seen,provider

def response(body,finish='stop'):
    return httpx.Response(200,json={'id':'chat-test','model':'test-model','object':'chat.completion','created':1,'choices':[{'index':0,'message':{'role':'assistant','content':body if isinstance(body,str) else json.dumps(body,ensure_ascii=False)},'finish_reason':finish}],'usage':{'prompt_tokens':30,'completion_tokens':20,'total_tokens':50}})

def send(engine,conv,key='one',content='請使用繁體中文'):
    return engine.send('demo',conv['id'],content,key)

def test_persistent_chat_and_cross_conversation_memory(setup):
    store,engine,seen,provider=setup;c=engine.create('demo','p1');out=send(engine,c)
    assert out['status']=='COMPLETED'
    from app.engines.chat import ChatEngine
    restored=ChatEngine(Store(store.path),provider).conversation('demo',c['id'])
    assert [m['role'] for m in restored['messages']]==['user','assistant']
    assert restored['memories'][0]['status']=='CANDIDATE'
    other=engine.create('demo','p1');send(engine,other,'second')
    assert '請使用繁體中文' in seen[1]['messages'][1]['content']
    assert len(engine.state('demo','p1')['memories'])==1

def test_rejects_forged_sources(setup):
    store,engine,_,provider=setup
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:response({'reply':'收到','memories':[{'kind':'NOTE','content':'假記憶','source_message_id':'someone-else','source_quote':'假引用'}]}))))
    c=engine.create('demo','p1');out=send(engine,c)
    assert out['status']=='COMPLETED' and out['warnings']
    assert engine.state('demo','p1')['memories']==[]

def test_scope_and_user_isolation(setup):
    store,engine,seen,_=setup;c=engine.create('demo','p1');send(engine,c)
    c2=engine.create('demo','p2');send(engine,c2,'two',content='規劃音樂')
    assert '請使用繁體中文' not in seen[1]['messages'][1]['content']
    with pytest.raises(ValueError):engine.conversation('other',c['id'])
    with pytest.raises(ValueError):engine.create('demo','missing')

def test_idempotency_and_conflict(setup):
    store,engine,_,_=setup;c=engine.create('demo','p1');first=send(engine,c);second=send(engine,c)
    assert second['stored_replay'] and second['reply']==first['reply']
    assert len(store.rows('model_calls','demo'))==1
    for overrides in ({'content':'改掉'}, {'budget':8192},{'mode':'FIXED','model':'test-model'}):
        params=dict(content='請使用繁體中文',key='one');params.update(overrides)
        with pytest.raises(ValueError):engine.send('demo',c['id'],**params)

def test_concurrent_send(setup):
    store,engine,_,provider=setup;entered=threading.Event();release=threading.Event()
    def slow(r):entered.set();release.wait(3);return response({'reply':'完成','memories':[]})
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(slow)))
    c=engine.create('demo','p1')
    with ThreadPoolExecutor(2) as pool:
        work=pool.submit(send,engine,c);assert entered.wait(2)
        with pytest.raises(ValueError,match='IN_PROGRESS'):send(engine,c,'different')
        release.set();assert work.result()['status']=='COMPLETED'
    assert len(store.rows('model_calls','demo'))==1

def test_stale_memory(setup):
    store,engine,_,provider=setup;c=engine.create('demo','p1');send(engine,c)
    memory=engine.state('demo','p1')['memories'][0]
    def changed(r):engine.mutate('demo',memory['id'],'FORGET');return response({'reply':'過期','memories':[]})
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(changed)))
    out=send(engine,c,'second')
    assert out['status']=='FAILED' and out['error']=='CHAT_MEMORY_CHANGED'
    assert len(engine.conversation('demo',c['id'])['messages'])==3

def test_expired_owner_cannot_commit(setup):
    store,engine,_,provider=setup;c=engine.create('demo','p1')
    def lost(r):
        with store.connect() as db:db.execute('UPDATE chat_locks SET owner=? WHERE conversation_id=?',('new-owner',c['id']))
        return response({'reply':'舊結果','memories':[]})
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lost)))
    out=send(engine,c)
    assert out['status']=='FAILED' and out['error']=='CHAT_LOCK_LOST'
    assert len(engine.conversation('demo',c['id'])['messages'])==1

def test_context_budget_and_constraints(setup):
    store,engine,seen,_=setup;c=engine.create('demo','p1')
    with pytest.raises(ValueError,match='CONTEXT'):engine.send('demo',c['id'],'x'*18000,'oversize',budget=4096)
    assert not store.rows('model_calls','demo')
    send(engine,c);memory=engine.state('demo','p1')['memories'][0]
    engine.mutate('demo',memory['id'],'EDIT','必要限制'+('不可省略'*900))
    with pytest.raises(ValueError,match='CONTEXT'):send(engine,c,'second')
    assert len(store.rows('model_calls','demo'))==1

@pytest.mark.parametrize('body,finish', [('', 'stop'), ('{"reply":"半段"','stop'), ({'reply':'截斷','memories':[]},'length')])
def test_invalid_reply_and_partial_memory(setup,body,finish):
    store,engine,_,provider=setup
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:response(body,finish))))
    c=engine.create('demo','p1');out=send(engine,c)
    assert out['status']=='FAILED'
    assert len(engine.conversation('demo',c['id'])['messages'])==1
    assert len(store.rows('model_calls','demo'))==1
    assert store.spend()['committed']>0

def test_forget_not_reextracted(setup):
    store,engine,_,_=setup;c=engine.create('demo','p1');send(engine,c)
    mem=engine.state('demo','p1')['memories'][0];engine.mutate('demo',mem['id'],'CONFIRM')
    engine.mutate('demo',mem['id'],'EDIT','改成英文')
    edited=engine.state('demo','p1')['memories'][0]
    assert edited['versions'][0]['content']=='請使用繁體中文'
    engine.mutate('demo',mem['id'],'FORGET');other=engine.create('demo','p1');send(engine,other,'other')
    assert engine.state('demo','p1')['memories']==[]

@pytest.mark.parametrize('body',[[],{'reply':42,'memories':[]},{'reply':'收到','memories':[{'kind':[], 'content':None}]}])
def test_wrong_json_types_do_not_crash(setup,body):
    store,engine,_,provider=setup
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:response(body))))
    out=send(engine,engine.create('demo','p1'))
    assert out['status'] in ('FAILED','COMPLETED')
    assert len(store.rows('model_calls','demo'))==1

def test_complete_turns_only_in_history(setup):
    store,engine,seen,provider=setup;c=engine.create('demo','p1');send(engine,c)
    broken=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:response('', 'stop'))))
    engine.provider=broken;send(engine,c,'failed','失敗輸入');engine.provider=provider
    out=send(engine,c,'next','新的輸入')
    assert out['status']=='COMPLETED'
    prompt=json.dumps(seen[-1]['messages'],ensure_ascii=False)
    assert '失敗輸入' not in prompt and '新的輸入' in prompt
    assert out['context']['history_messages']==2

def test_forgotten_content_not_recreated_under_another_kind(setup):
    store,engine,_,provider=setup
    def preference(r):
        current=json.loads(json.loads(r.content)['messages'][-1]['content'])
        return response({'reply':'收到','memories':[{'kind':'PREFERENCE','content':'請使用繁體中文','source_message_id':current['source_message_id'],'source_quote':'請使用繁體中文'}]})
    engine.provider=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(preference)))
    c=engine.create('demo','p1');send(engine,c)
    memory=engine.state('demo','p1')['memories'][0];engine.mutate('demo',memory['id'],'FORGET')
    engine.provider=provider;send(engine,engine.create('demo','p1'),'different-kind')
    assert engine.state('demo','p1')['memories']==[]

def test_failed_paid_call_returns_its_own_receipt(setup):
    store,engine,_,provider=setup
    failed=MixRoute(store,provider.settings,http_client=httpx.Client(transport=httpx.MockTransport(lambda r:httpx.Response(503,json={'error':{'message':'synthetic outage','type':'server_error'}}))))
    engine.provider=failed;out=send(engine,engine.create('demo','p1'))
    assert out['status']=='FAILED'
    receipt=store.rows('model_calls','demo')[0]
    assert out['usage'] and out['usage']['id']==receipt['id']
    assert out['usage']['cost_upper_bound_usd']>0 and out['usage']['total_tokens'] is None
