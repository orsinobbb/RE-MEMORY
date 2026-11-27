"""Local persistent conversation, separate from task/evaluator truth."""
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone
from .chat_context import build_context, parse_reply, OUTPUT_RESERVE
from .mixroute import ProviderBlocked

def now():return datetime.now(timezone.utc).isoformat()
def digest(value):return hashlib.sha256(json.dumps(value,ensure_ascii=False,sort_keys=True).encode()).hexdigest()

class ChatEngine:
    def __init__(self,store,provider):self.store=store;self.provider=provider

    def scope(self,user,project_id):
        if project_id!='PERSONAL' and not self.store.get('projects',project_id,user):raise ValueError('CHAT_PROJECT_NOT_FOUND')

    def create(self,user,project_id='PERSONAL'):
        self.scope(user,project_id)
        row={'id':str(uuid.uuid4()),'user_id':user,'project_id':project_id,'title':'新的對話','created_at':now(),'updated_at':now()}
        self.store.put('conversations',row);return row

    def state(self,user,project_id='PERSONAL'):
        self.scope(user,project_id)
        conversations=sorted(self.store.rows('conversations',user,project_id),key=lambda r:r['updated_at'],reverse=True)
        memories=[m for m in self.store.rows('chat_memories',user,project_id) if m['status']!='FORGOTTEN']
        return {'project_id':project_id,'conversations':conversations,'memories':memories,'storage':'LOCAL','provider':'MIXROUTE'}

    def conversation(self,user,id):
        c=self.store.get('conversations',id,user)
        if not c:raise ValueError('CHAT_NOT_FOUND')
        rows=[m for m in self.store.rows('chat_messages',user,c['project_id']) if m['conversation_id']==id]
        rows.sort(key=lambda m:m['sequence'])
        return {'conversation':c,'messages':rows,'memories':self.state(user,c['project_id'])['memories']}

    def _rows(self,db,table,user,project):
        return [json.loads(r[0]) for r in db.execute(f'SELECT data FROM {table} WHERE user_id=? AND project_id=? ORDER BY id',(user,project))]

    def _snapshot(self,memories):return digest(sorted(memories,key=lambda m:m['id']))

    def send(self,user,id,content,key,mode='SMART',model=None,budget=4096):
        if not isinstance(content,str) or not content.strip() or len(content)>20000:raise ValueError('CHAT_CONTENT_INVALID')
        if not isinstance(key,str) or not 1<=len(key)<=200:raise ValueError('CHAT_KEY_INVALID')
        if mode not in ('SMART','FIXED') or not isinstance(budget,int) or not 2048<=budget<=16384:raise ValueError('CHAT_PARAMETERS_INVALID')
        c=self.store.get('conversations',id,user)
        if not c:raise ValueError('CHAT_NOT_FOUND')
        fingerprint=digest([id,content,mode,model,budget]);request_id=digest(key);owner=str(uuid.uuid4());message_id=str(uuid.uuid4());record=None
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT data FROM chat_requests WHERE id=? AND user_id=?',(request_id,user)).fetchone()
            if existing:
                saved=json.loads(existing[0])
                if saved['fingerprint']!=fingerprint:raise ValueError('CHAT_IDEMPOTENCY_CONFLICT')
                if saved.get('result'):return {**saved['result'],'stored_replay':True}
            lock=db.execute('SELECT * FROM chat_locks WHERE user_id=? AND conversation_id=?',(user,id)).fetchone()
            if lock and time.time()-lock['started']<300:raise ValueError('CHAT_IN_PROGRESS')
            # An abandoned same-key turn is not automatically billed again.
            if existing:raise ValueError('CHAT_INTERRUPTED_USE_NEW_REQUEST')
            if lock:
                abandoned=[r for r in self._rows(db,'chat_requests',user,c['project_id']) if r.get('owner')==lock['owner']]
                for old in abandoned:
                    old['result']={'status':'FAILED','error':'CHAT_INTERRUPTED','stored_replay':False}
                    self.store.put('chat_requests',old,db)
                    for message in self._rows(db,'chat_messages',user,c['project_id']):
                        if message.get('request_id')==old['id']:
                            message['status']='FAILED';self.store.put('chat_messages',message,db)
            memories=[m for m in self._rows(db,'chat_memories',user,c['project_id']) if m['status']!='FORGOTTEN']
            snapshot=self._snapshot(memories)
            previous=[m for m in self._rows(db,'chat_messages',user,c['project_id']) if m['conversation_id']==id]
            previous.sort(key=lambda m:m['sequence'])
            history=[]
            for i,m in enumerate(previous):
                if m['role']=='assistant' and m['status']=='COMPLETED' and i>0:
                    before=previous[i-1]
                    if before['role']=='user' and before['status']=='COMPLETED' and before['request_id']==m['request_id']:
                        history.append([{'role':'user','content':before['content']},{'role':'assistant','content':m['content']}])
            packed,metadata=build_context(content,message_id,history,memories,min(budget,self.provider.settings.context_limit))
            db.execute('INSERT OR REPLACE INTO chat_locks VALUES (?,?,?,?)',(user,id,owner,time.time()))
            source={'id':message_id,'user_id':user,'project_id':c['project_id'],'conversation_id':id,'request_id':request_id,'role':'user','content':content,'status':'PENDING','sequence':max([m['sequence'] for m in previous]+[0])+1,'created_at':now()}
            request={'id':request_id,'user_id':user,'project_id':c['project_id'],'owner':owner,'fingerprint':fingerprint,'conversation_id':id,'result':None}
            self.store.put('chat_messages',source,db);self.store.put('chat_requests',request,db)
        try:
            record=self.provider.call(packed,mode,model,max_tokens=OUTPUT_RESERVE,user=user)
            reply,candidates,warnings=parse_reply(record,source)
            with self.store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                lock=db.execute('SELECT owner FROM chat_locks WHERE user_id=? AND conversation_id=?',(user,id)).fetchone()
                if not lock or lock['owner']!=owner:raise ValueError('CHAT_LOCK_LOST')
                all_memories=self._rows(db,'chat_memories',user,c['project_id'])
                if self._snapshot([m for m in all_memories if m['status']!='FORGOTTEN'])!=snapshot:raise ValueError('CHAT_MEMORY_CHANGED')
                new=[]
                for row in candidates:
                    if any(row['content'] in [m['content']]+[v['content'] for v in m.get('versions',[])] for m in all_memories):continue
                    memory={**row,'id':str(uuid.uuid4()),'user_id':user,'project_id':c['project_id'],'conversation_id':id,'status':'CANDIDATE','created_at':now(),'updated_at':now(),'versions':[]}
                    self.store.put('chat_memories',memory,db);all_memories.append(memory);new.append(memory)
                source['status']='COMPLETED';self.store.put('chat_messages',source,db)
                assistant={'id':str(uuid.uuid4()),'user_id':user,'project_id':c['project_id'],'conversation_id':id,'request_id':request_id,'role':'assistant','content':reply,'status':'COMPLETED','sequence':source['sequence']+1,'created_at':now(),'model_call_id':record['id']}
                self.store.put('chat_messages',assistant,db)
                c['updated_at']=now()
                if c['title']=='新的對話':c['title']=content[:36]
                self.store.put('conversations',c,db)
                usage={k:record.get(k) for k in ('id','model','requested_model','total_tokens','input_tokens','output_tokens','cost_usd','cost_upper_bound_usd','latency_ms')}
                result={'status':'COMPLETED','reply':reply,'message':assistant,'new_memories':new,'warnings':warnings,'context':metadata,'usage':usage,'stored_replay':False}
                request['result']=result;self.store.put('chat_requests',request,db)
                db.execute('DELETE FROM chat_locks WHERE user_id=? AND conversation_id=? AND owner=?',(user,id,owner))
            return result
        except (ProviderBlocked,ValueError) as error:
            record=record or getattr(error,'record',None)
            result={'status':'FAILED','error':str(error),'stored_replay':False,'context':metadata,
                'usage':{k:record.get(k) for k in ('id','model','total_tokens','cost_usd','cost_upper_bound_usd')} if record else None}
            with self.store.connect() as db:
                db.execute('BEGIN IMMEDIATE')
                source['status']='FAILED';source['error']=str(error);self.store.put('chat_messages',source,db)
                # Do not overwrite a result already retired by a new owner.
                saved=db.execute('SELECT data FROM chat_requests WHERE id=? AND user_id=?',(request_id,user)).fetchone()
                if saved and not json.loads(saved[0]).get('result'):
                    request['result']=result;self.store.put('chat_requests',request,db)
                db.execute('DELETE FROM chat_locks WHERE user_id=? AND conversation_id=? AND owner=?',(user,id,owner))
            return result

    def mutate(self,user,id,action,content=None):
        if action not in ('CONFIRM','EDIT','FORGET'):raise ValueError('CHAT_MEMORY_ACTION_INVALID')
        if action=='EDIT' and (not isinstance(content,str) or not content.strip() or len(content)>4000):raise ValueError('CHAT_MEMORY_CONTENT_INVALID')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT data FROM chat_memories WHERE id=? AND user_id=?',(id,user)).fetchone()
            if not row:raise ValueError('CHAT_MEMORY_NOT_FOUND')
            memory=json.loads(row[0])
            if memory['status']=='FORGOTTEN':raise ValueError('CHAT_MEMORY_FORGOTTEN')
            memory['versions'].append({k:memory.get(k) for k in ('content','status','updated_at')})
            if action=='EDIT':memory['content']=content.strip();memory['edited_by_user']=True
            memory['status']='FORGOTTEN' if action=='FORGET' else 'CONFIRMED';memory['updated_at']=now()
            self.store.put('chat_memories',memory,db)
        return memory
