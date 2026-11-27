"""A persistent two-stage synthetic handoff; never resets old tasks or costs."""
import hashlib
import json

from .task import Orchestrator
from .mixroute import MixRoute
from .memory_evolution import MemoryEvolution

PROJECT_ID='LIVE-DEMO-20261127'
REFERENCE='2026-11-26'
QUERY='請接續記憶交接示範專案'


class LiveDemo:
    def __init__(self,store,provider=None):
        self.store=store;self.provider=provider or MixRoute(store)
        self.orchestrator=Orchestrator(store,self.provider)

    def _delivery(self,tid,user):
        with self.store.connect() as db:
            row=db.execute('SELECT result FROM deliveries WHERE user_id=? AND task_id=?',(user,tid)).fetchone()
        return json.loads(row[0]) if row else None

    def state(self,user='demo'):
        project=self.store.get('projects',PROJECT_ID,user)
        stages=[]
        for task in self.store.rows('tasks',user,PROJECT_ID):
            out=self._delivery(task['id'],user)
            artifact=self.store.get('artifacts',task.get('artifact_id'),user) if task.get('artifact_id') else None
            call=(out or {}).get('model_call')
            session=self.store.get('sessions',(out or {}).get('session_id'),user) if out else None
            stages.append({**task,'artifact':artifact,'model_call':call,'mode':(artifact or {}).get('mode'),
                           'session_id':(out or {}).get('session_id'),'raw_history_count':(session or {}).get('raw_history_count'),
                           'handoff_proof':self._proof(task,artifact,out,user) if out else None})
        reference=max([REFERENCE]+[f['valid_from'][:10] for f in self.store.facts(PROJECT_ID,user)])
        return {'prepared':bool(project),'project_id':PROJECT_ID,'project':project,'query':QUERY,
                'reference_date':reference,'dataset':'DEMO','stages':stages}

    def prepare(self,user='demo'):
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            if not MemoryEvolution._get(db,'projects',PROJECT_ID,user):
                base={'user_id':user,'project_id':PROJECT_ID,'created_at':'2026-11-25T10:00:00+08:00'}
                self.store.put('projects',{**base,'id':PROJECT_ID,'name':'記憶交接示範專案','topic':'交接','description':'合成資料、兩個模型與空白Session的記憶交接','last_active':'2026-11-25','dataset':'DEMO'},db)
                texts={'GOAL':'根據前一階段成果，建立可驗證的合成資料交接與風險檢查清單。',
                       'CONSTRAINT':'僅使用合成資料；不得上傳音檔或私人資料；保留來源與版本；輸出使用繁體中文。',
                       'DECISION':'第一階段建立驗收方案，第二階段核對方案並交付風險檢查清單；不重複已完成工作。'}
                eid=PROJECT_ID+'-source-v1'
                self.store.put('evidence',{**base,'id':eid,'source':'synthetic://live-demo/spec-v1','content':'DEMO SOURCE\n'+'\n'.join(texts.values()),'trusted':True,'version':1},db)
                fact_ids=[]
                for kind,content in texts.items():
                    fid=PROJECT_ID+'-'+kind.lower()+'-v1';fact_ids.append(fid)
                    fact={**base,'id':fid,'kind':kind,'subject':PROJECT_ID,'relation':kind.lower(),'content':content,'evidence_ids':[eid],
                          'valid_from':'2026-11-25','version':1,'verification':'VERIFIED','trust':'SOURCE','mandatory':True,'superseded':False}
                    self.store.put('facts',fact,db);self.store.put({'GOAL':'goals','CONSTRAINT':'constraints','DECISION':'decisions'}[kind],fact,db)
                self.store.put('aliases',{**base,'id':PROJECT_ID+'-alias','alias':'記憶交接示範','status':'CONFIRMED','method':'SOURCE','evidence_ids':[eid],
                                         'uses':1,'last_used':'2026-11-25','strength':1,'ambiguous':False},db)
                for stage,title in [(1,'建立第一階段合成資料驗收方案'),(2,'根據前一成果核對風險，形成下一階段交接清單')]:
                    self.store.put('tasks',{**base,'id':PROJECT_ID+f'-stage-{stage}','title':title,'status':'PENDING','artifact_id':None,
                                            'dependency_ids':fact_ids,'required_artifact_ids':[],
                                            'depends_on_task_ids':[PROJECT_ID+'-stage-1'] if stage==2 else [],'tool':'markdown_handoff'},db)
                self.store.reindex(user,db)
        return self.state(user)

    def _proof(self,task,artifact,out,user):
        prior_ids=task.get('depends_on_task_ids',[])
        if not prior_ids:return {'prior_artifact_loaded':False,'required_prior_task_ids':[]}
        prior=self.store.get('tasks',prior_ids[0],user)
        prior_artifact=self.store.get('artifacts',(prior or {}).get('artifact_id'),user) if prior else None
        loaded=((out or {}).get('retrieval') or {}).get('context',{}).get('loaded',[])
        match=next((a for a in loaded if prior_artifact and a.get('id')==prior_artifact['id']),None)
        valid=bool(match and match.get('content')==prior_artifact.get('content') and match.get('sha256')==hashlib.sha256(match['content'].encode()).hexdigest())
        return {'prior_artifact_loaded':valid,'required_prior_task_ids':prior_ids,
                'prior_artifact_id':(prior_artifact or {}).get('id'),'prior_sha256':(prior_artifact or {}).get('sha256'),
                'prior_content':(match or {}).get('content'),'verification_scope':'EXACT_PERSISTED_PRIOR_CONTENT_IN_MODEL_CONTEXT'}

    def run(self,stage,mode,idempotency_key,user='demo'):
        state=self.state(user)
        if not state['prepared']:return {'status':'BLOCKED','reason':'PREPARE_DEMO_FIRST','api_call_made':False}
        if stage not in (1,2) or mode not in ('SMART','FIXED','SIMULATION'):raise ValueError('INVALID_DEMO_STAGE_OR_MODE')
        task=self.store.get('tasks',PROJECT_ID+f'-stage-{stage}',user)
        if task['status']=='COMPLETED':
            existing=self._delivery(task['id'],user);artifact=self.store.get('artifacts',task.get('artifact_id'),user)
            if not existing or not artifact or not artifact.get('verified') or hashlib.sha256(artifact['content'].encode()).hexdigest()!=artifact.get('sha256'):
                return {'status':'BLOCKED','reason':'ARTIFACT_REVALIDATION_REQUIRED','api_call_made':False}
            return {**existing,'status':'ALREADY_COMPLETED','artifact':artifact,'api_call_made':False,'stored_replay':True,'stage':stage,
                    'handoff_proof':self._proof(task,artifact,existing,user)}
        if stage==1 and mode=='FIXED':raise ValueError('FIRST_STAGE_USES_SMART_OR_SIMULATION')
        if stage==2 and mode=='SMART':raise ValueError('SECOND_STAGE_USES_DIFFERENT_FIXED_MODEL')
        model=None;different_from_model=None
        if stage==2:
            first=self.store.get('tasks',PROJECT_ID+'-stage-1',user)
            if first['status']!='COMPLETED':return {'status':'BLOCKED','reason':'FIRST_STAGE_NOT_COMPLETE','api_call_made':False}
            if mode=='FIXED':
                actual=((self._delivery(first['id'],user) or {}).get('model_call') or {}).get('model')
                if not actual:return {'status':'BLOCKED','reason':'FIRST_STAGE_MUST_BE_LIVE_FOR_CROSS_MODEL','api_call_made':False}
                different_from_model=actual
                model=next((m for m in self.provider.settings.authorized_models if m.casefold()!=actual.casefold()),None)
                if not model:return {'status':'BLOCKED','reason':'NO_OTHER_AUTHORIZED_MODEL','api_call_made':False}
        session=self.orchestrator.new_session(user)
        out=self.orchestrator.run({'query':QUERY,'project_id':PROJECT_ID,'task_id':task['id'],'mode':mode,'model':model,'budget':4096,
                                   'session_id':session['id'],'idempotency_key':idempotency_key,'reference_date':state['reference_date'],
                                   'different_from_model':different_from_model},user)
        return {**out,'stage':stage,'raw_history_count':0,'api_call_made':bool(out.get('model_call')) and not out.get('stored_replay'), 'stored_replay':bool(out.get('stored_replay')),
                'handoff_proof':self._proof(task,out.get('artifact'),out,user)}
