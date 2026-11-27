def matching_aliases(aliases,query):
    folded=query.casefold()
    return [a for a in aliases if a["status"] in ("CANDIDATE","CONFIRMED") and a["alias"].casefold() in folded]

def confirmed_target(aliases,query):
    ids={a["project_id"] for a in matching_aliases(aliases,query) if a["status"]=="CONFIRMED"}
    return next(iter(ids)) if len(ids)==1 else None

def alias_evidence(aliases,query,pid):
    found=[a for a in matching_aliases(aliases,query) if a["project_id"]==pid]
    score=max((a["strength"]*(1 if a["status"]=="CONFIRMED" else .6) for a in found),default=0)
    return score,found
