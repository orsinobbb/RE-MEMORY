"""Evaluator-only truth. Never imported by retrieval/context/task engines."""
def cases(split="blind"):
    pairs=[
      ("我要你繼續做昨天的音樂專案。","PROJECT-028"),
      ("接續 MIDI 專案","PROJECT-028"),
      ("繼續音樂轉 PDF","PROJECT-028"),
      ("繼續鋼琴課","PROJECT-002"),
      ("接續冒險島","PROJECT-003"),
      ("繼續工作管理","PROJECT-004"),
      ("接續 PROJECT-1004","PROJECT-1004"),
      ("繼續音樂專案",None),
      ("昨天的量子火箭專案",None),
      ("繼續音訊轉換系統","PROJECT-028"),
    ]
    if split=="dev":pairs=[("請繼續轉譜工具","PROJECT-028"),("接續樂理教材","PROJECT-002"),("島嶼遊戲","PROJECT-003"),("音樂專案",None)]
    return [{"id":f"{split}-{i}","query":q,"project_id":pid,"critical_fact_ids":[pid+"-goal-v2",pid+"-constraint-v2",pid+"-decision-v2"] if pid else []} for i,(q,pid) in enumerate(pairs)]
