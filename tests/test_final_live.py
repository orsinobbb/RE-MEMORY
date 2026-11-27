import hashlib
import json
from pathlib import Path
import pytest
from benchmarks.final_live import evaluate_final, summarize
from tests.test_live_evaluation import MemoryOnlyProvider

CASE={'id':'truth-secret-771','query':'請接續 MIDI 專案的待辦','expected_project':'PROJECT-028','expected_outcome':'COMPLETE'}

def test_fixed_case_hash_and_labels_are_not_in_provider_inputs(tmp_path):
    class Spy(MemoryOnlyProvider):
        messages=[]
        def call(self,messages,*args,**kwargs):
            self.messages.append(messages)
            assert 'truth-secret-771' not in json.dumps(messages)
            assert 'expected_project' not in json.dumps(messages)
            return super().call(messages,*args,**kwargs)
    provider=Spy();out=evaluate_final(provider=provider,directory=tmp_path,cases=[CASE],arms=['E'])
    row=out['results'][0]
    assert row['task_success_rate']==1 and row['duplicate_completed_rate']==0
    assert len(provider.messages)==1 and row['api_calls']==1
    assert row['api_cost_usd'] is None
    source=Path('benchmarks/generators/final-cases.json')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==Path(source.with_suffix('.sha256')).read_text().strip()
    assert row['case_results'][0]['output']['artifact']['factual_status']=='CLAIM'

def test_expected_stops_require_no_generation(tmp_path):
    class NoCall:
        def call(self,*args,**kwargs):raise AssertionError('No paid call for unknown project')
    case={**CASE,'query':'接續北極星量子衛星計畫','expected_project':None,'expected_outcome':'STOP'}
    row=evaluate_final(provider=NoCall(),directory=tmp_path,cases=[case],arms=['F'])['results'][0]
    assert row['stop_success_rate']==1 and row['api_calls']==0
    assert row['task_success_rate'] is None

def test_retry_retains_known_subtotal_and_failure_not_success(tmp_path):
    class Bad(MemoryOnlyProvider):
        def call(self,*args,**kwargs):return {**super().call(*args,**kwargs),'content':'incomplete','retry_count':1}
    row=evaluate_final(provider=Bad(),directory=tmp_path,cases=[CASE],arms=['E'])['results'][0]
    assert row['task_success_rate']==0 and row['api_calls']==2
    assert row['api_tokens'] is None and row['known_api_tokens']==50
    assert row['case_results'][0]['output']['status']=='BLOCKED'

def test_summarize_does_not_award_wrong_project_or_paid_stop():
    case={**CASE,'expected_project':None,'expected_outcome':'STOP'}
    row=summarize('F',[{'case':case,'output':{'status':'COMPLETED','project_id':'PROJECT-028','artifact':{'verified':True}},'calls':[{'id':'x','total_tokens':50}], 'duplicate_status':None}],4096)
    assert row['stop_success_rate']==0 and row['wrong_project_execution_rate']==1

def test_invalid_arm_and_tampered_frozen_cases_are_rejected(tmp_path):
    with pytest.raises(ValueError,match='ARM'):evaluate_final(provider=MemoryOnlyProvider(),directory=tmp_path,arms=['A'])
    source=tmp_path/'cases.json';source.write_text('{"cases":[]}');source.with_suffix('.sha256').write_text('0'*64)
    with pytest.raises(ValueError,match='HASH'):evaluate_final(provider=MemoryOnlyProvider(),directory=tmp_path,case_file=source)

def test_fixed_other_arm_uses_explicit_model(tmp_path):
    class Spy(MemoryOnlyProvider):
        def call(self,messages,mode,model,*args,**kwargs):
            assert mode=='FIXED' and model=='other-authorized'
            return super().call(messages,mode,model,*args,**kwargs)
    assert evaluate_final(provider=Spy(),directory=tmp_path,cases=[CASE],arms=['OTHER'],other_model='other-authorized')['results'][0]['api_calls']==1
