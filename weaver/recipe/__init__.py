
import elephant.local_

class Recipe(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)

    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipes"
        return d

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self):
        
        # materials

        yield {"$unwind": "$materials"}
        yield {"$match": {"materials": {"$ne": None}}}
        yield {"$lookup": {
                "from": "weaver.designs.files", 
                "let": {"material_id": "$materials.part.id"}, 
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$material_id"]}}}], 
                "as": "materials._design",
                }}
        yield {"$addFields": {"materials._design": {"$arrayElemAt": ["$materials._design", 0]}}}
        yield {"$group": {
                "_id": "$_id",
                "materials": {"$push": "$materials"},
                }}



    def _factory(self, d):
        return Recipe(self.manager, self, d)


