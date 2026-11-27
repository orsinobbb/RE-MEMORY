from fastapi.testclient import TestClient
from app.main import create_app
from app.storage.database import Store
from app.engines.mixroute import Settings
from benchmarks.generators.synthetic import seed

def client(tmp_path):
    s=Store(tmp_path/"api.db");seed(s,10,42,"2026-11-26")
    return s,TestClient(create_app(s,Settings()))

def test_real_state_memory_and_local_health(tmp_path):
    s,c=client(tmp_path)
    assert c.get('/api/health').json()['status']=='ok'
    assert c.get('/api/state').json()['stats']['projects']==10
    data=c.get('/api/memory',params={'project_id':'PROJECT-028'}).json()
    assert data['project']['name']=='音訊轉換系統' and data['facts'] and data['evidence']
    assert c.get('/api/memory',params={'project_id':'missing'}).status_code==404

def test_stream_retrieval_and_artifact_download(tmp_path):
    s,c=client(tmp_path)
    req={'query':'昨天的音樂專案','budget':4096,'strategy':'E'}
    out=c.post('/api/retrieve',json=req).json()
    assert out['project_id']=='PROJECT-028' and out['context']['coverage']==1
    stream=c.post('/api/retrieve/stream',json=req)
    assert 'event: round' in stream.text and 'event: result' in stream.text
    session=c.post('/api/session',json={}).json()
    result=c.post('/api/execute',json={**req,'mode':'SIMULATION','session_id':session['id'],'idempotency_key':'test'}).json()
    assert result['status']=='COMPLETED'
    assert '不得上傳原始音訊' in c.get('/api/artifact/'+result['artifact']['id']).text

def test_limits_origin_guard_and_key_absence(tmp_path):
    s,c=client(tmp_path)
    assert c.post('/api/retrieve',json={'query':'music','budget':999999}).status_code==422
    assert c.post('/api/retrieve',json={'query':'music','budget':4096},headers={'Origin':'https://malicious.invalid'}).status_code==403
    assert c.get('/.env').status_code==404
    assert 'api_key' not in c.get('/api/state').text.lower()
    assert c.post('/api/execute',json={'query':'MIDI 專案','budget':4096,'mode':'FIXED','idempotency_key':'live-disabled'}).json()['status']=='BLOCKED'

def test_missing_usage_is_unknown_in_resource_totals(tmp_path):
    s,c=client(tmp_path);s.put('model_calls',{'id':'failed','user_id':'demo','status':'FAILED','total_tokens':None,'cost_usd':None})
    resource=c.get('/api/state').json()['resources']
    assert resource['api_tokens'] is None and resource['known_api_tokens']==0 and resource['usage_unknown_calls']==1
