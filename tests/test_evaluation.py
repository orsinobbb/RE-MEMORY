from app.engines.evaluation import evaluate

def test_offline_evaluation_does_not_fabricate_live_success_or_cost(tmp_path):
    result=evaluate(count=10,budgets=[4096],strategies=['A','B','C','D','E','F'],directory=tmp_path)
    assert len(result['results'])==6
    for row in result['results']:
        assert row['task_success_rate'] is None and row['api_cost_usd'] is None
        assert row['critical_memory_recall'] is None or 0<=row['critical_memory_recall']<=1
    assert result['results'][-1]['status']=='NOT_RUN_REQUIRES_LIVE_SMART_ROUTING'
    assert result['results'][4]['top1_accuracy']>0
    assert result['results'][0]['mean_rounds']!=result['results'][4]['mean_rounds']

def test_truth_is_separate_from_memory_database(tmp_path):
    out=evaluate(count=10,budgets=[2048],strategies=['E'],directory=tmp_path)
    assert out['ground_truth_isolated'] and out['split']=='blind'
    assert out['results'][0]['cases']>=8
