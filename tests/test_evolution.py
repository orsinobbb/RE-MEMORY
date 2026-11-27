import sqlite3
from concurrent.futures import ThreadPoolExecutor

import pytest

from app.storage.database import Store
from app.engines.entity_resolution import explicit_target
from benchmarks.generators.synthetic import seed


USER = "demo"
PROJECT = "PROJECT-028"
REFERENCE = "2026-11-27"


def setup(tmp_path):
    store = Store(tmp_path / "evolution.db")
    seed(store, 10, 42, "2026-11-26")
    return store


def evolution(store):
    # Import in the test body so the initial missing feature is a test failure,
    # rather than preventing collection of the acceptance suite.
    from app.engines.memory_evolution import MemoryEvolution
    return MemoryEvolution(store)


def proof(store, content, *, user=USER, project=PROJECT, trusted=True):
    record = {
        "id": "new-proof", "user_id": user, "project_id": project,
        "source": "synthetic://evolution/source", "content": content,
        "trusted": trusted, "version": 3,
    }
    store.put("evidence", record)
    return record["id"]


def snapshot(store):
    with store.connect() as db:
        return {
            table: [tuple(row) for row in db.execute(f"SELECT * FROM {table} ORDER BY 1,2")]
            for table in ("facts", "goals", "constraints", "decisions", "tasks", "artifacts", "aliases", "events", "project_fts")
        }


@pytest.mark.parametrize("kind,mirror,event", [
    ("GOAL", "goals", "GOAL_CHANGED"),
    ("CONSTRAINT", "constraints", "CONSTRAINT_CHANGED"),
    ("DECISION", "decisions", None),
])
def test_fact_update_versions_mirrors_events_and_requires_artifact_revalidation(tmp_path, kind, mirror, event):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == kind)
    old_task = store.get("tasks", f"done-{PROJECT}", USER)
    prior_artifact = store.get("artifacts", f"prior-{PROJECT}", USER)
    other_artifact = store.get("artifacts", "prior-PROJECT-002", USER)
    content = f"更新{kind}：僅使用合成資料，保留現有里程碑。"
    eid = proof(store, f"核實來源記錄\n{content}\n版本三")

    new = evolution(store).update_fact(USER, old["id"], content, eid, REFERENCE)

    assert new["version"] == old["version"] + 1
    assert new["id"] != old["id"] and new["content"] == content
    assert new["valid_from"] == REFERENCE and not new["superseded"]
    assert new["verification"] == "VERIFIED" and new["trust"] == old["trust"]
    assert new["evidence_ids"] == [eid]
    historical = store.get("facts", old["id"], USER)
    assert historical == {**old, "superseded": True}
    assert store.get(mirror, old["id"], USER) == historical
    assert store.get(mirror, new["id"], USER) == new
    assert old["id"] not in {fact["id"] for fact in store.facts(PROJECT, USER)}
    changed = [row for row in store.rows("events", USER, PROJECT) if row["type"] == "FACT_UPDATED"]
    assert len(changed) == 1
    assert changed[0]["previous_fact_id"] == old["id"] and changed[0]["fact_id"] == new["id"]
    if event:
        assert len([row for row in store.rows("events", USER, PROJECT) if row["type"] == event]) == 1

    artifact = store.get("artifacts", prior_artifact["id"], USER)
    assert artifact["verified"] is False and artifact["revalidation_required"] is True
    assert artifact["invalidated_reason"] == "FACT_UPDATED"
    assert artifact["content"] == prior_artifact["content"] and artifact["sha256"] == prior_artifact["sha256"]
    assert store.get("artifacts", other_artifact["id"], USER) == other_artifact
    assert store.get("tasks", old_task["id"], USER) == old_task
    pending = store.get("tasks", f"task-{PROJECT}", USER)
    assert pending["status"] == "PENDING" and new["id"] in pending["dependency_ids"]
    assert old["id"] not in pending["dependency_ids"]


@pytest.mark.parametrize("case", ["missing", "untrusted", "wrong_project", "wrong_owner", "original_missing"])
def test_invalid_proof_refuses_all_changes(tmp_path, case):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    content = "新目標"
    eid = "absent"
    if case != "missing":
        eid = proof(store, content, trusted=case != "untrusted", project="PROJECT-002" if case == "wrong_project" else PROJECT, user="outsider" if case == "wrong_owner" else USER)
    if case == "original_missing":
        with store.connect() as db:
            db.execute("DELETE FROM evidence WHERE id=? AND user_id=?", (old["evidence_ids"][0], USER))
    before = snapshot(store)
    with pytest.raises(ValueError):
        evolution(store).update_fact(USER, old["id"], content, eid, REFERENCE)
    assert snapshot(store) == before


