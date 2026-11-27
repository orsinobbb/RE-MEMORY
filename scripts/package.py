"""Positive-list source archive. Never bundles keys, state, backups or private UI."""
from pathlib import Path
import zipfile,hashlib,json
from dotenv import dotenv_values
root=Path(__file__).resolve().parents[1]
folders={'app','frontend','tests','benchmarks','docs','submission','scripts','.kiro','reports'}
files={'SECURITY.md','AGENTS.md','README.md','DEPLOYMENT.md','.env.example','.gitignore','pyproject.toml','uv.lock','start_mac.sh','start_windows.bat'}
excluded={'__pycache__','.pytest_cache','.ruff_cache','private','runtime','backups','.venv','dist'}
env=dotenv_values(root/'.env');secrets=[env.get(k) for k in ('MIXROUTE_API_KEY','MIXROUTE_SMART_API_KEY') if env.get(k)]
paths=[]
for p in sorted(root.rglob('*')):
    rel=p.relative_to(root)
    if not p.is_file() or p.is_symlink() or excluded.intersection(rel.parts):continue
    if rel.parts[0] not in folders and str(rel) not in files:continue
    if p.name.startswith('.env') and p.name!='.env.example':continue
    data=p.read_bytes()
    if any(secret.encode() in data for secret in secrets):raise SystemExit('Credential detected; archive refused')
    paths.append((rel,data,p.stat().st_mode))
directory=root/'dist';directory.mkdir(exist_ok=True);target=directory/'RE-MEMORY-source.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for rel,data,mode in paths:
        info=zipfile.ZipInfo('RE-MEMORY/'+str(rel));info.external_attr=(mode&0xffff)<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,data)
digest=hashlib.sha256(target.read_bytes()).hexdigest();(directory/'SHA256SUMS').write_text(digest+'  '+target.name+'\n')
print(json.dumps({'path':str(target),'files':len(paths),'bytes':target.stat().st_size,'sha256':digest,'credential_scan':'PASS'}))
