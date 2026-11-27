import hashlib,re

def validate(content,context):
    if not isinstance(content,str) or not content.strip():return False,"EMPTY_ARTIFACT"
    if len(content)>20000:return False,"ARTIFACT_TOO_LARGE"
    for heading in ("目標","限制","下一步"):
        if not re.search(r'^#{1,3}\s+'+heading+r'\s*$',content,re.MULTILINE):return False,"MISSING_HEADING:"+heading
    normalized="".join(content.split())
    for fact in context["loaded"]:
        if fact.get("kind")=="CONSTRAINT" and "".join(fact["content"].split()) not in normalized:
            return False,"CRITICAL_CONSTRAINT_OMITTED"
    for fact in context['loaded']:
        if fact.get('kind')=='GOAL' and ''.join(fact['content'].split()) not in normalized:return False,'CURRENT_GOAL_OMITTED'
    checks=re.findall(r'^- \[ \] .+$',content,re.MULTILINE)
    if len(checks)!=3:return False,'THREE_UNEXECUTED_ACCEPTANCE_CHECKS_REQUIRED'
    return True,hashlib.sha256(content.encode()).hexdigest()