@pytest.mark.parametrize("kind,trust,verification", [
    ("CLAIM", "AI", "UNVERIFIED"),
    ("INFERENCE", "AI", "VERIFIED"),
    ("GOAL", "AI", "VERIFIED"),
    ("CLAIM", "SOURCE", "VERIFIED"),
])
def test_exact_trusted_proof_never_promotes_ai_claim_or_inference(tmp_path, kind, trust, verification):
    store = setup(tmp_path)
    old = {**store.facts(PROJECT, USER)[0], "id": "ai-fact-v1", "kind": kind, "version": 1, "trust": trust, "verification": verification}
    store.put("facts", old)
    content = "AI 生成的新內容仍需驗證"
    new = evolution(store).update_fact(USER, old["id"], content, proof(store, content), REFERENCE)
    assert new["kind"] == kind and new["trust"] == trust
    assert new["verification"] == "UNVERIFIED"


def test_trusted_source_without_new_content_does_not_verify_new_fact(tmp_path):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    new = evolution(store).update_fact(USER, old["id"], "未出現在來源的新主張", proof(store, "來源只支持舊內容"), REFERENCE)
    assert new["verification"] == "UNVERIFIED"
    assert new["content"] == "未出現在來源的新主張"


def test_same_owner_reindex_and_cross_owner_update_rejection(tmp_path):
    store = setup(tmp_path)
    other = {"id": PROJECT, "user_id": "outsider", "project_id": PROJECT, "name": "外部擁有者", "topic": "教育", "description": "保持其他擁有者索引"}
    store.put("projects", other)
    store.reindex("outsider")
    with store.connect() as db:
        original_index = [tuple(row) for row in db.execute("SELECT * FROM project_fts WHERE user_id=?", ("outsider",))]
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    with pytest.raises(ValueError):
        evolution(store).update_fact("outsider", old["id"], "他人修改", "not-owned", REFERENCE)
    content = "全新穹頂驗收工作"
    new = evolution(store).update_fact(USER, old["id"], content, proof(store, content), REFERENCE)
    assert any(project["id"] == PROJECT for project in store.search(USER, "穹頂"))
    with store.connect() as db:
        assert [tuple(row) for row in db.execute("SELECT * FROM project_fts WHERE user_id=?", ("outsider",))] == original_index
    assert new["user_id"] == USER


def test_alias_confirmation_changes_one_row_preserves_ambiguity_and_records_event(tmp_path):
    store = setup(tmp_path)
    aliases = [alias for alias in store.rows("aliases", USER) if alias["alias"] == "音樂專案"]
    target = next(alias for alias in aliases if alias["project_id"] == PROJECT)
    other = next(alias for alias in aliases if alias["project_id"] != PROJECT)
    confirmed = evolution(store).confirm_alias(USER, target["id"], REFERENCE)
    assert confirmed["id"] == target["id"] and confirmed["status"] == "CONFIRMED"
    assert confirmed["ambiguous"] == target["ambiguous"]
    assert confirmed["evidence_ids"] == target["evidence_ids"] and confirmed["method"] == target["method"]
    assert confirmed["confirmed_by"] == USER and confirmed["confirmed_at"] == REFERENCE
    assert explicit_target(store.projects(USER), store.rows("aliases", USER), "繼續音樂專案") == (PROJECT, "CONFIRMED_ALIAS")
    assert store.get("aliases", other["id"], USER) == other
    assert len([alias for alias in store.rows("aliases", USER) if alias["alias"] == "音樂專案"]) == 2
    events = [event for event in store.rows("events", USER) if event["type"] == "USER_ALIAS_CONFIRMED"]
    assert len(events) == 1 and events[0]["alias_id"] == target["id"]
    assert evolution(store).confirm_alias(USER, target["id"], REFERENCE) == confirmed
    assert len([event for event in store.rows("events", USER) if event["type"] == "USER_ALIAS_CONFIRMED"]) == 1
    with pytest.raises(ValueError):
        evolution(store).confirm_alias("outsider", target["id"], REFERENCE)


