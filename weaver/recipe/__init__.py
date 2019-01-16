import copy
import functools
import itertools
import logging
import operator

import elephant.local_

import weaver.engine
import weaver.quantity

logger = logging.getLogger(__name__)

class MaterialsList:
    def __init__(self, materials=list()):
        self.materials = materials

    def __add__(self, other):
        if isinstance(other, weaver.material.Material):
            return MaterialsList(self.materials + [other])
        if isinstance(other, MaterialsList):
            return MaterialsList(self.materials + other.materials)
        raise TypeError(f'expected Material got {type(other)}')

    def group(self):
        keyfunc = lambda m: m.design_ref
        materials = list(sorted(self.materials, key=keyfunc))

        for k, g in itertools.groupby(materials, key=keyfunc):
            g = list(g)
            q = functools.reduce(operator.add, [m.quantity for m in g])
            yield weaver.material.Material(k, q)

class Recipe(elephant.local_.doc.Doc):
    def __init__(self, e, d, _d, is_subobject, ):
        super().__init__(e, d, _d, is_subobject, )
        self.d["_collection"] = "weaver recipes"

    async def temp_materials(self, user):
        for m in self.d['materials']:
            if not isinstance(m, weaver.material.Material):
                raise TypeError(f'expected Material got {type(m)} {m!r}')
            yield m

    async def check(self):
        for m in self.d.get('materials', []):
            if not isinstance(m, weaver.material.Material):
                raise TypeError(f'expected Material got {type(m)} {m!r}')

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
        # how much of design d does this recipe produce/consume
        
        logger.debug((
                f'recipe get quantity for design '
                f'{str(d.d["_id"])[-4:]} '
                f'{str(d.d["_elephant"]["ref"])[-4:]}'))

        for m in self.d['materials']:
            if m.design_ref == d.freeze():

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

        d = await self.e.h.weaver.e_designs.find_one_by_ref(user, m.design_ref)

        q1 = self.quantity(d)

        logger.info(f'recipe requires {q1} of {d.d["description"]}')

        q2 = q0 * q1

        async for c1 in d.cost(user, q2):
            
            async for _ in self._cost(user, q0, materials, c + c1):

                yield _

    async def cost(self, user, q0):

        q0 = q0 if isinstance(q0, weaver.quantity.Quantity) else weaver.quantity.Quantity(q0)

        assert weaver.quantity.unit.unit_eq(q0.unit, None)

        materials = iter(self.d.get("materials", []))
 
        async for c in self._cost(user, q0, materials, 0): yield c

    async def _materials_leaf(self, user, q0, materials, l):

        try:
            m = next(materials)
            while m.quantity.num < 0:
                m = next(materials)
        except StopIteration:
            yield l
            return

        d = await self.e.h.weaver.e_designs.find_one_by_ref(user, m.design_ref)

        q1 = self.quantity(d)

        logger.info(f'recipe requires {q1} of {d.d["description"]}')

        q2 = q0 * q1

        async for l_1 in d.materials_leaf(user, q2):
            async for l_2 in self._materials_leaf(user, q0, materials, l + l_1):
                yield l_2

    async def materials_leaf(self, user, q0):

        q0 = q0 if isinstance(q0, weaver.quantity.Quantity) else weaver.quantity.Quantity(q0)

        assert weaver.quantity.unit.unit_eq(q0.unit, None)

        materials = iter(self.d.get("materials", []))
 
        async for c in self._materials_leaf(user, q0, materials, MaterialsList()): yield c
           

class Engine(weaver.engine.EngineLocal):

    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, e_queries)
        self._doc_class = Recipe


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


