"""Memory ablations; completion correctness is checked by the external validator.

A selects whole recent owner records, B reuses a frozen lossy summary, C uses
three current facts from the already selected project, and D uses basic required
context. None of A/B/C repairs missing necessary memory or reads evaluator truth.
"""
import hashlib
import json
from datetime import datetime, timezone

from app.storage.database import terms

from .budget import allocate, token_method, tokens
from .context_builder import SYSTEM, TOOLS, build_context


HISTORY_TABLES = ("projects", "facts", "events", "tasks", "artifacts", "evidence")
SUMMARY_LOSSES = [
    "CURRENT_GOALS_OMITTED", "CURRENT_CONSTRAINTS_OMITTED",
    "SOURCE_CONTENT_OMITTED", "TASK_DEPENDENCIES_OMITTED",
    "CHANGES_AFTER_SUMMARY_FREEZE_OMITTED",
]


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _snapshot(value):
    return hashlib.sha256(_json(value).encode()).hexdigest()


def _pack(pid, budget, query, strategy, scope, memory, loaded, evidence=None,
          not_loaded=None, extra=None, missing=None):
    evidence = evidence or []
    missing = missing or []
    parts = {
        "system": SYSTEM, "user": query, "mandatory": _json(memory),
        "work": _json({"project_id": pid}), "evidence": _json(evidence),
        "tools": TOOLS,
    }
    messages = [
        {"role": "system", "content": SYSTEM + "\n" + TOOLS},
        {"role": "user", "content": "REQUEST\n" + query + "\n" + scope + "\n"
         + parts["mandatory"] + "\nSELECTED_PROJECT\n" + parts["work"]
         + "\nSOURCE_EVIDENCE_DATA\n" + parts["evidence"]},
    ]
    counts, _ = allocate(parts, budget, output=512, margin=128)
    prompt = tokens(messages)
    overhead = max(prompt - sum(counts[name] for name in parts), 0)
    counts["tools"] += overhead
    counts["total"] += overhead
    fits = counts["total"] <= budget
    facts = [row for row in loaded if row.get("kind") in ("GOAL", "CONSTRAINT", "DECISION")
             and row.get("project_id") == pid]
    task = next((row for row in loaded if row.get("status") == "PENDING"
                 and row.get("project_id") == pid), None)
    manifest = {
        "project_id": pid,
        "goal_version": max((row.get("version", 1) for row in facts if row["kind"] == "GOAL"), default=None),
        "active_task": task["id"] if task else None,
        "mandatory_memory": [row["id"] for row in facts if not row.get("superseded")],
        "required_dependencies": task.get("dependency_ids", []) if task else [],
        "unresolved_conflicts": [],
        "evidence_references": [row["id"] for row in evidence],
        "missing_information": missing,
        "memory_snapshot": _snapshot({"memory": memory, "evidence": evidence}),
        "token_budget": budget, "strategy": strategy,
        "coverage_status": "NOT_CHECKED_BY_BASELINE", "truncated": False,
        **(extra or {}),
    }
    return {
        "feasible": fits, "coverage": None, "manifest": manifest,
        "missing": missing, "conflicts": [],
        "faults": [] if fits else [{"type": "BUDGET_LIMIT_REACHED", "reason": "BUDGET", "resolved": False}],
        "loaded": loaded, "not_loaded": not_loaded or [],
        "token_breakdown": counts, "token_method": token_method(),
        "prompt_tokens_estimate": prompt, "messages": messages,
        "budget_status": "FEASIBLE" if fits else "BUDGET", "memory_scope": scope,
        "actual_tokens": None, "actual_tokens_status": "UNKNOWN", "strategy": strategy,
    }


def _time(row):
    for key in ("updated_at", "date", "created_at", "last_active"):
        value = row.get(key)
        if not value:
            continue
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return parsed.replace(tzinfo=timezone.utc).timestamp() if parsed.tzinfo is None else parsed.timestamp()
        except (ValueError, TypeError):
            continue
    return float("-inf")


def _recent_history(store, pid, user, budget, query):
    histories = {table: store.rows(table, user) for table in HISTORY_TABLES}
    cards = [{"table": table, "record": row} for table, rows in histories.items() for row in rows]
    cards.sort(key=lambda card: (-_time(card["record"]), -card["record"].get("version", 1),
                                card["table"], card["record"]["id"]))
    empty = _pack(pid, budget, query, "A", "RECENT_HISTORY_WINDOW", [], [])
    used = empty["token_breakdown"]["total"]
    selected, dropped = [], []
    # Conservative per-record accounting avoids repeatedly tokenizing a large
    # owner history; final message packing below still enforces the hard limit.
    for card in cards:
        cost = tokens(card) + 2
        if used + cost <= budget:
            selected.append(card)
            used += cost
        else:
            dropped.append(card)
    while True:
        loaded = [card["record"] for card in selected]
        extra = {
            "history_counts": {table: len(rows) for table, rows in histories.items()},
            "selected_count": len(selected), "dropped_count": len(dropped),
            "selected_records": [{"table": card["table"], "id": card["record"]["id"]} for card in selected],
            "dropped_records": [{"table": card["table"], "id": card["record"]["id"]} for card in dropped],
            "evidence_references": [card["record"]["id"] for card in selected if card["table"] == "evidence"],
            "losses": ["HISTORY_RECORDS_DROPPED"] if dropped else [],
            "selection_order": "TIMESTAMP_DESCENDING_WHOLE_RECORDS",
        }
        out = _pack(pid, budget, query, "A", "RECENT_HISTORY_WINDOW", selected, loaded,
                    not_loaded=[card["record"]["id"] for card in dropped], extra=extra)
        if out["feasible"] or not selected:
            return out
        dropped.append(selected.pop())


