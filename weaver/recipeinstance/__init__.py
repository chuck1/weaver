
import elephant.local_

class RecipeInstance(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)
        self.manager = manager

    async def update_temp(self, user):
        pass        
        
    def freeze(self):
        """
        this does not return ref because it does not make
        sense for multiple versions of this to coexist
        in fact, this could be converted to global
        """
        return self.d['_id']

    async def get_recipe(self, user):

        d2 = await self.manager.e_recipes.find_one(
                user,
                self.d['recipe']['ref'],
                {'_id': self.d['recipe']['id']},
                )

        return d2

    async def get_designinstance(self, user):
        """
        get the designinstance that this was created to produce
        """
        d3 = await self.manager.e_designinstances.find_one(
                user,
                "master",
               	{'_id': self.d['designinstance']['id']})
        
        return d3

    async def get_designinstances(self, user):

        d2 = await self.get_recipe(user)

        print(f'    recipeinstance: {self!r}')
        print(f'    recipe:         {d2!r}')

        for m in d2.d['materials']:
            print(f'      {m["part"]!r}')

            d3 = await self.manager.e_designinstances.find_one(
                    user,
                    "master",
                    {
                        'design': m['part'],
                        'recipeinstance_for': self.freeze(),
                    },
                    )

            if d3 is None:
                print('creating missing designinstance!!!')

                d3 = await self.manager.e_designinstances.put(
                        user,
                        "master",
                        None,
                        {
                            'design': m['part'],
                            'recipeinstance_for': self.freeze(),
                        })

            yield d3

    async def quantity(self, user):
        
        r = await self.get_recipe(user)
   
        di = await self.get_designinstance(user)

        d = await di.get_design(user)

        q0 = await di.quantity(user)

        q1 = r.quantity(d)
  
        return -q0 / q1
        

    async def to_array(self):
        d = dict(self.d)
        d["_collection"] = "weaver recipeinstances"
        return d

class Engine(elephant.local_.Engine):
    def __init__(self, manager, coll, e_queries):
        super().__init__(coll, e_queries)
        self.manager = manager
        self.h = manager.h

    def pipe0(self):
        # recipe
        yield {'$lookup': {
                'from': 'weaver recipes',
                'let': {'recipe_id': '$recipe'},
                'pipeline': [
                    {'$match': {'_id': '$$recipe_id'}},
                    ],
                'as': '_recipe',
                }}
        yield {'$project': {
                '_recipe': {'$arrayElemAt': ['$_recipe', 0]},
                }}

    def _factory(self, d):
        return RecipeInstance(self.manager, self, d)


