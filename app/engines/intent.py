import re
from datetime import date,timedelta

TOPICS=("音樂","遊戲","管理","教育","研究","攝影")
def parse_intent(query,reference):
    day=date.fromisoformat(reference)
    explicit=re.search(r"\d{4}-\d{2}-\d{2}",query)
    when=(day-timedelta(days=1)).isoformat() if "昨天" in query or "yesterday" in query.casefold() else (explicit.group() if explicit else None)
    topic=next((t for t in TOPICS if t in query),None)
    if not topic and re.search(r"midi|music|音檔|轉譜|鋼琴|樂器|樂理",query,re.I):topic="音樂"
    return {"time":when,"topic":topic,"action":"CONTINUE" if re.search(r"繼續|接續|continue|resume",query,re.I) else "RETRIEVE","object":"PROJECT"}
