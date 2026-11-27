import sqlite3
from pathlib import Path
from datetime import datetime
root=Path(__file__).resolve().parents[1];source=root/'data/runtime/rememory.db'
if not source.exists():raise SystemExit('Runtime database not found')
directory=root/'data/backups';directory.mkdir(parents=True,exist_ok=True)
target=directory/('rememory-'+datetime.now().strftime('%Y%m%d-%H%M%S-%f')+'.db')
with sqlite3.connect(source) as src,sqlite3.connect(target) as dst:src.backup(dst)
print(target)
