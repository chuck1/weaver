import logging

import elephant.local_
import weaver.recipeinstance

logger = logging.getLogger(__name__)

class DesignInstance(elephant.local_.File):
    """
    types identified by fields present

    'recipeinstance_for' - this was created as one of the materials for a recipeinstance
    'quantity'           - this was created manually to originate demand
    'recipeinstance'     - a recipeinstance created to produce this
    """
    def __init__(self, manager, e, d):
        super().__init__(e, d)
        self.manager = manager

    async def update_temp(self, user):
        await super().update_temp(user)
        
    async def quantity_demand(self, user):
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        if 'quantity' in self.d:
            # type 0
            logger.debug('DI demand type 0')
            return self.d['quantity']

        # type 1
        ri = await self.get_recipeinstance_for(user)

        if not (await ri.is_planned(user)):
            logger.debug('DI demand type 1 not planned')
            return 0

        r  = await ri.get_recipe(user)

        d  = await self.get_design(user)

        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

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

        d0 = await self.manager.e_recipeinstances.find_one(
                user,
                "master",
                {"_id": self.d['recipeinstance_for']})

        assert d0 is not None
  
        return d0

    async def get_recipeinstance(self, user):
        if 'recipeinstance' not in self.d: return

        d0 = await self.manager.e_recipeinstances.find_one(
                user,
                "master",
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

        d0 = await self.manager.e_designs.find_one(
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
        d["_collection"] = "weaver designinstances"
        return d

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self):

        yield from super().pipe0()

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

    def _factory(self, d):
        return DesignInstance(self.manager, self, d)


