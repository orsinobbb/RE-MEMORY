from app.storage.database import Store
from benchmarks.generators.synthetic import seed
from app.engines.task import Orchestrator

def setup(tmp_path):
    s=Store(tmp_path/"task.db");seed(s,10,42,"2026-11-26");return s,Orchestrator(s)

def test_new_session_is_empty_and_simulated_recovery_creates_actual_artifact(tmp_path):
    s,o=setup(tmp_path);session=o.new_session()
    assert session["raw_history_count"]==0
    out=o.run({"query":"昨天的音樂專案","budget":4096,"mode":"SIMULATION","session_id":session["id"],"idempotency_key":"one"})
    assert out["status"]=="COMPLETED" and out["mode"]=="SIMULATION"
    assert "不得上傳原始音訊到第三方" in out["artifact"]["content"]
    assert s.get("tasks","task-PROJECT-028","demo")["status"]=="COMPLETED"
    assert s.get("artifacts",out["artifact"]["id"],"demo")["verified"]

def test_idempotency_returns_same_artifact_and_never_repeats_work(tmp_path):
    s,o=setup(tmp_path)
    req={"query":"MIDI 專案","budget":4096,"mode":"SIMULATION","idempotency_key":"one"}
    a=o.run(req);b=o.run(req)
    assert a["artifact"]["id"]==b["artifact"]["id"]
    c=o.run({**req,"idempotency_key":"two"})
    assert c["status"]=="ALREADY_COMPLETED"
    assert len([t for t in s.rows("events","demo") if t["type"]=="TASK_COMPLETED"])==1

def test_ambiguity_and_missing_memory_cannot_create_artifact(tmp_path):
    s,o=setup(tmp_path)
    out=o.run({"query":"音樂專案","budget":4096,"mode":"SIMULATION","idempotency_key":"a"})
    assert out["status"]=="BLOCKED"
    with s.connect() as db:db.execute("DELETE FROM evidence WHERE project_id=?",("PROJECT-028",))
    out=o.run({"query":"MIDI 專案","budget":4096,"mode":"SIMULATION","idempotency_key":"b"})
    assert out["status"]=="BLOCKED"

def test_idempotency_key_mismatch_and_unknown_session_are_rejected(tmp_path):
    s,o=setup(tmp_path)
    o.run({"query":"MIDI 專案","budget":4096,"mode":"SIMULATION","idempotency_key":"a"})
    assert o.run({"query":"鋼琴課","budget":4096,"mode":"SIMULATION","idempotency_key":"a"})["status"]=="BLOCKED"
    assert o.run({"query":"鋼琴課","budget":4096,"mode":"SIMULATION","session_id":"invalid","idempotency_key":"b"})["status"]=="BLOCKED"
