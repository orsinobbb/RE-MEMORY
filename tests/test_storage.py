from app.storage.database import Store
from benchmarks.generators.synthetic import seed


def test_deterministic_scale_and_chinese_search(tmp_path):
    for count in (10, 100, 1000):
        s = Store(tmp_path / f"{count}.db")
        seed(s, count, 42, "2026-11-26")
        assert len(s.projects("demo")) == count
        assert len(s.rows("events", "demo")) >= count * 3
        assert s.get("projects", "PROJECT-028", "demo")["name"] == "音訊轉換系統"
        assert any(p["id"] == "PROJECT-028" for p in s.search("demo", "音檔"))


def test_provenance_version_and_many_to_many_alias(tmp_path):
    s = Store(tmp_path / "v.db")
    seed(s, 10, 42, "2026-11-26")
    facts = s.facts("PROJECT-028", "demo")
    assert all(f["evidence_ids"] and f["version"] == 2 for f in facts)
    assert len(s.facts("PROJECT-028", "demo", current=False)) > len(facts)
    aliases = [a for a in s.rows("aliases", "demo") if a["alias"] == "音樂專案"]
    assert {a["project_id"] for a in aliases} == {"PROJECT-028", "PROJECT-002"}
    assert all(a["status"] == "CANDIDATE" for a in aliases)


def test_acl_and_sql_injection_cannot_cross_users(tmp_path):
    s = Store(tmp_path / "a.db")
    seed(s, 10, 42, "2026-11-26")
    assert s.projects("outsider") == []
    assert s.search("outsider", "' OR 1=1 --") == []
    assert s.get("projects", "PROJECT-028", "outsider") is None
    s.put("projects", {"id": "PROJECT-028", "user_id": "outsider", "project_id": "PROJECT-028", "name": "separate"})
    assert s.get("projects", "PROJECT-028", "demo")["name"] == "音訊轉換系統"


def test_generator_is_reproducible_and_completed_artifacts_exist(tmp_path):
    a, b = Store(tmp_path / "a.db"), Store(tmp_path / "b.db")
    seed(a, 10, 9, "2026-11-26")
    seed(b, 10, 9, "2026-11-26")
    assert a.projects("demo") == b.projects("demo")
    for task in a.rows("tasks", "demo"):
        if task["status"] == "COMPLETED":
            assert task["artifact_id"]
            assert a.get("artifacts", task["artifact_id"], "demo")["verified"]
def test_new_claim_is_unverified_by_default():
    from app.schemas.models import FactCell
    claim=FactCell(id='claim',user_id='demo',kind='CLAIM',subject='p',relation='says',content='model output',valid_from='2026-11-26')
    assert claim.verification=='UNVERIFIED' and claim.trust!='SOURCE'
