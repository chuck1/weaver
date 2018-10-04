import elephant.local_
import weaver.engine

class Query(elephant.local_.doc.Query):
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d["_collection"] = "weaver recipeinstances queries"

class Engine(weaver.engine.EngineLocal):
    def __init__(self, manager, coll):
        super().__init__(manager, coll)
        self._doc_class = Query


