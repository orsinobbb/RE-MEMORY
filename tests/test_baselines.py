"""Baseline contracts use synthetic stored records, never evaluator answers."""
import json

import pytest

from app.engines.budget import tokens
from app.storage.database import Store
from benchmarks.generators.synthetic import seed


def memory(tmp_path):
    store = Store(tmp_path / "baseline.db")
    seed(store, 4, 42, "2026-11-26")
    return store


def context(store, strategy, budget=65536, reference="2026-11-26", pid="PROJECT-028", query="繼續 MIDI 專案"):
    from app.engines.baselines import build_baseline_context

    return build_baseline_context(store, pid, "demo", budget, query, reference, strategy)


def test_recent_history_can_keep_all_owner_records_when_the_window_fits(tmp_path):
    store = memory(tmp_path)
    store.put("projects", {"id": "private", "user_id": "other", "project_id": "private", "name": "PRIVATE OWNER SENTINEL"})
    out = context(store, "A")
    payload = out["messages"][1]["content"]

    assert out["feasible"]
    assert "人生冒險島" in payload
    assert "舊目標已取代" in payload
    assert "前一階段合成資料測試已通過" in payload
    assert "SESSION_INTERRUPTED" in payload
    assert "synthetic://PROJECT-028/spec-v2" in payload
    assert "PRIVATE OWNER SENTINEL" not in payload
    assert out["manifest"]["history_counts"] == {
        "projects": 4, "facts": 16, "events": 12,
        "tasks": 8, "artifacts": 4, "evidence": 4,
    }
    assert out["manifest"]["truncated"] is False
    assert out["manifest"]["selected_count"] == 48
    assert out["manifest"]["dropped_count"] == 0
    assert out["memory_scope"] == "RECENT_HISTORY_WINDOW"
    assert set(out["manifest"]["evidence_references"]) == {
        row["id"] for row in store.rows("evidence", "demo")
    }


def test_recent_history_drops_whole_oversized_records_and_discloses_loss(tmp_path):
    store = memory(tmp_path)
    detail = "完整歷史不可截斷" * 2000 + "END OF FULL HISTORY"
    store.put("events", {"id": "large", "user_id": "demo", "project_id": "PROJECT-004", "date": "2026-11-26", "detail": detail})
    out = context(store, "A", budget=1024)

    assert out["feasible"]
    assert out["token_breakdown"]["total"] <= 1024
    assert "END OF FULL HISTORY" not in out["messages"][1]["content"]
    assert "large" not in {row["id"] for row in out["loaded"]}
    assert "large" in out["not_loaded"]
    assert out["manifest"]["dropped_count"] > 0
    assert "HISTORY_RECORDS_DROPPED" in out["manifest"]["losses"]
    assert store.get("events", "large", "demo")["detail"] == detail
    assert out["manifest"]["truncated"] is False


def test_recent_history_window_changes_with_budget_without_mandatory_supplement(tmp_path):
    store = memory(tmp_path)
    store.put("events", {"id": "recent", "user_id": "demo", "project_id": "PROJECT-028", "date": "2026-11-26", "detail": "RECENT WHOLE RECORD"})
    narrow = context(store, "A", budget=1024)
    wide = context(store, "A", budget=65536)
    assert narrow["manifest"]["selected_count"] < wide["manifest"]["selected_count"]
    assert narrow["token_breakdown"]["total"] < wide["token_breakdown"]["total"]
    assert narrow["loaded"][0]["id"] == "recent"
    assert "不得上傳原始音訊到第三方" not in narrow["messages"][1]["content"]
    assert narrow["coverage"] is None


