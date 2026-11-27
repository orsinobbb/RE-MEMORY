import hashlib,json,time,uuid
from datetime import datetime
from zoneinfo import ZoneInfo
from .retrieval import Router
from .context_builder import build_context
from .baselines import build_baseline_context
from .mixroute import MixRoute,ProviderBlocked
from .validation import validate
from app.governance.policy import check_tool

class Orchestrator:
    def __init__(self,store,provider=None):self.store=store;self.provider=provider or MixRoute(store)

    def new_session(self,user="demo",previous=None):
        record={"id":str(uuid.uuid4()),"user_id":user,"project_id":"","created_at":datetime.now(ZoneInfo("Asia/Taipei")).isoformat(),"raw_history_count":0,"raw_history":[],"previous_session_id":previous}
        self.store.put("sessions",record);return {k:v for k,v in record.items() if k!="raw_history"}

    def run(self,request,user="demo"):
        start=time.perf_counter();query=request.get("query","");mode=request.get("mode","SIMULATION");budget=request.get("budget",4096)
        key=request.get("idempotency_key") or str(uuid.uuid4());session_id=request.get("session_id")
        identity={"query":query,"mode":mode,"model":request.get("model"),"project_id":request.get("project_id"),"strategy":request.get("strategy","E")}
        if request.get('task_id'):identity['task_id']=request['task_id']
        if request.get('different_from_model'):identity['different_from_model']=request['different_from_model']
        fingerprint=hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
        base={"mode":mode,"session_id":session_id,"elapsed_ms":0}
        def blocked(reason,**extra):return {**base,"status":"BLOCKED","reason":str(reason),"elapsed_ms":round((time.perf_counter()-start)*1000,2),**extra}
        def valid_artifact(a):return bool(a and a.get('verified') and hashlib.sha256(a['content'].encode()).hexdigest()==a.get('sha256'))
        if mode not in ("SIMULATION","FIXED","SMART"):return blocked("INVALID_MODE")
        if session_id and not self.store.get("sessions",session_id,user):return blocked("SESSION_NOT_FOUND")
        with self.store.connect() as db:prior=db.execute("SELECT request_hash,result FROM deliveries WHERE user_id=? AND key=?",(user,key)).fetchone()
        if prior:
            if prior["request_hash"]!=fingerprint:return blocked("IDEMPOTENCY_KEY_REUSED_FOR_DIFFERENT_REQUEST")
            saved=json.loads(prior["result"])
            if not valid_artifact(self.store.get('artifacts',saved['artifact']['id'],user)):return blocked('ARTIFACT_REVALIDATION_REQUIRED')
            return {**saved,'stored_replay':True,'api_call_made':False}
        if not session_id:session_id=self.new_session(user)["id"];base["session_id"]=session_id
        strategy=request.get("strategy","E")
        retrieval=Router(self.store).retrieve(query,user,budget,request.get("reference_date","2026-11-26"),strategy)
        pid=request.get("project_id") or retrieval["project_id"]
        if not pid:return blocked(retrieval["clarification"] or retrieval["stop_reason"],retrieval=retrieval)
        if not self.store.get("projects",pid,user):return blocked("PROJECT_NOT_FOUND")
        tasks=self.store.rows("tasks",user,pid)
        active=next((t for t in tasks if t["status"]=="PENDING"),None)
        if active and request.get('task_id') and active['id']!=request['task_id']:
            return blocked('ACTIVE_TASK_DOES_NOT_MATCH_REQUEST',project_id=pid)
        if not active:
            if request.get('task_id'):
                requested=next((t for t in tasks if t['id']==request['task_id']),None)
                if not requested or requested['status']!='COMPLETED':return blocked('REQUESTED_TASK_NOT_COMPLETED',project_id=pid)
                artifact=self.store.get('artifacts',requested.get('artifact_id'),user)
                if not valid_artifact(artifact):return blocked('ARTIFACT_REVALIDATION_REQUIRED',project_id=pid)
                with self.store.connect() as db:
                    delivered=db.execute('SELECT result FROM deliveries WHERE user_id=? AND task_id=?',(user,requested['id'])).fetchone()
                saved=json.loads(delivered['result']) if delivered else {}
                return {**base,**saved,'status':'ALREADY_COMPLETED','project_id':pid,'artifact':artifact,'mode':artifact.get('mode','UNKNOWN'),
                        'stored_replay':True,'api_call_made':False,'reason':'指定任務已完成；讀取其保存成品'}
            done=[t for t in tasks if t["status"]=="COMPLETED" and t.get("artifact_id")]
            artifact=self.store.get("artifacts",done[-1]["artifact_id"],user) if done else None
            if not valid_artifact(artifact):return blocked('ARTIFACT_REVALIDATION_REQUIRED',project_id=pid)
            return {**base,"mode":artifact.get('mode','UNKNOWN'),"requested_mode":mode,"status":"ALREADY_COMPLETED","project_id":pid,"reason":"沒有未完成任務；已完成工作不重複執行","artifact":artifact,'stored_replay':True,'api_call_made':False}
        context=build_context(self.store,pid,user,budget,query,request.get("reference_date","2026-11-26"))
        if not context["feasible"]:return blocked("MEMORY_OR_BUDGET_INCOMPLETE",project_id=pid,retrieval=retrieval)
        model_context=build_baseline_context(self.store,pid,user,budget,query,request.get('reference_date','2026-11-26'),strategy) if strategy in ('A','B','C','D') else context
        if not model_context['feasible']:return blocked('BASELINE_BUDGET_EXCEEDED',project_id=pid,retrieval=retrieval)
        try:check_tool(active.get("tool"))
        except ValueError as error:return blocked(error)
        owner=str(uuid.uuid4())
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            delivered=db.execute('SELECT request_hash,result FROM deliveries WHERE user_id=? AND key=?',(user,key)).fetchone()
            if delivered:
                if delivered['request_hash']!=fingerprint:return blocked('IDEMPOTENCY_KEY_REUSED_FOR_DIFFERENT_REQUEST')
                saved=json.loads(delivered['result'])
                if not valid_artifact(self.store.get('artifacts',saved['artifact']['id'],user)):return blocked('ARTIFACT_REVALIDATION_REQUIRED')
                return {**saved,'stored_replay':True,'api_call_made':False}
            claim=db.execute('SELECT * FROM execution_claims WHERE user_id=? AND key=?',(user,key)).fetchone()
            if claim:
                if time.time()-claim['started']>300:
                    db.execute('DELETE FROM execution_claims WHERE user_id=? AND owner=?',(user,claim['owner']))
                    db.execute('DELETE FROM task_locks WHERE user_id=? AND owner=?',(user,claim['owner']))
                    return blocked('INTERRUPTED_EXECUTION_REQUIRES_RETRY')
                if claim['request_hash']!=fingerprint:return blocked('IDEMPOTENCY_KEY_REUSED_FOR_DIFFERENT_REQUEST')
                return {**base,'status':'IN_PROGRESS','project_id':pid,'reason':'此請求已有執行者'}
            existing=db.execute("SELECT owner,started FROM task_locks WHERE user_id=? AND task_id=?",(user,active["id"])).fetchone()
            if existing:
                if time.time()-existing['started']>300:
                    db.execute('DELETE FROM task_locks WHERE user_id=? AND task_id=?',(user,active['id']))
                    db.execute('DELETE FROM execution_claims WHERE user_id=? AND owner=?',(user,existing['owner']))
                    return blocked('INTERRUPTED_EXECUTION_REQUIRES_RETRY')
                return {**base,"status":"IN_PROGRESS","project_id":pid,"reason":"此任務已有執行者"}
            # Re-check status inside the lock transaction.
            latest=json.loads(db.execute("SELECT data FROM tasks WHERE user_id=? AND id=?",(user,active["id"])).fetchone()[0])
            if latest["status"]!="PENDING":return blocked('TASK_CHANGED_RETRY_REQUIRED',project_id=pid)
            db.execute("INSERT INTO task_locks VALUES (?,?,?,?)",(user,active["id"],owner,time.time()))
            db.execute('INSERT INTO execution_claims VALUES (?,?,?,?,?)',(user,key,fingerprint,owner,time.time()))
        call=None
        try:
            if mode=="SIMULATION":
                goal=next(f["content"] for f in context["loaded"] if f.get("kind")=="GOAL")
                constraints=[f["content"] for f in context["loaded"] if f.get("kind")=="CONSTRAINT"]
                content="# 接續工作驗收清單\n\nDEMO / SIMULATION — 本機白名單工具產生，未呼叫模型。\n\n## 目標\n"+goal+"\n\n## 限制\n"+"\n".join(constraints)+"\n\n## 下一步\n- [ ] 建立合成資料輸入與預期輸出。\n- [ ] 驗證版本、來源及必要限制。\n- [ ] 逐項執行驗收並記錄結果；本成果僅為清單，未宣稱完成後續測試。\n\n來源："+", ".join(context["manifest"]["evidence_references"])+"\n"
            else:
                call=self.provider.call(model_context["messages"],mode,request.get("model"),model_context["token_breakdown"]["output_reserve"],user,parameter="standard")
                if request.get('different_from_model') and (call.get('model') or '').casefold()==request['different_from_model'].casefold():
                    return blocked('CROSS_MODEL_RESOLVED_TO_PRIOR_MODEL',project_id=pid,model_call=call,retrieval=retrieval)
                content=call["content"]
                if call.get("finish_reason")=="length":return blocked("ARTIFACT_TRUNCATED",project_id=pid,model_call=call,retrieval=retrieval)
            valid,result=validate(content,context)
            if not valid:return blocked("ARTIFACT_VALIDATION_FAILED:"+result,project_id=pid,model_call=call,retrieval=retrieval)
            artifact={"id":"artifact-"+str(uuid.uuid4()),"user_id":user,"project_id":pid,"task_id":active["id"],"content":content,"sha256":result,"verified":True,"verification_scope":"STRUCTURE_CURRENT_GOAL_AND_CONSTRAINTS","factual_status":"CLAIM","mode":mode,"created_at":datetime.now(ZoneInfo("Asia/Taipei")).isoformat()}
            out={**base,"status":"COMPLETED","project_id":pid,"artifact":artifact,"model_call":call,"retrieval":retrieval,"elapsed_ms":round((time.perf_counter()-start)*1000,2)}
            with self.store.connect() as db:
                db.execute("BEGIN IMMEDIATE")
                current=build_context(self.store,pid,user,budget,query,request.get("reference_date","2026-11-26"))
                if not current["feasible"] or current["manifest"]["memory_snapshot"]!=context["manifest"]["memory_snapshot"]:
                    return blocked("MEMORY_CHANGED_DURING_EXECUTION",project_id=pid,model_call=call)
                active.update(status="COMPLETED",artifact_id=artifact["id"])
                self.store.put("artifacts",artifact,db);self.store.put("tasks",active,db)
                self.store.put("events",{"id":str(uuid.uuid4()),"user_id":user,"project_id":pid,"type":"TASK_COMPLETED","date":"2026-11-26","detail":active["title"],"artifact_id":artifact["id"],"evidence_ids":[artifact["id"]]},db)
                self.store.put("snapshots",{"id":context["manifest"]["memory_snapshot"],"user_id":user,"project_id":pid,"manifest":context["manifest"]},db)
                db.execute("INSERT INTO deliveries VALUES (?,?,?,?,?,?)",(user,key,fingerprint,active["id"],artifact["id"],json.dumps(out,ensure_ascii=False)))
            return out
        except ProviderBlocked as error:return blocked(error,project_id=pid,retrieval=retrieval,model_call=error.record)
        finally:
            with self.store.connect() as db:
                db.execute("DELETE FROM task_locks WHERE user_id=? AND task_id=? AND owner=?",(user,active["id"],owner))
                db.execute('DELETE FROM execution_claims WHERE user_id=? AND key=? AND owner=?',(user,key,owner))
