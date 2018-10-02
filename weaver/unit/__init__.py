
import elephant.global_
import elephant.local_.doc
import weaver.engine

class Unit(elephant.global_.File):
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d["_collection"] = "weaver units"

class Query(elephant.local_.doc.Doc):
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d["_collection"] = "weaver units queries"

class EngineQuery(weaver.engine.EngineLocal):
    def __init__(self, manager, coll):
        super().__init__(manager, coll)
        self._doc_class = Query

class Engine(weaver.engine.EngineGlobal):

    def __init__(self, manager, coll):
        super().__init__(manager, coll, "weaver units", EngineQuery(manager, coll.queries))
        self._doc_class = Unit


