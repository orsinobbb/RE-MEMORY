"""Reproducible synthetic memory; never creates or reads evaluator truth."""
import hashlib
import random
from datetime import date,timedelta
from app.schemas.models import FactCell,Alias

def seed(store,count=10,random_seed=42,reference="2026-11-26"):
    if not 4<=count<=1000: raise ValueError("Project count must be 4–1000")
    rng=random.Random(random_seed)
    day=date.fromisoformat(reference)
    yesterday=(day-timedelta(days=1)).isoformat()
    presets=[
      ("PROJECT-028","音訊轉換系統","音樂","音檔轉 MIDI、樂器分離與樂譜 PDF",["音樂專案","轉換音檔","轉譜工具","MIDI 專案","樂器分離","音樂轉 PDF"]),
      ("PROJECT-002","鋼琴樂理教材","音樂","鋼琴和弦教材與練習課程",["音樂專案","鋼琴課","樂理教材"]),
      ("PROJECT-003","人生冒險島","遊戲","冒險島背景音樂與像素地圖",["冒險島","島嶼遊戲"]),
      ("PROJECT-004","AI 工作管理","管理","追蹤音樂專案與其他任務",["工作管理","看板"])]
    user="demo"
    store.put("users",{"id":user,"user_id":user,"name":"Synthetic User","dataset":"DEMO"})
    with store.connect() as db:
        for i in range(count):
            if i<4:
                pid,name,topic,desc,names=presets[i]; active=yesterday
            else:
                pid=f"PROJECT-{1000+i:04d}"; topic=rng.choice(["音樂","研究","攝影","教育","管理","遊戲"])
                name=f"{topic}研究工作室 {i:04d}"; desc=f"{topic}資料整理，獨立目標 {i}"
                names=[f"{topic}工作室{i}"]; active=(day-timedelta(days=rng.randint(2,90))).isoformat()
            base={"user_id":user,"project_id":pid,"created_at":active+"T10:00:00+08:00"}
            store.put("projects",{**base,"id":pid,"name":name,"topic":topic,"description":desc,"last_active":active,"dataset":"DEMO"},db)
            eid=f"evidence-{pid}"
            goal="建立音檔轉 MIDI 與 PDF 的驗收計畫" if i==0 else f"完成{name}的下一階段驗收計畫"
            constraint="只使用合成音檔；不得上傳原始音訊到第三方；輸出使用繁體中文" if i==0 else "只使用合成資料；輸出使用繁體中文"
            decision="樂器分離測試已完成，接續 MIDI 轉換驗收清單" if i==0 else f"保留{name}既有里程碑，接續下一階段"
            content=f"DEMO SOURCE\n目標：{goal}\n限制：{constraint}\n決策：{decision}"
            store.put("evidence",{**base,"id":eid,"source":f"synthetic://{pid}/spec-v2","content":content,"version":2,"trusted":True},db)
            fact_ids=[]
            for kind,text in [("GOAL",goal),("CONSTRAINT",constraint),("DECISION",decision)]:
                fid=f"{pid}-{kind.lower()}-v2"; fact_ids.append(fid)
                fact=FactCell(**base,id=fid,kind=kind,subject=pid,relation=kind.lower(),content=text,evidence_ids=[eid],valid_from=active,version=2,mandatory=True,verification='VERIFIED',trust='SOURCE')
                store.put("facts",fact,db)
                store.put({"GOAL":"goals","CONSTRAINT":"constraints","DECISION":"decisions"}[kind],fact,db)
            store.put("facts",FactCell(**base,id=f"{pid}-goal-v1",kind="GOAL",subject=pid,relation="goal",content="舊目標已取代",evidence_ids=[eid],valid_from=active,version=1,superseded=True,verification='VERIFIED',trust='SOURCE'),db)
            task_id=f"task-{pid}"
            store.put("tasks",{**base,"id":task_id,"title":"撰寫 MIDI 轉換驗收清單" if i==0 else f"撰寫{name}驗收清單","status":"PENDING","dependency_ids":fact_ids,"required_artifact_ids":[],"artifact_id":None,"tool":"markdown_handoff"},db)
            done_id=f"done-{pid}"; artifact_id=f"prior-{pid}"
            artifact=f"# 已完成里程碑\n{name}前一階段合成資料測試已通過。\n來源：{eid}\n"
            store.put("artifacts",{**base,"id":artifact_id,"task_id":done_id,"content":artifact,"sha256":hashlib.sha256(artifact.encode()).hexdigest(),"verified":True,"mode":"DEMO"},db)
            store.put("tasks",{**base,"id":done_id,"title":"前一階段合成資料測試","status":"COMPLETED","dependency_ids":[],"required_artifact_ids":[],"artifact_id":artifact_id,"tool":"markdown_handoff"},db)
            for j,alias in enumerate(names):
                store.put("aliases",Alias(**base,id=f"alias-{pid}-{j}",alias=alias,evidence_ids=[eid],last_used=active,status="CANDIDATE" if alias=="音樂專案" else "CONFIRMED",method="INFERENCE" if alias=="音樂專案" else "USER",uses=8 if i==0 else 2,strength=.95 if i==0 else .65,ambiguous=alias=="音樂專案"),db)
            for j,kind in enumerate(["PROJECT_CREATED","DOCUMENT_IMPORTED","SESSION_INTERRUPTED"]):
                detail="完成樂器分離，準備接續 MIDI 轉換" if i==0 and j==2 else desc
                store.put("events",{**base,"id":f"event-{pid}-{j}","type":kind,"date":active,"detail":detail,"evidence_ids":[eid]},db)
            store.put("topics",{**base,"id":f"topic-{pid}","name":topic},db)
            store.put("entities",{**base,"id":f"entity-{pid}","name":"MIDI" if i==0 else name},db)
        store.put("relations",{"id":"tracker-relation","user_id":user,"project_id":"PROJECT-004","from":"PROJECT-004","to":"PROJECT-028","type":"TRACKS","evidence_ids":["evidence-PROJECT-004"]},db)
    store.reindex(user)
