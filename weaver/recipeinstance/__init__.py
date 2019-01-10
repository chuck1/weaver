import enum
import logging
import bson
import elephant.global_.doc
import elephant.local_
import weaver.engine

logger = logging.getLogger(__name__)

class Status(enum.Enum):
    PLANNED  = 0
    COMPLETE = 1

class RecipeInstance(elephant.global_.doc.Doc):
    """
    recipe         - ref of recipe
    designinstance - id of designinstance that this was created to produce
    """
    def __init__(self, e, d, _d):
        super().__init__(e, d, _d)
        self.d["_collection"] = "weaver recipeinstances"

    async def check(self):
        await super().check()

    async def update_temp(self, user):
        await super().update_temp(user)

        self.d["_temp"]["cost"] = await self.cost(user)
        
    def valid(self):
        assert 'status' in self.d
        Status(self.d['status'])

    async def get_recipe(self, user):

        logger.debug((
                f'recipeinstance get recipe '
                f'{str(self.d["recipe"]._id)[-4:]} '
                f'{str(self.d["recipe"].ref)[-4:]}'))

        d2 = await self.e.manager.e_recipes.find_one(
                user,
                self.d['recipe'].ref,
                {'_id': self.d['recipe']._id},
                )

        #logger.debug(f'recipe {d2.d["_elephant"]!r}')

        assert isinstance(d2, weaver.recipe.Recipe)

        return d2

    async def get_designinstance(self, user):
        """
        get the designinstance that this was created to produce
        """

        if 'designinstance' not in self.d: return

        assert isinstance(self.d['designinstance'], elephant.ref.DocRef)

        d3 = await self.e.manager.e_designinstances.find_one_by_ref(
                user,
               	self.d['designinstance'],
                )
        
        return d3

    async def is_planned(self, user):
        di = await self.get_designinstance(user)
        if di:
            if di.d.get('recipeinstance', None) == self.freeze():
                return True
            else:
                logger.error('RI type 1 reference doesnt match {0} != {1}'.format(
                        di.d.get('recipeinstance', None),
                        self.d['_id'],
                        ))
                raise Exception()
                return False
        


        if Status(self.d['status']) == weaver.recipeinstance.Status.PLANNED:
            return True

        return False

    async def get_designinstances(self, user):

        d2 = await self.get_recipe(user)

        print(f'    recipeinstance: {self!r}')
        print(f'    recipe:         {d2!r}')

        for m in d2.d.get('materials', []):
            #logger.info(f'      {m.design!r}')

            q0 = {
                    'behavior.WeaverDesigninstanceBehaviorRecipeinstance.0': self.freeze(),
                    'design': m.design_ref,
                    }

            d3 = await self.e.manager.e_designinstances.find_one(user, q0)

            if d3 is None:
                logger.info('creating missing designinstance')

                d3 = await self.e.manager.e_designinstances.put(
                        user,
                        None,
                        {
                            'behavior': weaver.designinstance.doc.behavior.BehaviorRecipeinstance(self.freeze()),
                            'design': m.design_ref,
                        })
 
                if (await self.e.manager.e_designinstances.find_one(user, q0)) is None:
                    raise Exception()

            yield d3

    async def quantity(self, user):

        if "quantity" in self.d:
            return self.d["quantity"]
        
        r = await self.get_recipe(user)
   
        di = await self.get_designinstance(user)

        logger.info(f'di = {di}')
        logger.info(f'     {di.d["behavior"]}')
        logger.info(f'     {di.d["behavior"].quantity}')

        d = await di.get_design(user)

        logger.info(f'd  = {d}')
        logger.info(f'     {d.d.get("unit")}')

        q0 = await di.quantity_demand(user)

        q1 = r.quantity(d)
  
        q2 = -q0 / q1 * (await d.conversion(q0.unit, q1.unit))

        if not weaver.quantity.unit.unit_eq(q2.unit, None):
            logger.error(repr(q2.unit))
            raise Exception("recipeinstance quantity should have no units")

        return q2
        

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

class Engine(weaver.engine.EngineGlobal):
    def __init__(self, manager, coll, e_queries):
        super().__init__(manager, coll, "master", e_queries)
        self._doc_class = RecipeInstance

    async def get_test_object(self, user, b0={}):

        recipe = await self.manager.e_recipes.get_test_object(user)

        b1 = {
            "recipe": recipe.freeze(),
            #"mode": DesignInstanceMode.INVENTORY.value,
            #"quantity": weaver.quantity.Quantity(1, design.d.get("unit")),
            }

        b1.update(b0)

        b = await self._doc_class.get_test_document(b1)

        o = await self.put(user, None, b)

        return o

    def pipe0(self, user):

        yield from super().pipe0(user)

        return

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


