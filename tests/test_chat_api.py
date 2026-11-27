from fastapi.testclient import TestClient
import json, httpx
from app.main import create_app
from app.storage.database import Store
from app.engines.mixroute import Settings, MixRoute

def client(tmp_path):
    store=Store(tmp_path/'api.db');settings=Settings(enabled=False)
    return TestClient(create_app(store,settings)),store

def test_chat_api_persistence_and_validation(tmp_path):
    api,store=client(tmp_path)
    response=api.post('/api/chat/conversations',json={'project_id':'PERSONAL'})
    assert response.status_code==200
    id=response.json()['id']
    assert api.get('/api/chat').json()['conversations'][0]['id']==id
    assert api.get(f'/api/chat/conversations/{id}').json()['messages']==[]
    out=api.post(f'/api/chat/conversations/{id}/messages',json={'content':'請使用繁體中文','idempotency_key':'one'})
    assert out.json()['status']=='FAILED' and out.json()['error']=='LIVE_API_DISABLED'
    assert api.get(f'/api/chat/conversations/{id}').json()['messages'][0]['status']=='FAILED'
    assert api.post(f'/api/chat/conversations/{id}/messages',json={'content':' ','idempotency_key':'two'}).status_code==409
    assert api.post(f'/api/chat/conversations/{id}/messages',json={'content':'hi','idempotency_key':'one','mode':'SIMULATION'}).status_code==422
    assert api.post('/api/chat/conversations',json={'project_id':'private'}).status_code==409

def test_chat_origin_and_private_data(tmp_path):
    api,store=client(tmp_path)
    assert api.post('/api/chat/conversations',json={},headers={'Origin':'https://example.net'}).status_code==403
    assert api.get('/chat.js').status_code==200
    assert "script-src 'self'" in api.get('/chat.js').headers['content-security-policy']
    data=api.get('/api/chat').json()
    assert 'api_key' not in json.dumps(data) and 'smart_key' not in json.dumps(data)
