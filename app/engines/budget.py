import json
import os
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def tokenizer():
    try:
        import tiktoken
        cache=Path(__file__).resolve().parents[2]/"data/runtime/tokenizer"
        cache.mkdir(parents=True,exist_ok=True)
        os.environ.setdefault("TIKTOKEN_CACHE_DIR",str(cache))
        return tiktoken.get_encoding("cl100k_base")
    except Exception:
        return None

def tokens(value):
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,separators=(",",":"))
    encoding=tokenizer()
    return len(encoding.encode(text,disallowed_special=())) if encoding else len(text.encode())

def token_method():
    return "cl100k_base estimate; actual provider usage separate" if tokenizer() else "conservative UTF-8 byte upper bound"

def allocate(parts,budget,output=384,margin=128):
    counts={name:tokens(text) for name,text in parts.items()}
    counts.update(output_reserve=output,safety_margin=margin)
    counts["total"]=sum(counts.values())
    return counts,counts["total"]<=budget
