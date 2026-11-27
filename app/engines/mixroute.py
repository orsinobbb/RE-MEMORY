import json,time,uuid,math
from dataclasses import dataclass,field
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from dotenv import dotenv_values
from openai import OpenAI,APIStatusError
from .budget import tokens

class ProviderBlocked(RuntimeError):
    def __init__(self,message,record=None):super().__init__(message);self.record=record

@dataclass
class Settings:
    base_url:str="https://api.mixroute.ai/v1"
    api_key:str=field(default="",repr=False)
    smart_key:str=field(default="",repr=False)
    fixed_model:str=""
    smart_model:str="auto"
    authorized_models:list=field(default_factory=list)
    max_price:float|None=None
    context_limit:int=16384
    enabled:bool=False
    timeout:float=30
    max_retries:int=1
    dev_budget:float=35
    initial_budget:float=5
    credit_balance:float|None=None
    emergency_reserve:float=15

    @classmethod
    def from_env(cls,path=None):
        v=dotenv_values(path or Path(__file__).resolve().parents[2]/".env")
        def numeric(name,default):
            try:
                value=float(v[name]) if v.get(name) else default
                return value if value is None or math.isfinite(value) else default
            except (ValueError,TypeError):return default
        return cls(base_url=(v.get("MIXROUTE_BASE_URL") or "").rstrip('/'),api_key=v.get("MIXROUTE_API_KEY") or "",smart_key=v.get("MIXROUTE_SMART_API_KEY") or "",
          fixed_model=v.get("MIXROUTE_FIXED_MODEL") or "",smart_model=v.get("MIXROUTE_SMART_MODEL") or "auto",authorized_models=[x.strip() for x in (v.get("MIXROUTE_AUTHORIZED_MODELS") or "").split(',') if x.strip()],
          max_price=numeric("MIXROUTE_MAX_USD_PER_MILLION",None),context_limit=int(numeric("MIXROUTE_MODEL_CONTEXT_LIMIT",16384)),enabled=(v.get("MIXROUTE_ENABLED") or "").lower()=="true",timeout=numeric("MIXROUTE_TIMEOUT_SECONDS",30),max_retries=min(max(int(numeric("MIXROUTE_MAX_RETRIES",1)),0),2),dev_budget=min(numeric("MIXROUTE_DEV_BUDGET_USD",35),35),credit_balance=numeric('MIXROUTE_CREDIT_BALANCE_USD',None),emergency_reserve=max(numeric('MIXROUTE_EMERGENCY_RESERVE_USD',15),15))

