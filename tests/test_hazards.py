import pytest
from app.storage.database import Store
from app.engines.task import Orchestrator
from benchmarks.generators.synthetic import seed
from benchmarks.generators.hazards import inject

@pytest.mark.parametrize('hazard',['conflict','future','expired','claim','missing_source','prompt_injection'])
def test_synthetic_hazard_blocks_before_model_or_artifact(tmp_path,hazard):
    s=Store(tmp_path/'h.db');seed(s,10,42,'2026-11-26');inject(s,hazard)
    class ForbiddenProvider:
        def call(self,*args,**kwargs):raise AssertionError('Incomplete context must never call provider')
    out=Orchestrator(s,ForbiddenProvider()).run({'query':'MIDI 專案','mode':'FIXED','budget':4096,'idempotency_key':'hazard'})
    assert out['status']=='BLOCKED'
    assert s.get('tasks','task-PROJECT-028','demo')['status']=='PENDING'
