import enum
import logging

import elephant.local_

logger = logging.getLogger(__name__)

class Status(enum.Enum):
    PLANNED = 0
    COMPLETE = 1

class RecipeInstance(elephant.global_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)
        self.manager = manager

    async def update_temp(self, user):

        if "_temp" not in self.d: self.d["_temp"] = {}

        if "cost" not in self.d["_temp"]:
            self.d["_temp"]["cost"] = await self.cost(user)
      
        
    def freeze(self):
        """
        this does not return ref because it does not make
        sense for multiple versions of this to coexist
        in fact, this could be converted to global
        """
        return self.d['_id']

    def valid(self):
        assert 'status' in self.d
        Status(self.d['status'])

    async def get_recipe(self, user):

        logger.debug((
                f'recipeinstance get recipe '
                f'{str(self.d["recipe"]["id"])[-4:]} '
                f'{str(self.d["recipe"]["ref"])[-4:]}'))

        d2 = await self.manager.e_recipes.find_one(
                user,
                self.d['recipe']['ref'],
                {'_id': self.d['recipe']['id']},
                )

        #logger.debug(f'recipe {d2.d["_elephant"]!r}')

        return d2

    async def get_designinstance(self, user):
        """
        get the designinstance that this was created to produce
        """
        d3 = await self.manager.e_designinstances.find_one(
                user,
               	{'_id': self.d['designinstance']})
        
        return d3

    async def is_planned(self, user):
        di = await self.get_designinstance(user)
        if di:
            if di.d.get('recipeinstance', None) == self.d['_id']:
                return True
            else:
                logger.debug('RI type 1 reference doesnt match {0} != {1}'.format(
                        di.d.get('recipeinstance', None),
                        self.d['_id'],
                        ))
                return False
        
        if self.d['status'] == weaver.recipeinstance.Status.PLANNED:
            return True

        return False

    async def get_designinstances(self, user):

        d2 = await self.get_recipe(user)

        print(f'    recipeinstance: {self!r}')
        print(f'    recipe:         {d2!r}')

        for m in d2.d['materials']:
            print(f'      {m["design"]!r}')

            d3 = await self.manager.e_designinstances.find_one(
                    user,
                    {
                        'design': m['design'],
                        'recipeinstance_for': self.freeze(),
                    },
                    )

            if d3 is None:
                print('creating missing designinstance!!!')

                d3 = await self.manager.e_designinstances.put(
                        user,
                        None,
                        {
                            'design': m['design'],
                            'recipeinstance_for': self.freeze(),
                        })

            yield d3

    async def quantity(self, user):
        
        r = await self.get_recipe(user)
   
        di = await self.get_designinstance(user)

        d = await di.get_design(user)

        q0 = await di.quantity_demand(user)

        q1 = r.quantity(d)
  
        return -q0 / q1
        

    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipeinstances"
        return d

    async def cost(self, user):
        
        #recipe = await self.get_recipe(user)

        #for m in recipe.d["materials"]:

        c = 0

        async for di in self.get_designinstances(user):

            c += await di.cost(user)
            
            #if m["quantity"]["num"] < 0: continue

        return c

class Engine(elephant.global_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, "master", e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self):

        yield from super().pipe0()

        # recipe
        yield {"$addFields": {"recipe_id": "$recipe.id"}}
       
        yield {"$lookup": {
                "from": "weaver.recipes.files",
                "let": {"recipe_id1": "$recipe_id"},
                "pipeline": [
                    {"$match": {"$expr": {"$eq": ["$_id","$$recipe_id1"]}}}],
                "as": "_recipe"
                }}

        yield {'$project': {
                '_recipe': {'$arrayElemAt': ['$_recipe', 0]},
                'recipe': 1,
                }}

    def _factory(self, d):
        return RecipeInstance(self.manager, self, d)











