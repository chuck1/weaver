import elephant.local_

class Query(elephant.local_.File):
    def __init__(self, e, d):
        super().__init__(e, d)
        self.d["_collection"] = "weaver recipes queries"

class Engine(elephant.local_.Engine):
    async def _factory(self, d):
        return Query(self, d)