def test_static_summary_freezes_old_goal_and_events_without_new_constraint_injection(tmp_path):
    store = memory(tmp_path)
    first = context(store, "B")
    payload = first["messages"][1]["content"]
    assert "舊目標已取代" in payload
    assert "音檔轉 MIDI、樂器分離與樂譜 PDF" in payload
    assert "完成樂器分離，準備接續 MIDI 轉換" in payload
    assert "不得上傳原始音訊到第三方" not in payload

    project = store.get("projects", "PROJECT-028", "demo")
    store.put("projects", {**project, "description": "NEW PROJECT SUMMARY"})
    event = store.get("events", "event-PROJECT-028-2", "demo")
    store.put("events", {**event, "detail": "NEW EVENT"})
    old = store.get("facts", "PROJECT-028-goal-v1", "demo")
    store.put("facts", {**old, "content": "NEW OLD GOAL"})
    second = context(store, "B", reference="2026-11-27")

    assert second["messages"] == first["messages"]
    assert second["manifest"]["memory_snapshot"] == first["manifest"]["memory_snapshot"]
    assert second["manifest"]["summary_reference_date"] == "2026-11-26"
    assert second["manifest"]["frozen_at"]
    assert "CURRENT_GOALS_OMITTED" in second["manifest"]["losses"]
    assert "CURRENT_CONSTRAINTS_OMITTED" in second["manifest"]["losses"]
    assert second["manifest"]["goal_version"] == 1
    assert second["manifest"]["mandatory_memory"] == []
    assert len([row for row in store.rows("snapshots", "demo", "PROJECT-028") if row.get("baseline") == "B"]) == 1


def test_single_pass_context_uses_only_three_relevant_current_facts_and_their_sources(tmp_path):
    store = memory(tmp_path)
    with store.connect() as db:
        db.execute("DELETE FROM facts WHERE user_id=? AND project_id=?", ("demo", "PROJECT-028"))
    for index, kind, text in (
        (1, "GOAL", "needle goal"),
        (2, "DECISION", "needle decision"),
        (3, "FACT", "needle note"),
        (4, "CONSTRAINT", "UNSELECTED NECESSARY CONSTRAINT"),
    ):
        eid = f"candidate-source-{index}"
        store.put("evidence", {"id": eid, "user_id": "demo", "project_id": "PROJECT-028", "source": f"synthetic://candidate/{index}", "content": f"SOURCE {text}", "trusted": True})
        store.put("facts", {"id": f"candidate-{index}", "user_id": "demo", "project_id": "PROJECT-028", "kind": kind, "content": text, "version": 2, "superseded": False, "mandatory": True, "evidence_ids": [eid]})
    out = context(store, "C", query="needle")
    payload = out["messages"][1]["content"]

    assert {row["id"] for row in out["loaded"] if row.get("kind")} == {"candidate-1", "candidate-2", "candidate-3"}
    assert "SOURCE needle note" in payload
    assert "UNSELECTED NECESSARY CONSTRAINT" not in payload
    assert "前一階段合成資料測試已通過" not in payload
    assert out["manifest"]["selection_limit"] == 3
    assert out["coverage"] is None
    assert out["feasible"]


def test_basic_context_keeps_latest_necessary_constraints(tmp_path):
    out = context(memory(tmp_path), "D", budget=4096)
    assert out["feasible"] and out["coverage"] == 1
    assert "不得上傳原始音訊到第三方" in out["messages"][1]["content"]
    assert "舊目標" not in out["messages"][1]["content"]
    assert out["manifest"]["goal_version"] == 2


@pytest.mark.parametrize("strategy", list("ABCD"))
def test_baseline_budget_and_provider_usage_contract(tmp_path, strategy):
    store = memory(tmp_path)
    out = context(store, strategy, budget=4096)
    counts = out["token_breakdown"]
    assert counts["output_reserve"] == 512
    assert counts["total"] >= tokens(out["messages"]) + 512 + counts["safety_margin"]
    assert not out["feasible"] or counts["total"] <= 4096
    assert out["actual_tokens"] is None
    assert out["actual_tokens_status"] == "UNKNOWN"
    assert {"messages", "loaded", "manifest", "faults", "missing", "conflicts", "not_loaded"}.issubset(out)
    tiny = context(store, strategy, budget=200)
    assert not tiny["feasible"]


def test_unknown_strategy_is_not_silently_the_enhanced_strategy(tmp_path):
    with pytest.raises(ValueError, match="strategy"):
        context(memory(tmp_path), "E")


def test_missing_or_other_owner_project_has_no_memory_payload(tmp_path):
    store = memory(tmp_path)
    store.put("projects", {"id": "private", "user_id": "other", "project_id": "private", "name": "PRIVATE OWNER SENTINEL"})
    out = context(store, "A", pid="private")
    assert not out["feasible"]
    assert out["missing"] == ["PROJECT_NOT_FOUND"]
    assert out["loaded"] == []
    assert out["messages"] == []
    assert "PRIVATE OWNER SENTINEL" not in json.dumps(out)
