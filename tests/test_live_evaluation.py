import json
from app.engines.evaluation_live import evaluate_live

class MemoryOnlyProvider:
    def call(self,messages,mode,model,max_tokens,user,**kwargs):
        data=messages[1]['content'].split('CURRENT_MANDATORY_MEMORY\n')[1].split('\nWORK_STATE')[0]
        facts=json.loads(data)
        goal=next(f['content'] for f in facts if f['kind']=='GOAL')
        constraints='\n'.join(f['content'] for f in facts if f['kind']=='CONSTRAINT')
        return {'id':'mock-call','model':'mock-fixed','mode':mode,'input_tokens':30,'output_tokens':20,'total_tokens':50,'cost_usd':None,'content':f'## 目標\n{goal}\n## 限制\n{constraints}\n## 下一步\n- [ ] 一\n- [ ] 二\n- [ ] 三','finish_reason':'stop'}

def test_live_evaluator_counts_actual_returned_usage_and_duplicate_guard(tmp_path):
    out=evaluate_live(count=10,budget=4096,strategies=['E'],provider=MemoryOnlyProvider(),directory=tmp_path,max_cases=2)
    row=out['results'][0]
    assert row['task_success_rate']==1 and row['wrong_project_execution_rate']==0
    assert row['duplicate_completed_rate']==0 and row['mean_e2e_tokens']==50
    assert row['api_cost_usd'] is None and row['api_calls']==2
    assert all(c['raw_history_count']==0 for c in row['case_results'])

def test_retry_keeps_final_response_subtotal_but_full_usage_unknown(tmp_path):
    class RetriedProvider(MemoryOnlyProvider):
        def call(self,*args,**kwargs):return {**super().call(*args,**kwargs),'retry_count':1}
    row=evaluate_live(count=10,budget=4096,strategies=['E'],provider=RetriedProvider(),directory=tmp_path,max_cases=1)['results'][0]
    assert row['mean_e2e_tokens'] is None and row['known_api_tokens']==50
    assert row['case_results'][0]['usage_tokens'] is None

def test_preflight_block_has_zero_calls_and_does_not_crash(tmp_path):
    from app.engines.mixroute import ProviderBlocked
    class BlockedProvider:
        def call(self,*args,**kwargs):raise ProviderBlocked('BUDGET_LIMIT_REACHED')
    row=evaluate_live(count=10,budget=4096,strategies=['E'],provider=BlockedProvider(),directory=tmp_path,max_cases=1)['results'][0]
    assert row['api_calls']==0 and row['task_success_rate']==0
    assert row['case_results'][0]['status']=='BLOCKED'
