import httpx,pytest
from concurrent.futures import ThreadPoolExecutor
from app.storage.database import Store
from app.engines.mixroute import MixRoute,Settings,ProviderBlocked

def config(**overrides):
    return Settings(base_url="https://api.mixroute.ai/v1",api_key="test-not-a-real-key",smart_key="test-smart-not-real",fixed_model="test-model",smart_model="auto",authorized_models=["test-model"],max_price=.42,context_limit=163840,enabled=True,max_retries=1,**overrides)

def test_unknown_price_and_empty_pool_block_before_network(tmp_path):
    s=Store(tmp_path/"p.db");c=config();c.max_price=None
    with pytest.raises(ProviderBlocked):MixRoute(s,c).call([{"role":"user","content":"hello"}],"FIXED",max_tokens=16)
    c=config();c.authorized_models=[]
    with pytest.raises(ProviderBlocked):MixRoute(s,c).call([{"role":"user","content":"hello"}],"SMART",max_tokens=16)
    assert s.rows("model_calls","demo")==[]

def test_real_sdk_parses_usage_and_keeps_billed_cost_unknown(tmp_path):
    s=Store(tmp_path/"p.db")
    def handler(request):
        return httpx.Response(200,json={"id":"chatcmpl-test","object":"chat.completion","created":1,"model":"test-model","choices":[{"index":0,"message":{"role":"assistant","content":"# 目標\n測試"},"finish_reason":"stop"}],"usage":{"prompt_tokens":20,"completion_tokens":10,"total_tokens":30}},headers={"x-request-id":"request-42"})
    out=MixRoute(s,config(),http_client=httpx.Client(transport=httpx.MockTransport(handler))).call([{"role":"user","content":"hello"}],"FIXED",max_tokens=16)
    assert out["input_tokens"]==20 and out["output_tokens"]==10 and out["total_tokens"]==30
    assert out["request_id"]=="request-42" and out["response_id"]=="chatcmpl-test"
    assert out["cost_usd"] is None
    assert out["cost_upper_bound_usd"]>0 and out["content"]=="# 目標\n測試"
    assert s.rows("model_calls","demo")[0]["total_tokens"]==30

def test_finite_retries_and_unknown_timeout_cost_reserved(tmp_path):
    s=Store(tmp_path/"p.db");attempts=[]
    def handler(request):
        attempts.append(1)
        return httpx.Response(503,json={"error":{"message":"test unavailable","type":"server_error"}})
    with pytest.raises(ProviderBlocked):MixRoute(s,config(),http_client=httpx.Client(transport=httpx.MockTransport(handler))).call([{"role":"user","content":"hello"}],"FIXED",max_tokens=16)
    assert len(attempts)==2
    assert s.spend()["unsettled"]>0

def test_atomic_reservations_cannot_cross_cap(tmp_path):
    s=Store(tmp_path/"p.db");provider=MixRoute(s,config(dev_budget=.001,initial_budget=.001))
    def reserve(i):
        try:provider.reserve(str(i),.0006);return True
        except ProviderBlocked:return False
    with ThreadPoolExecutor(max_workers=2) as pool:result=list(pool.map(reserve,[1,2]))
    assert sum(result)==1 and s.spend()["committed"]<=.001
