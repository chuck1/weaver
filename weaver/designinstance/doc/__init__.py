import copy
import datetime
import enum
import logging
import pprint

import pymongo

import elephant.local_
import weaver.recipeinstance
from .behavior import *

logger = logging.getLogger(__name__)

    # created to represent actual inventory
    #INVENTORY      = 0
    # created as ingredient for recipeinstance
    #RECIPEINSTANCE = 1
    # created to create demand without a recipeinstance or an on-hand quantity
    #DEMAND         = 2
    # design has been ordered and will arrive and be added to inventory in the future
    # should have an 'arrival' field
    #ORDER          = 3


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

    def init1(self):
        self.d["behavior"].doc = self

    async def check(self):
        await self.check_0()

        if not isinstance(self.d["design"], elephant.ref.DocRef):
            raise TypeError()

        if not isinstance(self.d["behavior"], weaver.designinstance.doc.behavior.Behavior):
            raise TypeError(f'expected Behavior not {type(self.d["behavior"])}')

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
        #DesignInstanceMode(self.d["mode"])
        pass

    async def update_temp(self, user):
        await super().update_temp(user)

        self.d["_temp"]["design"] = await self.get_design(user, temp=False)

    async def quantity_demand(self, user):
    
        self.init1()
    
        d  = await self.get_design(user)

        if isinstance(self.d["behavior"], BehaviorDemand):
            y = await self.d["behavior"].quantity_demand(user)
            y = y * await d.conversion(y.unit, d.d.get("unit"))
            return y

        if isinstance(self.d["behavior"], BehaviorRecipeinstance):
            y = await self.d["behavior"].quantity_recipeinstance_for(user)
            y = y * await d.conversion(y.unit, d.d.get("unit"))
            return y

    async def cost(self, user):

        if 'recipeinstance' in self.d:
            ri = await self.get_recipeinstance(user)
            return await ri.cost(user)

        d = await self.get_design(user)

        if "cost" in d.d:
            return d.d["cost"]

        return 0

    async def get_recipeinstance_for(self, user):
        if not isinstance(self.d["behavior"], BehaviorRecipeinstance):
            raise Exception()

        d0 = await self.e.manager.e_recipeinstances.find_one_by_ref(
                user,
                self.d["behavior"].recipeinstance_for,
                )

        if d0 is None:
            # recipeinstance might have been deleted
            return None

        return d0

    async def get_recipeinstance(self, user):
        if 'recipeinstance' not in self.d: return

        d0 = await self.e.manager.e_recipeinstances.find_one_by_ref(
                user,
                self.d['recipeinstance'],
                )

        assert d0 is not None
  
        return d0

    async def get_design(self, user, temp=True):
        """
        temp (bool) - include "_temp" field in returned object
        """

        #if 'design' not in self.d: return

        logger.debug((
                f'designinstance get design '
                f'{str(self.d["design"]._id)[-4:]} '
                f'{str(self.d["design"].ref)[-4:]} '
                ))

        d0 = await self.e.manager.e_designs.find_one(
                user,
                self.d['design'].ref,
                {"_id": self.d['design']._id},
                temp=temp,
                )

        assert d0 is not None

        assert \
                d0.d["_elephant"]["ref"] == self.d['design'].ref or \
                d0.d["_elephant"]["refs"][d0.d["_elephant"]["ref"]] == self.d['design'].ref
 
        return d0

    async def set_recipe(self, user, ref_recipe):

        d1 = await self.e.manager.e_recipes.find_one_by_ref(
                user,
                ref_recipe,
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







