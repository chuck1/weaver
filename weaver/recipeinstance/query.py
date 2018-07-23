import elephant.local_

class Query(elephant.local_.File):
    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipeinstances queries"
        return d

class Engine(elephant.local_.Engine):
    def _factory(self, d):
        return Query(self, d)

