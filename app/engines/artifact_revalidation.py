"""Bounded human review of artifact revisions, without a model or task execution."""
import hashlib
import json
import uuid

from app.engines.coverage import check_fact_coverage
from app.engines.memory_evolution import MemoryEvolution
from app.engines.validation import validate


class TransactionReader:
    """Keep all validation reads in the same SQLite transaction as the save."""
    def __init__(self, db):
        self.db = db

    def get(self, table, record_id, user):
        return MemoryEvolution._get(self.db, table, record_id, user)

    def rows(self, table, user, project_id=None):
        return sorted(MemoryEvolution._rows(self.db, table, user, project_id), key=lambda r: r['id'])

    def facts(self, project_id, user):
        return [f for f in self.rows('facts', user, project_id) if not f.get('superseded')]


class ArtifactRevalidation:
    def __init__(self, store):
        self.store = store
        self.evolution = MemoryEvolution(store)

    def _review(self, db, user, artifact_id, reference):
        self.evolution._reference(reference)
        reader = TransactionReader(db)
        artifact = reader.get('artifacts', artifact_id, user)
        if not artifact:
            raise ValueError('ARTIFACT_NOT_FOUND')
        pid = artifact['project_id']
        if not reader.get('projects', pid, user):
            raise ValueError('PROJECT_NOT_FOUND')
        task = reader.get('tasks', artifact['task_id'], user)
        if not task or task['project_id'] != pid or task['status'] != 'COMPLETED' or task.get('artifact_id') != artifact_id:
            raise ValueError('ARTIFACT_IS_NOT_CURRENT_COMPLETED_TASK_REVISION')
        if artifact.get('verified') or not artifact.get('revalidation_required'):
            raise ValueError('ARTIFACT_REVALIDATION_NOT_REQUIRED')
        if hashlib.sha256(artifact['content'].encode()).hexdigest() != artifact['sha256']:
            raise ValueError('ARTIFACT_HASH_MISMATCH')
        self.evolution._ensure_idle(db, user, pid)
        # Historical completed-task dependencies stay historical. Current
        # mandatory facts plus current pending-task dependencies govern repair.
        tasks = reader.rows('tasks', user, pid)
        active = next((t for t in tasks if t['status'] == 'PENDING'), None)
        coverage = check_fact_coverage(reader, pid, user, reference[:10], active.get('dependency_ids', []) if active else ())
        if coverage['missing'] or coverage['conflicts'] or coverage['coverage'] != 1:
            raise ValueError('CURRENT_FACTS_NOT_VERIFIED')
        snapshot_data = {'artifact': artifact, 'facts': reader.facts(pid, user), 'evidence': coverage['evidence'], 'tasks': tasks, 'reference_date': reference[:10]}
        snapshot = hashlib.sha256(json.dumps(snapshot_data, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        facts = coverage['facts']
        goal = '\n'.join(f['content'] for f in facts if f['kind'] == 'GOAL')
        constraints = '\n'.join('- ' + f['content'] for f in facts if f['kind'] == 'CONSTRAINT')
        draft = f'# 目標\n{goal}\n\n# 限制\n{constraints}\n\n# 下一步\n- [ ] 核對目前來源\n- [ ] 核對交接內容\n- [ ] 保存驗收紀錄\n'
        return {'artifact': artifact, 'facts': facts, 'evidence': coverage['evidence'], 'snapshot': snapshot, 'draft': draft,
                'verification_scope': 'STRUCTURE_CURRENT_GOAL_AND_CONSTRAINTS', 'factual_status': 'CLAIM'}

    def review(self, user, artifact_id, reference):
        with self.store.connect() as db:
            db.execute('BEGIN')
            return self._review(db, user, artifact_id, reference)

    def save(self, user, artifact_id, content, snapshot, acknowledged, reference):
        if acknowledged is not True:
            raise ValueError('BOUNDED_REVIEW_ACKNOWLEDGMENT_REQUIRED')
        with self.store.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            review = self._review(db, user, artifact_id, reference)
            if snapshot != review['snapshot']:
                raise ValueError('STALE_REVIEW_REFRESH_REQUIRED')
            valid, result = validate(content, {'loaded': review['facts']})
            if not valid:
                raise ValueError(result)
            old = review['artifact']; pid = old['project_id']
            new = {**old, 'id': 'artifact-' + str(uuid.uuid4()), 'content': content, 'sha256': result,
                   'version': int(old.get('version', 1)) + 1, 'parent_artifact_id': artifact_id,
                   'verified': True, 'revalidation_required': False, 'factual_status': 'CLAIM',
                   'verification_scope': review['verification_scope'], 'revision_method': 'USER_REVIEW',
                   'review_snapshot': snapshot, 'reviewed_by': user, 'created_at': reference,
                   'current_fact_ids': [f['id'] for f in review['facts']],
                   'evidence_ids': [e['id'] for e in review['evidence']]}
            for key in ('invalidated_reason', 'invalidated_at', 'invalidated_fact_ids', 'superseded_by_revision'):
                new.pop(key, None)
            self.store.put('artifacts', new, db)
            self.store.put('artifacts', {**old, 'superseded_by_revision': new['id']}, db)
            for task in self.evolution._rows(db, 'tasks', user, pid):
                if task.get('artifact_id') == artifact_id:
                    task['artifact_id'] = new['id']
                    self.store.put('tasks', task, db)
                elif task['status'] == 'PENDING' and artifact_id in task.get('required_artifact_ids', []):
                    task['required_artifact_ids'] = [new['id'] if aid == artifact_id else aid for aid in task['required_artifact_ids']]
                    self.store.put('tasks', task, db)
            # Cached deliveries continue to reference the historical artifact;
            # the existing orchestrator rejects invalidated cached content.
            self.evolution._event(db, user, pid, 'ARTIFACT_REVALIDATED', reference,
                                  artifact_id=new['id'], previous_artifact_id=artifact_id,
                                  verification_scope=new['verification_scope'],
                                  detail='保存目前目標與限制的交接修訂；工作完成狀態保持原紀錄。')
            return new