def _frozen_summary(store, project, user, reference):
    pid = project["id"]
    summary_id = "baseline-static-summary-B:" + pid
    with store.connect() as db:
        existing = db.execute("SELECT data FROM snapshots WHERE user_id=? AND id=?", (user, summary_id)).fetchone()
        if existing:
            return json.loads(existing[0])
        # Filter to this project's old GOAL directly; this is not an all-facts
        # scan or an enhanced necessary-memory coverage pass.
        old = db.execute(
            "SELECT data FROM facts WHERE user_id=? AND project_id=? "
            "AND json_extract(data,'$.kind')='GOAL' "
            "AND json_extract(data,'$.superseded')=1 "
            "ORDER BY CAST(json_extract(data,'$.version') AS INTEGER),id LIMIT 1",
            (user, pid),
        ).fetchone()
        old_goal = json.loads(old[0]) if old else None
        events = [json.loads(row[0]) for row in db.execute(
            "SELECT data FROM events WHERE user_id=? AND project_id=? ORDER BY id", (user, pid))]
        summary = {
            "project": {key: project.get(key) for key in ("id", "name", "topic", "description")},
            "old_goal": {key: old_goal.get(key) for key in ("id", "project_id", "kind", "content", "version", "superseded", "evidence_ids")} if old_goal else None,
            "event_summary": [{key: event.get(key) for key in ("id", "date", "type", "detail")} for event in events],
            "reference_date": reference,
        }
        frozen = {
            "id": summary_id, "user_id": user, "project_id": pid, "baseline": "B",
            "summary": summary, "frozen_at": datetime.now(timezone.utc).isoformat(),
            "losses": SUMMARY_LOSSES + ([] if old_goal else ["OLD_GOAL_UNAVAILABLE"]),
            "source_ids": [pid] + ([old_goal["id"]] if old_goal else []) + [event["id"] for event in events],
        }
        store.put("snapshots", frozen, db)
        return frozen


def _single_pass(store, pid, user, budget, query):
    facts = store.facts(pid, user)
    query_terms = set(terms(query))
    facts.sort(key=lambda row: (-len(query_terms.intersection(terms(row.get("content", "")))),
                               -row.get("version", 1), row["id"]))
    selected = facts[:3]
    sources, missing = {}, []
    for fact in selected:
        for eid in fact.get("evidence_ids", []):
            source = store.get("evidence", eid, user)
            if source and source.get("project_id") == pid:
                sources[eid] = source
            else:
                missing.append("SOURCE_NOT_LOADED:" + eid)
    evidence = list(sources.values())
    return _pack(pid, budget, query, "C", "SINGLE_PASS_CURRENT_FACTS", selected,
                 selected + evidence, evidence=evidence,
                 not_loaded=[row["id"] for row in facts[3:]], missing=list(dict.fromkeys(missing)),
                 extra={"selection_limit": 3, "selected_count": len(selected),
                        "dropped_count": len(facts[3:]), "losses": ["FACTS_OUTSIDE_TOP_THREE_OMITTED", "TASK_DEPENDENCIES_OMITTED"],
                        "project_selection": "REUSED_ROUTER_SINGLE_FTS_RESULT"})


def build_baseline_context(store, pid, user, budget, query, reference, strategy):
    """Return the build_context contract; A/B/C feasibility means packing only.

    The caller supplies the selected project and checks generated artifacts
    against a separate latest-necessary-memory validation context. C does not
    repeat project search. B creates one owner/project snapshot on its first use.
    """
    if strategy not in ("A", "B", "C", "D"):
        raise ValueError("Unsupported baseline strategy")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a nonnegative integer")
    project = store.get("projects", pid, user)
    if not project:
        out = _pack(pid, budget, query, strategy, "NO_PROJECT", [], [], missing=["PROJECT_NOT_FOUND"])
        out.update(feasible=False, coverage=0, loaded=[], messages=[], prompt_tokens_estimate=0, budget_status="BLOCKED",
                   faults=[{"reason": "PROJECT_NOT_FOUND", "resolved": False}])
        out["token_breakdown"] = {"system": 0, "user": 0, "mandatory": 0, "work": 0, "evidence": 0,
                                  "tools": 0, "output_reserve": 512, "safety_margin": 128, "total": 640}
        return out
    if strategy == "A":
        return _recent_history(store, pid, user, budget, query)
    if strategy == "B":
        frozen = _frozen_summary(store, project, user, reference)
        old = frozen["summary"]["old_goal"]
        return _pack(pid, budget, query, "B", "FROZEN_STATIC_SUMMARY", frozen["summary"],
                     [old] if old else [], extra={"summary_id": frozen["id"], "frozen_at": frozen["frozen_at"],
                     "summary_reference_date": frozen["summary"]["reference_date"], "source_record_ids": frozen["source_ids"],
                     "losses": frozen["losses"], "not_loaded_status": "NOT_ENUMERATED_BY_STATIC_SUMMARY"})
    if strategy == "C":
        return _single_pass(store, pid, user, budget, query)
    out = build_context(store, pid, user, budget, query, reference)
    out.update(strategy="D", memory_scope="NON_PERSONALIZED_REQUIRED_CONTEXT",
               actual_tokens=None, actual_tokens_status="UNKNOWN")
    if out["token_breakdown"]["total"] > budget:
        out["budget_status"] = "BUDGET"
    return out
