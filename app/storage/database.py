import json
import re
import sqlite3
import math
from contextlib import contextmanager
from pathlib import Path

TABLES = {"users","projects","facts","aliases","evidence","events","goals","constraints",
          "decisions","tasks","artifacts","relations","snapshots","sessions","traces",
          "model_calls","evaluations","topics","entities","conversations","chat_messages","chat_memories","chat_requests"}

def terms(text):
    found = re.findall(r"[a-z0-9_-]+", text.casefold())
    for run in re.findall(r"[\u3400-\u9fff]+", text):
        found.extend(run[i:i+2] for i in range(len(run)-1))
        if len(run)==1: found.append(run)
    return list(dict.fromkeys(found))

class Store:
    def __init__(self,path):
        self.path=Path(path)
        self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            for table in sorted(TABLES):
                db.execute(f"CREATE TABLE IF NOT EXISTS {table} (id TEXT NOT NULL,user_id TEXT NOT NULL,project_id TEXT NOT NULL,data TEXT NOT NULL,PRIMARY KEY(user_id,id))")
                db.execute(f"CREATE INDEX IF NOT EXISTS idx_{table}_owner ON {table}(user_id,project_id)")
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS project_fts USING fts5(id UNINDEXED,user_id UNINDEXED,content)")
            db.execute("CREATE TABLE IF NOT EXISTS deliveries(user_id TEXT,key TEXT,request_hash TEXT,task_id TEXT,artifact_id TEXT,result TEXT,PRIMARY KEY(user_id,key),UNIQUE(user_id,task_id))")
            db.execute("CREATE TABLE IF NOT EXISTS task_locks(user_id TEXT,task_id TEXT,owner TEXT,started REAL,PRIMARY KEY(user_id,task_id))")
            db.execute("CREATE TABLE IF NOT EXISTS execution_claims(user_id TEXT,key TEXT,request_hash TEXT,owner TEXT,started REAL,PRIMARY KEY(user_id,key))")
            db.execute("CREATE TABLE IF NOT EXISTS chat_locks(user_id TEXT,conversation_id TEXT,owner TEXT,started REAL,PRIMARY KEY(user_id,conversation_id))")
            db.execute("CREATE TABLE IF NOT EXISTS cost_ledger(id TEXT PRIMARY KEY,reserved REAL NOT NULL,actual REAL,status TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS budget_windows(id TEXT PRIMARY KEY,starting_spend REAL NOT NULL,extra_limit REAL NOT NULL,ceiling REAL NOT NULL,active INTEGER NOT NULL)")
            db.execute("CREATE UNIQUE INDEX IF NOT EXISTS one_active_budget_window ON budget_windows(active) WHERE active=1")

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=15)
        db.row_factory=sqlite3.Row
        try:
            with db: yield db
        finally: db.close()

    def put(self,table,record,db=None):
        if table not in TABLES: raise ValueError("Table not permitted")
        if hasattr(record,"model_dump"): record=record.model_dump(mode="json")
        args=(record["id"],record["user_id"],record.get("project_id",""),json.dumps(record,ensure_ascii=False))
        sql=f"INSERT INTO {table} VALUES (?,?,?,?) ON CONFLICT(user_id,id) DO UPDATE SET project_id=excluded.project_id,data=excluded.data"
        if db is not None: db.execute(sql,args)
        else:
            with self.connect() as conn: conn.execute(sql,args)

    def rows(self,table,user_id,project_id=None):
        if table not in TABLES: raise ValueError("Table not permitted")
        sql=f"SELECT data FROM {table} WHERE user_id=?"
        args=[user_id]
        if project_id is not None: sql+=" AND project_id=?"; args.append(project_id)
        with self.connect() as db:
            return [json.loads(r[0]) for r in db.execute(sql+" ORDER BY id",args)]

    def get(self,table,id,user_id):
        if table not in TABLES: raise ValueError("Table not permitted")
        with self.connect() as db:
            row=db.execute(f"SELECT data FROM {table} WHERE id=? AND user_id=?",(id,user_id)).fetchone()
        return json.loads(row[0]) if row else None

    def projects(self,user_id): return self.rows("projects",user_id)
    def facts(self,pid,user_id,current=True):
        rows=self.rows("facts",user_id,pid)
        return [f for f in rows if not f.get("superseded")] if current else rows

    def reindex(self,user_id,db=None):
        def update(conn):
            projects=[json.loads(r[0]) for r in conn.execute('SELECT data FROM projects WHERE user_id=?',(user_id,))]
            facts={}
            for row in conn.execute('SELECT data FROM facts WHERE user_id=?',(user_id,)):
                fact=json.loads(row[0])
                if not fact.get('superseded'):facts.setdefault(fact['project_id'],[]).append(fact['content'])
            conn.execute('DELETE FROM project_fts WHERE user_id=?',(user_id,))
            for p in projects:
                content=' '.join([p['name'],p['topic'],p['description']]+facts.get(p['id'],[]))
                conn.execute('INSERT INTO project_fts VALUES (?,?,?)',(p['id'],user_id,' '.join(terms(content))))
        if db is not None:update(db)
        else:
            with self.connect() as conn:update(conn)

    def search(self,user_id,query,limit=50):
        tokens=terms(query)
        if not tokens: return []
        expression=" OR ".join('"'+t.replace('"','""')+'"' for t in tokens[:40])
        with self.connect() as db:
            rows=db.execute("SELECT p.data FROM project_fts f JOIN projects p ON p.id=f.id AND p.user_id=f.user_id WHERE project_fts MATCH ? AND p.user_id=? ORDER BY bm25(project_fts) LIMIT ?",(expression,user_id,limit)).fetchall()
        return [json.loads(r[0]) for r in rows]

    def spend(self):
        with self.connect() as db:
            rows=db.execute("SELECT reserved,actual,status FROM cost_ledger").fetchall()
        return {"settled":sum(r["actual"] or 0 for r in rows),
                "committed":sum(r["actual"] if r["actual"] is not None else r["reserved"] for r in rows),
                "unsettled":sum(r["reserved"] for r in rows if r["actual"] is None)}

    def start_budget_window(self, id, extra_limit=3):
        """Persistent extra-spend ceiling; repeated activation never resets it."""
        if not isinstance(id,str) or not id or not math.isfinite(extra_limit) or not 0<extra_limit<=3:
            raise ValueError('INVALID_BUDGET_WINDOW')
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing=db.execute('SELECT * FROM budget_windows WHERE id=?',(id,)).fetchone()
            if existing:
                if existing['extra_limit']!=extra_limit:raise ValueError('BUDGET_WINDOW_PARAMETERS_CHANGED')
                return dict(existing)
            if db.execute('SELECT id FROM budget_windows WHERE active=1').fetchone():raise ValueError('ANOTHER_BUDGET_WINDOW_IS_ACTIVE')
            spent=db.execute('SELECT COALESCE(SUM(CASE WHEN actual IS NULL THEN reserved ELSE actual END),0) FROM cost_ledger').fetchone()[0]
            db.execute('INSERT INTO budget_windows VALUES (?,?,?,?,1)',(id,spent,extra_limit,spent+extra_limit))
            return dict(db.execute('SELECT * FROM budget_windows WHERE id=?',(id,)).fetchone())
