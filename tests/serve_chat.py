"""Loopback synthetic chat fixture: all HTTP inference intercepted locally."""
import json, tempfile
from pathlib import Path
import httpx,uvicorn
from app.main import create_app
from app.storage.database import Store
from app.engines.mixroute import Settings,MixRoute

def handler(request):
    current=json.loads(json.loads(request.content)['messages'][-1]['content'])
    content=current['content']
    if content.startswith('FAIL_PAID_SYNTHETIC'):return httpx.Response(503,json={'error':{'message':'synthetic outage','type':'server_error'}})
    return httpx.Response(200,json={'id':'fixture-response','model':'fixture','object':'chat.completion','created':1,'choices':[{'index':0,'message':{'role':'assistant','content':json.dumps({'reply':'合成回覆：'+content,'memories':[{'kind':'PREFERENCE','content':content,'source_message_id':current['source_message_id'],'source_quote':content}]},ensure_ascii=False)},'finish_reason':'stop'}],'usage':{'prompt_tokens':30,'completion_tokens':20,'total_tokens':50}})

if __name__=='__main__':
    with tempfile.TemporaryDirectory(prefix='rememory-chat-') as folder:
        store=Store(Path(folder)/'fixture.db')
        settings=Settings(enabled=True,api_key='fixture-key',smart_key='fixture-smart',fixed_model='fixture',authorized_models=['fixture'],max_price=.01,max_retries=0)
        provider=MixRoute(store,settings,http_client=httpx.Client(transport=httpx.MockTransport(handler)))
        uvicorn.run(create_app(store,settings,provider),host='127.0.0.1',port=8793)
