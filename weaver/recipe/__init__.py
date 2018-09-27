import copy
import logging

import elephant.local_

import weaver.engine
import weaver.quantity

logger = logging.getLogger(__name__)

class Recipe(elephant.local_.File):
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d["_collection"] = "weaver recipes"

    async def update_temp_material(self, user, material):
        if not material: return material

        assert isinstance(material, weaver.material.Material)

        if 'id' not in material.design:
            logger.warning(f'invalid material: {material!r}')
            return material

        ref = material.design['ref']

        d = await self.e.h.weaver.e_designs.find_one(user, ref, {'_id': material.design['id']})

        m = weaver.material.Material(d, material.quantity)

        return m

    async def temp_materials(self, user):

        for m in self.d['materials']:

            yield await self.update_temp_material(user, m)

    async def check(self):
        for m in self.d.get('materials', []):
            assert isinstance(m, weaver.material.Material)
            #if 'quantity' not in m:
            #    m['quantity'] = weaver.quantity.Quantity(0)
            #else:
            #    if not ((m['quantity'] is None) or isinstance(m['quantity'], weaver.quantity.Quantity)):
            #        raise Exception(f'quantity should be Quantity object, not {type(m["quantity"])} {m["quantity"]}')

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
            if m.design == d.freeze():

                q = m.quantity

                #if not weaver.quantity.unit_eq(q.unit, d.d.get("unit")):
                #    await d.conversion(q.unit, d.d.get("unit"))

                return q

        raise Exception('design not found in materials of recipe')

        for m in self.d.get("materials", []):
            logger.error(f'm: {m["design"]}')
            logger.error(f'd: {d.freeze()}')

        self.print_materials(logger.error)
        logger.error(f'design: {d.d!r}')

    async def _cost(self, user, q0, materials, c):

        try:
            m = next(materials)
            while m.quantity.num < 0:
                m = next(materials)
        except StopIteration:
            yield c
            return

        d = await self.e.h.weaver.e_designs.find_one(user, m.design["ref"], {"_id": m.design["id"]})

        q1 = self.quantity(d)

        q2 = q0 * q1

        async for c1 in d.cost(user, q2):
            
            async for _ in self._cost(user, q0, materials, c + c1): yield _

    async def cost(self, user, q0):

        q0 = q0 if isinstance(q0, weaver.quantity.Quantity) else weaver.quantity.Quantity(q0)

        assert weaver.quantity.unit_eq(q0.unit, None)

        materials = iter(self.d.get("materials", []))
 
        async for c in self._cost(user, q0, materials, 0): yield c


class Engine(weaver.engine.EngineLocal):

    _doc_class = Recipe

    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, e_queries)

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


