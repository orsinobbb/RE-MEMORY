"""Owner-scoped, transactional memory revisions and explicit alias confirmation.

This module does not call a model, execute a task, or revalidate an artifact.
Evidence trust is necessary but is not enough to verify newly invented text.
"""
import json
import re
import uuid
from datetime import date, datetime

from app.storage.database import TABLES


MIRRORS = {"GOAL": "goals", "CONSTRAINT": "constraints", "DECISION": "decisions"}
KIND_EVENTS = {"GOAL": "GOAL_CHANGED", "CONSTRAINT": "CONSTRAINT_CHANGED"}


class MemoryEvolution:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def _reference(reference):
        if not isinstance(reference, str):
            raise ValueError("INVALID_REFERENCE_DATE")
        try:
            day = date.fromisoformat(reference[:10])
            if len(reference) > 10:
                datetime.fromisoformat(reference.replace("Z", "+00:00"))
        except ValueError as error:
            raise ValueError("INVALID_REFERENCE_DATE") from error
        return day

    @staticmethod
    def _get(db, table, record_id, user):
        if table not in TABLES:
            raise ValueError("TABLE_NOT_ALLOWED")
        row = db.execute(f"SELECT data FROM {table} WHERE id=? AND user_id=?", (record_id, user)).fetchone()
        return json.loads(row[0]) if row else None

    @staticmethod
    def _rows(db, table, user, project_id=None):
        if table not in TABLES:
            raise ValueError("TABLE_NOT_ALLOWED")
        sql = f"SELECT data FROM {table} WHERE user_id=?"
        args = [user]
        if project_id is not None:
            sql += " AND project_id=?"
            args.append(project_id)
        return [json.loads(row[0]) for row in db.execute(sql, args)]

    def _proof(self, db, user, project_id, evidence_id):
        evidence = self._get(db, "evidence", evidence_id, user)
        if not evidence or evidence.get("project_id") != project_id or evidence.get("trusted") is not True:
            raise ValueError("EVIDENCE_MISSING_UNTRUSTED_OR_WRONG_PROJECT")
        return evidence

    def _event(self, db, user, project_id, event_type, reference, **detail):
        record = {
            "id": str(uuid.uuid4()), "user_id": user, "project_id": project_id,
            "type": event_type, "date": reference[:10], "created_at": reference,
            **detail,
        }
        self.store.put("events", record, db)

    def _reindex(self, db, user):
        # The shared index includes project metadata/current facts, while
        # personalized aliases remain in the explicit L1/entity-resolution path.
        self.store.reindex(user, db=db)

    def _ensure_idle(self, db, user, project_id):
        task_ids = {t['id'] for t in self._rows(db, 'tasks', user, project_id)}
        locks = db.execute('SELECT task_id FROM task_locks WHERE user_id=?', (user,))
        if any(row[0] in task_ids for row in locks):
            raise ValueError('PROJECT_EXECUTION_IN_PROGRESS')

    def update_fact(self, user, fact_id, content, evidence_id, reference, *, require_supported=False):
        day = self._reference(reference)
        if not isinstance(content, str) or not content.strip():
            raise ValueError("EMPTY_FACT_CONTENT")
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = self._get(db, "facts", fact_id, user)
            if not old:
                raise ValueError("FACT_NOT_FOUND")
            if old.get("superseded"):
                raise ValueError("FACT_VERSION_SUPERSEDED")
            project_id = old["project_id"]
            self._ensure_idle(db, user, project_id)
            if not self._get(db, "projects", project_id, user):
                raise ValueError("PROJECT_NOT_FOUND")
            if day < date.fromisoformat(old["valid_from"][:10]):
                raise ValueError("FACT_UPDATE_CANNOT_PRECEDE_CURRENT_VERSION")
            original_proofs = old.get("evidence_ids", [])
            if not original_proofs:
                raise ValueError("ORIGINAL_EVIDENCE_MISSING")
            for original_id in original_proofs:
                self._proof(db, user, project_id, original_id)
            evidence = self._proof(db, user, project_id, evidence_id)

            version = int(old.get("version", 1)) + 1
            new_id = re.sub(r"-v\d+$", f"-v{version}", fact_id) if re.search(r"-v\d+$", fact_id) else f"{fact_id}-v{version}"
            if self._get(db, "facts", new_id, user):
                raise ValueError("FACT_VERSION_ALREADY_EXISTS")
            supported = isinstance(evidence.get("content"), str) and content in evidence["content"]
            verified = (
                supported and old.get("verification") == "VERIFIED"
                and old.get("trust") in ("USER", "SOURCE")
                and old.get("kind") not in ("CLAIM", "INFERENCE", "UNKNOWN")
            )
            if require_supported and not verified:
                raise ValueError('SOURCE_SUPPORTED_VERIFIED_REVISION_REQUIRED')
            historical = {**old, "superseded": True}
            new = {
                **old, "id": new_id, "version": version, "content": content,
                "evidence_ids": [evidence_id], "valid_from": reference, "valid_to": None,
                "created_at": reference, "superseded": False,
                "verification": "VERIFIED" if verified else "UNVERIFIED",
                "previous_fact_id": fact_id,
            }
            self.store.put("facts", historical, db)
            self.store.put("facts", new, db)
            mirror = MIRRORS.get(old["kind"])
            if mirror:
                self.store.put(mirror, historical, db)
                self.store.put(mirror, new, db)

            invalidated = []
            # Existing artifacts do not uniformly expose fact dependencies.
            # Conservatively invalidate the project, retaining its full history.
            for artifact in self._rows(db, "artifacts", user, project_id):
                artifact.update(verified=False, revalidation_required=True, invalidated_reason="FACT_UPDATED", invalidated_at=reference)
                artifact["invalidated_fact_ids"] = list(dict.fromkeys(artifact.get("invalidated_fact_ids", []) + [fact_id]))
                self.store.put("artifacts", artifact, db)
                invalidated.append(artifact["id"])
            for task in self._rows(db, "tasks", user, project_id):
                if task["status"] == "PENDING" and fact_id in task.get("dependency_ids", []):
                    task["dependency_ids"] = [new_id if dep == fact_id else dep for dep in task["dependency_ids"]]
                    self.store.put("tasks", task, db)

            self._reindex(db, user)
            detail = {
                "detail": f"{old['kind']} 更新為版本 {version}；相關成果需要重新驗證。",
                "fact_id": new_id, "previous_fact_id": fact_id,
                "version": version, "evidence_ids": [evidence_id],
                "invalidated_artifact_ids": invalidated,
            }
            self._event(db, user, project_id, "FACT_UPDATED", reference, **detail)
            if old["kind"] in KIND_EVENTS:
                self._event(db, user, project_id, KIND_EVENTS[old["kind"]], reference, **detail)
        return new

    def confirm_alias(self, user, alias_id, reference):
        self._reference(reference)
        with self.store.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            alias = self._get(db, "aliases", alias_id, user)
            if not alias:
                raise ValueError("ALIAS_NOT_FOUND")
            if not self._get(db, "projects", alias["project_id"], user):
                raise ValueError("PROJECT_NOT_FOUND")
            if alias["status"] == "CONFIRMED":
                return alias
            if alias["status"] != "CANDIDATE":
                raise ValueError("ALIAS_NOT_CONFIRMABLE")
            # Keep the original creation method/proof and other ambiguous rows.
            # Explicit user confirmation is separately attributable evidence.
            alias.update(status="CONFIRMED", confirmed_by=user, confirmed_at=reference, confirmation_method="USER")
            self.store.put("aliases", alias, db)
            self._reindex(db, user)
            self._event(
                db, user, alias["project_id"], "USER_ALIAS_CONFIRMED", reference,
                alias_id=alias_id, detail=f"使用者確認稱呼：{alias['alias']}",
                evidence_ids=alias.get("evidence_ids", []),
            )
        return alias
