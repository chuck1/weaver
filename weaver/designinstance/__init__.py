import enum
import logging
import pprint
import pymongo
import elephant.local_
import weaver.recipeinstance

logger = logging.getLogger(__name__)

class DesignInstanceMode(enum.Enum):
    # created to represent actual inventory
    INVENTORY      = 0
    # created as ingredient for recipeinstance
    RECIPEINSTANCE = 1
    # created to create demand without a recipeinstance or an on-hand quantity
    DEMAND         = 2

class DesignInstance(elephant.global_.File):
    """
    types identified by fields present

    'design'             - reference to the design
    'recipeinstance_for' - this was created as one of the materials for a recipeinstance
    'quantity'           - this was created manually to originate demand
    'recipeinstance'     - a recipeinstance created to produce this
    'quantity_actual'    - actual quantity in inventory
    """
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d['_collection'] = 'weaver designinstances'

    def behavior(self):
        pass

    async def check_0(self):
        DesignInstanceMode(self.d["mode"])

    async def update_temp(self, user):
        await super().update_temp(user)
        
    async def quantity_demand(self, user):
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        d  = await self.get_design(user)
        u0 = d.d.get("unit", None)
        assert (u0 is None) or isinstance(u0, weaver.quantity.unit.BaseUnit)

        if 'quantity' in self.d:
            # type 0
            logger.debug(f'DI demand type 0. q = {self.d["quantity"]}')

            q = weaver.quantity.Quantity(self.d['quantity'])
            q = q * (await d.conversion(q.unit, u0))

            print("assert equal")
            print(u0)
            print(q.unit)

            assert weaver.quantity.unit.unit_eq(u0, q.unit)
            return q

        # type 1
        ri = await self.get_recipeinstance_for(user)

        if not (await ri.is_planned(user)):
            logger.debug('DI demand type 1 not planned')
            print('DI demand type 1 not planned')
            return 0

        r  = await ri.get_recipe(user)


        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

        u1 = q.unit

        pprint.pprint(d.d)

        print("u0", u0)
        print("u1", u1)

        assert (u1 is None) or isinstance(u1, weaver.quantity.unit.BaseUnit)

        assert weaver.quantity.unit.unit_eq(u0, u1)

        return q        

    async def cost(self, user):

        if 'recipeinstance' in self.d:
            ri = await self.get_recipeinstance(user)
            return await ri.cost(user)

        d = await self.get_design(user)

        if "cost" in d.d:
            return d.d["cost"]

        return 0

    async def quantity_inventory(self, user):
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        if 'quantity' in self.d:
            # type 0
            return 0

        # type 1
        ri = await self.get_recipeinstance_for(user)

        if ri.d.get('status', None) != weaver.recipeinstance.Status.COMPLETE:
            return 0

        r  = await ri.get_recipe(user)

        d  = await self.get_design(user)

        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

        return q        

    async def get_recipeinstance_for(self, user):
        if 'recipeinstance_for' not in self.d: return

        d0 = await self.e.manager.e_recipeinstances.find_one(
                user,
                {"_id": self.d['recipeinstance_for']})

        assert d0 is not None
  
        return d0

    async def get_recipeinstance(self, user):
        if 'recipeinstance' not in self.d: return

        d0 = await self.e.manager.e_recipeinstances.find_one(
                user,
                {"_id": self.d['recipeinstance']})

        assert d0 is not None
  
        return d0

    async def get_design(self, user):
        if 'design' not in self.d: return

        logger.debug((
                f'designinstance get design '
                f'{str(self.d["design"]["id"])[-4:]} '
                f'{str(self.d["design"]["ref"])[-4:]} '
                ))

        d0 = await self.e.manager.e_designs.find_one(
                user,
                self.d['design']['ref'],
                {"_id": self.d['design']['id']})

        assert d0 is not None

        assert \
                d0.d["_elephant"]["ref"] == self.d['design']['ref'] or \
                d0.d["_elephant"]["refs"][d0.d["_elephant"]["ref"]] == self.d['design']['ref']
 
        return d0

    async def to_array(self):
        d = dict(self.d)
        return d

class Engine(weaver.engine.EngineGlobal):
    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, "master", e_queries)
        self._doc_class = DesignInstance

    async def counter(self, name):
        counter = self.manager.h.db.counters.find_one_and_update(
            {'name': name},
            {'$inc': {'count': 1}},
            upsert=True,
            return_document=pymongo.ReturnDocument.BEFORE,
            )

    async def next_id(self):
        return await self.counter('designinstane_id')

    async def pre_put_new(self, d_0):
        d_0['id_1'] = await self.next_id()
        return d_0

    def pipe0(self, user):

        yield from super().pipe0(user)

        # design
        yield {'$addFields': {'design_id': '$design.id'}}
        yield {'$lookup': {
                'from': 'weaver.designs.files',
                'let': {'design_id': '$design_id'},
                'pipeline': [
                    {'$match': {'$expr': {'$eq': ['$_id', '$$design_id']}}},
                    ],
                'as': '_design',
                }}
        yield {'$addFields': {
                '_design': {'$arrayElemAt': ['$_design', 0]},
                }}



