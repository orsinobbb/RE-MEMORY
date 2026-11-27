from .semantic_dictionary import alias_evidence

WEIGHTS={"time":.20,"topic":.20,"alias":.20,"behavior":.10,"content":.15,"unfinished":.10,"frequency":.05}

def score_candidate(project,intent,query,aliases,events,tasks,layer,weights=None):
    pid=project["id"];names=[a for a in aliases if a["project_id"]==pid and a["status"] in ("CONFIRMED","CANDIDATE")]
    matched,found=alias_evidence(aliases,query,pid)
    positive=[];negative=[]
    time=1.0 if intent["time"]==project["last_active"] else 0.0
    topic=1.0 if intent["topic"]==project["topic"] else 0.0
    dims={"time":time if intent["time"] else None,"topic":topic if intent["topic"] else None,
          "alias":matched if layer>=1 else None,"behavior":None,"content":None,"unfinished":None,"frequency":None}
    if time and intent["time"]:positive.append("活動日期吻合")
    if intent["time"] and not time:negative.append("活動日期不吻合")
    if topic:positive.append("主題索引吻合")
    if layer>=1:
        positive.extend(f"{a['status']} 別名：{a['alias']}（來源 {','.join(a['evidence_ids'])}）" for a in found)
        dims["frequency"]=min(max((a["uses"] for a in found),default=0)/8,1)
    if layer>=2:
        active_events=[e for e in events if e["project_id"]==pid and e["type"]=="SESSION_INTERRUPTED"]
        clues=[a["alias"].casefold() for a in names if a["status"]=="CONFIRMED"]
        links=sum(1 for clue in clues if any(clue in e["detail"].casefold() for e in active_events))
        dims["behavior"]=min(.2+links*.4,1) if active_events else 0
        dims["content"]=min(.4+links*.25,1) if topic else 0
        pending=[t for t in tasks if t["project_id"]==pid and t["status"]=="PENDING"]
        # Completed work controls execution eligibility, not negative identity evidence.
        dims["unfinished"]=.9 if pending else None
        if links:positive.append("中斷活動與已確認稱呼連結："+", ".join(clues))
        if not pending:negative.append("沒有未完成工作")
        else:positive.append("有尚未完成且具依賴來源的任務")
    use={k:v for k,v in (weights or WEIGHTS).items() if dims.get(k) is not None}
    denominator=sum(use.values())
    score=sum(dims[k]*v for k,v in use.items())/denominator if denominator else 0
    if intent["time"] and not time:score*=.55
    if intent["topic"] and not topic:score*=.4
    return {"project_id":pid,"name":project["name"],"score":round(score,4),"dimensions":dims,
            "weights":{k:round(v/denominator,4) for k,v in use.items()} if denominator else {},
            "positive_evidence":positive,"negative_evidence":negative}
