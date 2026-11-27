import json,queue,threading,uuid
from datetime import date,datetime,timezone
from pathlib import Path
from typing import Literal
from fastapi import FastAPI,HTTPException,Request
from fastapi.responses import FileResponse,Response,StreamingResponse,JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel,Field
from app.storage.database import Store
from app.engines.mixroute import MixRoute,Settings,ProviderBlocked
from app.engines.retrieval import Router
from app.engines.task import Orchestrator
from app.engines.evaluation import evaluate
from app.engines.memory_evolution import MemoryEvolution
from app.engines.artifact_revalidation import ArtifactRevalidation
from app.engines.live_demo import LiveDemo
from benchmarks.generators.synthetic import seed
from app.chat_routes import mount_chat_routes

ROOT=Path(__file__).resolve().parents[1]
class RetrievalRequest(BaseModel):
    query:str=Field(min_length=1,max_length=2000)
    budget:int=Field(default=4096,ge=128,le=16384)
    strategy:Literal["A","B","C","D","E","F"]="E"
    reference_date:date=date(2026,11,26)
class ExecuteRequest(RetrievalRequest):
    mode:Literal["SIMULATION","FIXED","SMART"]="SIMULATION"
    model:str|None=None
    session_id:str|None=None
    project_id:str|None=None
    idempotency_key:str=Field(min_length=1,max_length=200)
class SessionRequest(BaseModel):
    previous_session_id:str|None=None
class MemoryMutationRequest(BaseModel):
    reference_date:date=date(2026,11,27)
class FactRevisionRequest(MemoryMutationRequest):
    content:str=Field(min_length=1,max_length=4000)
    evidence_id:str=Field(min_length=1,max_length=200)
class ArtifactRevisionRequest(MemoryMutationRequest):
    content:str=Field(min_length=1,max_length=20000)
    snapshot:str=Field(min_length=64,max_length=64)
    acknowledged:bool=False
class DemoRunRequest(BaseModel):
    stage:Literal[1,2]
    mode:Literal['SMART','FIXED','SIMULATION']
    idempotency_key:str=Field(min_length=1,max_length=200)
class BenchmarkRequest(BaseModel):
    count:Literal[10,100,1000]=10
    budgets:list[int]=Field(default_factory=lambda:[4096],min_length=1,max_length=5)
    strategies:list[Literal["A","B","C","D","E","F"]]=Field(default_factory=lambda:list("ABCDEF"),min_length=1,max_length=6)
    live:bool=False

