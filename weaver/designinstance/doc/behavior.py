import elephant
import weaver.quantity

class Behavior:

    @classmethod
    async def decode(cls, h, args):
        args = await h.decode(args)
        return cls(*args)

    def __init__(self, doc):
        self.doc = doc

    async def quantity_inventory(self, user):
        return None

    async def quantity_order(self, user, *args):
        return None

    async def quantity_demand(self, user):
        return None

    async def quantity_recipeinstance_for(self, *args):
        return None

class BehaviorInventory(Behavior):

    def __init__(self, quantity):
        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError()
        
        self.quantity = quantity

    async def quantity_inventory(self, user):
        return self.quantity

    async def __encode__(self, h, user, mode):
        if mode == elephant.EncodeMode.DATABASE:
            args = [self.quantity]

        elif mode == elephant.EncodeMode.CLIENT:
            args = [self.quantity]

        return {'WeaverDesigninstanceBehaviorInventory': await elephant.util.encode(h, user, mode, args)}


class BehaviorDemand(Behavior):

    def __init__(self, quantity):
        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError(f'expected Quantity not {type(quantity)}')
        
        self.quantity = quantity

    async def quantity_demand(self, user):
        return self.quantity

    async def __encode__(self, h, user, mode):
        if mode == elephant.EncodeMode.DATABASE:
            args = [self.quantity]

        elif mode == elephant.EncodeMode.CLIENT:
            args = [self.quantity]

        return {'WeaverDesigninstanceBehaviorDemand': await elephant.util.encode(h, user, mode, args)}

class BehaviorOrder(Behavior):

    def __init__(self, quantity, arrival):
        if not isinstance(quantity, weaver.quantity.Quantity):
            raise TypeError()
 
        if not ((arrival is None) or isinstance(arrival, datetime.datetime)):
            raise TypeError()
       
        self.quantity = quantity
        self.arrival = arrival


    async def quantity_order(self, user):
        if self.arrival is not None:
            if self.arrival > when:
                return None

        return self.quantity

class BehaviorRecipeinstance(Behavior):
    """
    Designinstance was created as ingredient for recipeinstance
    """

    def __init__(self, recipeinstance_for):
        if not isinstance(recipeinstance_for, elephant.ref.DocRef):
            raise TypeError()

        self.recipeinstance_for = recipeinstance_for

    async def quantity_recipeinstance_for(self, user, recipeinstance_before):

        

        ri = await self.doc.get_recipeinstance_for(user)

        if recipeinstance_before is not None:
            if ri.d.get("when", now) > recipeinstance_before:
                return None

        d = await self.doc.get_design(user)

        if ri is None:
            return weaver.quantity.Quantity(0, d.d.get("unit"))
           
        if not (await ri.is_planned(user)):
            logger.info('DI demand type 1 not planned')
            return weaver.quantity.Quantity(0, d.d.get("unit"))

        r  = await ri.get_recipe(user)

        q_r = await ri.quantity(user)

        q_m = r.quantity(d)

        q = q_r * q_m

        u0 = d.d.get("unit", None)

        # convert to the design units
        q = q * (await d.conversion(q.unit, u0))

        u1 = q.unit

        logger.info("u0", u0)
        logger.info("u1", u1)

        assert (u1 is None) or isinstance(u1, weaver.quantity.unit.BaseUnit)

        if not weaver.quantity.unit.unit_eq(u0, u1):
            raise Exception(f'design unit ({u0!s}) does not equal ingredient unit ({u1!s})')

        return q        

    async def __encode__(self, h, user, mode):
        if mode == elephant.EncodeMode.DATABASE:
            args = [self.recipeinstance_for]

        elif mode == elephant.EncodeMode.CLIENT:
            args = [self.recipeinstance_for]

        return {'WeaverDesigninstanceBehaviorRecipeinstance': await elephant.util.encode(h, user, mode, args)}









