import hashlib

def check_fact_coverage(store,pid,user,reference,dependency_ids=()):
    """Source-backed facts only; never substitutes for normal task coverage."""
    facts=store.facts(pid,user)
    mandatory=[f for f in facts if f.get("mandatory") or f["kind"] in ("GOAL","CONSTRAINT","DECISION")]
    dependency_ids=set(dependency_ids)
    mandatory+= [f for f in facts if f['id'] in dependency_ids and f['id'] not in {x['id'] for x in mandatory}]
    required=[];missing=[];conflicts=[];sources={};covered=0;valid_ids=set()
    for kind in ("GOAL","CONSTRAINT","DECISION"):
        if not any(f["kind"]==kind for f in mandatory):required.append("kind:"+kind);missing.append("缺少 "+kind)
    for f in mandatory:
        required.append(f["id"]);valid=True
        if f.get("conflict"):conflicts.append(f["id"]);valid=False
        if f.get("verification")!="VERIFIED" or f.get("trust") not in ("SOURCE","USER") or f['kind'] in ('CLAIM','INFERENCE','UNKNOWN'):
            missing.append("未驗證必要記憶："+f["id"]);valid=False
        if f["valid_from"][:10]>reference or f.get("valid_to") and f["valid_to"][:10]<reference:
            missing.append("記憶過期或尚未生效："+f["id"]);valid=False
        if not f["evidence_ids"]:missing.append("無來源："+f["id"]);valid=False
        for eid in f["evidence_ids"]:
            e=store.get("evidence",eid,user)
            if not e or e["project_id"]!=pid or not e.get("trusted"):
                missing.append("來源缺失或未核實："+eid);valid=False
            else:sources[eid]=e
            if e and f['content'] not in e.get('content',''):
                missing.append('來源未支持必要記憶：'+f['id']);valid=False
        if valid:covered+=1;valid_ids.add(f['id'])
    for dep in dependency_ids:
        required.append("dependency:"+dep)
        if dep in valid_ids:covered+=1
        else:missing.append("必要依賴缺失："+dep)
    return {"facts":mandatory,"evidence":list(sources.values()),"required":required,
            "missing":list(dict.fromkeys(missing)),"conflicts":conflicts,
            "coverage":covered/len(required) if required else 0, "covered_count":covered}

def check_coverage(store,pid,user,reference):
    tasks=store.rows("tasks",user,pid)
    active=next((t for t in tasks if t["status"]=="PENDING"),None)
    result=check_fact_coverage(store,pid,user,reference,active.get('dependency_ids',[]) if active else ())
    required=result['required'];missing=result['missing'];covered=result.pop('covered_count')
    required.append("active_task")
    if active:
        covered+=1
        required_artifacts=active.get("required_artifact_ids",[])
        for tid in active.get('depends_on_task_ids',[]):
            required.append('prior_task:'+tid)
            prior=store.get('tasks',tid,user)
            if prior and prior['project_id']==pid and prior['status']=='COMPLETED' and prior.get('artifact_id'):
                covered+=1;required_artifacts=required_artifacts+[prior['artifact_id']]
            else:missing.append('尚未完成的前置階段：'+tid)
    else:missing.append("沒有可接續的未完成任務");required_artifacts=[]
    completed=[t for t in tasks if t["status"]=="COMPLETED"]
    artifacts=list(dict.fromkeys(required_artifacts+[t.get("artifact_id") for t in completed]))
    for aid in artifacts:
        required.append("artifact:"+str(aid))
        a=store.get("artifacts",aid,user) if aid else None
        if a and a["project_id"]==pid and a.get("verified") and hashlib.sha256(a["content"].encode()).hexdigest()==a["sha256"]:covered+=1
        else:missing.append("成果缺失或雜湊不符："+str(aid))
    return {**result,"task":active,"completed":completed,
            "required":required,"missing":list(dict.fromkeys(missing)),
            "coverage":covered/len(required) if required else 0}