def test_confirmed_alias_resolves_without_leaking_personal_dictionary_into_fts(tmp_path):
    store = setup(tmp_path)
    alias = next(alias for alias in store.rows("aliases", USER, PROJECT) if alias["status"] == "CANDIDATE")
    alias["alias"] = "alias-cobalt-only"
    store.put("aliases", alias)
    evolution(store).confirm_alias(USER, alias["id"], REFERENCE)
    assert explicit_target(store.projects(USER), store.rows("aliases", USER), "接續 alias-cobalt-only") == (PROJECT, "CONFIRMED_ALIAS")
    with store.connect() as db:
        index = db.execute("SELECT content FROM project_fts WHERE user_id=? AND id=?", (USER, PROJECT)).fetchone()[0]
    assert "alias-cobalt-only" not in index


def test_alias_rejected_state_and_superseded_fact_cannot_be_updated(tmp_path):
    store = setup(tmp_path)
    alias = next(alias for alias in store.rows("aliases", USER) if alias["status"] == "CANDIDATE")
    alias["status"] = "REJECTED"
    store.put("aliases", alias)
    with pytest.raises(ValueError):
        evolution(store).confirm_alias(USER, alias["id"], REFERENCE)
    old = next(fact for fact in store.facts(PROJECT, USER, current=False) if fact["superseded"])
    with pytest.raises(ValueError):
        evolution(store).update_fact(USER, old["id"], "不可覆寫舊版本", proof(store, "不可覆寫舊版本"), REFERENCE)


def test_event_failure_rolls_back_fact_mirrors_artifacts_tasks_and_index(tmp_path):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    eid = proof(store, "新的核實目標")
    with store.connect() as db:
        db.execute("CREATE TRIGGER reject_update_event BEFORE INSERT ON events WHEN json_extract(NEW.data,'$.type')='FACT_UPDATED' BEGIN SELECT RAISE(ABORT,'test event failure'); END")
    before = snapshot(store)
    with pytest.raises(sqlite3.IntegrityError):
        evolution(store).update_fact(USER, old["id"], "新的核實目標", eid, REFERENCE)
    assert snapshot(store) == before


def test_alias_event_failure_rolls_back_confirmation_and_owner_index(tmp_path):
    store = setup(tmp_path)
    alias = next(alias for alias in store.rows("aliases", USER) if alias["status"] == "CANDIDATE")
    with store.connect() as db:
        db.execute("CREATE TRIGGER reject_alias_event BEFORE INSERT ON events WHEN json_extract(NEW.data,'$.type')='USER_ALIAS_CONFIRMED' BEGIN SELECT RAISE(ABORT,'test alias event failure'); END")
    before = snapshot(store)
    with pytest.raises(sqlite3.IntegrityError):
        evolution(store).confirm_alias(USER, alias["id"], REFERENCE)
    assert snapshot(store) == before


def test_concurrent_updates_keep_one_current_version_and_one_update_event(tmp_path):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    content = "並行更新的核實目標"
    eid = proof(store, content)

    def update(_):
        try:
            return evolution(store).update_fact(USER, old["id"], content, eid, REFERENCE)
        except ValueError as error:
            assert str(error) == "FACT_VERSION_SUPERSEDED"
            return None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(update, range(2)))
    assert sum(result is not None for result in results) == 1
    current = [fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL"]
    assert len(current) == 1 and current[0]["version"] == 3
    assert len([event for event in store.rows("events", USER) if event["type"] == "FACT_UPDATED"]) == 1


def test_concurrent_alias_confirmation_remains_idempotent(tmp_path):
    store = setup(tmp_path)
    alias = next(alias for alias in store.rows("aliases", USER) if alias["status"] == "CANDIDATE")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: evolution(store).confirm_alias(USER, alias["id"], REFERENCE), range(2)))
    assert results[0] == results[1]
    assert len([event for event in store.rows("events", USER) if event["type"] == "USER_ALIAS_CONFIRMED"]) == 1


@pytest.mark.parametrize("content,reference", [("", REFERENCE), (None, REFERENCE), ("新內容", "invalid"), ("新內容", "2026-11-24")])
def test_invalid_content_or_reference_never_mutates_memory(tmp_path, content, reference):
    store = setup(tmp_path)
    old = next(fact for fact in store.facts(PROJECT, USER) if fact["kind"] == "GOAL")
    eid = proof(store, "新內容")
    before = snapshot(store)
    with pytest.raises(ValueError):
        evolution(store).update_fact(USER, old["id"], content, eid, reference)
    assert snapshot(store) == before
