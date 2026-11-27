"""Append observed stage timing and disk/API metrics; no secrets are read."""
import argparse,json,time
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
root=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser();p.add_argument("stage");p.add_argument("--start",type=float,required=True);p.add_argument("--checks",required=True)
a=p.parse_args();now=time.time()
size=sum(f.stat().st_size for f in root.rglob("*") if f.is_file() and not f.is_symlink())
path=root/"reports/resources.json";report=json.loads(path.read_text())
record={"stage":a.stage,"completed_at":datetime.now(ZoneInfo("Asia/Taipei")).isoformat(),"elapsed_seconds":round(now-a.start,2),"checks":a.checks,"project_disk_bytes":size,"api_calls":report.get("api_calls",0),"api_tokens":report.get("api_tokens",0),"api_cost_usd":report.get("api_cost_usd",0)}
report["stages"].append(record);path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n")
with (root/"reports/progress.md").open("a") as f:f.write(f"\nStage {a.stage}: {record['elapsed_seconds']}s; {a.checks}; disk {size} bytes; API calls {record['api_calls']}, tokens {record['api_tokens']}, cost {record['api_cost_usd']}.\n")
print(json.dumps(record,ensure_ascii=False))