class MixRoute:
    def __init__(self,store,settings=None,http_client=None):
        self.store=store;self.settings=settings or Settings.from_env();self.http_client=http_client

    def redact(self,text):
        text=str(text)
        for key in (self.settings.api_key,self.settings.smart_key):
            if key:text=text.replace(key,"[REDACTED]")
        return text[:600]

    def client(self,mode):
        key=self.settings.smart_key if mode=="SMART" else self.settings.api_key
        if not key:raise ProviderBlocked("API_KEY_EMPTY")
        if self.settings.base_url!="https://api.mixroute.ai/v1":raise ProviderBlocked("UNVERIFIED_API_ENDPOINT")
        return OpenAI(api_key=key,base_url=self.settings.base_url,timeout=self.settings.timeout,max_retries=0,http_client=self.http_client)

    def models(self,mode="FIXED"):
        return [{"id":m.id} for m in self.client(mode).models.list().data]

    def reserve(self,id,amount):
        if not math.isfinite(amount) or amount<=0:raise ProviderBlocked("INVALID_RESERVATION")
        if any(not math.isfinite(v) for v in (self.settings.dev_budget,self.settings.initial_budget,self.settings.emergency_reserve)) or self.settings.credit_balance is not None and not math.isfinite(self.settings.credit_balance):raise ProviderBlocked('INVALID_BUDGET_CONFIGURATION')
        cap=min(self.settings.dev_budget,self.settings.initial_budget,35)
        if self.settings.credit_balance is not None:cap=min(cap,max(self.settings.credit_balance-self.settings.emergency_reserve,0))
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            window=db.execute('SELECT ceiling FROM budget_windows WHERE active=1').fetchone()
            if window:cap=min(cap,window['ceiling'])
            used=db.execute("SELECT COALESCE(SUM(CASE WHEN actual IS NULL THEN reserved ELSE actual END),0) FROM cost_ledger").fetchone()[0]
            if used+amount>cap:raise ProviderBlocked("BUDGET_LIMIT_REACHED")
            db.execute("INSERT INTO cost_ledger VALUES (?,?,NULL,'RESERVED')",(id,amount))

    def call(self,messages,mode="FIXED",model=None,max_tokens=384,user="demo",parameter="standard"):
        s=self.settings
        if not s.enabled:raise ProviderBlocked("LIVE_API_DISABLED")
        if mode not in ("FIXED","SMART"):raise ProviderBlocked("INVALID_PROVIDER_MODE")
        if s.max_price is None or not math.isfinite(s.max_price) or s.max_price<=0:raise ProviderBlocked("PRICING_UPPER_BOUND_UNKNOWN")
        if mode=="SMART" and not s.authorized_models:raise ProviderBlocked("SMART_MODEL_POOL_UNKNOWN")
        requested=s.smart_model if mode=="SMART" else model or s.fixed_model
        if not requested:raise ProviderBlocked("MODEL_ID_UNKNOWN")
        allowed={m.casefold() for m in s.authorized_models}
        if mode=="FIXED" and requested.casefold() not in allowed:raise ProviderBlocked("MODEL_NOT_IN_PRICED_ALLOWLIST")
        if mode=="SMART" and requested!="auto":raise ProviderBlocked("SMART_MODEL_MUST_BE_AUTO")
        if tokens(messages)+max_tokens+128>s.context_limit:raise ProviderBlocked("MODEL_CONTEXT_LIMIT_EXCEEDED")
        if not 1<=max_tokens<=2048:raise ProviderBlocked("OUTPUT_LIMIT_OUT_OF_RANGE")
        # UTF-8 bytes + message framing is conservative across tokenizers.
        input_bound=len(json.dumps(messages,ensure_ascii=False).encode())+512
        per_attempt=(input_bound+max_tokens)*s.max_price/1_000_000
        client=self.client(mode)
        id=str(uuid.uuid4());self.reserve(id,per_attempt*(s.max_retries+1))
        start=time.perf_counter();last_error="";attempts=0
        for attempt in range(s.max_retries+1):
            attempts+=1
            try:
                kwargs={"model":requested,"messages":messages}
                kwargs["max_completion_tokens" if parameter=="completion" else "max_tokens"]=max_tokens
                raw=client.chat.completions.with_raw_response.create(**kwargs)
                response=raw.parse();usage=response.usage
                content=response.choices[0].message.content if response.choices else None
                total=usage.total_tokens if usage else None
                consumed_bound=(total*s.max_price/1_000_000 if total is not None else per_attempt)+attempt*per_attempt
                # Actual provider invoice is UNKNOWN; keep the priced upper bound committed.
                with self.store.connect() as db:db.execute("UPDATE cost_ledger SET reserved=?,status=? WHERE id=?",(consumed_bound,"USAGE_UPPER_BOUND" if total is not None else "USAGE_UNKNOWN",id))
                compliant=bool(response.model) and response.model.casefold() in allowed
                record={"id":id,"user_id":user,"project_id":"","mode":mode,"status":"SUCCESS" if compliant else "BLOCKED_UNAUTHORIZED_RESOLVED_MODEL","requested_model":requested,"model":response.model,"response_id":response.id,"request_id":raw.headers.get("x-request-id"),"finish_reason":response.choices[0].finish_reason if response.choices else None,
                  "input_tokens":usage.prompt_tokens if usage else None,"output_tokens":usage.completion_tokens if usage else None,"total_tokens":total,"cost_usd":None,"cost_source":"UNKNOWN_PENDING_BILLING_RECONCILIATION","cost_upper_bound_usd":consumed_bound,"retry_count":attempt,"latency_ms":round((time.perf_counter()-start)*1000,2),"content":self.redact(content) if content else content,"created_at":datetime.now(ZoneInfo("Asia/Taipei")).isoformat()}
                # Do not truncate artifact content; redaction only for secret strings.
                if content:
                    record["content"]=content
                    for key in (s.api_key,s.smart_key):
                        if key:record["content"]=record["content"].replace(key,"[REDACTED]")
                self.store.put("model_calls",record)
                if not compliant:raise ProviderBlocked("RESOLVED_MODEL_OUTSIDE_PRICED_ALLOWLIST",record)
                return record
            except ProviderBlocked:
                raise
            except Exception as error:
                body=getattr(error,"body",None)
                last_error=self.redact(json.dumps(body,ensure_ascii=False) if body else str(error))
                transient=isinstance(error,APIStatusError) and (error.status_code in (429,500,502,503,504))
                if transient and attempt<s.max_retries:continue
                break
        with self.store.connect() as db:db.execute("UPDATE cost_ledger SET status='ERROR_COST_UNKNOWN' WHERE id=?",(id,))
        record={"id":id,"user_id":user,"project_id":"","mode":mode,"status":"FAILED","requested_model":requested,"error":last_error,"attempts":attempts,"retry_count":attempts-1,"total_tokens":None,"cost_usd":None,"cost_upper_bound_usd":per_attempt*attempts,"latency_ms":round((time.perf_counter()-start)*1000,2)}
        self.store.put("model_calls",record)
        raise ProviderBlocked(last_error,record)
