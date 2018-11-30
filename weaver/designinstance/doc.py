import copy
import datetime
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
    # design has been ordered and will arrive and be added to inventory in the future
    # should have an 'arrival' field
    ORDER          = 3

class Behavior:
    def __init__(self, doc):
        self.doc = doc

    async def quantity_inventory(self, user):
        raise NotImplementedError()

class BehaviorInventory(Behavior):

    async def quantity_inventory(self, user):
        return self.doc.d["quantity"]

    async def check(self):
        if not isinstance(self.doc.d["design"], elephant.ref.DocRef): raise TypeError()
        if not isinstance(self.doc.d["quantity"], weaver.quantity.Quantity): raise TypeError()

class BehaviorDemand(Behavior):

    async def quantity_inventory(self, user):
        raise NotImplementedError()

    async def check(self):
        if not isinstance(self.doc.d["design"], elephant.ref.DocRef): raise TypeError()
        if not isinstance(self.doc.d["quantity"], weaver.quantity.Quantity): raise TypeError()

class BehaviorOrder(Behavior):

    async def quantity_inventory(self, user):
        raise NotImplementedError()

    async def check(self):
        if not isinstance(self.doc.d["quantity"], weaver.quantity.Quantity): raise TypeError()
        if not isinstance(self.doc.d["arrival"], datetime.datetime): raise TypeError()

class BehaviorRecipeInstance(Behavior):

    async def quantity_order(self, user):
        return self.doc.d["quantity"]

    async def check(self):
        if not isinstance(self.doc.d["recipeinstance_for"], elephant.ref.DocRef): raise TypeError()
        #if not isinstance(self.doc.d["quantity"], weaver.quantity.Quantity): raise TypeError()

class DesignInstance(elephant.global_.doc.Doc):
    """
    types identified by fields present

    'design'             - reference to the design
    'recipeinstance_for' - this was created as one of the materials for a recipeinstance
    'quantity'           - this was created manually to originate demand
    'recipeinstance'     - a recipeinstance created to produce this
    'quantity_actual'    - actual quantity in inventory
    """
    def __init__(self, e, d, _d, *args, **kwargs):
        super().__init__(e, d, _d, *args, **kwargs)
        self.d['_collection'] = 'weaver designinstances'

    def behavior(self):
        return {
                DesignInstanceMode.INVENTORY:      BehaviorInventory(self),
                DesignInstanceMode.DEMAND:         BehaviorDemand(self),
                DesignInstanceMode.RECIPEINSTANCE: BehaviorRecipeInstance(self),
                DesignInstanceMode.ORDER:          BehaviorOrder(self),
                }[DesignInstanceMode(self.d["mode"])]

    async def check(self):
        await self.check_0()
        await self.behavior().check()

    @classmethod
    async def get_test_document(self, b0={}):
        """
        because a design reference is required, cannot create test document
        without actual database context
        """
        b1 = {}
        b1.update(b0)
        return await super().get_test_document(b1)

    async def check_0(self):
        DesignInstanceMode(self.d["mode"])

    async def update_temp(self, user):
        await super().update_temp(user)
        

        self.d["_temp"]["design"] = await self.get_design(user)


    async def quantity_recipeinstance_for(self, user):

        d = await self.get_design(user)

        ri = await self.get_recipeinstance_for(user)

        if not (await ri.is_planned(user)):
            logger.info('DI demand type 1 not planned')
            print('DI demand type 1 not planned')
            return weaver.quantity.Quantity(0, d.d.get("unit"))

        r  = await ri.get_recipe(user)

        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

        u0 = d.d.get("unit", None)
        u1 = q.unit

        pprint.pprint(d.d)

        print("u0", u0)
        print("u1", u1)

        assert (u1 is None) or isinstance(u1, weaver.quantity.unit.BaseUnit)

        assert weaver.quantity.unit.unit_eq(u0, u1)

        return q        

    async def quantity_demand(self, user):
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        d  = await self.get_design(user)
        u0 = d.d.get("unit", None)
        assert (u0 is None) or isinstance(u0, weaver.quantity.unit.BaseUnit)

        if 'quantity' in self.d:
            # type 0
            logger.debug(f'DI demand type 0. q = {self.d["quantity"]}')

            q = self.d['quantity']
            q = q * (await d.conversion(q.unit, u0))

            print("assert equal")
            print(u0)
            print(q.unit)

            if not weaver.quantity.unit.unit_eq(u0, q.unit):
                raise Exception(f"Units must be equal. {u0!s} and {q.unit!s}")
            return q

        return await self.quantity_recipeinstance_for(user)

    async def cost(self, user):

        if 'recipeinstance' in self.d:
            ri = await self.get_recipeinstance(user)
            return await ri.cost(user)

        d = await self.get_design(user)

        if "cost" in d.d:
            return d.d["cost"]

        return 0

    async def quantity_inventory(self, user):

        return await self.behavior().quantity_inventory(user)
        
        assert not (('quantity' in self.d) and ('recipeinstance_for' in self.d))

        if 'quantity' in self.d:
            # type 0
            return 0

        # type 1
        ri = await self.get_recipeinstance_for(user)

        if ri.d.get('status', None) != weaver.recipeinstance.Status.COMPLETE:
            return 0

        # TODO instead of the following, consider creating INVENTORY mode design 
        # instance upon recipeinstance completion

        r  = await ri.get_recipe(user)

        d  = await self.get_design(user)

        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

        return q        

    async def get_recipeinstance_for(self, user):
        if 'recipeinstance_for' not in self.d: return

        d0 = await self.e.manager.e_recipeinstances.find_one_by_ref(
                user,
                self.d['recipeinstance_for'],
                )

        assert d0 is not None
  
        return d0

    async def get_recipeinstance(self, user):
        if 'recipeinstance' not in self.d: return

        d0 = await self.e.manager.e_recipeinstances.find_one_by_ref(
                user,
                self.d['recipeinstance'],
                )

        assert d0 is not None
  
        return d0

    async def get_design(self, user):
        #if 'design' not in self.d: return

        logger.debug((
                f'designinstance get design '
                f'{str(self.d["design"]._id)[-4:]} '
                f'{str(self.d["design"].ref)[-4:]} '
                ))

        d0 = await self.e.manager.e_designs.find_one(
                user,
                self.d['design'].ref,
                {"_id": self.d['design']._id})

        assert d0 is not None

        assert \
                d0.d["_elephant"]["ref"] == self.d['design'].ref or \
                d0.d["_elephant"]["refs"][d0.d["_elephant"]["ref"]] == self.d['design'].ref
 
        return d0

    async def set_recipe(self, user, ref_recipe):

        d1 = await self.e.manager.e_recipes.find_one(
                user,
                ref_recipe.ref,
                {'_id': ref_recipe._id},
                )
        
        logger.debug(f'recipe: {d1!r}')

        ri = await self.e.manager.e_recipeinstances.put(
                user,
                None,
                {
                    "recipe":         ref_recipe,
                    "designinstance": self.freeze(),
                    "status":         weaver.recipeinstance.Status.PLANNED.value,
                },
                )
                    
        logger.debug(f'recipeinstance: {ri!r}')

        self.d["recipeinstance"] = ri.freeze()
        await self.put(user)

        return ri

    async def to_array(self):
        d = dict(self.d)
        return d

    def subobject(self):
        o = copy.deepcopy(self)
        o.is_subobject = True
        if "design" in self.d["_temp"]:
            del self.d["_temp"]["design"]
        return o







