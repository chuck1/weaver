
import elephant.local_

class RecipeInstance(elephant.local_.File):
    def __init__(self, manager, e, d):
        super().__init__(e, d)

    async def update_temp(self, user):
        pass        
        
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


