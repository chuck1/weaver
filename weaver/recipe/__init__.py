import logging

import elephant.local_

import weaver.quantity

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

        m = dict(material)

        m['design'] = d

        if "quantity" in m:
            if not isinstance(m['quantity'], weaver.quantity.Quantity):
                m['quantity'] = weaver.quantity.Quantity(m['quantity'])

        return m


    async def temp_materials(self, user):

        for m in self.d['materials']:

            yield await self.update_temp_material(user, m)

    async def check(self):
        for m in self.d.get('materials', []):
            if 'quantity' not in m:
                m['quantity'] = weaver.quantity.Quantity(0)

    async def update_temp(self, user):
        
        await super().update_temp(user)

        if 'materials' in self.d:
            self.d['_temp']['materials'] = [_ async for _ in self.temp_materials(user)]
       
    def print_materials(self, p):
        p(f'recipe materials:')
        for m in self.d.get("materials", []):
            if '_design' in m:
                p('  ' + m['_design'].get('description',''))
            else:
                p('  ' + repr(m))

    async def temp(self, user):
        if "_temp" not in self.d: await self.update_temp(user)
        return self.d["_temp"]

    async def list_upstream(self, user, query=None):
        for m in (await self.temp(user)).get("materials", []):
            if "quantity" in m:
                if m["quantity"].num < 0:
                    logger.info(f'upstream: skip material {m["design"]!r} with quantity {m["quantity"]!r}')
                    continue
            yield m["design"]

    async def list_downstream(self, user, query=None):
        for m in (await self.temp(user)).get("materials", []):
            if m["quantity"].num > 0: continue
            yield m["design"]

    def quantity(self, d):
        
        logger.debug((
                f'recipe get quantity for design '
                f'{str(d.d["_id"])[-4:]} '
                f'{str(d.d["_elephant"]["ref"])[-4:]}'))

        for m in self.d['materials']:
            if m['design'] == d.freeze():
                  
                if 'quantity' not in m:
                    return weaver.quantity.Quantity(0)
 
                return weaver.quantity.Quantity(m['quantity'])

        raise Exception('design not found in materials of recipe')

        for m in self.d.get("materials", []):
            logger.error(f'm: {m["design"]}')
            logger.error(f'd: {d.freeze()}')

        self.print_materials(logger.error)
        logger.error(f'design: {d.d!r}')
 
    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipes"

        async def _(l):
            for m in l:
                m["design"] = await m["design"].to_array()
                if "quantity" in m:
                    m["quantity"] = await m["quantity"].to_array()
                yield m

        if "materials" in d.get("_temp", {}):
            d["_temp"]["materials"] = [i async for i in _(d["_temp"]["materials"])]

        return d

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self, user):

        yield from super().pipe0(user)
        
        # tags
        yield {'$lookup': {
                'from': 'tags.files',
                'let': {"tags0": "$tags"},
                'pipeline': [
                    {"$match": {"$expr": 
                        {"$in": ["$_id", {"$ifNull": ["$$tags0",[]]}]}}},
                    ],
                'as': '_tags',
                }}

        return

        # materials
        yield {"$unwind": {
                "path": "$materials",
                "preserveNullAndEmptyArrays": True,
                }}
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
                "_tags":  {"$first": "$_tags"},
                "steps": {"$first": "$steps"}
                }}


    async def _factory(self, d):
        return Recipe(self.manager, self, d)


