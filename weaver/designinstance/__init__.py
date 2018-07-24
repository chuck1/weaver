
import elephant.local_

class DesignInstance(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)
        self.manager = manager

    async def update_temp(self, user):
        pass        
        
    async def quantity(self, user):
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        if 'quantity' in self.d:
            return self.d['quantity']

        ri = await self.get_recipeinstance_for(user)

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

    async def get_design(self, user):
        if 'design' not in self.d: return

        d0 = await self.manager.e_designs.find_one(
                user,
                self.d['design']['ref'],
                {"_id": self.d['design']['id']})

        assert d0 is not None
  
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
        #yield {'$project': {
        #        '_design': {'$arrayElemAt': ['$_design', 0]},
        #        }}

    def _factory(self, d):
        return DesignInstance(self.manager, self, d)


