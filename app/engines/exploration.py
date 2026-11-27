from dataclasses import dataclass,field

@dataclass
class SearchState:
    budget:int
    searched:set=field(default_factory=set)
    read_versions:set=field(default_factory=set)
    clues:list=field(default_factory=list)
    rounds:list=field(default_factory=list)
    spent:int=0

    def observe(self,version,content_tokens):
        if version in self.read_versions:return 0
        self.read_versions.add(version);self.spent+=content_tokens
        return content_tokens

def next_clues(aliases,candidate_ids):
    return list(dict.fromkeys(a["alias"] for a in aliases if a["project_id"] in candidate_ids and a["status"]=="CONFIRMED"))[:12]

def sufficient(candidates,explicit=False):
    if not candidates:return False
    margin=candidates[0]["score"]-(candidates[1]["score"] if len(candidates)>1 else 0)
    return explicit or (candidates[0]["score"]>=.72 and margin>=.12)