def create_app(store=None,settings=None,provider=None):
    s=store or Store(ROOT/"data/runtime/rememory.db")
    if not s.projects("demo"):seed(s,10,42,"2026-11-26")
    settings=settings or Settings.from_env();provider=provider or MixRoute(s,settings);orchestrator=Orchestrator(s,provider)
    live_demo=LiveDemo(s,provider)
    app=FastAPI(title="RE:MEMORY",version="0.1.0");app.state.store=s;app.state.settings=settings
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=["localhost","127.0.0.1","testserver"])
    @app.middleware("http")
    async def local_origin(request:Request,call_next):
        origin=request.headers.get("origin")
        if request.method not in ("GET","HEAD","OPTIONS") and origin and origin!=str(request.base_url).rstrip('/'):
            return JSONResponse({"error":"CROSS_ORIGIN_MUTATION_BLOCKED"},status_code=403)
        response=await call_next(request)
        response.headers["X-Content-Type-Options"]="nosniff";response.headers["Referrer-Policy"]="no-referrer"
        response.headers["Content-Security-Policy"]="default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'"
        return response
    @app.get("/api/health")
    def health():return {"status":"ok","dataset":"DEMO","service":"RE:MEMORY"}
    @app.get("/api/state")
    def state():
        calls=s.rows("model_calls","demo");spend=s.spend()
        reference=max(['2026-11-26']+[f['valid_from'][:10] for f in s.rows('facts','demo') if not f.get('superseded')])
        actual=sum(c["cost_usd"] for c in calls) if calls and all(c.get("cost_usd") is not None for c in calls) else (0 if not calls else None)
        return {"dataset":"DEMO","reference_date":reference,"projects":s.projects("demo"),"tasks":s.rows("tasks","demo"),"events":s.rows("events","demo"),
          "resources":{"api_calls":sum(c.get("attempts",c.get("retry_count",0)+1) for c in calls),"api_tokens":sum(c['total_tokens'] for c in calls) if all(c.get('total_tokens') is not None and c.get('retry_count',0)==0 for c in calls) else None,"known_api_tokens":sum(c.get('total_tokens') or 0 for c in calls),"api_cost_usd":actual,"api_reserved_usd":spend["unsettled"],"usage_unknown_calls":sum(c.get("total_tokens") is None or c.get('retry_count',0)>0 for c in calls)},
          "settings":{"fixed_model":settings.fixed_model,"smart_model":settings.smart_model,"enabled":settings.enabled,"configured":bool(settings.api_key and settings.smart_key)},
          "stats":{name:len(s.rows(table,"demo")) for name,table in (("projects","projects"),("facts","facts"),("aliases","aliases"),("artifacts","artifacts"))}}
    @app.get("/api/memory")
    def memory(project_id:str,q:str=""):
        p=s.get("projects",project_id,"demo")
        if not p:raise HTTPException(404,"PROJECT_NOT_FOUND")
        facts=s.facts(project_id,"demo",current=False)
        if q:facts=[f for f in facts if q.casefold() in f["content"].casefold()]
        return {"project":p,"facts":facts,"aliases":s.rows("aliases","demo",project_id),"evidence":s.rows("evidence","demo",project_id),"relations":[r for r in s.rows("relations","demo") if project_id in (r["from"],r["to"])],"tasks":s.rows("tasks","demo",project_id),"artifacts":s.rows("artifacts","demo",project_id)}
    @app.post("/api/retrieve")
    def retrieve(r:RetrievalRequest):return Router(s).retrieve(r.query,"demo",r.budget,r.reference_date.isoformat(),r.strategy)
    def repair_action(action):
        try:return action()
        except ValueError as error:raise HTTPException(409,str(error)) from error
    @app.get('/api/demo')
    def demo_state():return live_demo.state()
    @app.post('/api/demo/prepare')
    def prepare_demo():return live_demo.prepare()
    @app.post('/api/demo/run')
    def run_demo(r:DemoRunRequest):return repair_action(lambda:live_demo.run(r.stage,r.mode,r.idempotency_key))
    @app.post('/api/memory/aliases/{id}/confirm')
    def confirm_alias(id:str,r:MemoryMutationRequest):
        return repair_action(lambda:MemoryEvolution(s).confirm_alias('demo',id,r.reference_date.isoformat()))
    @app.post('/api/memory/facts/{id}/revise')
    def revise_fact(id:str,r:FactRevisionRequest):
        return repair_action(lambda:MemoryEvolution(s).update_fact('demo',id,r.content,r.evidence_id,r.reference_date.isoformat(),require_supported=True))
    @app.get('/api/artifact/{id}/review')
    def review_artifact(id:str,reference_date:date=date(2026,11,27)):
        return repair_action(lambda:ArtifactRevalidation(s).review('demo',id,reference_date.isoformat()))
    @app.post('/api/artifact/{id}/revalidate')
    def revalidate_artifact(id:str,r:ArtifactRevisionRequest):
        return repair_action(lambda:ArtifactRevalidation(s).save('demo',id,r.content,r.snapshot,r.acknowledged,r.reference_date.isoformat()))
    @app.post("/api/retrieve/stream")
    def stream(r:RetrievalRequest):
        q=queue.Queue()
        def work():
            try:
                result=Router(s).retrieve(r.query,"demo",r.budget,r.reference_date.isoformat(),r.strategy,lambda row:q.put(("round",row)))
                q.put(("result",result))
            except Exception:q.put(("error",{"error":"RETRIEVAL_FAILED"}))
            finally:q.put(None)
        def events():
            threading.Thread(target=work,daemon=True).start()
            while True:
                item=q.get()
                if item is None:break
                yield f"event: {item[0]}\ndata: {json.dumps(item[1],ensure_ascii=False)}\n\n"
        return StreamingResponse(events(),media_type="text/event-stream")
    @app.post("/api/session")
    def session(r:SessionRequest):return orchestrator.new_session(previous=r.previous_session_id)
    @app.post("/api/execute")
    def execute(r:ExecuteRequest):return orchestrator.run(r.model_dump(mode="json"))
    @app.get("/api/models")
    def models():
        # Only verified-priced models are selectable; the catalogue is not a pool proof.
        allowed=list(dict.fromkeys([x for x in [settings.fixed_model]+settings.authorized_models if x]))
        return {"fixed":[{"id":m} for m in allowed],"smart":[{"id":settings.smart_model}] if settings.smart_key else [],"configured":bool(settings.api_key and settings.smart_key),"enabled":settings.enabled}
    @app.post("/api/benchmark")
    def benchmark(r:BenchmarkRequest):
        if any(b not in (1024,2048,4096,8192,16384) for b in r.budgets):raise HTTPException(422,"Unsupported context budget")
        if r.live:raise HTTPException(409,"Use the bounded benchmarks/live.py CLI for paid trials; UI benchmark is offline")
        result=evaluate(r.count,r.budgets,r.strategies)
        s.put("evaluations",{"id":result["id"],"user_id":"demo","project_id":"","created_at":datetime.now(timezone.utc).isoformat(),"result":result})
        (ROOT/"benchmarks/results").mkdir(parents=True,exist_ok=True)
        (ROOT/"benchmarks/results"/(result["id"]+".json")).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n")
        return result
    @app.get("/api/benchmark/latest")
    def latest():
        rows=s.rows("evaluations","demo");return max(rows,key=lambda r:r.get("created_at",""))["result"] if rows else {"results":[]}
    @app.get("/api/export/{id}")
    def export(id:str):
        row=s.get("evaluations",id,"demo")
        if not row:raise HTTPException(404,"RESULT_NOT_FOUND")
        return Response(json.dumps(row["result"],ensure_ascii=False,indent=2),media_type="application/json",headers={"Content-Disposition":'attachment; filename="re-memory-benchmark.json"'})
    @app.get("/api/artifact/{id}")
    def artifact(id:str):
        row=s.get("artifacts",id,"demo")
        if not row:raise HTTPException(404,"ARTIFACT_NOT_FOUND")
        return Response(row["content"],media_type="text/markdown",headers={"Content-Disposition":'attachment; filename="re-memory-handoff.md"'})
    @app.get("/")
    def index():return FileResponse(ROOT/"frontend/index.html")
    @app.get("/style.css")
    def style():return FileResponse(ROOT/"frontend/style.css")
    @app.get("/app.js")
    def script():return FileResponse(ROOT/"frontend/app.js")
    mount_chat_routes(app,s,provider)
    return app

app=create_app()
