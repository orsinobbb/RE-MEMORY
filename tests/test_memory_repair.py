import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from app.engines.memory_evolution import MemoryEvolution
from app.engines.mixroute import Settings
from app.main import create_app
from tests.test_evolution import setup, snapshot, proof, USER, PROJECT, REFERENCE


def engine(store):
    from app.engines.artifact_revalidation import ArtifactRevalidation
    return ArtifactRevalidation(store)


def changed(store):
    old = next(f for f in store.facts(PROJECT, USER) if f['kind'] == 'GOAL')
    content = '更新目標：僅使用合成資料完成 MIDI 驗收。'
    MemoryEvolution(store).update_fact(USER, old['id'], content, proof(store, content), REFERENCE)
    return f'prior-{PROJECT}'


def draft(review):
    facts = review['facts']
    goal = '\n'.join(f['content'] for f in facts if f['kind'] == 'GOAL')
    constraints = '\n'.join('- ' + f['content'] for f in facts if f['kind'] == 'CONSTRAINT')
    return f'# 目標\n{goal}\n# 限制\n{constraints}\n# 下一步\n- [ ] 核對來源\n- [ ] 核對內容\n- [ ] 保存驗收紀錄\n'


def save(store, aid, review, content=None, acknowledged=True):
    return engine(store).save(USER, aid, content or draft(review), review['snapshot'], acknowledged, REFERENCE)


def test_review_and_save_revision_preserve_history_and_normal_coverage(tmp_path):
    from app.engines.coverage import check_coverage
    store = setup(tmp_path)
    aid = changed(store)
    old = store.get('artifacts', aid, USER)
    task_before = store.get('tasks', f'done-{PROJECT}', USER)
    pending = store.get('tasks', f'task-{PROJECT}', USER)
    pending['required_artifact_ids'] = [aid]
    store.put('tasks', pending)
    assert check_coverage(store, PROJECT, USER, REFERENCE)['missing']
    review = engine(store).review(USER, aid, REFERENCE)
    new = save(store, aid, review)
    assert new['id'] != aid and new['parent_artifact_id'] == aid and new['version'] == 2
    assert new['verified'] and new['factual_status'] == 'CLAIM' and new['mode'] == old['mode']
    assert new['verification_scope'] == 'STRUCTURE_CURRENT_GOAL_AND_CONSTRAINTS'
    assert store.get('artifacts', aid, USER)['content'] == old['content']
    assert store.get('artifacts', aid, USER)['sha256'] == old['sha256']
    assert not store.get('artifacts', aid, USER)['verified']
    task_after = store.get('tasks', task_before['id'], USER)
    assert task_after == {**task_before, 'artifact_id': new['id']}
    assert store.get('tasks', pending['id'], USER)['required_artifact_ids'] == [new['id']]
    assert not check_coverage(store, PROJECT, USER, REFERENCE)['missing']
    assert len([e for e in store.rows('events', USER, PROJECT) if e['type'] == 'ARTIFACT_REVALIDATED']) == 1
    assert not store.rows('model_calls', USER)


@pytest.mark.parametrize('case', ['stale', 'no_ack', 'invalid', 'wrong_owner', 'wrong_task_project', 'invalid_fact', 'locked'])
def test_revalidation_refuses_unsafe_changes_atomically(tmp_path, case):
    store = setup(tmp_path); aid = changed(store)
    review = engine(store).review(USER, aid, REFERENCE)
    if case == 'stale':
        fact = store.facts(PROJECT, USER)[0]; fact['content'] += ' changed'; store.put('facts', fact)
    elif case == 'wrong_task_project':
        task = store.get('tasks', f'done-{PROJECT}', USER); task['project_id'] = 'PROJECT-002'; store.put('tasks', task)
    elif case == 'invalid_fact':
        fact = store.facts(PROJECT, USER)[0]; fact['verification'] = 'UNVERIFIED'; store.put('facts', fact)
    elif case == 'locked':
        with store.connect() as db:
            db.execute('INSERT INTO task_locks VALUES (?,?,?,?)', (USER, f'task-{PROJECT}', 'busy', time.time()))
    before = snapshot(store)
    with pytest.raises(ValueError):
        engine(store).save('outsider' if case == 'wrong_owner' else USER, aid, 'bad' if case == 'invalid' else draft(review), review['snapshot'], case != 'no_ack', REFERENCE)
    assert snapshot(store) == before


def test_only_one_concurrent_revision_commits(tmp_path):
    store = setup(tmp_path); aid = changed(store); review = engine(store).review(USER, aid, REFERENCE)
    def worker():
        try: return save(store, aid, review)['id']
        except ValueError: return None
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: worker(), range(2)))
    assert sum(r is not None for r in results) == 1


def test_revision_rolls_back_if_event_write_fails(tmp_path, monkeypatch):
    store = setup(tmp_path); aid = changed(store); review = engine(store).review(USER, aid, REFERENCE)
    before = snapshot(store); original = store.put
    def fail(table, row, db=None):
        if table == 'events': raise RuntimeError('event unavailable')
        return original(table, row, db)
    monkeypatch.setattr(store, 'put', fail)
    with pytest.raises(RuntimeError): save(store, aid, review)
    assert snapshot(store) == before


def test_api_supported_fact_revision_alias_and_artifact_review(tmp_path):
    store = setup(tmp_path); client = TestClient(create_app(store, Settings(enabled=False)))
    fact = next(f for f in store.facts(PROJECT, USER) if f['kind'] == 'GOAL')
    body = {'content': fact['content'], 'evidence_id': fact['evidence_ids'][0], 'reference_date': REFERENCE}
    before = snapshot(store)
    assert client.post(f"/api/memory/facts/{fact['id']}/revise", json={**body, 'content': '無來源支持的主張'}).status_code == 409
    assert snapshot(store) == before
    response = client.post(f"/api/memory/facts/{fact['id']}/revise", json=body)
    assert response.status_code == 200 and response.json()['version'] == 3
    assert client.get('/api/state').json()['reference_date'] == REFERENCE
    assert client.post(f"/api/memory/facts/{fact['id']}/revise", json=body).status_code == 409
    alias = next(a for a in store.rows('aliases', USER, PROJECT) if a['status'] == 'CANDIDATE')
    response = client.post(f"/api/memory/aliases/{alias['id']}/confirm", json={'reference_date': REFERENCE})
    assert response.status_code == 200 and response.json()['status'] == 'CONFIRMED'
    aid = f'prior-{PROJECT}'
    review = client.get(f'/api/artifact/{aid}/review?reference_date={REFERENCE}').json()
    response = client.post(f'/api/artifact/{aid}/revalidate', json={'content': draft(review), 'snapshot': review['snapshot'], 'acknowledged': True, 'reference_date': REFERENCE})
    assert response.status_code == 200 and response.json()['parent_artifact_id'] == aid
    assert client.post(f"/api/memory/aliases/{alias['id']}/confirm", json={'reference_date': REFERENCE}, headers={'Origin': 'https://evil.invalid'}).status_code == 403


def test_fact_revision_during_execution_is_blocked(tmp_path):
    store = setup(tmp_path); old = store.facts(PROJECT, USER)[0]
    with store.connect() as db:
        db.execute('INSERT INTO task_locks VALUES (?,?,?,?)', (USER, f'task-{PROJECT}', 'busy', time.time()))
    before = snapshot(store)
    with pytest.raises(ValueError, match='PROJECT_EXECUTION_IN_PROGRESS'):
        MemoryEvolution(store).update_fact(USER, old['id'], old['content'], old['evidence_ids'][0], REFERENCE)
    assert snapshot(store) == before
