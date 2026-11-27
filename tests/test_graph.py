from app.engines.retrieval import Router
from app.storage.database import Store
from benchmarks.generators.synthetic import seed

def test_personalized_exploration_reads_sourced_relation_once(tmp_path):
    s=Store(tmp_path/'r.db');seed(s,10,42,'2026-11-26')
    out=Router(s).retrieve('昨天的音樂專案',budget=4096)
    round2=out['rounds'][2]
    assert 'relation:tracker-relation:v1' in out['read_versions']
    assert any('PROJECT-004' in x for x in round2['new_clues'])
    plain=Router(s).retrieve('昨天的音樂專案',budget=4096,strategy='D')
    assert not any(x.startswith('relation:') for x in plain['read_versions'])
