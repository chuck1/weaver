import elephant.local_
import elephant.global_

class EngineLocal(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries=None):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    async def _factory(self, d):
        return self._doc_class(self, await self.manager.h.decode(d), d)

class EngineGlobal(elephant.global_.Engine):
    def __init__(self, manager, coll, ref, e_queries=None):
        super().__init__(coll, ref, e_queries)
        self.manager = manager
        self.h = manager.h

    async def _factory(self, d):
        return self._doc_class(self, await self.manager.h.decode(d), d)



