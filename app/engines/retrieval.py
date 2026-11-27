import time,uuid
from .intent import parse_intent
from .entity_resolution import explicit_target
from .semantic_dictionary import matching_aliases
from .scoring import score_candidate
from .exploration import SearchState,next_clues,sufficient
from .context_builder import build_context
from .budget import tokens,token_method
from .search_adapter import FTSSearch
from .baselines import build_baseline_context

class Router:
    def __init__(self,store,search=None):self.store=store;self.search=search or FTSSearch(store)

    def retrieve(self,query,user="demo",budget=4096,reference="2026-11-26",strategy="E",on_round=None):
        start=time.perf_counter();state=SearchState(budget);intent=parse_intent(query,reference)
        projects=self.store.projects(user);aliases=self.store.rows("aliases",user)
        explicit,reason=explicit_target(projects,aliases if strategy in ("E","F") else [],query)
        chosen=None;candidates=[];stop="NO_NEW_CLUES";status="NOT_FOUND"
        layers=[0,1,2] if strategy in ("D","E","F") else ([0] if strategy=="A" else [1] if strategy=="B" else [2])
        if reason=='UNKNOWN_PROJECT_ID':layers=[];stop=reason
        if reason in ('MULTIPLE_EXPLICIT_PROJECTS','CONTRADICTORY_PROJECT_CUES'):layers=[];stop=reason;status='NEEDS_CONFIRMATION'
        matching=matching_aliases(aliases,query)
        ambiguous=len({a["project_id"] for a in matching})>1 and not intent["time"] and not explicit
        events=[];tasks=[]
        for layer in layers:
            graph_added=[];graph_spent=0
            if layer==0:
                pool=[p for p in projects if not intent["time"] or p["last_active"]==intent["time"]]
                if not pool:pool=projects[:50]
                new_reason="先讀專案與活動日期索引"
            elif layer==1:
                pool=[p for p in projects if p["id"] in {a["project_id"] for a in matching} or intent["topic"]==p["topic"] or p["id"]==explicit]
                new_reason="候選差距不足，加入使用者稱呼與關係索引"
            else:
                clues=next_clues(aliases,{c["project_id"] for c in candidates[:3]}) if strategy in ("E","F") else [c["name"] for c in candidates[:3]]
                if strategy in ("E","F"):
                    frontier={c["project_id"] for c in candidates[:3]}
                    for relation in self.store.rows("relations",user):
                        if not frontier.intersection((relation['from'],relation['to'])):continue
                        sources=[self.store.get('evidence',eid,user) for eid in relation.get('evidence_ids',[])]
                        if not sources or not all(e and e.get('trusted') for e in sources):continue
                        other=relation['to'] if relation['from'] in frontier else relation['from']
                        project=self.store.get('projects',other,user)
                        if not project:continue
                        version=f"relation:{relation['id']}:v{relation.get('version',1)}"
                        cost=state.observe(version,tokens(relation))
                        if cost:graph_added.append(version);graph_spent+=cost
                        clues.extend([other,project['name']])
                state.clues=list(dict.fromkeys(state.clues+clues))
                pool=self.search.search(user,query+" "+" ".join(clues),limit=50)
                events=self.store.rows("events",user);tasks=self.store.rows("tasks",user)
                new_reason="探索已確認稱呼、來源關係與中斷活動，補充全文及未完成工作證據" if strategy in ('E','F') else "補充全文及未完成工作證據"
            if explicit:pool=[p for p in projects if p["id"]==explicit]
            # Baselines do not use personalized aliases or expanded graph evidence.
            use_aliases=aliases if strategy in ("E","F") or explicit else []
            candidates=[score_candidate(p,intent,query,use_aliases,events,tasks,layer) for p in pool]
            candidates.sort(key=lambda c:(-c["score"],c["project_id"]))
            added=graph_added;spent=graph_spent
            for p in pool[:12]:
                version=f"project:{p['id']}:{p['last_active']}"
                cost=state.observe(version,tokens({"id":p["id"],"name":p["name"],"topic":p["topic"],"last_active":p["last_active"]}))
                if cost:added.append(version);spent+=cost
            for a in matching if layer>=1 else []:
                spent+=state.observe(f"alias:{a['id']}:{a['last_used']}",tokens(a))
            row={"round":len(state.rounds)+1,"layer":f"L{layer}","reason":new_reason,"search_terms":[query]+state.clues,"candidates":candidates[:8],"new_clues":state.clues[:],"new_information":added,"tokens":spent,"cumulative_tokens":state.spent}
            state.rounds.append(row)
            if on_round:on_round(row)
            if state.spent>budget:stop="TOKEN_BUDGET_EXCEEDED";status="BUDGET_EXCEEDED";break
            if explicit or layer==2 and sufficient(candidates) and not ambiguous and intent["topic"]:
                chosen=candidates[0]["project_id"] if candidates else None
                if chosen:status="RESOLVED";stop=reason or "EVIDENCE_AND_MARGIN_SUFFICIENT";break
        if not chosen and status!="BUDGET_EXCEEDED" and candidates:
            status="NEEDS_CONFIRMATION";stop="AMBIGUOUS_OR_INSUFFICIENT_EVIDENCE"
        context=(build_baseline_context(self.store,chosen,user,budget,query,reference,strategy) if strategy in ('A','B','C','D') else build_context(self.store,chosen,user,budget,query,reference)) if chosen else None
        if context:
            groups=[(3,"載入最新目標與工作狀態",[f for f in context["loaded"] if f.get("kind") in ("GOAL","RESULT")]),
                    (4,"強制檢查限制與決策",[f for f in context["loaded"] if f.get("kind") in ("CONSTRAINT","DECISION")]),
                    (5,"驗證原始來源與成果依賴",[f for f in context["loaded"] if "source" in f or 'task_id' in f])]
            if strategy in ('A','B','C'):groups=[(3,context['memory_scope'],context['loaded'])]
            for layer,why,items in groups:
                added=[];spent=0
                for item in items:
                    version=f"{item['id']}:v{item.get('version',1)}";cost=state.observe(version,tokens(item))
                    if cost:added.append(version);spent+=cost
                row={"round":len(state.rounds)+1,"layer":f"L{layer}","reason":why,"search_terms":[chosen],"candidates":candidates[:8],"new_clues":[],"new_information":added,"tokens":spent,"cumulative_tokens":state.spent}
                state.rounds.append(row)
                if on_round:on_round(row)
            if state.spent>budget and strategy not in ('A','B','C'):
                chosen=None;status='BUDGET_EXCEEDED';stop='TOKEN_BUDGET_EXCEEDED';context=None
        clarify="請確認你指的是："+"、".join(c["name"] for c in candidates[:3])+"？" if status=="NEEDS_CONFIRMATION" else None
        result={"id":str(uuid.uuid4()),"query":query,"intent":intent,"status":status,"project_id":chosen,"rounds":state.rounds,"candidates":candidates[:8],"retrieval_tokens":state.spent,
          "read_versions":sorted(state.read_versions),"stop_reason":stop,"clarification":clarify,"confidence_probability":None,"context":context,"token_method":token_method(),
          "resolved_by_confirmed_alias":reason=="CONFIRMED_ALIAS","strategy":strategy,"search_adapter":self.search.mode,"elapsed_ms":round((time.perf_counter()-start)*1000,2)}
        self.store.put("traces",{"id":result["id"],"user_id":user,"project_id":chosen or "","result":result})
        return result
