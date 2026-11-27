from app.storage.database import Store
from benchmarks.generators.synthetic import seed
from app.engines.retrieval import Router

def setup(tmp_path):
    s=Store(tmp_path/"router.db");seed(s,100,42,"2026-11-26");return s,Router(s)

def test_yesterday_music_uses_progressive_evidence(tmp_path):
    s,r=setup(tmp_path)
    out=r.retrieve("我要你繼續做昨天的音樂專案。","demo",4096,"2026-11-26")
    assert out["project_id"]=="PROJECT-028"
    assert [x["layer"] for x in out["rounds"][:3]]==["L0","L1","L2"]
    assert out["retrieval_tokens"]>0
    assert out["confidence_probability"] is None
    assert len(out["read_versions"])==len(set(out["read_versions"]))
    assert out["context"]["feasible"]

def test_ambiguous_alias_clarifies_without_execution(tmp_path):
    s,r=setup(tmp_path)
    out=r.retrieve("繼續音樂專案","demo",4096,"2026-11-26")
    assert out["project_id"] is None
    assert out["status"]=="NEEDS_CONFIRMATION"
    assert "音訊" in out["clarification"] and "鋼琴" in out["clarification"]

def test_confirmed_alias_explicit_id_and_user_scope(tmp_path):
    s,r=setup(tmp_path)
    assert r.retrieve("繼續鋼琴課","demo",4096,"2026-11-26")["project_id"]=="PROJECT-002"
    assert r.retrieve("繼續 PROJECT-028","demo",4096,"2026-11-26")["project_id"]=="PROJECT-028"
    assert r.retrieve("繼續 MIDI 專案","outsider",4096,"2026-11-26")["project_id"] is None

def test_unknown_queries_and_budget_bound(tmp_path):
    s,r=setup(tmp_path)
    assert r.retrieve("昨天的量子火箭專案","demo",4096,"2026-11-26")["project_id"] is None
    out=r.retrieve("昨天的音樂專案","demo",10,"2026-11-26")
    assert out["status"]=="BUDGET_EXCEEDED" and out["project_id"] is None
    assert len(out["rounds"])<=6

def test_rejected_alias_does_not_resolve(tmp_path):
    s,r=setup(tmp_path)
    alias=next(a for a in s.rows("aliases","demo") if a["alias"]=="MIDI 專案")
    alias["status"]="REJECTED";s.put("aliases",alias);s.reindex("demo")
    out=r.retrieve("MIDI 專案","demo",4096,"2026-11-26")
    assert not out.get("resolved_by_confirmed_alias",False)

def test_completion_does_not_erase_project_identity(tmp_path):
    s,r=setup(tmp_path)
    task=s.get('tasks','task-PROJECT-028','demo');task['status']='COMPLETED';s.put('tasks',task)
    assert r.retrieve('昨天的音樂專案',budget=4096)['project_id']=='PROJECT-028'

def test_specific_piano_cue_does_not_execute_music_alias_target(tmp_path):
    s,r=setup(tmp_path)
    assert r.retrieve('繼續昨天的鋼琴音樂專案',budget=4096)['project_id'] in ('PROJECT-002',None)
    assert r.retrieve('鋼琴課的 MIDI 專案',budget=4096)['project_id'] is None
