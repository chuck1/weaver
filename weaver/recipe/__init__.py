import logging

import elephant.local_

logger = logging.getLogger(__name__)

class Recipe(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)

    async def update_temp_material(self, user, material):
        if not material: return material
        if '_design' in material: return material
        if 'design' not in material: return material
        if 'id' not in material['design']:
            logger.warning(f'invalid material: {material!r}')
            return material

        ref = material['design']['ref']

        d = await self.e.h.weaver.e_designs.find_one(user, ref, {'_id': material['design']['id']})

        material['_design'] = await d.to_array()

        return material

    async def update_temp(self, user):
        
        if 'materials' in self.d:
            self.d['materials'] = [await self.update_temp_material(user, m) for m in self.d['materials']]
       

    def quantity(self, d):
        
        for m in self.d['materials']:
            if m['design'] == d.freeze():
                return m['quantity']

        raise Exception('design not found in materials of recipe')
 
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

        yield {"$unwind": {
                "path": "$materials",
                "preserveNullAndEmptyArrays": True,
                }}
        #yield {"$match": {"materials": {"$ne": None}}}
        yield {"$lookup": {
                "from": "weaver.designs.files", 
                "let": {"material_id": "$materials.design.id"}, 
                "pipeline": [{"$match": {"$expr": {"$eq": ["$_id", "$$material_id"]}}}], 
                "as": "materials._design",
                }}
        yield {"$addFields": {"materials._design": {"$arrayElemAt": ["$materials._design", 0]}}}
        yield {"$group": {
                "_id": "$_id",
                "materials": {"$push": "$materials"},
                "tags":  {"$first": "$tags"},
                "steps": {"$first": "$steps"}
                }}

    def _factory(self, d):
        return Recipe(self.manager, self, d)


