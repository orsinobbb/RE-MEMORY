from .semantic_dictionary import confirmed_target
import re
from app.storage.database import terms

GENERIC={'音樂','專案','工作','昨天','今天','繼續','接續','我要','資料','研究','系統','工具'}

def specific_terms(text):
    for word in sorted(GENERIC,key=len,reverse=True):text=text.replace(word,' ')
    return set(terms(text))

def explicit_target(projects,aliases,query):
    identifiers=re.findall(r'(?<![a-z0-9_-])project-[a-z0-9_-]+',query.casefold())
    if any(x not in {p['id'].casefold() for p in projects} for x in identifiers):return None,'UNKNOWN_PROJECT_ID'
    exact=[p["id"] for p in projects if re.search(r'(?<![a-z0-9_-])'+re.escape(p['id'].casefold())+r'(?![a-z0-9_-])',query.casefold()) or p["name"].casefold() in query.casefold()]
    if len(exact)>1:return None,'MULTIPLE_EXPLICIT_PROJECTS'
    if len(exact)==1:return exact[0],"EXPLICIT_PROJECT"
    alias=confirmed_target(aliases,query)
    query_terms=specific_terms(query)
    owners={}
    for project in projects:
        for term in specific_terms(project['name']+' '+project.get('description','')):
            owners.setdefault(term,set()).add(project['id'])
    targets=set().union(*(owners[t] for t in query_terms if len(owners.get(t,set()))==1)) if query_terms else set()
    if alias:targets.add(alias)
    if len(targets)>1:return None,'CONTRADICTORY_PROJECT_CUES'
    if len(targets)==1 and not alias:return next(iter(targets)),'UNIQUE_CANONICAL_CONTENT_CUE'
    return alias,"CONFIRMED_ALIAS" if alias else None
