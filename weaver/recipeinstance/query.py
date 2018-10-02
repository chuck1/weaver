import elephant.local_
import weaver.engine

class Query(elephant.local_.doc.Query):
    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipeinstances queries"
        return d

class Engine(weaver.engine.EngineLocal):
    def __init__(self, manager, coll):
        super().__init__(manager, coll)
        self._doc_class = Query


