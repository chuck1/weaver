
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

        yield {"$addFields": {"_material": "$materials"}}
        yield {"$unwind": "$_material"}
        yield {"$match": {"_material": {"$ne": None}}}
        yield {"$lookup": {
                "from": "weaver.designs.files", 
                "let": {"material_id": "$_material.part._id"}, 
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$material_id"]}}}], 
                "as": "_material.design",
                }}
        yield {"$addFields": {"_material.design": {"$arrayElemAt": ["$_material.design", 0]}}}
        yield {"$group": {
                "_id": "$_id",
                "_materials": {"$push": "$_material"},
                "materials": {"$first": "$materials"},
                }}



    def _factory(self, d):
        return Recipe(self.manager, self, d)


