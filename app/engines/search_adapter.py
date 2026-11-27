"""Replaceable retrieval adapter. P0 measures FTS, never labels it embeddings."""
class FTSSearch:
    mode='FTS5_FALLBACK_NO_EMBEDDINGS'
    def __init__(self,store):self.store=store
    def search(self,user,query,limit=50):return self.store.search(user,query,limit)
